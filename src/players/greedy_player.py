"""Greedy player that maximizes immediate value.

This player always chooses the action with the highest immediate value
based on card evaluation heuristics, including evolution opportunities.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.game.state import GameState, PlayerState

from .action import Action, ActionType
from .base import Player, PlayerInfo
from .evaluation import (
    calculate_evolution_potential,
    evaluate_card_for_play,
    evaluate_card_for_purchase,
)


class GreedyPlayer(Player):
    """Player that greedily maximizes immediate card value.

    In MARKET phase: Buys the highest-value affordable card, considering
    evolution potential.
    In PLAY phase: Evolves when possible, then plays the highest-value card.

    This player does not consider long-term strategy or opponent actions,
    but does take advantage of immediate evolution opportunities.
    """

    @property
    def info(self) -> PlayerInfo:
        """Return metadata about this player agent."""
        return PlayerInfo(
            name=self._name or f"greedy_{self.player_id}",
            agent_type="greedy",
            version="1.0.0",
        )

    def choose_market_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Buy the highest-value affordable card, considering evolution.

        Args:
            state: Current game state.
            player_state: This player's state.
            legal_actions: Available actions.

        Returns:
            The buy action for the highest-value card, or end_phase.
        """
        buy_actions = [
            a
            for a in legal_actions
            if a.action_type == ActionType.BUY_CARD and a.card is not None
        ]

        if not buy_actions:
            # No affordable cards, end market phase
            return Action.end_phase()

        # Score each buy option, including evolution potential bonus
        scored = []
        for a in buy_actions:
            base_score = evaluate_card_for_purchase(a.card, player_state, state)
            # Add evolution potential bonus (already in evaluate_card_for_purchase,
            # but we add extra weight for cards that would complete evolution)
            evo_bonus = calculate_evolution_potential(a.card, player_state)
            # Extra bonus if this would complete an evolution (have 2 copies)
            if evo_bonus >= 3.0:  # evolution_two_copies_bonus threshold
                evo_bonus += 5.0  # Strong priority for evolution completion
            scored.append((a, base_score + evo_bonus))

        scored.sort(key=lambda x: x[1], reverse=True)

        # Buy highest value card
        return scored[0][0]

    def choose_play_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Play cards with evolution priority, then highest value.

        Evolution is prioritized because Level 2 cards are strictly
        better than three Level 1 copies. After evolution, plays
        the highest-value card. Uses replace actions when board is full.

        Args:
            state: Current game state.
            player_state: This player's state.
            legal_actions: Available actions.

        Returns:
            The chosen play action, or end_phase.
        """
        # First priority: always evolve when possible
        evolve_actions = [
            a for a in legal_actions if a.action_type == ActionType.EVOLVE
        ]
        if evolve_actions:
            # Evolving is always beneficial - Level 2 cards are stronger
            return evolve_actions[0]

        # Second priority: play cards from hand
        play_actions = [
            a
            for a in legal_actions
            if a.action_type == ActionType.PLAY_CARD and a.card is not None
        ]

        if play_actions:
            # Score each play option
            scored = [
                (a, evaluate_card_for_play(a.card, player_state, state))
                for a in play_actions
            ]
            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[0][0]

        # Third priority: replace cards when board is full
        replace_actions = [
            a
            for a in legal_actions
            if a.action_type == ActionType.REPLACE_CARD
            and a.card is not None
            and a.target_card is not None
        ]

        if replace_actions:
            # Find the replacement with best value improvement
            best_action = None
            best_improvement = 0.0

            for action in replace_actions:
                new_value = evaluate_card_for_play(action.card, player_state, state)
                old_value = evaluate_card_for_play(
                    action.target_card, player_state, state
                )
                improvement = new_value - old_value

                if improvement > best_improvement:
                    best_improvement = improvement
                    best_action = action

            # Only replace if there's positive value improvement
            if best_action is not None and best_improvement > 0:
                return best_action

        return Action.end_phase()
