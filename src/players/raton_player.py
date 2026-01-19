"""Raton-focused strategy player.

This player implements a Raton linear scaling strategy:
- Prioritizes buying Raton family cards
- Values the +1 ATQ/+1 PV per Raton scaling
- Exploits Dragon conditional abilities with PO
- Can counter Econome-based opponents with Ecraseur
"""

from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.cards.models import Card
    from src.game.state import GameState, PlayerState

from src.cards.models import CardClass, Family

from .action import Action, ActionType
from .base import Player, PlayerInfo


class RatonPlayer(Player):
    """Player implementing Raton linear scaling strategy.

    Strategy overview:
    1. Early game: Buy mid-cost Ratons to start scaling
    2. Mid game: Reach threshold bonuses for +ATQ/+PV scaling
    3. Late game: Dragons with PO-conditional abilities + predatory Ecraseur

    The strategy exploits:
    - Family ability: +1 ATQ/+1 PV per Raton at 2/3/6 thresholds
    - Dragon class: Conditional scaling with PO spending
    - Ecraseur: Gains +1 ATQ per enemy Econome (predatory)
    """

    def __init__(
        self,
        player_id: int,
        name: str | None = None,
        raton_priority: float = 5.0,
        dragon_priority: float = 6.0,
        mage_priority: float = 4.0,
    ) -> None:
        """Initialize the Raton strategy player."""
        super().__init__(player_id, name)
        self.raton_priority = raton_priority
        self.dragon_priority = dragon_priority
        self.mage_priority = mage_priority

    @property
    def info(self) -> PlayerInfo:
        """Return metadata about this player agent."""
        return PlayerInfo(
            name=self._name or f"raton_{self.player_id}",
            agent_type="raton",
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

    def _is_ecraseur(self, card: "Card") -> bool:
        """Check if a card is an Ecraseur (predatory card)."""
        if card.bonus_text:
            return "econome" in card.bonus_text.lower()
        return False

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
        """Evaluate a card for purchase with Raton scaling focus."""
        base_value = (card.attack + card.health) / max(card.cost or 1, 1)
        score = base_value

        raton_count = self._count_family(player_state, Family.RATON)

        # RATON PRIORITY
        if card.family == Family.RATON:
            score += self.raton_priority

            # Threshold proximity bonus for scaling
            if raton_count == 1:  # About to hit 2
                score += 3.0
            elif raton_count == 2:  # About to hit 3
                score += 4.0
            elif raton_count == 5:  # About to hit 6
                score += 6.0

            # Synergy bonus - each Raton makes more valuable
            score += raton_count * 0.6

            # Ecraseur is situationally powerful
            if self._is_ecraseur(card):
                score += 3.0

        # DRAGON PRIORITY - conditional abilities with PO
        if card.card_class == CardClass.DRAGON:
            score += self.dragon_priority
            # Dragons are better with more Ratons
            if raton_count >= 2:
                score += 3.0
            # High attack Dragons are finishers
            if card.attack >= 4:
                score += 2.0

        # MAGE PRIORITY - spell doubling
        if card.card_class == CardClass.MAGE:
            mage_count = self._count_class(player_state, CardClass.MAGE)
            score += self.mage_priority
            if mage_count >= 2:
                score += 3.0

        # High stat cards are valued in scaling strategy
        total_stats = card.attack + card.health
        if total_stats >= 6:
            score += 1.5

        # Evolution potential
        evolution_candidates = self._get_evolution_candidates(player_state)
        if card.name in evolution_candidates:
            count = evolution_candidates[card.name]
            if count == 2:
                score += 8.0
            elif count == 1:
                score += 2.0

        # Non-Raton penalty in mid/late game
        if card.family != Family.RATON and raton_count >= 2:
            score -= 2.0
            # But Dragons are always valuable
            if card.card_class == CardClass.DRAGON:
                score += 3.0

        return score

    def _evaluate_card_for_play(
        self,
        card: "Card",
        player_state: "PlayerState",
        state: "GameState",
    ) -> float:
        """Evaluate a card for playing to board."""
        score = float(card.attack + card.health)

        # Prioritize Raton cards
        if card.family == Family.RATON:
            score += 5.0

        # High attack cards
        score += card.attack * 0.5

        # Dragons are finishers
        if card.card_class == CardClass.DRAGON:
            score += 6.0

        # Ecraseur for predatory advantage
        if self._is_ecraseur(card):
            score += 4.0

        return score

    def choose_market_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose market action with Raton scaling focus."""
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
        """Choose play action prioritizing Raton scaling strategy."""
        # Check for evolution opportunities
        evolve_actions = [
            a for a in legal_actions if a.action_type == ActionType.EVOLVE
        ]
        if evolve_actions:
            raton_evolves = [
                a
                for a in evolve_actions
                if a.evolve_cards and a.evolve_cards[0].family == Family.RATON
            ]
            if raton_evolves:
                return raton_evolves[0]
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
