"""Atlantide-focused strategy player.

This player implements an Atlantide healing/sustain strategy:
- Prioritizes buying Atlantide family cards
- Values end-of-turn health regeneration
- Exploits Archer synergies for damage
- Outlasts opponents through superior sustain
"""

from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.cards.models import Card
    from src.game.state import GameState, PlayerState

from src.cards.models import CardClass, Family

from .action import Action, ActionType
from .base import Player, PlayerInfo


class AtlantidePlayer(Player):
    """Player implementing Atlantide healing sustain strategy.

    Strategy overview:
    1. Early game: Build Archer count for defender-dependent damage
    2. Mid game: Stack Atlantides for healing/sustain thresholds
    3. Late game: Outlast opponents through regeneration while dealing steady damage

    The strategy exploits:
    - Family ability: +4/+8/+13 PV at end of turn at 2/4/6 Atlantides
    - Archer class: +4/+7/+10 damage vs Defenders
    - Envouteur class: +1/+2/+3 damage to all monsters
    """

    def __init__(
        self,
        player_id: int,
        name: str | None = None,
        atlantide_priority: float = 5.0,
        archer_priority: float = 4.0,
        envouteur_priority: float = 3.0,
        health_weight: float = 1.5,
    ) -> None:
        """Initialize the Atlantide strategy player."""
        super().__init__(player_id, name)
        self.atlantide_priority = atlantide_priority
        self.archer_priority = archer_priority
        self.envouteur_priority = envouteur_priority
        self.health_weight = health_weight

    @property
    def info(self) -> PlayerInfo:
        """Return metadata about this player agent."""
        return PlayerInfo(
            name=self._name or f"atlantide_{self.player_id}",
            agent_type="atlantide",
            version="1.0.0",
        )

    def _count_family(self, player_state: "PlayerState", family: Family) -> int:
        """Count cards of a family on board and in hand."""
        return sum(
            1 for c in player_state.board + player_state.hand if c.family == family
        )

    def _count_class(self, player_state: "PlayerState", card_class: CardClass) -> int:
        """Count cards of a class on board."""
        return sum(1 for c in player_state.board if c.card_class == card_class)

    def _get_evolution_candidates(self, player_state: "PlayerState") -> dict[str, int]:
        """Get cards we're close to evolving."""
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
        """Evaluate a card for purchase with Atlantide sustain focus."""
        # For sustain strategy, health is weighted more
        base_value = (card.attack + card.health * self.health_weight) / max(
            card.cost or 1, 1
        )
        score = base_value

        atlantide_count = self._count_family(player_state, Family.ATLANTIDE)
        archer_count = self._count_class(player_state, CardClass.ARCHER)

        # ATLANTIDE PRIORITY
        if card.family == Family.ATLANTIDE:
            score += self.atlantide_priority

            # Threshold proximity bonus for healing
            if atlantide_count == 1:  # About to hit 2 (+4 PV/turn)
                score += 4.0
            elif atlantide_count == 3:  # About to hit 4 (+8 PV/turn)
                score += 6.0
            elif atlantide_count == 5:  # About to hit 6 (+13 PV/turn)
                score += 8.0

            # Synergy bonus
            score += atlantide_count * 0.5

            # High health Atlantides are extra valuable
            if card.health >= 4:
                score += 2.0

        # ARCHER PRIORITY - damage vs Defenders
        if card.card_class == CardClass.ARCHER:
            score += self.archer_priority
            if archer_count >= 2:
                score += 3.0

        # ENVOUTEUR PRIORITY - buffs all monsters
        if card.card_class == CardClass.ENVOUTEUR:
            score += self.envouteur_priority
            # More valuable with more cards on board
            board_size = len(player_state.board)
            score += board_size * 0.3

        # High health cards are valued in sustain strategy
        if card.health >= 5:
            score += 2.0

        # Evolution potential
        evolution_candidates = self._get_evolution_candidates(player_state)
        if card.name in evolution_candidates:
            count = evolution_candidates[card.name]
            if count == 2:
                score += 8.0
            elif count == 1:
                score += 2.0

        # Non-Atlantide penalty in mid/late game
        if card.family != Family.ATLANTIDE and atlantide_count >= 2:
            score -= 2.0
            # But high-health cards are still okay
            if card.health >= 4:
                score += 1.5

        return score

    def _evaluate_card_for_play(
        self,
        card: "Card",
        player_state: "PlayerState",
        state: "GameState",
    ) -> float:
        """Evaluate a card for playing to board."""
        score = float(card.attack + card.health * self.health_weight)

        # Prioritize Atlantide cards
        if card.family == Family.ATLANTIDE:
            score += 5.0

        # High health cards are priority
        score += card.health * 0.5

        # Archers for damage
        if card.card_class == CardClass.ARCHER:
            score += 4.0

        return score

    def choose_market_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose market action with Atlantide sustain focus."""
        buy_actions = [
            a
            for a in legal_actions
            if a.action_type == ActionType.BUY_CARD and a.card is not None
        ]

        if not buy_actions:
            return Action.end_phase()

        scored = [
            (a, self._evaluate_card_for_market(a.card, player_state, state))
            for a in buy_actions
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored[0][0]

    def choose_play_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose play action prioritizing Atlantide sustain strategy."""
        # Check for evolution opportunities
        evolve_actions = [
            a for a in legal_actions if a.action_type == ActionType.EVOLVE
        ]
        if evolve_actions:
            atlantide_evolves = [
                a
                for a in evolve_actions
                if a.evolve_cards and a.evolve_cards[0].family == Family.ATLANTIDE
            ]
            if atlantide_evolves:
                return atlantide_evolves[0]
            return evolve_actions[0]

        # Play actions
        play_actions = [
            a
            for a in legal_actions
            if a.action_type == ActionType.PLAY_CARD and a.card is not None
        ]

        if not play_actions:
            equip_actions = [
                a for a in legal_actions if a.action_type == ActionType.EQUIP_WEAPON
            ]
            if equip_actions:
                return equip_actions[0]
            return Action.end_phase()

        scored = [
            (a, self._evaluate_card_for_play(a.card, player_state, state))
            for a in play_actions
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored[0][0]
