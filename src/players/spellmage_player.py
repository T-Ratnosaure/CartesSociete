"""SpellMage archetype strategy player.

This player implements a spell damage scaling strategy
independent of family identity.

Strategy Intent:
    Maximize spell damage by stacking Mage class cards to reach
    spell-doubling thresholds. Win through amplified spell effects.

Decision Priorities:
    1. Mage class cards for spell threshold bonuses
    2. Cards with spell-related bonus text
    3. Reaching 3+ Mages for spell doubling
    4. Spell damage over physical combat

Known Blind Spots:
    - Narrow focus on Mage class only
    - Weak if Mage threshold not reached
    - Ignores physical combat optimization
    - Vulnerable to early aggression
    - Does not value economy or defense
"""

from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.cards.models import Card
    from src.game.state import GameState, PlayerState

from src.cards.models import CardClass

from .action import Action, ActionType
from .base import Player, PlayerInfo


class SpellMagePlayer(Player):
    """Player implementing spell damage scaling strategy.

    This is an analytical probe agent that prioritizes Mage class cards
    to reach spell-doubling thresholds. It focuses on spell damage
    amplification over physical combat.

    The agent behaves as if: "Spells are the only path to victory."

    Attributes:
        mage_priority: How much to weight Mage cards (default 10.0).
        threshold_bonus: Extra value when approaching 3 Mages (default 8.0).
        spell_text_bonus: Value for spell-related bonus text (default 3.0).
    """

    def __init__(
        self,
        player_id: int,
        name: str | None = None,
        mage_priority: float = 10.0,
        threshold_bonus: float = 8.0,
        spell_text_bonus: float = 3.0,
    ) -> None:
        """Initialize the SpellMage strategy player.

        Args:
            player_id: The player's ID.
            name: Optional display name.
            mage_priority: Weight for Mage class cards.
            threshold_bonus: Extra value when approaching threshold.
            spell_text_bonus: Value for spell-related abilities.
        """
        super().__init__(player_id, name)
        self.mage_priority = mage_priority
        self.threshold_bonus = threshold_bonus
        self.spell_text_bonus = spell_text_bonus

    @property
    def info(self) -> PlayerInfo:
        """Return metadata about this player agent."""
        return PlayerInfo(
            name=self._name or f"spellmage_{self.player_id}",
            agent_type="spellmage",
            version="1.0.0",
        )

    def _count_class(self, player_state: "PlayerState", card_class: CardClass) -> int:
        """Count cards of a class on board."""
        return sum(1 for c in player_state.board if c.card_class == card_class)

    def _count_class_total(
        self, player_state: "PlayerState", card_class: CardClass
    ) -> int:
        """Count cards of a class on board and in hand."""
        return sum(
            1
            for c in player_state.board + player_state.hand
            if c.card_class == card_class
        )

    def _has_spell_text(self, card: "Card") -> bool:
        """Check if a card has spell-related bonus text."""
        if card.bonus_text:
            text = card.bonus_text.lower()
            return any(
                keyword in text
                for keyword in ["sort", "spell", "magie", "magic", "lance", "cast"]
            )
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
        """Evaluate a card for purchase with spell focus.

        Prioritizes:
        - Mage class cards (heavily weighted)
        - Spell-related bonus text
        - Reaching spell-doubling threshold

        De-prioritizes:
        - Non-Mage cards (unless supporting spells)
        - Pure physical damage cards
        """
        cost = card.cost or 1
        total_stats = card.attack + card.health

        # Base: minimal stat consideration
        score = total_stats / max(cost, 1)

        mage_count = self._count_class_total(player_state, CardClass.MAGE)

        # Mage class: core of the strategy
        if card.card_class == CardClass.MAGE:
            score += self.mage_priority

            # Threshold proximity bonuses
            if mage_count == 2:
                # About to hit 3 (spell doubling threshold)
                score += self.threshold_bonus * 2
            elif mage_count == 1:
                # Building towards threshold
                score += self.threshold_bonus
            elif mage_count >= 3:
                # Already have threshold, more Mages still good
                score += self.threshold_bonus * 0.5

            # Stacking bonus
            score += mage_count * 1.5

        # Spell-related bonus text
        if self._has_spell_text(card):
            score += self.spell_text_bonus
            # Extra bonus if already have Mages
            if mage_count >= 2:
                score += 2.0

        # Evolution potential for Mages
        evolution_candidates = self._get_evolution_candidates(player_state)
        if card.name in evolution_candidates:
            count = evolution_candidates[card.name]
            if count == 2 and card.card_class == CardClass.MAGE:
                # Evolving a Mage is very valuable
                score += 10.0
            elif count == 2:
                score += 4.0
            elif count == 1:
                score += 1.0

        # Penalty for non-Mage cards when building towards threshold
        if card.card_class != CardClass.MAGE:
            if mage_count < 3:
                # Still building threshold - focus on Mages
                score -= 3.0
            else:
                # Have threshold, non-Mages are just filler
                score -= 1.0

        # Envouteur has some spell synergy
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

        Play priority heavily favors Mages to reach threshold.
        """
        score = float(card.attack + card.health)

        mage_count = self._count_class(player_state, CardClass.MAGE)

        # Mages are top priority
        if card.card_class == CardClass.MAGE:
            score += self.mage_priority

            # Critical to reach threshold
            if mage_count < 3:
                score += 10.0

        # Spell-related cards
        if self._has_spell_text(card):
            score += self.spell_text_bonus

        return score

    def choose_market_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose market action with spell focus.

        Aggressively pursues Mage cards.
        May pass on non-Mages when building threshold.
        """
        buy_actions = [
            a
            for a in legal_actions
            if a.action_type == ActionType.BUY_CARD and a.card is not None
        ]

        if not buy_actions:
            return Action.end_phase()

        # Score and sort by spell value
        scored = [
            (a, self._evaluate_card_for_market(a.card, player_state, state))
            for a in buy_actions
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        best_action, best_score = scored[0]

        mage_count = self._count_class_total(player_state, CardClass.MAGE)

        # If building threshold and no Mages available, may save PO
        mages_in_market = any(
            a.card.card_class == CardClass.MAGE
            for a in buy_actions
            if a.card is not None
        )

        if not mages_in_market and mage_count < 3 and best_score < 3.0:
            # No Mages and still building - save for later
            return Action.end_phase()

        return best_action

    def choose_play_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose play action prioritizing Mage deployment.

        Play Mages first to reach spell-doubling threshold.
        """
        # Check for evolution opportunities
        evolve_actions = [
            a for a in legal_actions if a.action_type == ActionType.EVOLVE
        ]
        if evolve_actions:
            # Strongly prefer evolving Mages
            mage_evolves = [
                a
                for a in evolve_actions
                if a.evolve_cards and a.evolve_cards[0].card_class == CardClass.MAGE
            ]
            if mage_evolves:
                return mage_evolves[0]
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
                # Prefer equipping to Mages
                mage_equips = [
                    a
                    for a in equip_actions
                    if a.target_card and a.target_card.card_class == CardClass.MAGE
                ]
                if mage_equips:
                    return mage_equips[0]
                return equip_actions[0]
            return Action.end_phase()

        # Score and play best spell-focused card
        scored = [
            (a, self._evaluate_card_for_play(a.card, player_state, state))
            for a in play_actions
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored[0][0]
