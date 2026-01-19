"""Neige-focused strategy player.

This player implements a Neige economy engine strategy:
- Prioritizes buying Neige family cards
- Values PO generation and free card draws
- Exploits Combattant attack scaling
- Builds resource advantage for late game dominance
"""

from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.cards.models import Card
    from src.game.state import GameState, PlayerState

from src.cards.models import CardClass, Family

from .action import Action, ActionType
from .base import Player, PlayerInfo


class NeigePlayer(Player):
    """Player implementing Neige economy engine strategy.

    Strategy overview:
    1. Early game: Stack Economes for PO/card generation
    2. Mid game: Build Combattants for aggressive scaling
    3. Late game: Use free cards + PO to flood board with Combattants

    The strategy exploits:
    - Family ability: +1 PO/turn at 2 Neige; free card/turn at 4 Neige
    - Combattant class: +3/+7/+8 ATQ scaling (with -1 PV trade-off)
    - Mage class: Cast spells twice at threshold 3
    """

    def __init__(
        self,
        player_id: int,
        name: str | None = None,
        neige_priority: float = 5.0,
        econome_priority: float = 6.0,
        combattant_priority: float = 5.0,
        mage_priority: float = 4.0,
    ) -> None:
        """Initialize the Neige strategy player."""
        super().__init__(player_id, name)
        self.neige_priority = neige_priority
        self.econome_priority = econome_priority
        self.combattant_priority = combattant_priority
        self.mage_priority = mage_priority

    @property
    def info(self) -> PlayerInfo:
        """Return metadata about this player agent."""
        return PlayerInfo(
            name=self._name or f"neige_{self.player_id}",
            agent_type="neige",
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
        """Evaluate a card for purchase with Neige economy focus."""
        base_value = (card.attack + card.health) / max(card.cost or 1, 1)
        score = base_value

        neige_count = self._count_family(player_state, Family.NEIGE)
        combattant_count = self._count_class(player_state, CardClass.COMBATTANT)

        # NEIGE PRIORITY
        if card.family == Family.NEIGE:
            score += self.neige_priority

            # Threshold proximity bonus
            if neige_count == 1:  # About to hit 2 (+1 PO/turn)
                score += 4.0
            elif neige_count == 3:  # About to hit 4 (free card/turn)
                score += 7.0
            elif neige_count == 5:  # About to hit 6 (+1 Kdo)
                score += 5.0

            # Synergy bonus
            score += neige_count * 0.5

            # Cheap Neige cards build count faster
            if card.cost is not None and card.cost <= 2:
                score += 2.0

        # ECONOME PRIORITY
        if card.card_class == CardClass.ECONOME:
            score += self.econome_priority
            if state.turn <= 3:
                score += 3.0
            # Neige Economes are extra valuable
            if card.family == Family.NEIGE:
                score += 2.0

        # COMBATTANT PRIORITY - aggressive scaling
        if card.card_class == CardClass.COMBATTANT:
            score += self.combattant_priority
            # More Combattants = better scaling
            score += combattant_count * 1.0
            # High attack Combattants are valuable
            if card.attack >= 3:
                score += 2.0

        # MAGE PRIORITY - spell doubling
        if card.card_class == CardClass.MAGE:
            mage_count = self._count_class(player_state, CardClass.MAGE)
            score += self.mage_priority
            if mage_count >= 2:  # Approaching threshold 3
                score += 3.0

        # Evolution potential
        evolution_candidates = self._get_evolution_candidates(player_state)
        if card.name in evolution_candidates:
            count = evolution_candidates[card.name]
            if count == 2:
                score += 8.0
            elif count == 1:
                score += 2.0

        # Non-Neige penalty in mid/late game
        if card.family != Family.NEIGE and neige_count >= 2:
            score -= 2.0
            # But Economes and Combattants are welcome
            if card.card_class in (CardClass.ECONOME, CardClass.COMBATTANT):
                score += 2.0

        return score

    def _evaluate_card_for_play(
        self,
        card: "Card",
        player_state: "PlayerState",
        state: "GameState",
    ) -> float:
        """Evaluate a card for playing to board."""
        score = float(card.attack + card.health)

        # Prioritize Neige cards
        if card.family == Family.NEIGE:
            score += 5.0

        # Economes first for PO generation
        if card.card_class == CardClass.ECONOME:
            score += 8.0

        # Combattants for damage
        if card.card_class == CardClass.COMBATTANT:
            score += card.attack * 0.5 + 3.0

        return score

    def choose_market_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose market action with Neige economy focus."""
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
        """Choose play action prioritizing Neige economy strategy."""
        # Check for evolution opportunities
        evolve_actions = [
            a for a in legal_actions if a.action_type == ActionType.EVOLVE
        ]
        if evolve_actions:
            neige_evolves = [
                a
                for a in evolve_actions
                if a.evolve_cards and a.evolve_cards[0].family == Family.NEIGE
            ]
            if neige_evolves:
                return neige_evolves[0]
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
