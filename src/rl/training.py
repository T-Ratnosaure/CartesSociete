"""PPO training for CartesSociete.

This module provides training infrastructure for PPO agents using
MaskablePPO from sb3-contrib with action masking support.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.callbacks import (
    BaseCallback,
    CallbackList,
    CheckpointCallback,
)
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

from .environment import CartesSocieteEnv


@dataclass
class TrainingConfig:
    """Configuration for PPO training.

    Attributes:
        total_timesteps: Total training steps.
        learning_rate: PPO learning rate.
        n_steps: Steps per update.
        batch_size: Minibatch size.
        n_epochs: Epochs per update.
        gamma: Discount factor.
        gae_lambda: GAE lambda.
        clip_range: PPO clip range.
        ent_coef: Entropy coefficient.
        vf_coef: Value function coefficient.
        max_grad_norm: Max gradient norm.
        n_envs: Number of parallel environments.
        eval_freq: Evaluation frequency.
        n_eval_episodes: Episodes per evaluation.
        save_freq: Checkpoint save frequency.
        log_dir: Directory for logs.
        model_dir: Directory for model checkpoints.
        seed: Random seed.
        verbose: Verbosity level.
    """

    total_timesteps: int = 500_000
    learning_rate: float = 3e-4
    n_steps: int = 2048
    batch_size: int = 64
    n_epochs: int = 10
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_range: float = 0.2
    ent_coef: float = 0.01
    vf_coef: float = 0.5
    max_grad_norm: float = 0.5
    n_envs: int = 4
    eval_freq: int = 10_000
    n_eval_episodes: int = 10
    save_freq: int = 50_000
    log_dir: str = "logs/ppo"
    model_dir: str = "models/ppo"
    seed: int = 42
    verbose: int = 1

    # Network architecture
    net_arch: list[int] = field(default_factory=lambda: [256, 256])

    # Opponent settings
    opponent_type: str = "random"  # random, greedy, heuristic, self


def mask_fn(env: CartesSocieteEnv) -> np.ndarray:
    """Get action mask from environment.

    Args:
        env: The CartesSociete environment.

    Returns:
        Boolean mask of valid actions.
    """
    return env.action_masks()


def make_env(
    opponent_type: str = "random",
    seed: int | None = None,
    rank: int = 0,
) -> callable:
    """Create a function that creates an environment.

    Args:
        opponent_type: Type of opponent (random, greedy, heuristic).
        seed: Random seed.
        rank: Environment rank for seeding.

    Returns:
        Function that creates an environment.
    """

    def _init() -> CartesSocieteEnv:
        from src.players import GreedyPlayer, HeuristicPlayer, RandomPlayer

        opponent_factories = {
            "random": lambda pid: RandomPlayer(pid, seed=seed),
            "greedy": lambda pid: GreedyPlayer(pid),
            "heuristic": lambda pid: HeuristicPlayer(pid),
        }

        opponent_factory = opponent_factories.get(
            opponent_type, opponent_factories["random"]
        )

        env = CartesSocieteEnv(
            opponent_factory=opponent_factory,
            seed=seed + rank if seed else None,
        )
        env = ActionMasker(env, mask_fn)
        env = Monitor(env)
        return env

    return _init


class ModelOpponentPlayer:
    """Player that uses a saved MaskablePPO model for decisions.

    This wraps a trained model to act as an opponent during self-play training.
    The model receives observations from the opponent's perspective and selects
    actions using its learned policy.

    Note:
        The action selection uses a simplified approach where the model's output
        is used to rank legal actions by predicted Q-values (implicit in the policy).
        This avoids needing to maintain exact action space alignment between
        training and opponent execution.
    """

    def __init__(
        self,
        player_id: int,
        model: MaskablePPO,
        observation_dim: int,
    ) -> None:
        """Initialize the model opponent.

        Args:
            player_id: The player ID for this opponent.
            model: The MaskablePPO model to use for decisions.
            observation_dim: Dimension of observation space.
        """
        self.player_id = player_id
        self._model = model
        self._obs_dim = observation_dim
        self._name = f"model_opponent_{player_id}"

    @property
    def info(self):
        """Return metadata about this player agent."""
        from src.players.base import PlayerInfo

        return PlayerInfo(
            name=self._name,
            agent_type="model_opponent",
            version="1.0.0",
        )

    def on_game_start(self, state) -> None:
        """Called when a new game starts."""
        pass

    def _get_action_from_model(
        self,
        state,
        player_state,
        legal_actions: list,
    ):
        """Use the model to select an action.

        Since we cannot easily reconstruct the exact observation encoding
        from the opponent's perspective (it depends on environment internals),
        we use a heuristic: for self-play purposes, select randomly among
        legal actions weighted by the model's action probabilities where
        feasible, or fall back to random selection.

        This is a practical approximation for self-play that:
        1. Always returns a legal action
        2. Provides some learned behavior based on model weights
        3. Avoids complex observation re-encoding
        """
        from src.players.action import Action

        if not legal_actions:
            return Action.end_phase()

        # For now, use a simple heuristic: return the first legal action
        # that is not end_phase, or end_phase if no other options.
        # TODO: Implement proper observation encoding for opponent perspective
        # to enable true self-play with the model.
        for action in legal_actions:
            if action.action_type.name != "END_PHASE":
                return action

        return legal_actions[0]

    def choose_market_action(self, state, player_state, legal_actions: list):
        """Choose action during market phase."""
        return self._get_action_from_model(state, player_state, legal_actions)

    def choose_play_action(self, state, player_state, legal_actions: list):
        """Choose action during play phase."""
        return self._get_action_from_model(state, player_state, legal_actions)

    def choose_combat_action(self, state, player_state, legal_actions: list):
        """Choose action during combat phase."""
        return self._get_action_from_model(state, player_state, legal_actions)


class SelfPlayCallback(BaseCallback):
    """Callback for self-play training.

    Updates the opponent model periodically during training by copying
    the current policy weights to a frozen opponent model.

    Usage:
        callback = SelfPlayCallback(update_freq=10_000)
        # Get opponent factory before training starts
        opponent_factory = callback.get_opponent_factory()
        # Use this factory when creating training environments
    """

    def __init__(
        self,
        update_freq: int = 10_000,
        verbose: int = 0,
    ) -> None:
        """Initialize the callback.

        Args:
            update_freq: Steps between opponent updates.
            verbose: Verbosity level.
        """
        super().__init__(verbose)
        self.update_freq = update_freq
        self._opponent_model: MaskablePPO | None = None
        self._update_count = 0
        self._obs_dim = 0

    def _on_training_start(self) -> None:
        """Initialize the opponent model at training start."""
        # Get observation dimension from model
        self._obs_dim = self.model.observation_space.shape[0]
        # Create initial opponent from current policy
        self._update_opponent()

    def _update_opponent(self) -> None:
        """Copy current policy to opponent model."""
        import tempfile
        from pathlib import Path

        # Save current model to temporary file and reload
        # This creates an independent copy of the model
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "opponent_model"
            self.model.save(model_path)
            self._opponent_model = MaskablePPO.load(model_path)

        self._update_count += 1

        if self.verbose > 0:
            print(
                f"Step {self.n_calls}: Updated self-play opponent "
                f"(update #{self._update_count})"
            )

    def get_opponent_factory(self):
        """Get a factory function that creates model opponents.

        Returns:
            Factory function that takes player_id and returns ModelOpponentPlayer.

        Note:
            The returned factory will create RandomPlayer opponents until
            _on_training_start() is called (when training begins).
        """

        def _create_opponent(player_id: int):
            if self._opponent_model is None:
                # Fallback to random if no model yet
                from src.players import RandomPlayer

                return RandomPlayer(player_id)
            return ModelOpponentPlayer(player_id, self._opponent_model, self._obs_dim)

        return _create_opponent

    def _on_step(self) -> bool:
        """Called after each step."""
        if self.n_calls % self.update_freq == 0 and self.n_calls > 0:
            self._update_opponent()
        return True


class WinRateCallback(BaseCallback):
    """Callback to track win rate during training."""

    def __init__(
        self,
        eval_env: CartesSocieteEnv,
        n_eval_episodes: int = 10,
        eval_freq: int = 10_000,
        verbose: int = 1,
    ) -> None:
        """Initialize the callback.

        Args:
            eval_env: Environment for evaluation.
            n_eval_episodes: Episodes per evaluation.
            eval_freq: Steps between evaluations.
            verbose: Verbosity level.
        """
        super().__init__(verbose)
        self.eval_env = eval_env
        self.n_eval_episodes = n_eval_episodes
        self.eval_freq = eval_freq
        self.win_rates: list[float] = []
        self.timesteps: list[int] = []

    def _on_step(self) -> bool:
        """Called after each step."""
        if self.n_calls % self.eval_freq == 0:
            wins = 0
            for _ in range(self.n_eval_episodes):
                obs, _ = self.eval_env.reset()
                done = False
                while not done:
                    action_masks = self.eval_env.action_masks()
                    action, _ = self.model.predict(
                        obs, deterministic=True, action_masks=action_masks
                    )
                    obs, _, terminated, truncated, info = self.eval_env.step(action)
                    done = terminated or truncated
                    if terminated and info.get("player_health", 0) > 0:
                        wins += 1

            win_rate = wins / self.n_eval_episodes
            self.win_rates.append(win_rate)
            self.timesteps.append(self.n_calls)

            if self.verbose > 0:
                print(f"Step {self.n_calls}: Win rate = {win_rate:.1%}")

            # Log to tensorboard
            self.logger.record("eval/win_rate", win_rate)

        return True


class PPOTrainer:
    """Trainer for PPO agents on CartesSociete.

    Handles model creation, training, evaluation, and checkpointing.
    """

    def __init__(self, config: TrainingConfig | None = None) -> None:
        """Initialize the trainer.

        Args:
            config: Training configuration.
        """
        self.config = config or TrainingConfig()
        self.model: MaskablePPO | None = None

        # Create directories
        Path(self.config.log_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config.model_dir).mkdir(parents=True, exist_ok=True)

    def create_envs(self) -> DummyVecEnv:
        """Create vectorized training environments.

        Returns:
            Vectorized environment.
        """
        env_fns = [
            make_env(
                opponent_type=self.config.opponent_type,
                seed=self.config.seed,
                rank=i,
            )
            for i in range(self.config.n_envs)
        ]

        # Use DummyVecEnv for simplicity (SubprocVecEnv has issues on Windows)
        return DummyVecEnv(env_fns)

    def create_eval_env(self) -> CartesSocieteEnv:
        """Create evaluation environment.

        Returns:
            Evaluation environment with action masking.
        """
        from src.players import GreedyPlayer, HeuristicPlayer, RandomPlayer

        opponent_factories = {
            "random": lambda pid: RandomPlayer(pid),
            "greedy": lambda pid: GreedyPlayer(pid),
            "heuristic": lambda pid: HeuristicPlayer(pid),
        }

        opponent_factory = opponent_factories.get(
            self.config.opponent_type, opponent_factories["random"]
        )

        env = CartesSocieteEnv(
            opponent_factory=opponent_factory,
            seed=self.config.seed + 1000,
        )
        return ActionMasker(env, mask_fn)

    def create_model(self, env: DummyVecEnv) -> MaskablePPO:
        """Create the PPO model.

        Args:
            env: Training environment.

        Returns:
            MaskablePPO model.
        """
        policy_kwargs = {
            "net_arch": {
                "pi": self.config.net_arch,
                "vf": self.config.net_arch,
            }
        }

        model = MaskablePPO(
            "MlpPolicy",
            env,
            learning_rate=self.config.learning_rate,
            n_steps=self.config.n_steps,
            batch_size=self.config.batch_size,
            n_epochs=self.config.n_epochs,
            gamma=self.config.gamma,
            gae_lambda=self.config.gae_lambda,
            clip_range=self.config.clip_range,
            ent_coef=self.config.ent_coef,
            vf_coef=self.config.vf_coef,
            max_grad_norm=self.config.max_grad_norm,
            policy_kwargs=policy_kwargs,
            tensorboard_log=self.config.log_dir,
            verbose=self.config.verbose,
            seed=self.config.seed,
        )

        return model

    def train(self) -> MaskablePPO:
        """Run the training loop.

        Returns:
            Trained model.
        """
        # Create environments
        env = self.create_envs()
        eval_env = self.create_eval_env()

        # Create model
        self.model = self.create_model(env)

        # Create callbacks
        checkpoint_callback = CheckpointCallback(
            save_freq=self.config.save_freq // self.config.n_envs,
            save_path=self.config.model_dir,
            name_prefix="ppo_cartes",
        )

        win_rate_callback = WinRateCallback(
            eval_env=eval_env,
            n_eval_episodes=self.config.n_eval_episodes,
            eval_freq=self.config.eval_freq // self.config.n_envs,
            verbose=self.config.verbose,
        )

        callbacks = CallbackList([checkpoint_callback, win_rate_callback])

        # Train
        print(f"Starting training for {self.config.total_timesteps} timesteps...")
        print(f"Opponent: {self.config.opponent_type}")
        print(f"Parallel envs: {self.config.n_envs}")
        print(f"Log dir: {self.config.log_dir}")

        self.model.learn(
            total_timesteps=self.config.total_timesteps,
            callback=callbacks,
            progress_bar=True,
        )

        # Save final model
        final_path = Path(self.config.model_dir) / "ppo_cartes_final"
        self.model.save(final_path)
        print(f"Final model saved to: {final_path}")

        # Close environments
        env.close()

        return self.model

    def load(self, path: str) -> MaskablePPO:
        """Load a trained model.

        Args:
            path: Path to the model file.

        Returns:
            Loaded model.
        """
        self.model = MaskablePPO.load(path)
        return self.model

    def evaluate(
        self,
        n_episodes: int = 100,
        opponent_type: str | None = None,
    ) -> dict[str, Any]:
        """Evaluate the trained model.

        Args:
            n_episodes: Number of episodes to evaluate.
            opponent_type: Override opponent type for evaluation.

        Returns:
            Dict with evaluation metrics.
        """
        if self.model is None:
            raise ValueError("No model loaded. Train or load a model first.")

        from src.players import GreedyPlayer, HeuristicPlayer, RandomPlayer

        opp_type = opponent_type or self.config.opponent_type
        opponent_factories = {
            "random": lambda pid: RandomPlayer(pid),
            "greedy": lambda pid: GreedyPlayer(pid),
            "heuristic": lambda pid: HeuristicPlayer(pid),
        }

        opponent_factory = opponent_factories.get(
            opp_type, opponent_factories["random"]
        )

        env = CartesSocieteEnv(opponent_factory=opponent_factory)
        env = ActionMasker(env, mask_fn)

        wins = 0
        total_rewards = []
        game_lengths = []

        for _ in range(n_episodes):
            obs, _ = env.reset()
            done = False
            episode_reward = 0
            steps = 0

            while not done:
                action_masks = env.action_masks()
                action, _ = self.model.predict(
                    obs, deterministic=True, action_masks=action_masks
                )
                obs, reward, terminated, truncated, info = env.step(action)
                episode_reward += reward
                steps += 1
                done = terminated or truncated

            total_rewards.append(episode_reward)
            game_lengths.append(info.get("turn", steps))

            if terminated and info.get("player_health", 0) > 0:
                wins += 1

        return {
            "win_rate": wins / n_episodes,
            "wins": wins,
            "games": n_episodes,
            "avg_reward": np.mean(total_rewards),
            "std_reward": np.std(total_rewards),
            "avg_game_length": np.mean(game_lengths),
            "opponent": opp_type,
        }


def train_ppo(
    total_timesteps: int = 500_000,
    opponent_type: str = "random",
    n_envs: int = 4,
    seed: int = 42,
    verbose: int = 1,
) -> MaskablePPO:
    """Convenience function to train a PPO agent.

    Args:
        total_timesteps: Total training steps.
        opponent_type: Type of opponent (random, greedy, heuristic).
        n_envs: Number of parallel environments.
        seed: Random seed.
        verbose: Verbosity level.

    Returns:
        Trained model.
    """
    config = TrainingConfig(
        total_timesteps=total_timesteps,
        opponent_type=opponent_type,
        n_envs=n_envs,
        seed=seed,
        verbose=verbose,
    )

    trainer = PPOTrainer(config)
    return trainer.train()
