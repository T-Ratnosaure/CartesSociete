#!/usr/bin/env python
"""Run greedy vs greedy analysis for card balance.

Usage:
    uv run python scripts/run_greedy_analysis.py --games 500
"""

import argparse
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.analysis import CardTracker  # noqa: E402
from src.players import GreedyPlayer  # noqa: E402
from src.simulation import MatchConfig, MatchRunner  # noqa: E402


def main() -> int:
    """Run greedy vs greedy card analysis."""
    parser = argparse.ArgumentParser(
        description="Run greedy vs greedy card balance analysis."
    )
    parser.add_argument(
        "--games",
        type=int,
        default=500,
        help="Number of games to run (default: 500)",
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

    print("=" * 70)
    print("GREEDY VS GREEDY CARD BALANCE ANALYSIS")
    print("=" * 70)
    print(f"Games: {args.games}")
    print(f"Seed: {args.seed}")
    print()

    # Create tracker
    tracker = CardTracker()

    def factory(pid: int) -> GreedyPlayer:
        return GreedyPlayer(pid)

    # Run games with logging enabled
    print(f"Running {args.games} games (greedy vs greedy)...")
    print()

    config = MatchConfig(
        num_games=args.games,
        player_factories=[factory, factory],
        rotate_positions=True,
        base_seed=args.seed,
        log_events=True,  # Enable logging for card tracking
        verbose=args.verbose,
    )

    runner = MatchRunner()
    result = runner.run_match(config)

    print(f"Completed: {result.games_played} games")
    print(f"Average game length: {result.avg_game_length:.1f} turns")
    print()

    # Process all game results
    print("Processing game results for card statistics...")
    tracker.record_games(result.results)

    # Print summary
    print()
    print(tracker.summary())

    # Detailed analysis
    print()
    print("=" * 70)
    print("DETAILED CARD STATISTICS")
    print("=" * 70)

    reports = tracker.get_card_reports()

    # Top 15 by pick rate
    print()
    print("TOP 15 MOST BOUGHT CARDS:")
    print("-" * 60)
    print(f"{'Rank':<5} {'Card':<25} {'Bought':<8} {'Pick%':<8} {'Win%':<8} {'Status'}")
    print("-" * 60)
    pick_sorted = sorted(reports, key=lambda r: r.stats.times_bought, reverse=True)
    for i, report in enumerate(pick_sorted[:15], 1):
        print(
            f"{i:<5} {report.stats.name:<25} "
            f"{report.stats.times_bought:<8} "
            f"{report.pick_rate:>6.1%}  "
            f"{report.stats.win_rate:>6.1%}  "
            f"[{report.balance_status}]"
        )

    # Top 15 by win rate (minimum 10 games)
    print()
    print("TOP 15 HIGHEST WIN RATE (min 10 pickups):")
    print("-" * 60)
    print(f"{'Rank':<5} {'Card':<25} {'Games':<8} {'Win%':<8} {'Pick%':<8} {'Status'}")
    print("-" * 60)
    win_sorted = [r for r in reports if r.stats.games_with_card >= 10]
    win_sorted = sorted(win_sorted, key=lambda r: r.stats.win_rate, reverse=True)
    for i, report in enumerate(win_sorted[:15], 1):
        print(
            f"{i:<5} {report.stats.name:<25} "
            f"{report.stats.games_with_card:<8} "
            f"{report.stats.win_rate:>6.1%}  "
            f"{report.pick_rate:>6.1%}  "
            f"[{report.balance_status}]"
        )

    # Bottom 15 by win rate (minimum 10 games)
    print()
    print("BOTTOM 15 LOWEST WIN RATE (min 10 pickups):")
    print("-" * 60)
    print(f"{'Rank':<5} {'Card':<25} {'Games':<8} {'Win%':<8} {'Pick%':<8} {'Status'}")
    print("-" * 60)
    for i, report in enumerate(reversed(win_sorted[-15:]), 1):
        print(
            f"{i:<5} {report.stats.name:<25} "
            f"{report.stats.games_with_card:<8} "
            f"{report.stats.win_rate:>6.1%}  "
            f"{report.pick_rate:>6.1%}  "
            f"[{report.balance_status}]"
        )

    # Most evolved cards
    print()
    print("MOST EVOLVED CARDS:")
    print("-" * 60)
    evo_sorted = sorted(reports, key=lambda r: r.stats.times_evolved, reverse=True)
    for report in evo_sorted[:10]:
        if report.stats.times_evolved > 0:
            print(
                f"  {report.stats.name:<25} "
                f"Evolved: {report.stats.times_evolved:>3}x  "
                f"Rate: {report.stats.evolution_rate:>5.1%}  "
                f"Win: {report.stats.win_rate:>5.1%}"
            )

    # Cards by family (aggregate stats)
    print()
    print("=" * 70)
    print("FAMILY ANALYSIS")
    print("=" * 70)

    # Group cards by family prefix
    from collections import defaultdict

    family_stats: dict[str, dict] = defaultdict(
        lambda: {"cards": 0, "bought": 0, "games": 0, "wins": 0}
    )

    for report in reports:
        # Extract family from card name pattern or use "Unknown"
        name = report.stats.name
        # Common family prefixes
        families = [
            "Lapin",
            "Raton",
            "Cyborg",
            "Dragon",
            "Nature",
            "Magicien",
            "Chevalier",
            "Orc",
            "Nain",
            "Elfe",
            "Gobelin",
            "Pirate",
            "Barbare",
            "Mort-Vivant",
            "Mutant",
            "Demon",
        ]
        family = "Other"
        for f in families:
            if f.lower() in name.lower():
                family = f
                break

        family_stats[family]["cards"] += 1
        family_stats[family]["bought"] += report.stats.times_bought
        family_stats[family]["games"] += report.stats.games_with_card
        family_stats[family]["wins"] += report.stats.games_won_with_card

    print()
    print(f"{'Family':<15} {'Cards':<8} {'Bought':<10} {'Avg Win%':<10}")
    print("-" * 50)
    for family, stats in sorted(
        family_stats.items(), key=lambda x: x[1]["bought"], reverse=True
    ):
        win_rate = stats["wins"] / stats["games"] if stats["games"] > 0 else 0
        print(
            f"{family:<15} {stats['cards']:<8} {stats['bought']:<10} {win_rate:>8.1%}"
        )

    # Balance recommendations
    print()
    print("=" * 70)
    print("BALANCE RECOMMENDATIONS")
    print("=" * 70)

    overpowered = tracker.get_overpowered_cards()
    if overpowered:
        print()
        print("[!] POTENTIALLY OVERPOWERED (consider nerfing):")
        for report in overpowered[:10]:
            print(f"  - {report.stats.name}")
            print(f"    Pick: {report.pick_rate:.1%}, Win: {report.stats.win_rate:.1%}")
            for note in report.notes:
                print(f"    > {note}")

    underpowered = tracker.get_underpowered_cards()
    if underpowered:
        print()
        print("[!] POTENTIALLY UNDERPOWERED (consider buffing):")
        for report in underpowered[:10]:
            print(f"  - {report.stats.name}")
            print(f"    Pick: {report.pick_rate:.1%}, Win: {report.stats.win_rate:.1%}")
            for note in report.notes:
                print(f"    > {note}")

    traps = tracker.get_trap_cards()
    if traps:
        print()
        print("[!] TRAP CARDS (popular but underperforming):")
        for report in traps[:5]:
            print(f"  - {report.stats.name}")
            print(f"    Pick: {report.pick_rate:.1%}, Win: {report.stats.win_rate:.1%}")
            for note in report.notes:
                print(f"    > {note}")

    sleepers = tracker.get_sleeper_cards()
    if sleepers:
        print()
        print("[*] SLEEPER CARDS (unpopular but strong):")
        for report in sleepers[:5]:
            print(f"  - {report.stats.name}")
            print(f"    Pick: {report.pick_rate:.1%}, Win: {report.stats.win_rate:.1%}")
            for note in report.notes:
                print(f"    > {note}")

    if not overpowered and not underpowered and not traps:
        print()
        print("[OK] No major balance issues detected!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
