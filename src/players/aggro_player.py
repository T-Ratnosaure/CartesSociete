"""Aggro archetype strategy player.

This player implements an aggressive damage-maximization strategy
independent of family identity.

Strategy Intent:
    Maximize damage output per turn. Win quickly by overwhelming
    opponents with immediate board presence and high attack values.

Decision Priorities:
    1. High ATK cards over high PV cards
    2. Low-cost cards for faster board development
    3. Immediate damage potential over future scaling
    4. Board presence over economy/PO generation

Known Blind Spots:
    - Ignores defensive considerations entirely
    - Does not value healing or sustain
    - May run out of resources in long games
    - Vulnerable to control strategies
    - Does not consider opponent's board state
"""

from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.cards.models import Card
    from src.game.state import GameState, PlayerState

from src.cards.models import CardClass

from .action import Action, ActionType
from .base import Player, PlayerInfo


class AggroPlayer(Player):
    """Player implementing aggressive damage-maximization strategy.

    This is an analytical probe agent that exhibits a single-minded
    focus on maximizing damage output. It does not adapt to game state
    beyond immediate damage calculations.

    The agent behaves as if: "Winning quickly is the only objective."

    Attributes:
        attack_weight: How much to weight ATK in evaluations (default 3.0).
        cost_efficiency_weight: Bonus for low-cost cards (default 2.0).
        berserk_bonus: Extra value for Berserk class (default 4.0).
        archer_bonus: Extra value for Archer class (default 3.0).
    """

    def __init__(
        self,
        player_id: int,
        name: str | None = None,
        attack_weight: float = 3.0,
        cost_efficiency_weight: float = 2.0,
        berserk_bonus: float = 4.0,
        archer_bonus: float = 3.0,
    ) -> None:
        """Initialize the Aggro strategy player.

        Args:
            player_id: The player's ID.
            name: Optional display name.
            attack_weight: Weight multiplier for ATK values.
            cost_efficiency_weight: Bonus for cheap cards.
            berserk_bonus: Extra value for Berserk class cards.
            archer_bonus: Extra value for Archer class cards.
        """
        super().__init__(player_id, name)
        self.attack_weight = attack_weight
        self.cost_efficiency_weight = cost_efficiency_weight
        self.berserk_bonus = berserk_bonus
        self.archer_bonus = archer_bonus

    @property
    def info(self) -> PlayerInfo:
        """Return metadata about this player agent."""
        return PlayerInfo(
            name=self._name or f"aggro_{self.player_id}",
            agent_type="aggro",
            version="1.0.0",
        )

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
        """Evaluate a card for purchase with pure aggro focus.

        Prioritizes:
        - High ATK values (heavily weighted)
        - Low cost for faster deployment
        - Classes that deal extra damage (Berserk, Archer)

        Ignores:
        - Health/PV values (minimal weight)
        - Economy generation
        - Family synergies
        - Defensive capabilities
        """
        # ATK is king - heavily weight attack value
        score = card.attack * self.attack_weight

        # Minimal weight for health (only for tie-breaking)
        score += card.health * 0.2

        # Cost efficiency: cheap cards deploy faster
        cost = card.cost or 1
        if cost <= 2:
            score += self.cost_efficiency_weight * 2
        elif cost <= 3:
            score += self.cost_efficiency_weight

        # ATK per PO ratio - aggressive efficiency metric
        atk_per_po = card.attack / max(cost, 1)
        score += atk_per_po * 2.0

        # Berserk class: trades health for damage - perfect for aggro
        if card.card_class == CardClass.BERSERK:
            score += self.berserk_bonus
            # Extra bonus for high-ATK Berserks
            if card.attack >= 4:
                score += 2.0

        # Archer class: bonus damage vs Defenders
        if card.card_class == CardClass.ARCHER:
            score += self.archer_bonus

        # Combattant class: scales ATK with count
        if card.card_class == CardClass.COMBATTANT:
            score += 2.0

        # Evolution potential (only for high-ATK evolutions)
        evolution_candidates = self._get_evolution_candidates(player_state)
        if card.name in evolution_candidates:
            count = evolution_candidates[card.name]
            if count == 2:
                # Evolving is good if it increases ATK
                score += card.attack * 1.5
            elif count == 1:
                score += card.attack * 0.5

        # Penalty for economy-focused classes (not aggressive)
        if card.card_class == CardClass.ECONOME:
            score -= 2.0  # Aggro doesn't care about PO generation

        # Penalty for defensive classes
        if card.card_class in (CardClass.PROTECTEUR, CardClass.DEFENSEUR):
            score -= 1.0  # Defense is irrelevant to aggro

        return score

    def _evaluate_card_for_play(
        self,
        card: "Card",
        player_state: "PlayerState",
        state: "GameState",
    ) -> float:
        """Evaluate a card for playing to board.

        Play priority is purely based on immediate damage potential.
        """
        # ATK is the primary metric
        score = card.attack * self.attack_weight

        # Berserks should be played for immediate damage
        if card.card_class == CardClass.BERSERK:
            score += self.berserk_bonus

        # Archers for bonus damage
        if card.card_class == CardClass.ARCHER:
            score += self.archer_bonus

        # High ATK cards first
        if card.attack >= 4:
            score += 3.0

        return score

    def choose_market_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose market action with pure aggro focus.

        Always buy the highest-damage card available.
        Never pass if a purchase is possible.
        """
        buy_actions = [
            a
            for a in legal_actions
            if a.action_type == ActionType.BUY_CARD and a.card is not None
        ]

        if not buy_actions:
            return Action.end_phase()

        # Score and sort by aggro value
        scored = [
            (a, self._evaluate_card_for_market(a.card, player_state, state))
            for a in buy_actions
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        # Aggro always buys - no passing to save PO
        return scored[0][0]

    def choose_play_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose play action prioritizing immediate damage.

        Play high-ATK cards first. Always fill the board.
        """
        # Check for evolution opportunities (evolutions increase ATK)
        evolve_actions = [
            a for a in legal_actions if a.action_type == ActionType.EVOLVE
        ]
        if evolve_actions:
            # Prefer evolutions that maximize ATK gain
            best_evolve = max(
                evolve_actions,
                key=lambda a: (a.evolve_result.attack if a.evolve_result else 0),
            )
            return best_evolve

        # Play actions - deploy damage dealers
        play_actions = [
            a
            for a in legal_actions
            if a.action_type == ActionType.PLAY_CARD and a.card is not None
        ]

        if not play_actions:
            # Equip weapons for ATK boost
            equip_actions = [
                a for a in legal_actions if a.action_type == ActionType.EQUIP_WEAPON
            ]
            if equip_actions:
                # Prefer equipping to highest-ATK cards
                best_equip = max(
                    equip_actions,
                    key=lambda a: (a.target_card.attack if a.target_card else 0),
                )
                return best_equip
            return Action.end_phase()

        # Score and play highest damage card
        scored = [
            (a, self._evaluate_card_for_play(a.card, player_state, state))
            for a in play_actions
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored[0][0]
