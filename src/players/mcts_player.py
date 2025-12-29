"""Monte Carlo Tree Search player implementation.

This module provides a complete MCTS-based AI player that uses tree search
with UCB1 selection to find strong moves.
"""

import copy
import logging
import math
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.game.combat import resolve_combat
from src.game.executor import execute_action, get_legal_actions_for_player
from src.game.state import GamePhase

if TYPE_CHECKING:
    from src.game.state import GameState, PlayerState

from .action import Action, ActionType
from .base import Player, PlayerInfo

logger = logging.getLogger(__name__)


@dataclass
class MCTSConfig:
    """Configuration for MCTS player.

    Attributes:
        num_simulations: Number of simulations per decision (1-10000).
        exploration_constant: UCB1 exploration parameter (sqrt(2) default).
        max_rollout_depth: Maximum depth for random rollouts (1-100).
        use_stub: When True, falls back to random play (for testing).
    """

    num_simulations: int = 100
    exploration_constant: float = 1.414  # sqrt(2)
    max_rollout_depth: int = 10
    use_stub: bool = False

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

    Attributes:
        action: The action that led to this node (None for root).
        parent: Parent node in the tree.
        children: Child nodes.
        visits: Number of times this node was visited.
        total_value: Sum of values from simulations through this node.
        untried_actions: Actions not yet expanded from this node.
    """

    action: Action | None
    parent: "MCTSNode | None" = None
    children: list["MCTSNode"] = field(default_factory=list)
    visits: int = 0
    total_value: float = 0.0
    untried_actions: list[Action] = field(default_factory=list)

    def ucb1(self, exploration_constant: float) -> float:
        """Calculate UCB1 value for selection.

        UCB1 = exploitation + exploration
             = Q(s,a) / N(s,a) + c * sqrt(ln(N(s)) / N(s,a))

        Args:
            exploration_constant: The exploration parameter c.

        Returns:
            UCB1 score for this node.
        """
        if self.visits == 0:
            return float("inf")

        exploitation = self.total_value / self.visits

        if self.parent is None or self.parent.visits == 0:
            return exploitation

        exploration = exploration_constant * math.sqrt(
            math.log(self.parent.visits) / self.visits
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

    def is_fully_expanded(self) -> bool:
        """Check if all actions have been tried.

        Returns:
            True if no untried actions remain.
        """
        return len(self.untried_actions) == 0

    def is_terminal(self) -> bool:
        """Check if this is a terminal node (no children possible).

        Returns:
            True if this is a leaf node.
        """
        return self.is_fully_expanded() and len(self.children) == 0

    def best_child(self, exploration_constant: float) -> "MCTSNode":
        """Select the best child using UCB1.

        Args:
            exploration_constant: The exploration parameter.

        Returns:
            Child with highest UCB1 value.
        """
        return max(self.children, key=lambda c: c.ucb1(exploration_constant))

    def most_visited_child(self) -> "MCTSNode":
        """Get the child with most visits.

        Returns:
            Child with highest visit count.
        """
        return max(self.children, key=lambda c: c.visits)


class MCTSPlayer(Player):
    """Monte Carlo Tree Search player.

    The MCTS algorithm works as follows:
    1. Selection: Traverse tree using UCB1 until reaching a leaf
    2. Expansion: Add new child nodes for unexplored actions
    3. Simulation: Random rollout from the new node
    4. Backpropagation: Update visit counts and values up the tree

    Note:
        Simulations use depth-limited rollouts (default: 10 moves) with
        heuristic position evaluation rather than playing to game completion.
        This tradeoff improves performance while maintaining reasonable
        play quality. For deeper analysis, increase max_rollout_depth in
        MCTSConfig, though this will slow decision-making.
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

        if self.config.use_stub:
            logger.warning(
                f"MCTSPlayer {player_id} running in STUB mode - using random actions."
            )

    @property
    def info(self) -> PlayerInfo:
        """Return metadata about this player agent."""
        return PlayerInfo(
            name=self._name or f"mcts_{self.player_id}",
            agent_type="mcts",
            version="1.0.0",
        )

    def choose_market_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose market action using MCTS.

        Args:
            state: Current game state.
            player_state: This player's state.
            legal_actions: Available actions.

        Returns:
            The chosen action.
        """
        if self.config.use_stub or len(legal_actions) <= 1:
            if legal_actions:
                return self._rng.choice(legal_actions)
            return Action.end_phase()

        return self._run_mcts(state, player_state, legal_actions)

    def choose_play_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Choose play action using MCTS.

        Args:
            state: Current game state.
            player_state: This player's state.
            legal_actions: Available actions.

        Returns:
            The chosen action.
        """
        if self.config.use_stub or len(legal_actions) <= 1:
            if legal_actions:
                return self._rng.choice(legal_actions)
            return Action.end_phase()

        # Prioritize evolution if available
        evolve_actions = [
            a for a in legal_actions if a.action_type == ActionType.EVOLVE
        ]
        if evolve_actions:
            return evolve_actions[0]

        return self._run_mcts(state, player_state, legal_actions)

    def _run_mcts(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Run MCTS search and return best action.

        Args:
            state: Current game state.
            player_state: This player's state.
            legal_actions: Available actions.

        Returns:
            The best action found by MCTS.
        """
        if not legal_actions:
            return Action.end_phase()

        # Create root node
        root = MCTSNode(action=None)
        root.untried_actions = list(legal_actions)

        # Run simulations
        for _ in range(self.config.num_simulations):
            # Clone state for this simulation
            sim_state = self._clone_state(state)
            sim_player = self._get_player_state(sim_state, self.player_id)

            # Selection and expansion
            node = self._select(root)

            # Expand if possible
            if not node.is_fully_expanded() and node.untried_actions:
                node = self._expand(node, sim_state, sim_player)

            # Simulation (rollout)
            value = self._simulate(sim_state, sim_player)

            # Backpropagation
            self._backpropagate(node, value)

        # Return action with most visits
        if not root.children:
            return self._rng.choice(legal_actions)

        best = root.most_visited_child()
        return best.action if best.action else Action.end_phase()

    def _select(self, node: MCTSNode) -> MCTSNode:
        """Select a node to expand using UCB1.

        Traverses the tree until reaching a node that has
        untried actions or is terminal.

        Args:
            node: Starting node.

        Returns:
            Selected node for expansion.
        """
        while node.is_fully_expanded() and node.children:
            node = node.best_child(self.config.exploration_constant)
        return node

    def _expand(
        self,
        node: MCTSNode,
        state: "GameState",
        player_state: "PlayerState",
    ) -> MCTSNode:
        """Expand a node by adding a new child.

        Args:
            node: Node to expand.
            state: Current simulation state.
            player_state: Current player state.

        Returns:
            The newly created child node.
        """
        if not node.untried_actions:
            return node

        # Pick a random untried action
        action = self._rng.choice(node.untried_actions)
        node.untried_actions.remove(action)

        # Create child node
        child = MCTSNode(action=action, parent=node)
        node.children.append(child)

        # Execute the action on the simulation state
        self._execute_action(state, player_state, action)

        return child

    def _simulate(
        self,
        state: "GameState",
        player_state: "PlayerState",
    ) -> float:
        """Run a random rollout and return the value.

        Performs a depth-limited random rollout from the current state,
        then evaluates the resulting position using a heuristic.

        Args:
            state: Simulation state.
            player_state: Player state.

        Returns:
            Value between 0 and 1 representing the outcome.
        """
        depth = 0

        while depth < self.config.max_rollout_depth and not state.is_game_over():
            # Get current player
            current_player = self._get_player_state(state, self.player_id)
            if current_player.eliminated:
                return 0.0  # We lost

            # Get legal actions
            actions = get_legal_actions_for_player(state, current_player)
            if not actions:
                break

            # Random action
            action = self._rng.choice(actions)

            # Execute
            self._execute_action(state, current_player, action)

            # Advance phase if END_PHASE
            if action.action_type == ActionType.END_PHASE:
                self._advance_phase(state)

            depth += 1

        # Evaluate final position
        return self._evaluate_position(state, player_state)

    def _backpropagate(self, node: MCTSNode, value: float) -> None:
        """Backpropagate the simulation result up the tree.

        Args:
            node: Starting node.
            value: Value from simulation.
        """
        while node is not None:
            node.visits += 1
            node.total_value += value
            node = node.parent

    def _evaluate_position(
        self,
        state: "GameState",
        player_state: "PlayerState",
    ) -> float:
        """Evaluate the current position for this player.

        Args:
            state: Game state.
            player_state: Player state.

        Returns:
            Value between 0 and 1.
        """
        # Get our current state
        our_state = self._get_player_state(state, self.player_id)

        if our_state.eliminated:
            return 0.0

        # Get opponent states
        opponents = [p for p in state.players if p.player_id != self.player_id]
        all_eliminated = all(p.eliminated for p in opponents)

        if all_eliminated:
            return 1.0  # We won

        # Heuristic evaluation based on board strength
        our_attack = our_state.get_total_attack()
        our_health = our_state.get_total_health()
        our_life = our_state.health

        opp_attack = sum(p.get_total_attack() for p in opponents if not p.eliminated)
        opp_health = sum(p.get_total_health() for p in opponents if not p.eliminated)
        opp_life = sum(p.health for p in opponents if not p.eliminated)

        # Normalize to 0-1 range
        total_strength = (
            our_attack + our_health + our_life + opp_attack + opp_health + opp_life
        )
        if total_strength == 0:
            return 0.5

        our_strength = our_attack + our_health + our_life
        return our_strength / total_strength

    def _clone_state(self, state: "GameState") -> "GameState":
        """Create a deep copy of the game state.

        Args:
            state: State to clone.

        Returns:
            Deep copy of the state.
        """
        return copy.deepcopy(state)

    def _get_player_state(
        self,
        state: "GameState",
        player_id: int,
    ) -> "PlayerState":
        """Get player state by ID.

        Args:
            state: Game state.
            player_id: Player ID.

        Returns:
            PlayerState for the given ID.
        """
        for player in state.players:
            if player.player_id == player_id:
                return player
        raise ValueError(f"Player {player_id} not found in state")

    def _execute_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        action: Action,
    ) -> None:
        """Execute an action on the simulation state.

        Args:
            state: Game state (modified in place).
            player_state: Player state.
            action: Action to execute.
        """
        if action.action_type == ActionType.END_PHASE:
            return

        try:
            execute_action(state, player_state, action)
        except (ValueError, KeyError, IndexError, AttributeError) as e:
            # Invalid actions can occur during random rollouts due to
            # state divergence from the actual game. This is expected.
            logger.debug(f"Invalid action during MCTS simulation: {e}")

    def _advance_phase(self, state: "GameState") -> None:
        """Advance to the next game phase.

        Args:
            state: Game state to advance.
        """
        if state.phase == GamePhase.MARKET:
            state.phase = GamePhase.PLAY
        elif state.phase == GamePhase.PLAY:
            state.phase = GamePhase.COMBAT
            # Simplified combat resolution
            self._resolve_combat(state)
            state.phase = GamePhase.END
            state.turn += 1
            state.phase = GamePhase.MARKET
        elif state.phase == GamePhase.COMBAT:
            state.phase = GamePhase.END
        elif state.phase == GamePhase.END:
            state.turn += 1
            state.phase = GamePhase.MARKET

    def _resolve_combat(self, state: "GameState") -> None:
        """Simplified combat resolution for simulation.

        Args:
            state: Game state.
        """
        try:
            resolve_combat(state)
        except (ValueError, KeyError, IndexError, AttributeError) as e:
            # Combat errors can occur during simulation due to
            # inconsistent state from random rollouts. This is expected.
            logger.debug(f"Combat error during MCTS simulation: {e}")
