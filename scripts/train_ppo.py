#!/usr/bin/env python
"""Train a PPO agent to play CartesSociete.

Usage:
    uv run python scripts/train_ppo.py --timesteps 100000 --opponent random
    uv run python scripts/train_ppo.py --timesteps 500000 --opponent heuristic --envs 8
    uv run python scripts/train_ppo.py --evaluate --model models/ppo/ppo_cartes_final
"""

import argparse
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.rl import PPOTrainer, TrainingConfig  # noqa: E402

# Validation constants
MIN_TIMESTEPS = 1000
MAX_TIMESTEPS = 10_000_000
MIN_ENVS = 1
MAX_ENVS = 64

OPPONENT_TYPES = ["random", "greedy", "heuristic"]


def train(args: argparse.Namespace) -> int:
    """Train a PPO agent.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    print("=" * 60)
    print("PPO TRAINING - CartesSociete")
    print("=" * 60)

    config = TrainingConfig(
        total_timesteps=args.timesteps,
        opponent_type=args.opponent,
        n_envs=args.envs,
        seed=args.seed,
        verbose=1 if not args.quiet else 0,
        eval_freq=args.eval_freq,
        save_freq=args.save_freq,
        log_dir=args.log_dir,
        model_dir=args.model_dir,
    )

    print("Configuration:")
    print(f"  Total timesteps: {config.total_timesteps:,}")
    print(f"  Opponent type: {config.opponent_type}")
    print(f"  Parallel envs: {config.n_envs}")
    print(f"  Seed: {config.seed}")
    print(f"  Log dir: {config.log_dir}")
    print(f"  Model dir: {config.model_dir}")
    print("-" * 60)

    trainer = PPOTrainer(config)

    try:
        trainer.train()
        print("\nTraining completed successfully!")

        # Run evaluation
        print("\nEvaluating trained model...")
        for opponent in OPPONENT_TYPES:
            results = trainer.evaluate(n_episodes=100, opponent_type=opponent)
            print(
                f"  vs {opponent}: "
                f"{results['win_rate']:.1%} win rate "
                f"({results['wins']}/{results['games']} games)"
            )

        return 0

    except KeyboardInterrupt:
        print("\nTraining interrupted by user.")
        return 1
    except Exception as e:
        print(f"\nError during training: {e}", file=sys.stderr)
        return 1


def evaluate(args: argparse.Namespace) -> int:
    """Evaluate a trained PPO model.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    if not args.model:
        print("Error: --model is required for evaluation", file=sys.stderr)
        return 1

    model_path = Path(args.model)
    if not model_path.exists() and not model_path.with_suffix(".zip").exists():
        print(f"Error: Model not found: {args.model}", file=sys.stderr)
        return 1

    print("=" * 60)
    print("PPO EVALUATION - CartesSociete")
    print("=" * 60)
    print(f"Model: {args.model}")
    print(f"Episodes per opponent: {args.eval_episodes}")
    print("-" * 60)

    trainer = PPOTrainer()
    trainer.load(args.model)

    total_wins = 0
    total_games = 0

    for opponent in OPPONENT_TYPES:
        results = trainer.evaluate(
            n_episodes=args.eval_episodes,
            opponent_type=opponent,
        )

        total_wins += results["wins"]
        total_games += results["games"]

        print(
            f"vs {opponent:12s}: "
            f"{results['win_rate']:6.1%} win rate "
            f"({results['wins']:3d}/{results['games']} games) "
            f"| Avg reward: {results['avg_reward']:.2f} "
            f"| Avg length: {results['avg_game_length']:.1f}"
        )

    overall_win_rate = total_wins / total_games if total_games > 0 else 0
    print("-" * 60)
    print(
        f"Overall:       {overall_win_rate:6.1%} win rate "
        f"({total_wins}/{total_games} games)"
    )

    return 0


def main() -> int:
    """Main entry point for the script.

    Returns:
        Exit code (0 for success).
    """
    parser = argparse.ArgumentParser(
        description="Train and evaluate PPO agents for CartesSociete.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick training run
  uv run python scripts/train_ppo.py --timesteps 100000

  # Full training with heuristic opponent
  uv run python scripts/train_ppo.py --timesteps 500000 --opponent heuristic

  # Train with more parallel environments
  uv run python scripts/train_ppo.py --timesteps 1000000 --envs 8

  # Evaluate a trained model
  uv run python scripts/train_ppo.py --evaluate --model models/ppo/ppo_cartes_final
        """,
    )

    # Mode selection
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Evaluate a trained model instead of training",
    )

    # Training arguments
    parser.add_argument(
        "--timesteps",
        type=int,
        default=500_000,
        help=f"Timesteps (default: 500000, range: {MIN_TIMESTEPS}-{MAX_TIMESTEPS})",
    )
    parser.add_argument(
        "--opponent",
        type=str,
        default="random",
        choices=OPPONENT_TYPES,
        help="Type of opponent to train against (default: random)",
    )
    parser.add_argument(
        "--envs",
        type=int,
        default=4,
        help=f"Parallel environments (default: 4, range: {MIN_ENVS}-{MAX_ENVS})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--eval-freq",
        type=int,
        default=10_000,
        help="Steps between evaluations (default: 10000)",
    )
    parser.add_argument(
        "--save-freq",
        type=int,
        default=50_000,
        help="Steps between checkpoint saves (default: 50000)",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default="logs/ppo",
        help="Directory for TensorBoard logs (default: logs/ppo)",
    )
    parser.add_argument(
        "--model-dir",
        type=str,
        default="models/ppo",
        help="Directory for model checkpoints (default: models/ppo)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce output verbosity",
    )

    # Evaluation arguments
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Path to trained model for evaluation",
    )
    parser.add_argument(
        "--eval-episodes",
        type=int,
        default=100,
        help="Episodes per opponent for evaluation (default: 100)",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.evaluate:
        if not MIN_TIMESTEPS <= args.timesteps <= MAX_TIMESTEPS:
            parser.error(
                f"--timesteps must be between {MIN_TIMESTEPS} and {MAX_TIMESTEPS}"
            )
        if not MIN_ENVS <= args.envs <= MAX_ENVS:
            parser.error(f"--envs must be between {MIN_ENVS} and {MAX_ENVS}")

    if args.evaluate:
        return evaluate(args)
    else:
        return train(args)


if __name__ == "__main__":
    sys.exit(main())
