"""Cyborg-focused strategy player.

This player implements a Cyborg aggression strategy:
- Prioritizes buying Cyborg family cards
- Values Invocateurs for demon summoning
- Exploits Archer and Berserk class synergies
- Aggressive damage output with health trade-offs
"""

from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.cards.models import Card
    from src.game.state import GameState, PlayerState

from src.cards.models import CardClass, Family

from .action import Action, ActionType
from .base import Player, PlayerInfo


class CyborgPlayer(Player):
    """Player implementing Cyborg aggression strategy.

    Strategy overview:
    1. Early game: Buy cheap Cyborgs (Steamtroopers, Berserkers)
    2. Mid game: Build towards Archer/Berserk thresholds for damage scaling
    3. Late game: Summon demons via Invocateurs at 3/6 Cyborg thresholds

    The strategy exploits:
    - Hydra Steam summoned at 3 Cyborgs
    - Dragon Steam summoned at 6 Cyborgs
    - Archer class: +4/+7/+10 damage vs Defenders
    - Berserk class: +5/+10 damage for -2/-5 health trade-off
    """

    def __init__(
        self,
        player_id: int,
        name: str | None = None,
        cyborg_priority: float = 5.0,
        invocateur_priority: float = 8.0,
        archer_priority: float = 4.0,
        berserk_priority: float = 3.0,
    ) -> None:
        """Initialize the Cyborg strategy player."""
        super().__init__(player_id, name)
        self.cyborg_priority = cyborg_priority
        self.invocateur_priority = invocateur_priority
        self.archer_priority = archer_priority
        self.berserk_priority = berserk_priority

    @property
    def info(self) -> PlayerInfo:
        """Return metadata about this player agent."""
        return PlayerInfo(
            name=self._name or f"cyborg_{self.player_id}",
            agent_type="cyborg",
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

    def _is_invocateur(self, card: "Card") -> bool:
        """Check if a card is an Invocateur."""
        return card.card_class == CardClass.INVOCATEUR

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
        """Evaluate a card for purchase with Cyborg aggression focus."""
        base_value = (card.attack + card.health) / max(card.cost or 1, 1)
        score = base_value

        cyborg_count = self._count_family(player_state, Family.CYBORG)

        # CYBORG PRIORITY
        if card.family == Family.CYBORG:
            score += self.cyborg_priority

            # Extra bonus for Invocateurs (demon summoning)
            if self._is_invocateur(card):
                if cyborg_count >= 2:  # Close to threshold
                    score += self.invocateur_priority * 2
                else:
                    score += self.invocateur_priority

            # Bonus for cheap Cyborgs
            if card.cost is not None and card.cost <= 2:
                score += 3.0

            # Synergy bonus based on existing Cyborgs
            if cyborg_count >= 1:
                score += cyborg_count * 0.5

            # Threshold proximity bonus
            if cyborg_count == 2:  # About to hit 3
                score += 4.0
            elif cyborg_count == 5:  # About to hit 6
                score += 6.0

        # Class bonuses (work across families)
        if card.card_class == CardClass.ARCHER:
            archer_count = self._count_class(player_state, CardClass.ARCHER)
            score += self.archer_priority
            if archer_count >= 2:  # Approaching threshold
                score += 3.0

        if card.card_class == CardClass.BERSERK:
            score += self.berserk_priority
            # Berserks are high-risk high-reward
            if card.attack >= 4:
                score += 2.0

        # Evolution potential
        evolution_candidates = self._get_evolution_candidates(player_state)
        if card.name in evolution_candidates:
            count = evolution_candidates[card.name]
            if count == 2:
                score += 8.0
            elif count == 1:
                score += 2.0

        # Non-Cyborg penalty in mid/late game
        if card.family != Family.CYBORG and cyborg_count >= 2:
            score -= 2.0
            # But high-attack cards are still okay
            if card.attack >= 4:
                score += 1.5

        return score

    def _evaluate_card_for_play(
        self,
        card: "Card",
        player_state: "PlayerState",
        state: "GameState",
    ) -> float:
        """Evaluate a card for playing to board."""
        score = float(card.attack + card.health)

        # Prioritize Cyborg cards
        if card.family == Family.CYBORG:
            score += 5.0

        # High attack cards are priority for aggro
        score += card.attack * 0.5

        # Invocateurs enable demon summons
        if self._is_invocateur(card):
            score += 8.0

        return score

    def choose_market_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose market action with Cyborg aggression focus."""
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
        """Choose play action prioritizing Cyborg aggression."""
        # Check for evolution opportunities
        evolve_actions = [
            a for a in legal_actions if a.action_type == ActionType.EVOLVE
        ]
        if evolve_actions:
            cyborg_evolves = [
                a
                for a in evolve_actions
                if a.evolve_cards and a.evolve_cards[0].family == Family.CYBORG
            ]
            if cyborg_evolves:
                return cyborg_evolves[0]
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
