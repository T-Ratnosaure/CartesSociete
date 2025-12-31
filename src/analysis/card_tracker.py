"""Card tracking and analytics for balance analysis.

This module provides CardTracker for collecting and analyzing per-card
statistics from game simulations, helping identify overpowered and
underpowered cards.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.simulation.logger import EventType, GameEvent

if TYPE_CHECKING:
    from src.simulation.runner import GameResult


@dataclass
class CardStats:
    """Statistics for a single card.

    Attributes:
        name: Card name.
        times_bought: Number of times this card was bought.
        times_played: Number of times this card was played to board.
        times_evolved: Number of times this card was evolved.
        games_with_card: Number of games where this card was bought.
        games_won_with_card: Number of games won by players who bought this card.
        total_cost_spent: Total PO spent buying this card.
    """

    name: str
    times_bought: int = 0
    times_played: int = 0
    times_evolved: int = 0
    games_with_card: int = 0
    games_won_with_card: int = 0
    total_cost_spent: int = 0

    @property
    def pick_rate(self) -> float:
        """Rate at which this card is bought when available.

        This is games_with_card / total_games analyzed.
        Must be set externally after computing against total games.
        """
        # This is computed by CardTracker.get_card_report()
        return 0.0

    @property
    def play_rate(self) -> float:
        """Rate at which bought cards are played.

        Returns:
            Ratio of times_played to times_bought.
        """
        if self.times_bought == 0:
            return 0.0
        return self.times_played / self.times_bought

    @property
    def evolution_rate(self) -> float:
        """Rate at which this card is evolved.

        Returns:
            Ratio of evolutions to times bought (normalized for 3 cards per evo).
        """
        if self.times_bought == 0:
            return 0.0
        # Each evolution consumes 3 cards
        return (self.times_evolved * 3) / self.times_bought

    @property
    def win_rate(self) -> float:
        """Win rate when this card is in deck.

        Returns:
            Ratio of games_won_with_card to games_with_card.
        """
        if self.games_with_card == 0:
            return 0.0
        return self.games_won_with_card / self.games_with_card

    @property
    def avg_cost(self) -> float:
        """Average cost paid for this card.

        Returns:
            Average PO spent per purchase.
        """
        if self.times_bought == 0:
            return 0.0
        return self.total_cost_spent / self.times_bought


@dataclass
class CardReport:
    """Report on a card's performance and balance status.

    Attributes:
        stats: Raw statistics for this card.
        total_games: Total games analyzed.
        pick_rate: Actual pick rate across all games.
        relative_pick_rate: Pick rate relative to average.
        relative_win_rate: Win rate relative to baseline (0.5).
        power_score: Combined score indicating power level.
        balance_status: Classification of balance status.
        notes: Analysis notes.
    """

    stats: CardStats
    total_games: int
    pick_rate: float
    relative_pick_rate: float
    relative_win_rate: float
    power_score: float
    balance_status: str
    notes: list[str] = field(default_factory=list)


class CardTracker:
    """Tracks and analyzes card usage across game simulations.

    Collects data from game events to compute per-card statistics
    including pick rates, win correlations, and evolution rates.
    Provides analysis to identify balance issues.

    Example:
        >>> tracker = CardTracker()
        >>> for result in game_results:
        ...     tracker.record_game(result)
        >>> reports = tracker.get_card_reports()
        >>> for report in reports[:5]:
        ...     print(f"{report.stats.name}: {report.balance_status}")
    """

    # Thresholds for balance classification
    OVERPOWERED_WIN_RATE: float = 0.65
    UNDERPOWERED_WIN_RATE: float = 0.35
    HIGH_PICK_RATE: float = 0.5  # Picked in >50% of games
    LOW_PICK_RATE: float = 0.1  # Picked in <10% of games

    def __init__(self) -> None:
        """Initialize an empty tracker."""
        self._card_stats: dict[str, CardStats] = {}
        self._total_games: int = 0
        self._total_wins_by_player: dict[int, int] = defaultdict(int)

        # Per-game tracking (reset each game)
        self._current_game_cards: dict[int, set[str]] = defaultdict(set)

    @property
    def total_games(self) -> int:
        """Get total number of games analyzed."""
        return self._total_games

    @property
    def card_stats(self) -> dict[str, CardStats]:
        """Get all card statistics."""
        return self._card_stats.copy()

    def record_game(self, result: "GameResult") -> None:
        """Record statistics from a completed game.

        Processes all events in the game result to update
        card statistics.

        Args:
            result: Completed game result with events.
        """
        if not result.events:
            return

        self._total_games += 1

        # Reset per-game tracking
        cards_bought_by_player: dict[int, set[str]] = defaultdict(set)

        # Process events
        for event in result.events:
            self._process_event(event, cards_bought_by_player)

        # Update games_with_card and win correlation
        winner_id = result.winner_id

        for player_id, cards in cards_bought_by_player.items():
            for card_name in cards:
                if card_name not in self._card_stats:
                    self._card_stats[card_name] = CardStats(name=card_name)

                stats = self._card_stats[card_name]
                stats.games_with_card += 1

                if player_id == winner_id:
                    stats.games_won_with_card += 1

    def _process_event(
        self,
        event: GameEvent,
        cards_bought_by_player: dict[int, set[str]],
    ) -> None:
        """Process a single game event.

        Args:
            event: The game event to process.
            cards_bought_by_player: Tracking dict for current game.
        """
        if event.event_type == EventType.CARD_BOUGHT:
            card_name = event.data.get("card_name", "")
            cost = event.data.get("cost", 0)
            player_id = event.player_id

            if not card_name or player_id is None:
                return

            # Initialize stats if needed
            if card_name not in self._card_stats:
                self._card_stats[card_name] = CardStats(name=card_name)

            stats = self._card_stats[card_name]
            stats.times_bought += 1
            stats.total_cost_spent += cost

            # Track for this game's win correlation
            cards_bought_by_player[player_id].add(card_name)

        elif event.event_type == EventType.CARD_PLAYED:
            card_name = event.data.get("card_name", "")
            if card_name and card_name in self._card_stats:
                self._card_stats[card_name].times_played += 1

        elif event.event_type == EventType.EVOLUTION:
            base_card = event.data.get("base_card", "")
            if base_card and base_card in self._card_stats:
                self._card_stats[base_card].times_evolved += 1

    def record_games(self, results: list["GameResult"]) -> None:
        """Record statistics from multiple games.

        Args:
            results: List of game results to process.
        """
        for result in results:
            self.record_game(result)

    def get_card_report(self, card_name: str) -> CardReport | None:
        """Generate a detailed report for a specific card.

        Args:
            card_name: Name of the card to analyze.

        Returns:
            CardReport with analysis, or None if card not found.
        """
        if card_name not in self._card_stats:
            return None

        stats = self._card_stats[card_name]
        return self._create_report(stats)

    def get_card_reports(
        self,
        sort_by: str = "power_score",
        descending: bool = True,
    ) -> list[CardReport]:
        """Generate reports for all tracked cards.

        Args:
            sort_by: Attribute to sort by (power_score, pick_rate, win_rate).
            descending: Sort in descending order.

        Returns:
            List of CardReports sorted as specified.
        """
        reports = [
            self._create_report(stats) for stats in self._card_stats.values()
        ]

        if sort_by == "power_score":
            reports.sort(key=lambda r: r.power_score, reverse=descending)
        elif sort_by == "pick_rate":
            reports.sort(key=lambda r: r.pick_rate, reverse=descending)
        elif sort_by == "win_rate":
            reports.sort(key=lambda r: r.stats.win_rate, reverse=descending)
        elif sort_by == "name":
            reports.sort(key=lambda r: r.stats.name, reverse=descending)

        return reports

    def _create_report(self, stats: CardStats) -> CardReport:
        """Create a CardReport from CardStats.

        Args:
            stats: The card statistics.

        Returns:
            CardReport with analysis.
        """
        # Calculate rates
        pick_rate = (
            stats.games_with_card / self._total_games
            if self._total_games > 0
            else 0.0
        )

        # Average pick rate across all cards
        avg_pick_rate = self._calculate_avg_pick_rate()
        relative_pick_rate = (
            pick_rate / avg_pick_rate if avg_pick_rate > 0 else 1.0
        )

        # Win rate relative to baseline 50%
        relative_win_rate = stats.win_rate - 0.5

        # Power score: combination of pick rate and win rate
        # High pick + high win = overpowered
        # Low pick + low win = underpowered
        power_score = (pick_rate * 0.4 + stats.win_rate * 0.6) * 100

        # Determine balance status
        balance_status, notes = self._classify_balance(
            stats, pick_rate, relative_win_rate
        )

        return CardReport(
            stats=stats,
            total_games=self._total_games,
            pick_rate=pick_rate,
            relative_pick_rate=relative_pick_rate,
            relative_win_rate=relative_win_rate,
            power_score=power_score,
            balance_status=balance_status,
            notes=notes,
        )

    def _calculate_avg_pick_rate(self) -> float:
        """Calculate average pick rate across all cards."""
        if not self._card_stats or self._total_games == 0:
            return 0.0

        total_pick_rate = sum(
            s.games_with_card / self._total_games
            for s in self._card_stats.values()
        )
        return total_pick_rate / len(self._card_stats)

    def _classify_balance(
        self,
        stats: CardStats,
        pick_rate: float,
        relative_win_rate: float,
    ) -> tuple[str, list[str]]:
        """Classify a card's balance status.

        Args:
            stats: Card statistics.
            pick_rate: Pick rate across all games.
            relative_win_rate: Win rate minus baseline.

        Returns:
            Tuple of (status_string, notes_list).
        """
        notes: list[str] = []

        # Must-pick detection
        if pick_rate >= self.HIGH_PICK_RATE:
            notes.append(f"Very high pick rate ({pick_rate:.1%})")

        # Win rate analysis
        if stats.win_rate >= self.OVERPOWERED_WIN_RATE:
            notes.append(f"High win correlation ({stats.win_rate:.1%})")
        elif stats.win_rate <= self.UNDERPOWERED_WIN_RATE:
            notes.append(f"Low win correlation ({stats.win_rate:.1%})")

        # Evolution analysis
        if stats.evolution_rate > 0.3:
            notes.append(f"Frequently evolved ({stats.evolution_rate:.1%})")
        elif stats.times_bought >= 10 and stats.evolution_rate < 0.05:
            notes.append("Rarely evolved despite pickups")

        # Classify balance status
        if (
            pick_rate >= self.HIGH_PICK_RATE
            and stats.win_rate >= self.OVERPOWERED_WIN_RATE
        ):
            return "OVERPOWERED", notes
        elif (
            pick_rate >= self.HIGH_PICK_RATE
            and stats.win_rate <= self.UNDERPOWERED_WIN_RATE
        ):
            return "TRAP", notes  # Popular but loses games
        elif (
            pick_rate <= self.LOW_PICK_RATE
            and stats.win_rate >= self.OVERPOWERED_WIN_RATE
        ):
            return "SLEEPER", notes  # Underrated but powerful
        elif (
            pick_rate <= self.LOW_PICK_RATE
            and stats.win_rate <= self.UNDERPOWERED_WIN_RATE
        ):
            return "UNDERPOWERED", notes
        elif stats.win_rate >= self.OVERPOWERED_WIN_RATE:
            return "STRONG", notes
        elif stats.win_rate <= self.UNDERPOWERED_WIN_RATE:
            return "WEAK", notes
        else:
            return "BALANCED", notes

    def get_overpowered_cards(self) -> list[CardReport]:
        """Get list of potentially overpowered cards.

        Returns:
            List of CardReports for cards classified as overpowered or strong.
        """
        reports = self.get_card_reports()
        return [r for r in reports if r.balance_status in ("OVERPOWERED", "STRONG")]

    def get_underpowered_cards(self) -> list[CardReport]:
        """Get list of potentially underpowered cards.

        Returns:
            List of CardReports for cards classified as underpowered or weak.
        """
        reports = self.get_card_reports()
        return [r for r in reports if r.balance_status in ("UNDERPOWERED", "WEAK")]

    def get_trap_cards(self) -> list[CardReport]:
        """Get list of trap cards (popular but underperforming).

        Returns:
            List of CardReports for cards classified as traps.
        """
        reports = self.get_card_reports()
        return [r for r in reports if r.balance_status == "TRAP"]

    def get_sleeper_cards(self) -> list[CardReport]:
        """Get list of sleeper cards (unpopular but strong).

        Returns:
            List of CardReports for cards classified as sleepers.
        """
        reports = self.get_card_reports()
        return [r for r in reports if r.balance_status == "SLEEPER"]

    def summary(self) -> str:
        """Generate a human-readable summary.

        Returns:
            Multi-line string with balance analysis summary.
        """
        reports = self.get_card_reports()

        lines = [
            "=" * 60,
            "CARD BALANCE ANALYSIS",
            "=" * 60,
            f"Total Games Analyzed: {self._total_games}",
            f"Total Cards Tracked: {len(self._card_stats)}",
            "",
        ]

        # Count by status
        status_counts: dict[str, int] = defaultdict(int)
        for report in reports:
            status_counts[report.balance_status] += 1

        lines.append("Balance Distribution:")
        for status in [
            "OVERPOWERED",
            "STRONG",
            "BALANCED",
            "WEAK",
            "UNDERPOWERED",
            "TRAP",
            "SLEEPER",
        ]:
            count = status_counts.get(status, 0)
            if count > 0:
                lines.append(f"  {status}: {count}")

        # Top 5 by power score
        lines.append("")
        lines.append("Top 5 Cards by Power Score:")
        for i, report in enumerate(reports[:5], 1):
            lines.append(
                f"  {i}. {report.stats.name}: "
                f"{report.power_score:.1f} ({report.balance_status})"
            )

        # Bottom 5 by power score
        lines.append("")
        lines.append("Bottom 5 Cards by Power Score:")
        for i, report in enumerate(reports[-5:], 1):
            lines.append(
                f"  {i}. {report.stats.name}: "
                f"{report.power_score:.1f} ({report.balance_status})"
            )

        # Most picked
        lines.append("")
        lines.append("Most Picked Cards:")
        pick_sorted = sorted(reports, key=lambda r: r.pick_rate, reverse=True)
        for report in pick_sorted[:5]:
            lines.append(
                f"  - {report.stats.name}: "
                f"{report.pick_rate:.1%} pick rate, "
                f"{report.stats.win_rate:.1%} win rate"
            )

        # Problematic cards
        overpowered = self.get_overpowered_cards()
        if overpowered:
            lines.append("")
            lines.append("!!! POTENTIALLY OVERPOWERED:")
            for report in overpowered[:3]:
                lines.append(
                    f"  - {report.stats.name}: "
                    f"Pick {report.pick_rate:.1%}, Win {report.stats.win_rate:.1%}"
                )
                for note in report.notes:
                    lines.append(f"    > {note}")

        underpowered = self.get_underpowered_cards()
        if underpowered:
            lines.append("")
            lines.append("!!! POTENTIALLY UNDERPOWERED:")
            for report in underpowered[:3]:
                lines.append(
                    f"  - {report.stats.name}: "
                    f"Pick {report.pick_rate:.1%}, Win {report.stats.win_rate:.1%}"
                )
                for note in report.notes:
                    lines.append(f"    > {note}")

        return "\n".join(lines)

    def clear(self) -> None:
        """Clear all tracked statistics."""
        self._card_stats.clear()
        self._total_games = 0
        self._total_wins_by_player.clear()
        self._current_game_cards.clear()
