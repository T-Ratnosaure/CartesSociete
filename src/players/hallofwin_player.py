"""Hall of Win-focused strategy player.

This player implements a Hall of Win variance/gambling strategy:
- Prioritizes buying Hall of Win family cards
- Accepts high variance from coin flip mechanics
- Values healing synergies to offset bad flips
- Exploits Monture card draw for high-cost cards
"""

from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.cards.models import Card
    from src.game.state import GameState, PlayerState

from src.cards.models import CardClass, Family

from .action import Action, ActionType
from .base import Player, PlayerInfo


class HallOfWinPlayer(Player):
    """Player implementing Hall of Win variance strategy.

    Strategy overview:
    1. Early game: Accept variance, build basic board
    2. Mid game: Stack Hall of Win cards to average out coin flip volatility
    3. Late game: Leverage healing from coin flip successes + card draw

    The strategy exploits:
    - Family ability (Passive): Coin flip each turn
      - Heads: +11/+18 damage at thresholds
      - Tails: -5/-7 health at thresholds
    - Envouteur class: +1/+2/+3 damage to all monsters
    - Monture class: Draw cost-5 cards at threshold 3
    - Healing: Chauve Sourire gains health equal to damage dealt
    """

    def __init__(
        self,
        player_id: int,
        name: str | None = None,
        hallofwin_priority: float = 5.0,
        envouteur_priority: float = 4.0,
        monture_priority: float = 5.0,
        healing_priority: float = 4.0,
    ) -> None:
        """Initialize the Hall of Win strategy player."""
        super().__init__(player_id, name)
        self.hallofwin_priority = hallofwin_priority
        self.envouteur_priority = envouteur_priority
        self.monture_priority = monture_priority
        self.healing_priority = healing_priority

    @property
    def info(self) -> PlayerInfo:
        """Return metadata about this player agent."""
        return PlayerInfo(
            name=self._name or f"hallofwin_{self.player_id}",
            agent_type="hallofwin",
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

    def _has_healing(self, card: "Card") -> bool:
        """Check if a card has healing mechanics."""
        if card.bonus_text:
            text = card.bonus_text.lower()
            return "pv" in text and ("gagne" in text or "récupère" in text)
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
        """Evaluate a card for purchase with Hall of Win variance focus."""
        base_value = (card.attack + card.health) / max(card.cost or 1, 1)
        score = base_value

        hallofwin_count = self._count_family(player_state, Family.HALL_OF_WIN)

        # HALL OF WIN PRIORITY
        if card.family == Family.HALL_OF_WIN:
            score += self.hallofwin_priority

            # More Hall of Win cards = more consistent variance
            # (multiple coin flips average out)
            score += hallofwin_count * 0.8

            # High health helps survive bad flips
            if card.health >= 4:
                score += 2.0

        # ENVOUTEUR PRIORITY - buffs all monsters
        if card.card_class == CardClass.ENVOUTEUR:
            score += self.envouteur_priority
            envouteur_count = self._count_class(player_state, CardClass.ENVOUTEUR)
            # More valuable with more cards on board
            board_size = len(player_state.board)
            score += board_size * 0.3
            if envouteur_count >= 2:
                score += 3.0

        # MONTURE PRIORITY - draws high-cost cards
        if card.card_class == CardClass.MONTURE:
            score += self.monture_priority
            monture_count = self._count_class(player_state, CardClass.MONTURE)
            if monture_count >= 2:  # Approaching threshold 3
                score += 4.0

        # HEALING PRIORITY - offsets bad coin flips
        if self._has_healing(card):
            score += self.healing_priority
            # Healing is more valuable with more variance
            if hallofwin_count >= 2:
                score += 2.0

        # High health cards help survive variance
        if card.health >= 5:
            score += 1.5

        # Evolution potential
        evolution_candidates = self._get_evolution_candidates(player_state)
        if card.name in evolution_candidates:
            count = evolution_candidates[card.name]
            if count == 2:
                score += 8.0
            elif count == 1:
                score += 2.0

        # Non-Hall of Win penalty in mid/late game (less strict)
        if card.family != Family.HALL_OF_WIN and hallofwin_count >= 2:
            score -= 1.5
            # But healing and Envouteurs are always welcome
            if self._has_healing(card) or card.card_class == CardClass.ENVOUTEUR:
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

        # Prioritize Hall of Win cards
        if card.family == Family.HALL_OF_WIN:
            score += 5.0

        # High health cards first (survive variance)
        score += card.health * 0.5

        # Envouteurs buff the board
        if card.card_class == CardClass.ENVOUTEUR:
            score += 5.0

        # Healing cards are priority
        if self._has_healing(card):
            score += 4.0

        return score

    def choose_market_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose market action with Hall of Win variance focus."""
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
        """Choose play action prioritizing Hall of Win variance strategy."""
        # Check for evolution opportunities
        evolve_actions = [
            a for a in legal_actions if a.action_type == ActionType.EVOLVE
        ]
        if evolve_actions:
            hallofwin_evolves = [
                a
                for a in evolve_actions
                if a.evolve_cards and a.evolve_cards[0].family == Family.HALL_OF_WIN
            ]
            if hallofwin_evolves:
                return hallofwin_evolves[0]
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
