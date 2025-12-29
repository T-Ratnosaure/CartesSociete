"""Random player that selects uniformly from legal actions.

This player serves as a baseline for comparison and is useful for
Monte Carlo simulations.
"""

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.game.state import GameState, PlayerState

from .action import Action
from .base import Player, PlayerInfo


class RandomPlayer(Player):
    """Player that chooses random legal actions.

    Useful as a baseline and for Monte Carlo simulations.
    Supports seeding for reproducible behavior.

    Attributes:
        player_id: The player's ID in the game.
    """

    def __init__(
        self,
        player_id: int,
        name: str | None = None,
        seed: int | None = None,
    ) -> None:
        """Initialize the random player.

        Args:
            player_id: The player's ID.
            name: Optional display name.
            seed: Optional random seed for reproducibility.
        """
        super().__init__(player_id, name)
        self._rng = random.Random(seed)

    @property
    def info(self) -> PlayerInfo:
        """Return metadata about this player agent."""
        return PlayerInfo(
            name=self._name or f"random_{self.player_id}",
            agent_type="random",
            version="1.0.0",
        )

    def choose_market_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose a random legal market action.

        Args:
            state: Current game state.
            player_state: This player's state.
            legal_actions: Available actions.

        Returns:
            A randomly selected action.
        """
        return self._rng.choice(legal_actions)

    def choose_play_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose a random legal play action.

        Args:
            state: Current game state.
            player_state: This player's state.
            legal_actions: Available actions.

        Returns:
            A randomly selected action.
        """
        return self._rng.choice(legal_actions)
