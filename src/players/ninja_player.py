"""Ninja-focused strategy player.

This player implements a Ninja economy/replay strategy:
- Prioritizes buying Ninja family cards
- Values Economes for PO generation
- Exploits card replay mechanics at thresholds
- Builds towards turn efficiency and resource multiplication
"""

from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.cards.models import Card
    from src.game.state import GameState, PlayerState

from src.cards.models import CardClass, Family

from .action import Action, ActionType
from .base import Player, PlayerInfo


class NinjaPlayer(Player):
    """Player implementing Ninja economy/replay strategy.

    Strategy overview:
    1. Early game: Buy cheap Ninjas + Economes for PO generation
    2. Mid game: Accumulate Ninjas to unlock replay mechanic at 3/5
    3. Late game: Replay high-value cards for multiplied effects

    The strategy exploits:
    - Family ability: Select a Ninja to replay at 3 Ninjas, replay 2 at 5 Ninjas
    - Econome class: +1 PO per turn passive
    - Forgeron class: Draw 1/2/3 weapons at thresholds
    """

    def __init__(
        self,
        player_id: int,
        name: str | None = None,
        ninja_priority: float = 5.0,
        econome_priority: float = 6.0,
        forgeron_priority: float = 4.0,
    ) -> None:
        """Initialize the Ninja strategy player."""
        super().__init__(player_id, name)
        self.ninja_priority = ninja_priority
        self.econome_priority = econome_priority
        self.forgeron_priority = forgeron_priority

    @property
    def info(self) -> PlayerInfo:
        """Return metadata about this player agent."""
        return PlayerInfo(
            name=self._name or f"ninja_{self.player_id}",
            agent_type="ninja",
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
        """Evaluate a card for purchase with Ninja economy focus."""
        base_value = (card.attack + card.health) / max(card.cost or 1, 1)
        score = base_value

        ninja_count = self._count_family(player_state, Family.NINJA)
        econome_count = self._count_class(player_state, CardClass.ECONOME)

        # NINJA PRIORITY
        if card.family == Family.NINJA:
            score += self.ninja_priority

            # Threshold proximity bonus for replay mechanic
            if ninja_count == 2:  # About to hit 3 (replay 1 Ninja)
                score += 5.0
            elif ninja_count == 4:  # About to hit 5 (replay 2 Ninjas)
                score += 7.0

            # Synergy bonus
            score += ninja_count * 0.5

            # Cheap Ninjas build count faster
            if card.cost is not None and card.cost <= 2:
                score += 2.0

        # ECONOME PRIORITY - PO generation is key
        if card.card_class == CardClass.ECONOME:
            score += self.econome_priority
            # Early economes are more valuable
            if state.turn <= 3:
                score += 3.0
            # Stacking economes multiplies PO
            score += econome_count * 1.0
            # Ninja Economes are even better
            if card.family == Family.NINJA:
                score += 2.0

        # FORGERON PRIORITY - weapon draws
        if card.card_class == CardClass.FORGERON:
            score += self.forgeron_priority
            forgeron_count = self._count_class(player_state, CardClass.FORGERON)
            if forgeron_count >= 2:
                score += 3.0

        # Evolution potential
        evolution_candidates = self._get_evolution_candidates(player_state)
        if card.name in evolution_candidates:
            count = evolution_candidates[card.name]
            if count == 2:
                score += 8.0
            elif count == 1:
                score += 2.0

        # Non-Ninja penalty in mid/late game
        if card.family != Family.NINJA and ninja_count >= 2:
            score -= 2.0
            # But Economes and Forgerons are always welcome
            if card.card_class in (CardClass.ECONOME, CardClass.FORGERON):
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

        # Prioritize Ninja cards
        if card.family == Family.NINJA:
            score += 5.0

        # Economes first for PO generation
        if card.card_class == CardClass.ECONOME:
            score += 8.0

        # Forgerons for weapon draws
        if card.card_class == CardClass.FORGERON:
            score += 5.0

        return score

    def choose_market_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose market action with Ninja economy focus."""
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
        """Choose play action prioritizing Ninja economy strategy."""
        # Check for evolution opportunities
        evolve_actions = [
            a for a in legal_actions if a.action_type == ActionType.EVOLVE
        ]
        if evolve_actions:
            ninja_evolves = [
                a
                for a in evolve_actions
                if a.evolve_cards and a.evolve_cards[0].family == Family.NINJA
            ]
            if ninja_evolves:
                return ninja_evolves[0]
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
                # Prefer equipping to Ninja cards
                ninja_equips = [
                    a
                    for a in equip_actions
                    if a.target_card and a.target_card.family == Family.NINJA
                ]
                if ninja_equips:
                    return ninja_equips[0]
                return equip_actions[0]
            return Action.end_phase()

        scored = [
            (a, self._evaluate_card_for_play(a.card, player_state, state))
            for a in play_actions
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored[0][0]
