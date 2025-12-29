"""Monte Carlo Tree Search player (stub implementation).

This module provides a skeleton for MCTS-based play. Currently operates
in stub mode, falling back to random play. The structure is in place
for future full implementation.
"""

import logging
import math
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.game.state import GameState, PlayerState

from .action import Action
from .base import Player, PlayerInfo
from .random_player import RandomPlayer

logger = logging.getLogger(__name__)


@dataclass
class MCTSConfig:
    """Configuration for MCTS player.

    Attributes:
        num_simulations: Number of simulations per decision (1-10000).
        exploration_constant: UCB1 exploration parameter (sqrt(2) default).
        max_rollout_depth: Maximum depth for random rollouts (1-100).
        use_stub: When True, falls back to random play.
    """

    num_simulations: int = 100
    exploration_constant: float = 1.414  # sqrt(2)
    max_rollout_depth: int = 10
    use_stub: bool = True

    # Maximum bounds to prevent DoS
    MAX_SIMULATIONS: int = field(default=10000, repr=False, init=False)
    MAX_ROLLOUT_DEPTH: int = field(default=100, repr=False, init=False)

    def __post_init__(self) -> None:
        """Validate configuration bounds."""
        if not 1 <= self.num_simulations <= self.MAX_SIMULATIONS:
            raise ValueError(
                f"num_simulations must be between 1 and {self.MAX_SIMULATIONS}, "
                f"got {self.num_simulations}"
            )
        if not 1 <= self.max_rollout_depth <= self.MAX_ROLLOUT_DEPTH:
            raise ValueError(
                f"max_rollout_depth must be between 1 and {self.MAX_ROLLOUT_DEPTH}, "
                f"got {self.max_rollout_depth}"
            )
        if self.exploration_constant < 0:
            raise ValueError(
                f"exploration_constant must be non-negative, "
                f"got {self.exploration_constant}"
            )


@dataclass
class MCTSNode:
    """Node in the MCTS tree.

    This is a placeholder for future implementation.

    Attributes:
        state_hash: Hash of the game state at this node.
        action: The action that led to this node.
        parent: Parent node in the tree.
        children: Child nodes.
        visits: Number of times this node was visited.
        total_value: Sum of values from simulations through this node.
    """

    state_hash: str
    action: Action | None
    parent: "MCTSNode | None" = None
    children: list["MCTSNode"] = field(default_factory=list)
    visits: int = 0
    total_value: float = 0.0

    @property
    def ucb1(self) -> float:
        """Calculate UCB1 value for selection.

        UCB1 = exploitation + exploration
             = Q(s,a) / N(s,a) + c * sqrt(ln(N(s)) / N(s,a))

        Returns:
            UCB1 score for this node.
        """
        if self.visits == 0:
            return float("inf")

        exploitation = self.total_value / self.visits

        if self.parent is None or self.parent.visits == 0:
            return exploitation

        exploration = 1.414 * math.sqrt(
            math.log(self.parent.visits + 1) / (self.visits + 1)
        )

        return exploitation + exploration

    @property
    def average_value(self) -> float:
        """Get average value (exploitation term).

        Returns:
            Average value from simulations, or 0 if unvisited.
        """
        if self.visits == 0:
            return 0.0
        return self.total_value / self.visits


class MCTSPlayer(Player):
    """Monte Carlo Tree Search player.

    CURRENT STATUS: Stub implementation that falls back to random play.

    The MCTS algorithm works as follows:
    1. Selection: Traverse tree using UCB1 until reaching a leaf
    2. Expansion: Add new child nodes for unexplored actions
    3. Simulation: Random rollout from the new node
    4. Backpropagation: Update visit counts and values up the tree

    Future implementation will include:
    - State hashing for tree reuse across turns
    - Efficient game state cloning for simulation
    - Parallel simulation support
    - Optional neural network policy/value guidance
    """

    def __init__(
        self,
        player_id: int,
        name: str | None = None,
        config: MCTSConfig | None = None,
        seed: int | None = None,
    ) -> None:
        """Initialize MCTS player.

        Args:
            player_id: The player's ID.
            name: Optional display name.
            config: MCTS configuration.
            seed: Random seed for reproducibility.
        """
        super().__init__(player_id, name)
        self.config = config or MCTSConfig()
        self._rng = random.Random(seed)
        self._fallback = RandomPlayer(player_id, seed=seed)

        if self.config.use_stub:
            logger.warning(
                f"MCTSPlayer {player_id} running in STUB mode - "
                "using random actions. Set config.use_stub=False for full MCTS."
            )

    @property
    def info(self) -> PlayerInfo:
        """Return metadata about this player agent."""
        return PlayerInfo(
            name=self._name or f"mcts_{self.player_id}",
            agent_type="mcts",
            version="0.1.0-stub",
        )

    def choose_market_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose market action using MCTS (or fallback).

        Args:
            state: Current game state.
            player_state: This player's state.
            legal_actions: Available actions.

        Returns:
            The chosen action.
        """
        if self.config.use_stub:
            return self._fallback.choose_market_action(
                state, player_state, legal_actions
            )

        return self._run_mcts(state, player_state, legal_actions)

    def choose_play_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose play action using MCTS (or fallback).

        Args:
            state: Current game state.
            player_state: This player's state.
            legal_actions: Available actions.

        Returns:
            The chosen action.
        """
        if self.config.use_stub:
            return self._fallback.choose_play_action(state, player_state, legal_actions)

        return self._run_mcts(state, player_state, legal_actions)

    def _run_mcts(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Run MCTS search and return best action.

        This is a placeholder for the full implementation.

        Args:
            state: Current game state.
            player_state: This player's state.
            legal_actions: Available actions.

        Returns:
            The best action found by MCTS.

        Raises:
            ValueError: If legal_actions is empty.
        """
        if not legal_actions:
            raise ValueError("legal_actions cannot be empty")

        # Placeholder implementation - random selection
        logger.debug(f"MCTS would run {self.config.num_simulations} simulations here")

        # In full implementation:
        # 1. Create/retrieve root node for current state
        # 2. For i in range(num_simulations):
        #    - Select: Traverse tree using UCB1
        #    - Expand: Add new child node
        #    - Simulate: Random rollout
        #    - Backpropagate: Update values
        # 3. Return action with most visits

        return self._rng.choice(legal_actions)

    def _hash_state(self, state: "GameState") -> str:
        """Create a hash for the game state.

        Used for tree reuse across decisions.

        Args:
            state: The game state to hash.

        Returns:
            A string hash of the state.
        """
        # Placeholder - would need to capture:
        # - Turn number
        # - Player boards/hands
        # - Market cards
        # - PO amounts
        return f"state_{state.turn}_{state.phase.value}"
