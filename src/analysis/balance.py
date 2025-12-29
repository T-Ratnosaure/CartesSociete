"""Balance analysis tools for game simulation.

This module provides tools for analyzing game balance through simulation,
including win rate analysis, strategy effectiveness, and card power levels.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.players.base import Player

from src.simulation import MatchConfig, MatchResult, MatchRunner


@dataclass
class BalanceReport:
    """Report summarizing balance analysis results.

    Attributes:
        total_games: Total games simulated.
        win_rates: Win rate per player type.
        matchup_results: Results for each head-to-head matchup.
        avg_game_length: Average game length across all games.
        dominance_warnings: List of balance concerns found.
    """

    total_games: int
    win_rates: dict[str, float]
    matchup_results: dict[tuple[str, str], "MatchupStats"]
    avg_game_length: float
    dominance_warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """Generate human-readable summary.

        Returns:
            Multi-line string with balance report.
        """
        lines = [
            "=" * 50,
            "BALANCE ANALYSIS REPORT",
            "=" * 50,
            f"Total Games Analyzed: {self.total_games}",
            f"Average Game Length: {self.avg_game_length:.1f} turns",
            "",
            "Overall Win Rates:",
        ]

        for player_type, rate in sorted(
            self.win_rates.items(), key=lambda x: x[1], reverse=True
        ):
            lines.append(f"  {player_type}: {rate:.1%}")

        if self.dominance_warnings:
            lines.append("")
            lines.append("BALANCE WARNINGS:")
            for warning in self.dominance_warnings:
                lines.append(f"  ! {warning}")

        lines.append("")
        lines.append("Head-to-Head Results:")
        for (type1, type2), stats in sorted(self.matchup_results.items()):
            lines.append(f"  {type1} vs {type2}:")
            lines.append(f"    {type1}: {stats.win_rate_1:.1%} ({stats.wins_1} wins)")
            lines.append(f"    {type2}: {stats.win_rate_2:.1%} ({stats.wins_2} wins)")
            lines.append(f"    Draws: {stats.draws}")

        return "\n".join(lines)


@dataclass
class MatchupStats:
    """Statistics for a specific matchup.

    Attributes:
        type_1: First player type.
        type_2: Second player type.
        games: Total games played.
        wins_1: Wins by type 1.
        wins_2: Wins by type 2.
        draws: Number of draws.
        avg_length: Average game length.
    """

    type_1: str
    type_2: str
    games: int
    wins_1: int
    wins_2: int
    draws: int
    avg_length: float

    @property
    def win_rate_1(self) -> float:
        """Win rate for type 1."""
        if self.games == 0:
            return 0.0
        return self.wins_1 / self.games

    @property
    def win_rate_2(self) -> float:
        """Win rate for type 2."""
        if self.games == 0:
            return 0.0
        return self.wins_2 / self.games

    @property
    def draw_rate(self) -> float:
        """Draw rate."""
        if self.games == 0:
            return 0.0
        return self.draws / self.games


@dataclass
class BalanceConfig:
    """Configuration for balance analysis.

    Attributes:
        games_per_matchup: Number of games per head-to-head matchup.
        dominance_threshold: Win rate above which triggers dominance warning.
        min_win_rate_threshold: Win rate below which triggers weakness warning.
        base_seed: Base random seed for reproducibility.
    """

    games_per_matchup: int = 100
    dominance_threshold: float = 0.70
    min_win_rate_threshold: float = 0.30
    base_seed: int | None = 42

    # Bounds
    MAX_GAMES_PER_MATCHUP: int = field(default=1000, repr=False, init=False)

    def __post_init__(self) -> None:
        """Validate configuration."""
        if not 1 <= self.games_per_matchup <= self.MAX_GAMES_PER_MATCHUP:
            raise ValueError(
                f"games_per_matchup must be between 1 and {self.MAX_GAMES_PER_MATCHUP}"
            )
        if not 0.5 <= self.dominance_threshold <= 1.0:
            raise ValueError("dominance_threshold must be between 0.5 and 1.0")
        if not 0.0 <= self.min_win_rate_threshold <= 0.5:
            raise ValueError("min_win_rate_threshold must be between 0.0 and 0.5")


class BalanceAnalyzer:
    """Analyzes game balance through simulation.

    Uses the simulation framework to run games between different
    player types and analyze the results for balance issues.

    Example:
        >>> from src.players import RandomPlayer, GreedyPlayer
        >>> analyzer = BalanceAnalyzer()
        >>> factories = [
        ...     lambda pid: RandomPlayer(pid),
        ...     lambda pid: GreedyPlayer(pid),
        ... ]
        >>> report = analyzer.run_analysis(factories)
        >>> print(report.summary())
    """

    def __init__(self, config: BalanceConfig | None = None) -> None:
        """Initialize the balance analyzer.

        Args:
            config: Analysis configuration.
        """
        self.config = config or BalanceConfig()
        self._runner = MatchRunner()

    def run_analysis(
        self,
        player_factories: list[Callable[[int], "Player"]],
        verbose: bool = False,
    ) -> BalanceReport:
        """Run complete balance analysis between player types.

        Runs a round-robin tournament between all player types
        and analyzes the results for balance issues.

        Args:
            player_factories: List of factory functions creating players.
            verbose: Whether to print progress.

        Returns:
            BalanceReport with analysis results.
        """
        if len(player_factories) < 2:
            raise ValueError("Need at least 2 player factories for analysis")

        # Run round-robin tournament
        results = self._runner.run_round_robin(
            player_factories=player_factories,
            games_per_matchup=self.config.games_per_matchup,
            base_seed=self.config.base_seed,
            verbose=verbose,
        )

        # Process results
        return self._create_report(results)

    def run_matchup(
        self,
        factory_1: Callable[[int], "Player"],
        factory_2: Callable[[int], "Player"],
        num_games: int | None = None,
        verbose: bool = False,
    ) -> MatchupStats:
        """Run a specific matchup between two player types.

        Args:
            factory_1: Factory for player type 1.
            factory_2: Factory for player type 2.
            num_games: Number of games (uses config default if None).
            verbose: Whether to print progress.

        Returns:
            MatchupStats for this matchup.
        """
        games = num_games or self.config.games_per_matchup

        config = MatchConfig(
            num_games=games,
            player_factories=[factory_1, factory_2],
            rotate_positions=True,
            base_seed=self.config.base_seed,
            verbose=verbose,
        )

        result = self._runner.run_match(config)

        # Get player types
        p1 = factory_1(0)
        p2 = factory_2(1)
        type_1 = p1.info.agent_type
        type_2 = p2.info.agent_type

        return MatchupStats(
            type_1=type_1,
            type_2=type_2,
            games=result.games_played,
            wins_1=result.wins.get(type_1, 0),
            wins_2=result.wins.get(type_2, 0),
            draws=result.draws,
            avg_length=result.avg_game_length,
        )

    def _create_report(
        self,
        results: dict[tuple[str, str], MatchResult],
    ) -> BalanceReport:
        """Create balance report from match results.

        Args:
            results: Results from round-robin tournament.

        Returns:
            Comprehensive balance report.
        """
        # Aggregate statistics
        total_games = 0
        total_turns = 0
        wins_by_type: dict[str, int] = {}
        games_by_type: dict[str, int] = {}
        matchup_stats: dict[tuple[str, str], MatchupStats] = {}

        for (type1, type2), result in results.items():
            total_games += result.games_played
            total_turns += result.games_played * result.avg_game_length

            # Track wins
            wins_by_type[type1] = wins_by_type.get(type1, 0) + result.wins.get(type1, 0)
            wins_by_type[type2] = wins_by_type.get(type2, 0) + result.wins.get(type2, 0)

            # Track total games per type
            games_by_type[type1] = games_by_type.get(type1, 0) + result.games_played
            games_by_type[type2] = games_by_type.get(type2, 0) + result.games_played

            # Create matchup stats
            matchup_stats[(type1, type2)] = MatchupStats(
                type_1=type1,
                type_2=type2,
                games=result.games_played,
                wins_1=result.wins.get(type1, 0),
                wins_2=result.wins.get(type2, 0),
                draws=result.draws,
                avg_length=result.avg_game_length,
            )

        # Calculate overall win rates
        win_rates = {}
        for ptype in wins_by_type:
            if games_by_type.get(ptype, 0) > 0:
                win_rates[ptype] = wins_by_type[ptype] / games_by_type[ptype]
            else:
                win_rates[ptype] = 0.0

        avg_game_length = total_turns / total_games if total_games > 0 else 0.0

        # Check for balance issues
        warnings = self._check_balance_issues(win_rates, matchup_stats)

        return BalanceReport(
            total_games=total_games,
            win_rates=win_rates,
            matchup_results=matchup_stats,
            avg_game_length=avg_game_length,
            dominance_warnings=warnings,
        )

    def _check_balance_issues(
        self,
        win_rates: dict[str, float],
        matchup_stats: dict[tuple[str, str], MatchupStats],
    ) -> list[str]:
        """Check for balance issues and generate warnings.

        Args:
            win_rates: Overall win rates per type.
            matchup_stats: Head-to-head matchup statistics.

        Returns:
            List of warning messages.
        """
        warnings: list[str] = []

        # Check for dominant strategies
        for ptype, rate in win_rates.items():
            if rate >= self.config.dominance_threshold:
                warnings.append(
                    f"{ptype} appears dominant with {rate:.1%} overall win rate"
                )
            elif rate <= self.config.min_win_rate_threshold:
                warnings.append(
                    f"{ptype} appears weak with only {rate:.1%} overall win rate"
                )

        # Check for hard counters in matchups
        for (type1, type2), stats in matchup_stats.items():
            if stats.win_rate_1 >= self.config.dominance_threshold:
                warnings.append(
                    f"{type1} hard counters {type2} ({stats.win_rate_1:.1%} win rate)"
                )
            elif stats.win_rate_2 >= self.config.dominance_threshold:
                warnings.append(
                    f"{type2} hard counters {type1} ({stats.win_rate_2:.1%} win rate)"
                )

        # Check for high draw rates
        for (type1, type2), stats in matchup_stats.items():
            if stats.draw_rate >= 0.5:
                warnings.append(
                    f"High draw rate ({stats.draw_rate:.1%}) between "
                    f"{type1} and {type2} - possible stalemate issues"
                )

        return warnings


def quick_balance_check(
    player_factories: list[Callable[[int], "Player"]],
    games_per_matchup: int = 50,
    seed: int | None = 42,
) -> BalanceReport:
    """Run a quick balance check with default settings.

    Convenience function for rapid balance testing.

    Args:
        player_factories: Player factory functions to test.
        games_per_matchup: Games per matchup (default 50).
        seed: Random seed for reproducibility.

    Returns:
        BalanceReport with results.
    """
    config = BalanceConfig(
        games_per_matchup=games_per_matchup,
        base_seed=seed,
    )
    analyzer = BalanceAnalyzer(config)
    return analyzer.run_analysis(player_factories)
