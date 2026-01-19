"""Nature-focused strategy player.

This player implements a Nature imblocable damage strategy:
- Prioritizes buying Nature family cards
- Values Economes for PO generation
- Exploits imblocable (unblockable) damage scaling
- Builds towards guaranteed damage output
"""

from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.cards.models import Card
    from src.game.state import GameState, PlayerState

from src.cards.models import CardClass, Family

from .action import Action, ActionType
from .base import Player, PlayerInfo


class NaturePlayer(Player):
    """Player implementing Nature imblocable damage strategy.

    Strategy overview:
    1. Early game: Stack Economes for PO generation
    2. Mid game: Build towards 4-6 Nature cards for damage scaling
    3. Late game: Use accumulated PO to play high-cost Dragons with imblocable

    The strategy exploits:
    - Family ability: +2/+5/+8 imblocable damage at 2/4/6 Nature cards
    - Econome class: +1 PO per turn passive
    - Dragon class: Conditional imblocable damage with PO spending
    """

    def __init__(
        self,
        player_id: int,
        name: str | None = None,
        nature_priority: float = 5.0,
        econome_priority: float = 6.0,
        dragon_priority: float = 7.0,
    ) -> None:
        """Initialize the Nature strategy player."""
        super().__init__(player_id, name)
        self.nature_priority = nature_priority
        self.econome_priority = econome_priority
        self.dragon_priority = dragon_priority

    @property
    def info(self) -> PlayerInfo:
        """Return metadata about this player agent."""
        return PlayerInfo(
            name=self._name or f"nature_{self.player_id}",
            agent_type="nature",
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
        """Evaluate a card for purchase with Nature imblocable focus."""
        base_value = (card.attack + card.health) / max(card.cost or 1, 1)
        score = base_value

        nature_count = self._count_family(player_state, Family.NATURE)
        econome_count = self._count_class(player_state, CardClass.ECONOME)

        # NATURE PRIORITY
        if card.family == Family.NATURE:
            score += self.nature_priority

            # Threshold proximity bonus for imblocable damage
            if nature_count == 1:  # About to hit 2
                score += 3.0
            elif nature_count == 3:  # About to hit 4
                score += 5.0
            elif nature_count == 5:  # About to hit 6
                score += 7.0

            # Synergy bonus
            score += nature_count * 0.4

        # ECONOME PRIORITY - PO generation is key
        if card.card_class == CardClass.ECONOME:
            score += self.econome_priority
            # Early economes are more valuable
            if state.turn <= 3:
                score += 3.0
            # Stacking economes multiplies PO
            score += econome_count * 1.0

        # DRAGON PRIORITY - high imblocable damage dealers
        if card.card_class == CardClass.DRAGON:
            score += self.dragon_priority
            # Dragons are better with existing Nature cards
            if nature_count >= 2:
                score += 4.0

        # Evolution potential
        evolution_candidates = self._get_evolution_candidates(player_state)
        if card.name in evolution_candidates:
            count = evolution_candidates[card.name]
            if count == 2:
                score += 8.0
            elif count == 1:
                score += 2.0

        # Non-Nature penalty in mid/late game
        if card.family != Family.NATURE and nature_count >= 2:
            score -= 2.0
            # But Economes are always welcome
            if card.card_class == CardClass.ECONOME:
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

        # Prioritize Nature cards
        if card.family == Family.NATURE:
            score += 5.0

        # Economes first for PO generation
        if card.card_class == CardClass.ECONOME:
            score += 8.0

        # Dragons are finishers
        if card.card_class == CardClass.DRAGON:
            score += 6.0

        return score

    def choose_market_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose market action with Nature imblocable focus."""
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
        """Choose play action prioritizing Nature imblocable strategy."""
        # Check for evolution opportunities
        evolve_actions = [
            a for a in legal_actions if a.action_type == ActionType.EVOLVE
        ]
        if evolve_actions:
            nature_evolves = [
                a
                for a in evolve_actions
                if a.evolve_cards and a.evolve_cards[0].family == Family.NATURE
            ]
            if nature_evolves:
                return nature_evolves[0]
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
