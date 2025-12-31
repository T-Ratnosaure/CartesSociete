#!/usr/bin/env python
"""Run card balance analysis using the CardTracker.

This script runs many games with logging enabled to collect card
statistics and identify overpowered/underpowered cards.

Usage:
    uv run python scripts/run_card_analysis.py --games 100
    uv run python scripts/run_card_analysis.py --games 500 --seed 42 --verbose
"""

import argparse
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.analysis import CardTracker  # noqa: E402
from src.players import GreedyPlayer, HeuristicPlayer, RandomPlayer  # noqa: E402
from src.simulation import MatchConfig, MatchRunner  # noqa: E402


def main() -> int:
    """Run card balance analysis."""
    parser = argparse.ArgumentParser(
        description="Run card balance analysis with CardTracker."
    )
    parser.add_argument(
        "--games",
        type=int,
        default=100,
        help="Number of games to run (default: 100)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress during analysis",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("CARD BALANCE ANALYSIS")
    print("=" * 60)
    print(f"Games: {args.games}")
    print(f"Seed: {args.seed}")
    print()

    # Create tracker
    tracker = CardTracker()

    # Define player factories
    factories = [
        lambda pid: RandomPlayer(pid),
        lambda pid: GreedyPlayer(pid),
        lambda pid: HeuristicPlayer(pid),
    ]

    # Run games with logging enabled
    runner = MatchRunner()
    games_per_pair = args.games // 3  # Split across 3 matchups

    print(f"Running {games_per_pair} games per matchup...")
    print()

    total_results = []
    matchup_idx = 0

    # Run all pairwise matchups
    for i in range(len(factories)):
        for j in range(i + 1, len(factories)):
            p1 = factories[i](0)
            p2 = factories[j](1)
            type1 = p1.info.agent_type
            type2 = p2.info.agent_type

            if args.verbose:
                print(f"Running: {type1} vs {type2}...")

            config = MatchConfig(
                num_games=games_per_pair,
                player_factories=[factories[i], factories[j]],
                rotate_positions=True,
                base_seed=args.seed + matchup_idx * games_per_pair,
                log_events=True,  # Enable logging for card tracking
                verbose=False,
            )

            result = runner.run_match(config)
            total_results.extend(result.results)

            if args.verbose:
                print(f"  {type1}: {result.wins.get(type1, 0)} wins")
                print(f"  {type2}: {result.wins.get(type2, 0)} wins")
                print()

            matchup_idx += 1

    # Process all game results
    print(f"Processing {len(total_results)} game results...")
    tracker.record_games(total_results)

    # Print summary
    print()
    print(tracker.summary())

    # Detailed analysis for overpowered/underpowered cards
    print()
    print("=" * 60)
    print("DETAILED CARD ANALYSIS")
    print("=" * 60)

    reports = tracker.get_card_reports()

    # Top 10 by pick rate
    print()
    print("TOP 10 MOST PICKED CARDS:")
    print("-" * 50)
    pick_sorted = sorted(reports, key=lambda r: r.pick_rate, reverse=True)
    for i, report in enumerate(pick_sorted[:10], 1):
        print(
            f"{i:2}. {report.stats.name:20} "
            f"Pick: {report.pick_rate:5.1%}  "
            f"Win: {report.stats.win_rate:5.1%}  "
            f"[{report.balance_status}]"
        )

    # Top 10 by win rate (minimum 5 games)
    print()
    print("TOP 10 HIGHEST WIN RATE (min 5 pickups):")
    print("-" * 50)
    win_sorted = [r for r in reports if r.stats.games_with_card >= 5]
    win_sorted = sorted(win_sorted, key=lambda r: r.stats.win_rate, reverse=True)
    for i, report in enumerate(win_sorted[:10], 1):
        print(
            f"{i:2}. {report.stats.name:20} "
            f"Win: {report.stats.win_rate:5.1%}  "
            f"Pick: {report.pick_rate:5.1%}  "
            f"[{report.balance_status}]"
        )

    # Bottom 10 by win rate (minimum 5 games)
    print()
    print("BOTTOM 10 LOWEST WIN RATE (min 5 pickups):")
    print("-" * 50)
    for i, report in enumerate(win_sorted[-10:][::-1], 1):
        print(
            f"{i:2}. {report.stats.name:20} "
            f"Win: {report.stats.win_rate:5.1%}  "
            f"Pick: {report.pick_rate:5.1%}  "
            f"[{report.balance_status}]"
        )

    # Most evolved cards
    print()
    print("MOST EVOLVED CARDS:")
    print("-" * 50)
    evo_sorted = sorted(
        reports, key=lambda r: r.stats.times_evolved, reverse=True
    )
    for report in evo_sorted[:5]:
        if report.stats.times_evolved > 0:
            print(
                f"  - {report.stats.name:20} "
                f"Evolved: {report.stats.times_evolved}x  "
                f"Rate: {report.stats.evolution_rate:5.1%}"
            )

    # Summary recommendations
    print()
    print("=" * 60)
    print("BALANCE RECOMMENDATIONS")
    print("=" * 60)

    overpowered = tracker.get_overpowered_cards()
    if overpowered:
        print()
        print("[!] CONSIDER NERFING:")
        for report in overpowered[:5]:
            print(f"  - {report.stats.name}")
            for note in report.notes:
                print(f"    > {note}")

    underpowered = tracker.get_underpowered_cards()
    if underpowered:
        print()
        print("[!] CONSIDER BUFFING:")
        for report in underpowered[:5]:
            print(f"  - {report.stats.name}")
            for note in report.notes:
                print(f"    > {note}")

    traps = tracker.get_trap_cards()
    if traps:
        print()
        print("[!] TRAP CARDS (popular but underperforming):")
        for report in traps[:3]:
            print(f"  - {report.stats.name}")
            for note in report.notes:
                print(f"    > {note}")

    if not overpowered and not underpowered and not traps:
        print()
        print("[OK] No major balance issues detected!")
        print("     All cards appear to be performing within expected ranges.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
