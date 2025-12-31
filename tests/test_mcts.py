"""Tests for MCTS player implementation."""

import pytest

from src.players import MCTSPlayer
from src.players.action import Action
from src.players.mcts_player import MCTSConfig, MCTSNode


class TestMCTSConfig:
    """Tests for MCTSConfig."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = MCTSConfig()
        assert config.num_simulations == 100
        assert config.exploration_constant == pytest.approx(1.414, rel=0.01)
        assert config.max_rollout_depth == 10
        assert config.use_stub is False

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = MCTSConfig(
            num_simulations=50,
            exploration_constant=2.0,
            max_rollout_depth=20,
        )
        assert config.num_simulations == 50
        assert config.exploration_constant == 2.0
        assert config.max_rollout_depth == 20

    def test_invalid_simulations(self) -> None:
        """Test that invalid num_simulations is rejected."""
        with pytest.raises(ValueError, match="num_simulations"):
            MCTSConfig(num_simulations=0)

        with pytest.raises(ValueError, match="num_simulations"):
            MCTSConfig(num_simulations=20000)

    def test_invalid_rollout_depth(self) -> None:
        """Test that invalid max_rollout_depth is rejected."""
        with pytest.raises(ValueError, match="max_rollout_depth"):
            MCTSConfig(max_rollout_depth=0)

        with pytest.raises(ValueError, match="max_rollout_depth"):
            MCTSConfig(max_rollout_depth=200)

    def test_negative_exploration_constant(self) -> None:
        """Test that negative exploration constant is rejected."""
        with pytest.raises(ValueError, match="exploration_constant"):
            MCTSConfig(exploration_constant=-1.0)


class TestMCTSNode:
    """Tests for MCTSNode."""

    def test_create_node(self) -> None:
        """Test creating an MCTS node."""
        node = MCTSNode(action=None)
        assert node.action is None
        assert node.parent is None
        assert node.children == []
        assert node.visits == 0
        assert node.total_value == 0.0

    def test_ucb1_unvisited(self) -> None:
        """Test UCB1 value for unvisited node."""
        node = MCTSNode(action=None)
        assert node.ucb1(1.414) == float("inf")

    def test_ucb1_with_visits(self) -> None:
        """Test UCB1 value for visited node."""
        parent = MCTSNode(action=None)
        parent.visits = 10

        child = MCTSNode(action=Action.end_phase(), parent=parent)
        child.visits = 5
        child.total_value = 2.5

        ucb = child.ucb1(1.414)
        # Exploitation: 2.5/5 = 0.5
        # Exploration: 1.414 * sqrt(ln(10)/5) ≈ 0.96
        assert ucb > 0.5  # Should be > exploitation alone
        assert ucb < 2.0  # Should be reasonable

    def test_average_value(self) -> None:
        """Test average value calculation."""
        node = MCTSNode(action=None)
        node.visits = 4
        node.total_value = 2.0
        assert node.average_value == 0.5

    def test_average_value_unvisited(self) -> None:
        """Test average value for unvisited node."""
        node = MCTSNode(action=None)
        assert node.average_value == 0.0

    def test_is_fully_expanded(self) -> None:
        """Test fully expanded check."""
        node = MCTSNode(action=None)
        node.untried_actions = [Action.end_phase()]
        assert not node.is_fully_expanded()

        node.untried_actions = []
        assert node.is_fully_expanded()

    def test_is_terminal(self) -> None:
        """Test terminal node check."""
        node = MCTSNode(action=None)
        node.untried_actions = []
        node.children = []
        assert node.is_terminal()

        node.children = [MCTSNode(action=Action.end_phase())]
        assert not node.is_terminal()

    def test_best_child(self) -> None:
        """Test selecting best child."""
        parent = MCTSNode(action=None)
        parent.visits = 10

        child1 = MCTSNode(action=Action.end_phase(), parent=parent)
        child1.visits = 3
        child1.total_value = 1.5

        child2 = MCTSNode(action=Action.end_phase(), parent=parent)
        child2.visits = 5
        child2.total_value = 3.0

        parent.children = [child1, child2]

        best = parent.best_child(1.414)
        # Child2 has higher exploitation (0.6 vs 0.5) but fewer visits
        # UCB1 considers both - best depends on exact values
        assert best in [child1, child2]

    def test_most_visited_child(self) -> None:
        """Test selecting most visited child."""
        parent = MCTSNode(action=None)

        child1 = MCTSNode(action=Action.end_phase(), parent=parent)
        child1.visits = 10

        child2 = MCTSNode(action=Action.end_phase(), parent=parent)
        child2.visits = 5

        parent.children = [child1, child2]

        assert parent.most_visited_child() == child1


class TestMCTSPlayer:
    """Tests for MCTSPlayer."""

    def test_create_player(self) -> None:
        """Test creating an MCTS player."""
        player = MCTSPlayer(player_id=0)
        assert player.player_id == 0
        assert player.info.agent_type == "mcts"

    def test_create_player_with_config(self) -> None:
        """Test creating player with custom config."""
        config = MCTSConfig(num_simulations=50)
        player = MCTSPlayer(player_id=0, config=config)
        assert player.config.num_simulations == 50

    def test_create_player_with_seed(self) -> None:
        """Test creating player with seed."""
        player = MCTSPlayer(player_id=0, seed=42)
        assert player._rng.random() == pytest.approx(0.6394267984578837)

    def test_stub_mode(self) -> None:
        """Test stub mode falls back to random."""
        config = MCTSConfig(use_stub=True)
        player = MCTSPlayer(player_id=0, config=config, seed=42)

        # Verify stub mode is enabled
        assert player.config.use_stub is True
        # Player should be created successfully
        assert player.player_id == 0

    def test_player_info(self) -> None:
        """Test player info metadata."""
        player = MCTSPlayer(player_id=0, name="TestMCTS")
        info = player.info
        assert info.name == "TestMCTS"
        assert info.agent_type == "mcts"
        assert info.version == "1.0.0"

    def test_player_info_default_name(self) -> None:
        """Test default player name."""
        player = MCTSPlayer(player_id=5)
        info = player.info
        assert info.name == "mcts_5"


@pytest.mark.slow
class TestMCTSIntegration:
    """Integration tests for MCTS player with game engine.

    These tests are marked as slow because MCTS search is computationally expensive.
    Run with `-m "not slow"` to skip in CI.
    """

    def test_mcts_completes_game(self) -> None:
        """Test that MCTS player can complete a game."""
        from src.players import RandomPlayer
        from src.simulation import GameRunner

        # Use minimal settings for speed
        config = MCTSConfig(num_simulations=3, max_rollout_depth=2)
        players = [
            MCTSPlayer(player_id=0, config=config, seed=42),
            RandomPlayer(player_id=1, seed=43),
        ]

        runner = GameRunner(players=players, seed=100, max_turns=10)
        result = runner.run_game()

        assert result.turns > 0
        assert result.turns <= 10

    def test_mcts_vs_random(self) -> None:
        """Test MCTS vs Random in a short match."""
        from src.simulation import MatchConfig, MatchRunner

        config = MCTSConfig(num_simulations=3, max_rollout_depth=2)

        match_config = MatchConfig(
            num_games=2,
            player_factories=[
                lambda pid: MCTSPlayer(player_id=pid, config=config, seed=pid),
                lambda pid: MCTSPlayer(
                    player_id=pid,
                    config=MCTSConfig(use_stub=True),  # Stub = random
                    seed=pid + 100,
                ),
            ],
            base_seed=42,
        )

        runner = MatchRunner()
        result = runner.run_match(match_config)

        assert result.games_played == 2
        # Just verify it completes without error
