#!/usr/bin/env python
"""Run Lapin vs Lapin analysis for card balance.

This script runs Lapin-focused games to properly evaluate
synergy-dependent cards like Lapincruste.

Usage:
    uv run python scripts/run_lapin_analysis.py --games 200
"""

import argparse
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.analysis import CardTracker  # noqa: E402
from src.players import LapinPlayer  # noqa: E402
from src.simulation import MatchConfig, MatchRunner  # noqa: E402


def main() -> int:
    """Run Lapin vs Lapin card analysis."""
    parser = argparse.ArgumentParser(
        description="Run Lapin vs Lapin card balance analysis."
    )
    parser.add_argument(
        "--games",
        type=int,
        default=200,
        help="Number of games to run (default: 200)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("LAPIN VS LAPIN CARD ANALYSIS")
    print("=" * 70)
    print(f"Games: {args.games}")
    print(f"Seed: {args.seed}")
    print()
    print("This analysis tests how synergy cards perform when players")
    print("actually build around them (Lapin swarm strategy).")
    print()

    # Create tracker
    tracker = CardTracker()

    def factory(pid: int) -> LapinPlayer:
        return LapinPlayer(pid)

    # Run games with logging enabled
    print(f"Running {args.games} games (lapin vs lapin)...")
    print()

    config = MatchConfig(
        num_games=args.games,
        player_factories=[factory, factory],
        rotate_positions=True,
        base_seed=args.seed,
        log_events=True,
        verbose=False,
    )

    runner = MatchRunner()
    result = runner.run_match(config)

    print(f"Completed: {result.games_played} games")
    print(f"Average game length: {result.avg_game_length:.1f} turns")
    print()

    # Process all game results
    tracker.record_games(result.results)

    # Focus on Lapin cards
    reports = tracker.get_card_reports()
    lapin_reports = [r for r in reports if "lapin" in r.stats.name.lower()]

    print("=" * 70)
    print("LAPIN CARDS PERFORMANCE (in Lapin-focused games)")
    print("=" * 70)
    print()
    print(f"{'Card Name':<25} {'Bought':<8} {'Pick%':<8} {'Win%':<8} {'Evolved':<8}")
    print("-" * 65)

    # Sort by times bought
    lapin_reports.sort(key=lambda r: r.stats.times_bought, reverse=True)
    for report in lapin_reports:
        print(
            f"{report.stats.name:<25} "
            f"{report.stats.times_bought:<8} "
            f"{report.pick_rate:>6.1%}  "
            f"{report.stats.win_rate:>6.1%}  "
            f"{report.stats.times_evolved:<8}"
        )

    # Specifically analyze Lapincruste
    print()
    print("=" * 70)
    print("LAPINCRUSTE ANALYSIS")
    print("=" * 70)

    lapincruste_report = None
    for r in reports:
        if "lapincruste" in r.stats.name.lower():
            lapincruste_report = r
            break

    if lapincruste_report:
        stats = lapincruste_report.stats
        print(f"Times Bought: {stats.times_bought}")
        print(f"Pick Rate: {lapincruste_report.pick_rate:.1%}")
        print(f"Win Rate: {stats.win_rate:.1%}")
        print(f"Times Evolved: {stats.times_evolved}")
        print(f"Balance Status: {lapincruste_report.balance_status}")
        print()
        print("Analysis:")
        if stats.win_rate >= 0.5:
            print(
                "  - Lapincruste shows POSITIVE win correlation in Lapin-focused games"
            )
            print("  - This validates it as an ENABLER card, not underpowered")
        else:
            print("  - Lapincruste still shows low win correlation")
            print("  - The Lapin swarm strategy may need stronger support cards")
    else:
        print("Lapincruste not found in results")

    # Compare with other cards
    print()
    print("=" * 70)
    print("TOP PERFORMING CARDS (in Lapin strategy games)")
    print("=" * 70)
    print()

    all_sorted = sorted(
        [r for r in reports if r.stats.games_with_card >= 10],
        key=lambda r: r.stats.win_rate,
        reverse=True,
    )

    print("TOP 10 BY WIN RATE:")
    print(f"{'Card Name':<25} {'Win%':<8} {'Pick%':<8} {'Status'}")
    print("-" * 55)
    for report in all_sorted[:10]:
        print(
            f"{report.stats.name:<25} "
            f"{report.stats.win_rate:>6.1%}  "
            f"{report.pick_rate:>6.1%}  "
            f"[{report.balance_status}]"
        )

    print()
    print("BOTTOM 10 BY WIN RATE:")
    print(f"{'Card Name':<25} {'Win%':<8} {'Pick%':<8} {'Status'}")
    print("-" * 55)
    for report in all_sorted[-10:]:
        print(
            f"{report.stats.name:<25} "
            f"{report.stats.win_rate:>6.1%}  "
            f"{report.pick_rate:>6.1%}  "
            f"[{report.balance_status}]"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
