#!/usr/bin/env python
"""Run a single game between AI agents.

Usage:
    uv run python scripts/run_game.py --p1 random --p2 greedy
    uv run python scripts/run_game.py --p1 heuristic --p2 mcts --seed 42 --verbose
    uv run python scripts/run_game.py --p1 random --p2 greedy --log-file game.json
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.players import (  # noqa: E402
    GreedyPlayer,
    HeuristicPlayer,
    MCTSPlayer,
    RandomPlayer,
)
from src.simulation import GameRunner  # noqa: E402

PLAYER_TYPES = {
    "random": RandomPlayer,
    "greedy": GreedyPlayer,
    "heuristic": HeuristicPlayer,
    "mcts": MCTSPlayer,
}


def create_player(player_type: str, player_id: int, seed: int | None = None) -> object:
    """Create a player of the specified type.

    Args:
        player_type: Type of player (random, greedy, heuristic, mcts).
        player_id: The player's ID.
        seed: Optional random seed.

    Returns:
        Player instance.

    Raises:
        ValueError: If player type is unknown.
    """
    if player_type not in PLAYER_TYPES:
        raise ValueError(
            f"Unknown player type: {player_type}. "
            f"Available: {', '.join(PLAYER_TYPES.keys())}"
        )

    player_class = PLAYER_TYPES[player_type]

    # Check if player supports seed
    if player_type in ("random", "mcts") and seed is not None:
        return player_class(player_id=player_id, seed=seed)
    return player_class(player_id=player_id)


def main() -> int:
    """Main entry point for the script.

    Returns:
        Exit code (0 for success).
    """
    parser = argparse.ArgumentParser(
        description="Run a single game between AI agents.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python scripts/run_game.py --p1 random --p2 greedy
  uv run python scripts/run_game.py --p1 heuristic --p2 mcts --seed 42
  uv run python scripts/run_game.py --p1 random --p2 greedy --log-file game.json
        """,
    )

    parser.add_argument(
        "--p1",
        type=str,
        required=True,
        choices=PLAYER_TYPES.keys(),
        help="Player 1 type",
    )
    parser.add_argument(
        "--p2",
        type=str,
        required=True,
        choices=PLAYER_TYPES.keys(),
        help="Player 2 type",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed game progress",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="File to save game events (JSON format)",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=100,
        help="Maximum turns before draw (default: 100)",
    )

    args = parser.parse_args()

    # Create players
    try:
        player1 = create_player(args.p1, player_id=0, seed=args.seed)
        player2 = create_player(args.p2, player_id=1, seed=args.seed)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    players = [player1, player2]

    if args.verbose:
        print(f"Game: {player1.info.agent_type} vs {player2.info.agent_type}")
        if args.seed is not None:
            print(f"Seed: {args.seed}")
        print("-" * 40)

    # Run the game
    runner = GameRunner(
        players=players,
        seed=args.seed,
        log_events=True,
        max_turns=args.max_turns,
    )

    result = runner.run_game()

    # Print results
    if result.winner_id is not None:
        winner = players[result.winner_id]
        print(f"Winner: {winner.name} ({result.winner_type})")
    else:
        print("Result: Draw (timeout)")

    print(f"Turns: {result.turns}")

    if args.verbose:
        print("\nPlayer Statistics:")
        for player_id, stats in result.player_stats.items():
            player = players[player_id]
            print(f"\n  {player.name} ({stats.player_type}):")
            print(f"    Cards Bought: {stats.cards_bought}")
            print(f"    Cards Played: {stats.cards_played}")
            print(f"    Evolutions: {stats.evolutions}")
            print(f"    Damage Dealt: {stats.damage_dealt}")
            print(f"    Damage Taken: {stats.damage_taken}")
            print(f"    Final Health: {stats.final_health}")

    # Save events if requested
    if args.log_file:
        events_data = [e.to_dict() for e in result.events]
        with open(args.log_file, "w", encoding="utf-8") as f:
            json.dump(events_data, f, indent=2)
        print(f"\nEvents saved to: {args.log_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
