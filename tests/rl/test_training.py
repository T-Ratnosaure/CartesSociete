"""Tests for the PPO training module."""

import tempfile
from pathlib import Path

import pytest

from src.rl import PPOTrainer, TrainingConfig


class TestTrainingConfig:
    """Test suite for TrainingConfig."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = TrainingConfig()

        assert config.total_timesteps == 500_000
        assert config.learning_rate == 3e-4
        assert config.n_steps == 2048
        assert config.batch_size == 64
        assert config.n_epochs == 10
        assert config.gamma == 0.99
        assert config.n_envs == 4
        assert config.opponent_type == "random"

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = TrainingConfig(
            total_timesteps=100_000,
            n_envs=2,
            opponent_type="greedy",
        )

        assert config.total_timesteps == 100_000
        assert config.n_envs == 2
        assert config.opponent_type == "greedy"


class TestPPOTrainer:
    """Test suite for PPOTrainer."""

    def test_trainer_creation(self) -> None:
        """Test that trainer can be created."""
        trainer = PPOTrainer()
        assert trainer is not None
        assert trainer.config is not None
        assert trainer.model is None

    def test_trainer_with_config(self) -> None:
        """Test trainer with custom config."""
        config = TrainingConfig(n_envs=2)
        trainer = PPOTrainer(config)
        assert trainer.config.n_envs == 2

    def test_create_envs(self) -> None:
        """Test environment creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = TrainingConfig(
                n_envs=2,
                log_dir=f"{tmpdir}/logs",
                model_dir=f"{tmpdir}/models",
            )
            trainer = PPOTrainer(config)
            envs = trainer.create_envs()

            assert envs is not None
            assert envs.num_envs == 2
            envs.close()

    def test_create_eval_env(self) -> None:
        """Test evaluation environment creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = TrainingConfig(
                log_dir=f"{tmpdir}/logs",
                model_dir=f"{tmpdir}/models",
            )
            trainer = PPOTrainer(config)
            eval_env = trainer.create_eval_env()

            assert eval_env is not None

    def test_create_model(self) -> None:
        """Test model creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = TrainingConfig(
                n_envs=2,
                log_dir=f"{tmpdir}/logs",
                model_dir=f"{tmpdir}/models",
            )
            trainer = PPOTrainer(config)
            envs = trainer.create_envs()
            model = trainer.create_model(envs)

            assert model is not None
            envs.close()


@pytest.mark.slow
class TestPPOTrainerIntegration:
    """Integration tests for PPO training (marked slow)."""

    def test_minimal_training(self) -> None:
        """Test that minimal training completes without errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = TrainingConfig(
                total_timesteps=1024,  # Minimum for one update
                n_steps=512,
                n_envs=2,
                eval_freq=1_000_000,  # Disable eval during test
                save_freq=1_000_000,  # Disable save during test
                log_dir=f"{tmpdir}/logs",
                model_dir=f"{tmpdir}/models",
                verbose=0,
            )
            trainer = PPOTrainer(config)
            model = trainer.train()

            assert model is not None
            assert trainer.model is not None

            # Verify model was saved
            final_path = Path(tmpdir) / "models" / "ppo_cartes_final.zip"
            assert final_path.exists()

    def test_evaluate_requires_model(self) -> None:
        """Test that evaluation fails without a model."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = TrainingConfig(
                log_dir=f"{tmpdir}/logs",
                model_dir=f"{tmpdir}/models",
            )
            trainer = PPOTrainer(config)

            with pytest.raises(ValueError, match="No model loaded"):
                trainer.evaluate()
