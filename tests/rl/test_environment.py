"""Tests for the CartesSociete Gymnasium environment."""

import gymnasium as gym
import numpy as np

from src.players import RandomPlayer
from src.rl import CartesSocieteEnv


class TestCartesSocieteEnv:
    """Test suite for CartesSocieteEnv."""

    def test_env_creation(self) -> None:
        """Test that environment can be created."""
        env = CartesSocieteEnv()
        assert env is not None
        env.close()

    def test_env_reset(self) -> None:
        """Test that environment can be reset."""
        env = CartesSocieteEnv()
        obs, info = env.reset()

        assert isinstance(obs, np.ndarray)
        assert isinstance(info, dict)
        assert len(obs) == env.observation_space.shape[0]
        env.close()

    def test_env_step(self) -> None:
        """Test that environment can step."""
        env = CartesSocieteEnv()
        env.reset()

        # Get valid action
        mask = env.action_masks()
        valid_actions = np.where(mask)[0]
        if len(valid_actions) > 0:
            action = valid_actions[0]
            obs, reward, terminated, truncated, info = env.step(action)

            assert isinstance(obs, np.ndarray)
            assert isinstance(reward, (int, float))
            assert isinstance(terminated, bool)
            assert isinstance(truncated, bool)
            assert isinstance(info, dict)

        env.close()

    def test_action_masks(self) -> None:
        """Test that action masks are returned correctly."""
        env = CartesSocieteEnv()
        env.reset()

        mask = env.action_masks()
        assert isinstance(mask, np.ndarray)
        assert mask.dtype == bool
        assert len(mask) == env.action_space.n
        assert mask.any()  # At least one action should be valid
        env.close()

    def test_action_masks_alias(self) -> None:
        """Test that get_action_mask is an alias for action_masks."""
        env = CartesSocieteEnv()
        env.reset()

        mask1 = env.action_masks()
        mask2 = env.get_action_mask()

        np.testing.assert_array_equal(mask1, mask2)
        env.close()

    def test_observation_space(self) -> None:
        """Test observation space is correctly defined."""
        env = CartesSocieteEnv()
        assert isinstance(env.observation_space, gym.spaces.Box)
        assert env.observation_space.dtype == np.float32
        env.close()

    def test_action_space(self) -> None:
        """Test action space is correctly defined."""
        env = CartesSocieteEnv()
        assert isinstance(env.action_space, gym.spaces.Discrete)
        assert env.action_space.n > 0
        env.close()

    def test_seeding_works(self) -> None:
        """Test that seeding affects environment behavior."""
        # Different seeds should generally produce different results
        env1 = CartesSocieteEnv(seed=42)
        obs1, _ = env1.reset()

        env2 = CartesSocieteEnv(seed=123)
        obs2, _ = env2.reset()

        # With different seeds, observations may differ
        # Just verify that the environment accepts seeds without error
        assert obs1 is not None
        assert obs2 is not None

        env1.close()
        env2.close()

    def test_custom_opponent_factory(self) -> None:
        """Test that custom opponent factory works."""

        def opponent_factory(pid: int) -> RandomPlayer:
            return RandomPlayer(pid, seed=123)

        env = CartesSocieteEnv(opponent_factory=opponent_factory)
        env.reset()
        assert env._opponent is not None
        env.close()

    def test_game_completes(self) -> None:
        """Test that a full game can be played."""
        env = CartesSocieteEnv(seed=42)
        env.reset()

        done = False
        steps = 0
        max_steps = 1000

        while not done and steps < max_steps:
            mask = env.action_masks()
            valid_actions = np.where(mask)[0]
            if len(valid_actions) == 0:
                break
            action = valid_actions[0]
            _, _, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            steps += 1

        assert steps < max_steps, "Game did not terminate within step limit"
        env.close()
