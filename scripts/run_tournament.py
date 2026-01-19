#!/usr/bin/env python
"""Run a tournament (multiple games) between AI agents.

Usage:
    uv run python scripts/run_tournament.py --p1 random --p2 greedy --games 100
    uv run python scripts/run_tournament.py --p1 heuristic --p2 mcts --seed 42
    uv run python scripts/run_tournament.py --round-robin --games 20
"""

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.players import (  # noqa: E402
    AtlantidePlayer,
    CyborgPlayer,
    GreedyPlayer,
    HallOfWinPlayer,
    HeuristicPlayer,
    LapinPlayer,
    MCTSPlayer,
    NaturePlayer,
    NeigePlayer,
    NinjaPlayer,
    RandomPlayer,
    RatonPlayer,
)
from src.players.base import Player  # noqa: E402
from src.simulation import MatchConfig, MatchRunner  # noqa: E402

PLAYER_TYPES = {
    # Generic strategies
    "random": RandomPlayer,
    "greedy": GreedyPlayer,
    "heuristic": HeuristicPlayer,
    "mcts": MCTSPlayer,
    # Family-focused strategies
    "lapin": LapinPlayer,
    "cyborg": CyborgPlayer,
    "nature": NaturePlayer,
    "atlantide": AtlantidePlayer,
    "ninja": NinjaPlayer,
    "neige": NeigePlayer,
    "raton": RatonPlayer,
    "hallofwin": HallOfWinPlayer,
}

# Validation constants (matches MatchConfig.MAX_GAMES)
MIN_GAMES = 1
MAX_GAMES = 10000


def validate_output_path(path_str: str) -> Path:
    """Validate and sanitize output file path.

    Args:
        path_str: The path string to validate.

    Returns:
        Validated Path object.

    Raises:
        ValueError: If path is invalid or attempts path traversal.
    """
    path = Path(path_str).resolve()

    # Check for path traversal attempts
    if ".." in path_str:
        raise ValueError("Path traversal not allowed: '..' in path")

    # Ensure path is within project or current directory
    cwd = Path.cwd().resolve()
    try:
        path.relative_to(cwd)
    except ValueError:
        # Path is outside cwd, check if it's within project root
        try:
            path.relative_to(project_root.resolve())
        except ValueError:
            raise ValueError(
                f"Output path must be within project directory: {path}"
            ) from None

    return path


def create_player_factory(
    player_type: str,
) -> Callable[[int], Player]:
    """Create a factory function for a player type.

    Args:
        player_type: Type of player (random, greedy, heuristic, mcts).

    Returns:
        Factory function that creates players.

    Raises:
        ValueError: If player type is unknown.
    """
    if player_type not in PLAYER_TYPES:
        raise ValueError(
            f"Unknown player type: {player_type}. "
            f"Available: {', '.join(PLAYER_TYPES.keys())}"
        )

    player_class = PLAYER_TYPES[player_type]

    def factory(player_id: int) -> Player:
        return player_class(player_id=player_id)

    return factory


def run_head_to_head(args: argparse.Namespace) -> int:
    """Run a head-to-head match between two player types.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    try:
        factory1 = create_player_factory(args.p1)
        factory2 = create_player_factory(args.p2)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Tournament: {args.p1} vs {args.p2}")
    print(f"Games: {args.games}")
    if args.seed is not None:
        print(f"Base Seed: {args.seed}")
    print("-" * 40)

    config = MatchConfig(
        num_games=args.games,
        player_factories=[factory1, factory2],
        rotate_positions=not args.no_rotate,
        base_seed=args.seed,
        verbose=args.verbose,
    )

    runner = MatchRunner()
    result = runner.run_match(config)

    # Print results
    print("\n" + result.summary())

    # Save results if requested
    if args.output:
        try:
            output_path = validate_output_path(args.output)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        output_data = {
            "type": "head_to_head",
            "player1": args.p1,
            "player2": args.p2,
            "games_played": result.games_played,
            "wins": result.wins,
            "draws": result.draws,
            "win_rates": result.win_rates,
            "avg_game_length": result.avg_game_length,
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)
        print(f"\nResults saved to: {output_path}")

    return 0


def run_round_robin(args: argparse.Namespace) -> int:
    """Run a round-robin tournament between all player types.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    # Get player types to include
    if args.players:
        player_types = args.players.split(",")
        for pt in player_types:
            if pt not in PLAYER_TYPES:
                print(f"Error: Unknown player type: {pt}", file=sys.stderr)
                return 1
    else:
        player_types = list(PLAYER_TYPES.keys())

    print("Round-Robin Tournament")
    print(f"Players: {', '.join(player_types)}")
    print(f"Games per matchup: {args.games}")
    if args.seed is not None:
        print(f"Base Seed: {args.seed}")
    print("-" * 40)

    factories = [create_player_factory(pt) for pt in player_types]

    runner = MatchRunner()
    results = runner.run_round_robin(
        player_factories=factories,
        games_per_matchup=args.games,
        base_seed=args.seed,
        verbose=args.verbose,
    )

    # Print summary
    print("\n" + runner.get_round_robin_summary(results))

    # Save results if requested
    if args.output:
        try:
            output_path = validate_output_path(args.output)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        output_data = {
            "type": "round_robin",
            "players": player_types,
            "games_per_matchup": args.games,
            "matchups": {},
        }
        for (type1, type2), result in results.items():
            key = f"{type1}_vs_{type2}"
            output_data["matchups"][key] = {
                "games_played": result.games_played,
                "wins": result.wins,
                "draws": result.draws,
                "win_rates": result.win_rates,
                "avg_game_length": result.avg_game_length,
            }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)
        print(f"\nResults saved to: {output_path}")

    return 0


def main() -> int:
    """Main entry point for the script.

    Returns:
        Exit code (0 for success).
    """
    parser = argparse.ArgumentParser(
        description="Run tournaments between AI agents.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Head-to-head match
  uv run python scripts/run_tournament.py --p1 random --p2 greedy --games 100

  # Round-robin with all players
  uv run python scripts/run_tournament.py --round-robin --games 20

  # Round-robin with specific players
  uv run python scripts/run_tournament.py --round-robin --players random,greedy
        """,
    )

    parser.add_argument(
        "--round-robin",
        action="store_true",
        help="Run round-robin tournament between all player types",
    )
    parser.add_argument(
        "--p1",
        type=str,
        choices=PLAYER_TYPES.keys(),
        help="Player 1 type (for head-to-head)",
    )
    parser.add_argument(
        "--p2",
        type=str,
        choices=PLAYER_TYPES.keys(),
        help="Player 2 type (for head-to-head)",
    )
    parser.add_argument(
        "--players",
        type=str,
        default=None,
        help="Comma-separated player types for round-robin (default: all)",
    )
    parser.add_argument(
        "--games",
        type=int,
        default=100,
        help=f"Number of games (default: 100, range: {MIN_GAMES}-{MAX_GAMES})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Base random seed for reproducibility",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress during tournament",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="File to save results (JSON format)",
    )
    parser.add_argument(
        "--no-rotate",
        action="store_true",
        help="Don't rotate player positions between games",
    )

    args = parser.parse_args()

    # Validate games bounds
    if not MIN_GAMES <= args.games <= MAX_GAMES:
        parser.error(
            f"--games must be between {MIN_GAMES} and {MAX_GAMES}, got {args.games}"
        )

    # Validate arguments
    if args.round_robin:
        return run_round_robin(args)
    elif args.p1 and args.p2:
        return run_head_to_head(args)
    else:
        parser.error("Must specify either --round-robin or both --p1 and --p2")


if __name__ == "__main__":
    sys.exit(main())
