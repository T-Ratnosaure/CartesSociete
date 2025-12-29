"""Heuristic player with rule-based strategy.

This player implements sophisticated strategy including:
- Evolution tracking and prioritization
- Family synergy building
- Threat assessment
- Resource management
"""

from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.cards.models import Card
    from src.game.state import GameState, PlayerState

from .action import Action, ActionType
from .base import Player, PlayerInfo
from .evaluation import (
    calculate_family_synergy,
    evaluate_card_for_play,
    evaluate_card_for_purchase,
)


class HeuristicPlayer(Player):
    """Player with sophisticated rule-based strategy.

    Implements multiple strategic considerations:
    1. Evolution tracking - prioritizes completing evolutions
    2. Family synergy - builds cohesive family boards
    3. Threat assessment - considers opponent board states
    4. Resource management - efficient PO usage

    Attributes:
        evolution_weight: Weight for evolution potential scoring.
        synergy_weight: Weight for family synergy scoring.
        aggression: Multiplier for offensive vs defensive play.
    """

    def __init__(
        self,
        player_id: int,
        name: str | None = None,
        evolution_weight: float = 2.0,
        synergy_weight: float = 1.5,
        aggression: float = 1.0,
    ) -> None:
        """Initialize the heuristic player.

        Args:
            player_id: The player's ID.
            name: Optional display name.
            evolution_weight: Weight for evolution potential (default 2.0).
            synergy_weight: Weight for family synergy (default 1.5).
            aggression: Multiplier for offensive vs defensive play (default 1.0).
        """
        super().__init__(player_id, name)
        self.evolution_weight = evolution_weight
        self.synergy_weight = synergy_weight
        self.aggression = aggression

        # Track cards we're collecting for evolution
        self._evolution_targets: set[str] = set()

    @property
    def info(self) -> PlayerInfo:
        """Return metadata about this player agent."""
        return PlayerInfo(
            name=self._name or f"heuristic_{self.player_id}",
            agent_type="heuristic",
            version="1.0.0",
        )

    def on_game_start(self, state: "GameState") -> None:
        """Reset tracking at game start."""
        self._evolution_targets.clear()

    def _get_evolution_candidates(
        self,
        player_state: "PlayerState",
    ) -> dict[str, int]:
        """Get cards we're close to evolving.

        Args:
            player_state: Current player state.

        Returns:
            Dict mapping card name to count (cards with count >= 2 are priorities).
        """
        name_counts: Counter[str] = Counter()
        for card in player_state.hand + player_state.board:
            if card.level == 1:
                name_counts[card.name] += 1
        return dict(name_counts)

    def _should_save_po(
        self,
        player_state: "PlayerState",
        state: "GameState",
    ) -> bool:
        """Determine if we should save PO for next turn.

        Args:
            player_state: Current player state.
            state: Current game state.

        Returns:
            True if saving PO is strategically better.
        """
        # Save PO if close to evolution and might see the card next turn
        evolution_candidates = self._get_evolution_candidates(player_state)
        for name, count in evolution_candidates.items():
            if count == 2:
                # We need one more card to evolve - consider saving
                return player_state.po >= 2  # Save at least some PO
        return False

    def _evaluate_for_market(
        self,
        card: "Card",
        player_state: "PlayerState",
        state: "GameState",
    ) -> float:
        """Enhanced card evaluation for market phase.

        Args:
            card: The card to evaluate.
            player_state: Current player state.
            state: Current game state.

        Returns:
            Evaluation score.
        """
        base_score = evaluate_card_for_purchase(card, player_state, state)

        # Bonus for evolution targets
        evolution_candidates = self._get_evolution_candidates(player_state)
        if card.name in evolution_candidates:
            count = evolution_candidates[card.name]
            # Huge bonus if this completes evolution
            if count == 2:
                base_score += 10.0 * self.evolution_weight
            elif count == 1:
                base_score += 3.0 * self.evolution_weight

        # Track if we're starting to collect this card
        if card.level == 1:
            current_count = evolution_candidates.get(card.name, 0)
            if current_count == 0:
                # First copy - small bonus for high-value evolution targets
                if card.attack + card.health >= 5:
                    base_score += 1.0

        # Family synergy with weight
        base_score += calculate_family_synergy(card, player_state) * self.synergy_weight

        # Aggression adjustment
        base_score += card.attack * (self.aggression - 1.0) * 0.5

        return base_score

    def choose_market_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose market action with evolution and synergy awareness.

        Args:
            state: Current game state.
            player_state: This player's state.
            legal_actions: Available actions.

        Returns:
            The chosen market action.
        """
        buy_actions = [
            a
            for a in legal_actions
            if a.action_type == ActionType.BUY_CARD and a.card is not None
        ]

        if not buy_actions:
            return Action.end_phase()

        # Score each option with enhanced evaluation
        scored = [
            (a, self._evaluate_for_market(a.card, player_state, state))
            for a in buy_actions
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        best_action, best_score = scored[0]

        # Check if we should save PO instead
        if self._should_save_po(player_state, state) and best_score < 8.0:
            # Low-value buy - consider ending phase early
            if player_state.po > 3:  # Keep some buffer
                return Action.end_phase()

        return best_action

    def choose_play_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose play action prioritizing board development.

        Args:
            state: Current game state.
            player_state: This player's state.
            legal_actions: Available actions.

        Returns:
            The chosen play action.
        """
        # First check for evolution opportunities
        evolve_actions = [
            a for a in legal_actions if a.action_type == ActionType.EVOLVE
        ]
        if evolve_actions:
            # Always evolve if possible
            return evolve_actions[0]

        play_actions = [
            a
            for a in legal_actions
            if a.action_type == ActionType.PLAY_CARD and a.card is not None
        ]

        if not play_actions:
            # Check for beneficial replacements
            replace_actions = [
                a for a in legal_actions if a.action_type == ActionType.REPLACE_CARD
            ]
            if replace_actions:
                # Evaluate replacements
                best_replace = self._choose_best_replace(
                    replace_actions, player_state, state
                )
                if best_replace:
                    return best_replace

            return Action.end_phase()

        # Score play actions
        scored = [
            (a, evaluate_card_for_play(a.card, player_state, state))
            for a in play_actions
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored[0][0]

    def _choose_best_replace(
        self,
        replace_actions: list[Action],
        player_state: "PlayerState",
        state: "GameState",
    ) -> Action | None:
        """Choose the best replacement if beneficial.

        Args:
            replace_actions: Available replace actions.
            player_state: Current player state.
            state: Current game state.

        Returns:
            Best replace action, or None if no beneficial replacement.
        """
        best_action: Action | None = None
        best_improvement = 0.0

        for action in replace_actions:
            if action.card is None or action.target_card is None:
                continue

            new_value = evaluate_card_for_play(action.card, player_state, state)
            old_value = evaluate_card_for_play(action.target_card, player_state, state)
            improvement = new_value - old_value

            if improvement > best_improvement:
                best_improvement = improvement
                best_action = action

        # Only replace if there's meaningful improvement
        if best_improvement > 1.0:
            return best_action
        return None
