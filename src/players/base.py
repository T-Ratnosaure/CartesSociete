"""Abstract base class for player agents.

This module defines the Player interface that all AI agents must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.game.combat import CombatResult
    from src.game.state import GameState, PlayerState

from .action import Action


@dataclass
class PlayerInfo:
    """Metadata about a player agent.

    Attributes:
        name: Display name of the player.
        agent_type: Type of agent (random, greedy, heuristic, mcts).
        version: Version string for the agent implementation.
    """

    name: str
    agent_type: str
    version: str = "1.0.0"


class Player(ABC):
    """Abstract base class for all player agents.

    Players receive game state and return actions. They do not modify
    game state directly - the engine handles all mutations.

    Attributes:
        player_id: The player's ID in the game.
    """

    def __init__(self, player_id: int, name: str | None = None) -> None:
        """Initialize the player.

        Args:
            player_id: The player's ID in the game.
            name: Optional display name. Defaults to agent type + ID.
        """
        self.player_id = player_id
        self._name = name

    @property
    @abstractmethod
    def info(self) -> PlayerInfo:
        """Return metadata about this player agent.

        Returns:
            PlayerInfo with name, type, and version.
        """
        pass

    @property
    def name(self) -> str:
        """Get the player's display name.

        Returns:
            The display name, defaulting to agent_type + player_id.
        """
        return self._name or f"{self.info.agent_type}_{self.player_id}"

    @abstractmethod
    def choose_market_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose an action during the MARKET phase.

        Args:
            state: Current game state (read-only).
            player_state: This player's state.
            legal_actions: List of valid actions to choose from.

        Returns:
            The chosen action.
        """
        pass

    @abstractmethod
    def choose_play_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose an action during the PLAY phase.

        Args:
            state: Current game state (read-only).
            player_state: This player's state.
            legal_actions: List of valid actions to choose from.

        Returns:
            The chosen action.
        """
        pass

    # Observer hooks (optional overrides)

    def on_game_start(self, state: "GameState") -> None:
        """Called when a game begins.

        Override this method for any initialization needed at game start.

        Args:
            state: Initial game state.
        """
        pass

    def on_turn_start(self, state: "GameState", turn: int) -> None:
        """Called at the start of each turn.

        Args:
            state: Current game state.
            turn: The turn number starting.
        """
        pass

    def on_combat_result(self, result: "CombatResult") -> None:
        """Called after combat resolution.

        Override to observe combat outcomes for learning or tracking.

        Args:
            result: The combat result with damage dealt and eliminations.
        """
        pass

    def on_game_end(self, state: "GameState", winner_id: int | None) -> None:
        """Called when the game ends.

        Args:
            state: Final game state.
            winner_id: ID of the winning player, or None if draw.
        """
        pass
