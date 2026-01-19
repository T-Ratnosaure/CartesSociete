"""Lapin-focused strategy player.

This player implements a Lapin swarm strategy:
- Prioritizes buying Lapin family cards
- Values Lapincruste highly for board expansion
- Builds towards family threshold bonuses
- Floods the board with cheap Lapins
"""

from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.cards.models import Card
    from src.game.state import GameState, PlayerState

from src.cards.models import Family

from .action import Action, ActionType
from .base import Player, PlayerInfo


class LapinPlayer(Player):
    """Player implementing Lapin swarm strategy.

    Strategy overview:
    1. Early game: Buy any Lapin cards, especially cheap ones
    2. Mid game: Prioritize Lapincruste for board expansion
    3. Late game: Flood the board with Lapins for massive combined damage

    The strategy exploits:
    - Lapincruste: +2/+4 extra Lapin slots on board
    - Family thresholds: +1 slot at 3 Lapins, +2 at 5 Lapins
    - Cheap Lapins: Cost 1-2 cards that add up to big total damage

    Attributes:
        lapin_priority: How much to weight Lapin cards (default 5.0).
        lapincruste_priority: Extra weight for Lapincruste (default 10.0).
        evolution_weight: Weight for evolution potential (default 3.0).
    """

    def __init__(
        self,
        player_id: int,
        name: str | None = None,
        lapin_priority: float = 5.0,
        lapincruste_priority: float = 10.0,
        evolution_weight: float = 3.0,
    ) -> None:
        """Initialize the Lapin strategy player.

        Args:
            player_id: The player's ID.
            name: Optional display name.
            lapin_priority: Weight for Lapin family cards (default 5.0).
            lapincruste_priority: Extra weight for Lapincruste (default 10.0).
            evolution_weight: Weight for evolution potential (default 3.0).
        """
        super().__init__(player_id, name)
        self.lapin_priority = lapin_priority
        self.lapincruste_priority = lapincruste_priority
        self.evolution_weight = evolution_weight

        # Track evolution candidates
        self._evolution_targets: set[str] = set()

    @property
    def info(self) -> PlayerInfo:
        """Return metadata about this player agent."""
        return PlayerInfo(
            name=self._name or f"lapin_{self.player_id}",
            agent_type="lapin",
            version="1.0.0",
        )

    def on_game_start(self, state: "GameState") -> None:
        """Reset tracking at game start."""
        self._evolution_targets.clear()

    def _count_lapins(self, player_state: "PlayerState") -> int:
        """Count Lapin cards on board and in hand.

        Args:
            player_state: Current player state.

        Returns:
            Total Lapin count.
        """
        return sum(
            1
            for c in player_state.board + player_state.hand
            if c.family == Family.LAPIN
        )

    def _count_lapins_on_board(self, player_state: "PlayerState") -> int:
        """Count Lapin cards on board only.

        Args:
            player_state: Current player state.

        Returns:
            Lapin count on board.
        """
        return sum(1 for c in player_state.board if c.family == Family.LAPIN)

    def _has_lapincruste(self, player_state: "PlayerState") -> bool:
        """Check if we have Lapincruste on board.

        Args:
            player_state: Current player state.

        Returns:
            True if Lapincruste is on board.
        """
        for card in player_state.board:
            if card.family == Family.LAPIN and card.bonus_text:
                if "lapins supplémentaires" in card.bonus_text.lower():
                    return True
        return False

    def _is_lapincruste(self, card: "Card") -> bool:
        """Check if a card is Lapincruste.

        Args:
            card: The card to check.

        Returns:
            True if the card is Lapincruste.
        """
        if card.family != Family.LAPIN:
            return False
        if card.bonus_text and "lapins supplémentaires" in card.bonus_text.lower():
            return True
        return False

    def _get_evolution_candidates(
        self,
        player_state: "PlayerState",
    ) -> dict[str, int]:
        """Get cards we're close to evolving.

        Args:
            player_state: Current player state.

        Returns:
            Dict mapping card name to count.
        """
        name_counts: Counter[str] = Counter()
        for card in player_state.hand + player_state.board:
            if card.level == 1:
                name_counts[card.name] += 1
        return dict(name_counts)

    def _evaluate_card_for_market(
        self,
        card: "Card",
        player_state: "PlayerState",
        state: "GameState",
    ) -> float:
        """Evaluate a card for purchase with Lapin strategy focus.

        Args:
            card: The card to evaluate.
            player_state: Current player state.
            state: Current game state.

        Returns:
            Evaluation score (higher = better to buy).
        """
        # Base value: stats + cost efficiency
        base_value = (card.attack + card.health) / max(card.cost or 1, 1)
        score = base_value

        # EARLY GAME ADAPTATION: No cost-1 Lapins exist!
        # In early turns, buy efficient non-Lapin cards to not fall behind
        lapin_count = self._count_lapins(player_state)
        is_early_game = state.turn <= 2 and lapin_count == 0

        # LAPIN PRIORITY: Heavily weight Lapin family cards
        if card.family == Family.LAPIN:
            score += self.lapin_priority

            # Extra bonus for Lapincruste (board expansion)
            if self._is_lapincruste(card):
                # Lapincruste is CRITICAL if we don't have one yet
                if not self._has_lapincruste(player_state):
                    score += self.lapincruste_priority * 2
                else:
                    # Still good to have more
                    score += self.lapincruste_priority

            # Bonus for cheap Lapins (cost 2) - core of swarm strategy
            if card.cost is not None and card.cost <= 2:
                score += 3.0

            # Synergy bonus based on existing Lapins
            if lapin_count >= 1:
                score += lapin_count * 0.5  # Each Lapin makes more Lapins better

        # Evolution potential for Lapin cards
        evolution_candidates = self._get_evolution_candidates(player_state)
        if card.name in evolution_candidates:
            count = evolution_candidates[card.name]
            if count == 2:
                # This completes evolution!
                score += 8.0 * self.evolution_weight
            elif count == 1:
                score += 2.0 * self.evolution_weight

        # Non-Lapin cards handling
        if card.family != Family.LAPIN:
            if is_early_game:
                # EARLY GAME: Accept good non-Lapin cards to not fall behind
                # Prioritize cost-efficient cards that establish board presence
                if card.cost is not None and card.cost <= 2:
                    # Cheap cards are okay in early game
                    efficiency = (card.attack + card.health) / card.cost
                    if efficiency >= 2.0:  # At least 2 stats per PO
                        score += 2.0  # Bonus for efficient early cards
                    # Extra bonus for high-attack cards
                    if card.attack >= 3:
                        score += 1.0
            else:
                # MID/LATE GAME: Penalty for off-strategy cards
                score -= 2.0

                # But high-stat cards are still okay as fillers
                if card.attack + card.health >= 6:
                    score += 1.0

        return score

    def _evaluate_card_for_play(
        self,
        card: "Card",
        player_state: "PlayerState",
        state: "GameState",
    ) -> float:
        """Evaluate a card for playing to board.

        Args:
            card: The card to evaluate.
            player_state: Current player state.
            state: Current game state.

        Returns:
            Play priority score (higher = play first).
        """
        score = float(card.attack + card.health)

        # Prioritize playing Lapincruste FIRST (enables more Lapins)
        if self._is_lapincruste(card):
            score += 20.0  # Very high priority

        # Prioritize Lapin cards
        if card.family == Family.LAPIN:
            score += 5.0

            # Bonus for cheap Lapins
            if card.cost is not None and card.cost <= 2:
                score += 2.0

        return score

    def choose_market_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose market action with Lapin focus.

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

        # Score each card
        scored = [
            (a, self._evaluate_card_for_market(a.card, player_state, state))
            for a in buy_actions
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        best_action, best_score = scored[0]

        # If no good Lapin options and we have decent board, save PO
        lapin_in_market = any(
            a.card.family == Family.LAPIN for a in buy_actions if a.card is not None
        )

        if not lapin_in_market and best_score < 3.0:
            # No Lapins available and non-Lapin cards are meh
            # Save PO for next turn
            if self._count_lapins_on_board(player_state) >= 3:
                return Action.end_phase()

        return best_action

    def choose_play_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose play action prioritizing Lapin board flood.

        Args:
            state: Current game state.
            player_state: This player's state.
            legal_actions: Available actions.

        Returns:
            The chosen play action.
        """
        # First check for evolution opportunities (especially Lapin evolutions)
        evolve_actions = [
            a for a in legal_actions if a.action_type == ActionType.EVOLVE
        ]
        if evolve_actions:
            # Prefer Lapin evolutions
            lapin_evolves = [
                a
                for a in evolve_actions
                if a.evolve_cards and a.evolve_cards[0].family == Family.LAPIN
            ]
            if lapin_evolves:
                return lapin_evolves[0]
            return evolve_actions[0]

        # Play actions
        play_actions = [
            a
            for a in legal_actions
            if a.action_type == ActionType.PLAY_CARD and a.card is not None
        ]

        if not play_actions:
            # Check for weapon equipping
            equip_actions = [
                a for a in legal_actions if a.action_type == ActionType.EQUIP_WEAPON
            ]
            if equip_actions:
                # Prefer equipping to Lapin cards
                lapin_equips = [
                    a
                    for a in equip_actions
                    if a.target_card and a.target_card.family == Family.LAPIN
                ]
                if lapin_equips:
                    return lapin_equips[0]
                return equip_actions[0]

            return Action.end_phase()

        # Score play actions
        scored = [
            (a, self._evaluate_card_for_play(a.card, player_state, state))
            for a in play_actions
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored[0][0]
