"""Control archetype strategy player.

This player implements a defensive stability strategy
independent of family identity.

Strategy Intent:
    Maximize survivability and board resilience. Win by outlasting
    opponents through superior defensive positioning and health pools.

Decision Priorities:
    1. High PV (health) cards over high ATK cards
    2. Protecteur and Defenseur classes for damage mitigation
    3. Healing effects and sustain mechanics
    4. Board stability over aggressive plays

Known Blind Spots:
    - May lose to sustained damage over time
    - Slow to establish board presence
    - Vulnerable to imblocable damage
    - Does not value economy generation
    - May be too passive against scaling strategies
"""

from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.cards.models import Card
    from src.game.state import GameState, PlayerState

from src.cards.models import CardClass

from .action import Action, ActionType
from .base import Player, PlayerInfo


class ControlPlayer(Player):
    """Player implementing defensive stability strategy.

    This is an analytical probe agent that prioritizes survivability
    and defensive capabilities over damage output. It aims to outlast
    opponents through superior health pools.

    The agent behaves as if: "Not dying is winning."

    Attributes:
        health_weight: How much to weight PV in evaluations (default 3.0).
        protecteur_priority: Extra value for Protecteur class (default 6.0).
        defenseur_priority: Extra value for Defenseur class (default 5.0).
        healing_priority: Extra value for healing effects (default 4.0).
    """

    def __init__(
        self,
        player_id: int,
        name: str | None = None,
        health_weight: float = 3.0,
        protecteur_priority: float = 6.0,
        defenseur_priority: float = 5.0,
        healing_priority: float = 4.0,
    ) -> None:
        """Initialize the Control strategy player.

        Args:
            player_id: The player's ID.
            name: Optional display name.
            health_weight: Weight multiplier for PV values.
            protecteur_priority: Extra value for Protecteur class.
            defenseur_priority: Extra value for Defenseur class.
            healing_priority: Extra value for healing effects.
        """
        super().__init__(player_id, name)
        self.health_weight = health_weight
        self.protecteur_priority = protecteur_priority
        self.defenseur_priority = defenseur_priority
        self.healing_priority = healing_priority

    @property
    def info(self) -> PlayerInfo:
        """Return metadata about this player agent."""
        return PlayerInfo(
            name=self._name or f"control_{self.player_id}",
            agent_type="control",
            version="1.0.0",
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
        """Evaluate a card for purchase with defensive focus.

        Prioritizes:
        - High PV values (heavily weighted)
        - Protecteur class for damage redirection
        - Defenseur class for blocking
        - Healing effects

        De-prioritizes:
        - Low health glass cannons
        - Risky trade-off cards (Berserks)
        """
        # Health is king for control
        score = card.health * self.health_weight

        # Minimal weight for attack (only for tie-breaking)
        score += card.attack * 0.3

        # Cost efficiency based on health
        cost = card.cost or 1
        health_per_po = card.health / max(cost, 1)
        score += health_per_po * 1.5

        # Protecteur class: redirects damage, protects board
        if card.card_class == CardClass.PROTECTEUR:
            score += self.protecteur_priority
            # More valuable with cards to protect
            board_size = len(player_state.board)
            score += board_size * 0.5

        # Defenseur class: blocks attacks
        if card.card_class == CardClass.DEFENSEUR:
            score += self.defenseur_priority
            defenseur_count = self._count_class(player_state, CardClass.DEFENSEUR)
            # Stacking Defenseurs increases blocking
            score += defenseur_count * 1.0

        # Healing effects
        if self._has_healing(card):
            score += self.healing_priority

        # High health cards are premium
        if card.health >= 5:
            score += 3.0
        elif card.health >= 4:
            score += 1.5

        # Penalty for glass cannons (high ATK, low PV)
        if card.attack > card.health * 2:
            score -= 2.0

        # Penalty for Berserk (trades health - anti-control)
        if card.card_class == CardClass.BERSERK:
            score -= 3.0

        # Evolution potential (prefer health-gaining evolutions)
        evolution_candidates = self._get_evolution_candidates(player_state)
        if card.name in evolution_candidates:
            count = evolution_candidates[card.name]
            if count == 2:
                score += card.health * 1.5
            elif count == 1:
                score += card.health * 0.5

        # Envouteur class: buffs all monsters (defensive utility)
        if card.card_class == CardClass.ENVOUTEUR:
            score += 2.0

        return score

    def _evaluate_card_for_play(
        self,
        card: "Card",
        player_state: "PlayerState",
        state: "GameState",
    ) -> float:
        """Evaluate a card for playing to board.

        Play priority emphasizes defensive positioning.
        """
        # Health is primary metric
        score = card.health * self.health_weight

        # Protecteurs first to protect existing board
        if card.card_class == CardClass.PROTECTEUR:
            score += self.protecteur_priority + 5.0

        # Defenseurs for blocking
        if card.card_class == CardClass.DEFENSEUR:
            score += self.defenseur_priority

        # Healing cards are priority
        if self._has_healing(card):
            score += self.healing_priority

        # High health cards establish board stability
        if card.health >= 5:
            score += 4.0

        return score

    def choose_market_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose market action with defensive focus.

        Prioritizes high-health and defensive cards.
        May pass on low-health options.
        """
        buy_actions = [
            a
            for a in legal_actions
            if a.action_type == ActionType.BUY_CARD and a.card is not None
        ]

        if not buy_actions:
            return Action.end_phase()

        # Score and sort by control value
        scored = [
            (a, self._evaluate_card_for_market(a.card, player_state, state))
            for a in buy_actions
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        best_action, best_score = scored[0]

        # Control may pass on low-health cards
        if best_action.card and best_action.card.health <= 2:
            if best_score < 5.0:
                return Action.end_phase()

        return best_action

    def choose_play_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose play action prioritizing defensive positioning.

        Play Protecteurs first, then high-health cards.
        """
        # Check for evolution opportunities
        evolve_actions = [
            a for a in legal_actions if a.action_type == ActionType.EVOLVE
        ]
        if evolve_actions:
            # Prefer evolving high-health cards
            best_evolve = max(
                evolve_actions,
                key=lambda a: (a.evolve_result.health if a.evolve_result else 0),
            )
            return best_evolve

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
                # Prefer equipping to high-health cards (keep them alive)
                best_equip = max(
                    equip_actions,
                    key=lambda a: (a.target_card.health if a.target_card else 0),
                )
                return best_equip
            return Action.end_phase()

        # Score and play best defensive card
        scored = [
            (a, self._evaluate_card_for_play(a.card, player_state, state))
            for a in play_actions
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored[0][0]
