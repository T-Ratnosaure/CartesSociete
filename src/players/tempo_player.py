"""Tempo archetype strategy player.

This player implements an economy/action-efficiency strategy
independent of family identity.

Strategy Intent:
    Maximize PO generation and action efficiency. Win by accumulating
    more resources and playing more cards over time than opponents.

Decision Priorities:
    1. Econome class cards for PO generation
    2. Forgeron class for card draw (weapons)
    3. Cost-efficient cards (high stats per PO)
    4. Future flexibility over immediate impact

Known Blind Spots:
    - May fall behind in early damage races
    - Vulnerable to aggressive strategies
    - Economy advantages don't help if dead
    - Does not value defensive capabilities
    - May over-invest in economy when board presence is needed
"""

from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.cards.models import Card
    from src.game.state import GameState, PlayerState

from src.cards.models import CardClass

from .action import Action, ActionType
from .base import Player, PlayerInfo


class TempoPlayer(Player):
    """Player implementing economy/action-efficiency strategy.

    This is an analytical probe agent that prioritizes PO generation
    and turn efficiency over immediate damage output. It aims to
    out-resource opponents over time.

    The agent behaves as if: "More actions over time will win the game."

    Attributes:
        econome_priority: How much to weight Econome cards (default 8.0).
        forgeron_priority: How much to weight Forgeron cards (default 5.0).
        efficiency_weight: Bonus for cost-efficient cards (default 2.0).
        early_game_turns: Turns considered "early game" (default 3).
    """

    def __init__(
        self,
        player_id: int,
        name: str | None = None,
        econome_priority: float = 8.0,
        forgeron_priority: float = 5.0,
        efficiency_weight: float = 2.0,
        early_game_turns: int = 3,
    ) -> None:
        """Initialize the Tempo strategy player.

        Args:
            player_id: The player's ID.
            name: Optional display name.
            econome_priority: Weight for Econome class cards.
            forgeron_priority: Weight for Forgeron class cards.
            efficiency_weight: Bonus for cost-efficient cards.
            early_game_turns: Number of turns considered early game.
        """
        super().__init__(player_id, name)
        self.econome_priority = econome_priority
        self.forgeron_priority = forgeron_priority
        self.efficiency_weight = efficiency_weight
        self.early_game_turns = early_game_turns

    @property
    def info(self) -> PlayerInfo:
        """Return metadata about this player agent."""
        return PlayerInfo(
            name=self._name or f"tempo_{self.player_id}",
            agent_type="tempo",
            version="1.0.0",
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
        """Evaluate a card for purchase with tempo/economy focus.

        Prioritizes:
        - Econome class for PO generation
        - Forgeron class for card draw
        - Cost efficiency (stats per PO)
        - Cards that enable future actions

        De-prioritizes:
        - Expensive cards that consume resources
        - Cards with no scaling potential
        """
        cost = card.cost or 1
        total_stats = card.attack + card.health

        # Base: cost efficiency (stats per PO)
        efficiency = total_stats / max(cost, 1)
        score = efficiency * self.efficiency_weight

        # Econome class: PO generation is the core of tempo
        if card.card_class == CardClass.ECONOME:
            score += self.econome_priority
            econome_count = self._count_class(player_state, CardClass.ECONOME)
            # Stacking Economes compounds PO advantage
            score += econome_count * 2.0
            # Early Economes are more valuable (more turns to generate PO)
            if state.turn <= self.early_game_turns:
                score += 4.0

        # Forgeron class: card draw = more options
        if card.card_class == CardClass.FORGERON:
            score += self.forgeron_priority
            forgeron_count = self._count_class(player_state, CardClass.FORGERON)
            # Approaching threshold for more draws
            if forgeron_count >= 2:
                score += 3.0

        # Mage class: spell doubling is action multiplication
        if card.card_class == CardClass.MAGE:
            mage_count = self._count_class(player_state, CardClass.MAGE)
            score += 3.0
            if mage_count >= 2:
                score += 4.0  # Approaching threshold

        # Cheap cards = deploy faster, spend less
        if cost <= 2:
            score += 3.0
        elif cost <= 3:
            score += 1.5

        # High-cost cards are risky for tempo (consume resources)
        if cost >= 5:
            score -= 2.0

        # Evolution potential
        evolution_candidates = self._get_evolution_candidates(player_state)
        if card.name in evolution_candidates:
            count = evolution_candidates[card.name]
            if count == 2:
                score += 6.0  # Evolutions are efficient
            elif count == 1:
                score += 2.0

        # Slight bonus for balanced stats (flexible)
        if abs(card.attack - card.health) <= 1:
            score += 1.0

        return score

    def _evaluate_card_for_play(
        self,
        card: "Card",
        player_state: "PlayerState",
        state: "GameState",
    ) -> float:
        """Evaluate a card for playing to board.

        Play priority emphasizes economy generators and enablers.
        """
        score = float(card.attack + card.health)

        # Economes first - start generating PO immediately
        if card.card_class == CardClass.ECONOME:
            score += 10.0

        # Forgerons for card advantage
        if card.card_class == CardClass.FORGERON:
            score += 7.0

        # Mages for action multiplication
        if card.card_class == CardClass.MAGE:
            score += 5.0

        # Cheap cards are tempo-positive
        cost = card.cost or 1
        if cost <= 2:
            score += 2.0

        return score

    def choose_market_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose market action with tempo/economy focus.

        Prioritizes Economes and efficient cards.
        May save PO if no good tempo options available.
        """
        buy_actions = [
            a
            for a in legal_actions
            if a.action_type == ActionType.BUY_CARD and a.card is not None
        ]

        if not buy_actions:
            return Action.end_phase()

        # Score and sort by tempo value
        scored = [
            (a, self._evaluate_card_for_market(a.card, player_state, state))
            for a in buy_actions
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        best_action, best_score = scored[0]

        # Tempo may save PO if options are poor
        # (unlike Aggro which always buys)
        econome_count = self._count_class(player_state, CardClass.ECONOME)
        if best_score < 4.0 and econome_count >= 2:
            # Already have economy, save for better options
            return Action.end_phase()

        return best_action

    def choose_play_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose play action prioritizing economy generators.

        Play Economes and Forgerons first to maximize resource generation.
        """
        # Check for evolution opportunities
        evolve_actions = [
            a for a in legal_actions if a.action_type == ActionType.EVOLVE
        ]
        if evolve_actions:
            # Prefer evolving economy cards
            econome_evolves = [
                a
                for a in evolve_actions
                if a.evolve_cards and a.evolve_cards[0].card_class == CardClass.ECONOME
            ]
            if econome_evolves:
                return econome_evolves[0]
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

        # Score and play best tempo card
        scored = [
            (a, self._evaluate_card_for_play(a.card, player_state, state))
            for a in play_actions
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored[0][0]
