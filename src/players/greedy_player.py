"""Greedy player that maximizes immediate value.

This player always chooses the action with the highest immediate value
based on card evaluation heuristics.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.game.state import GameState, PlayerState

from .action import Action, ActionType
from .base import Player, PlayerInfo
from .evaluation import evaluate_card_for_play, evaluate_card_for_purchase


class GreedyPlayer(Player):
    """Player that greedily maximizes immediate card value.

    In MARKET phase: Buys the highest-value affordable card.
    In PLAY phase: Plays the highest-value card from hand.

    This player does not consider long-term strategy, evolution potential,
    or opponent actions beyond immediate card value.
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
        """Buy the highest-value affordable card.

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

        # Score each buy option
        scored = [
            (a, evaluate_card_for_purchase(a.card, player_state, state))
            for a in buy_actions
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        # Buy highest value card
        return scored[0][0]

    def choose_play_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Play the highest-value card from hand.

        Args:
            state: Current game state.
            player_state: This player's state.
            legal_actions: Available actions.

        Returns:
            The play action for the highest-value card, or end_phase.
        """
        play_actions = [
            a
            for a in legal_actions
            if a.action_type == ActionType.PLAY_CARD and a.card is not None
        ]

        if not play_actions:
            return Action.end_phase()

        # Score each play option
        scored = [
            (a, evaluate_card_for_play(a.card, player_state, state))
            for a in play_actions
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored[0][0]
