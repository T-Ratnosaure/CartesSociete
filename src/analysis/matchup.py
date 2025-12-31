"""Matchup analysis tools for detailed head-to-head statistics.

This module provides statistical analysis of matchups between player types,
including confidence intervals, effect sizes, and statistical significance.
"""

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.simulation import MatchResult

from .balance import MatchupStats

# Z-scores for common confidence levels (from standard normal distribution)
# These are the critical values for two-tailed tests
Z_SCORES: dict[float, float] = {
    0.80: 1.282,
    0.85: 1.440,
    0.90: 1.645,
    0.95: 1.960,
    0.99: 2.576,
}

# Chi-square critical values for df=1 at common alpha levels
# Used for testing independence in 2x2 contingency tables
CHI_SQUARE_CRITICAL: dict[float, float] = {
    0.10: 2.706,  # alpha = 0.10
    0.05: 3.841,  # alpha = 0.05
    0.01: 6.635,  # alpha = 0.01
    0.001: 10.828,  # alpha = 0.001
}


@dataclass
class StatisticalMatchup:
    """Extended matchup statistics with confidence intervals.

    Attributes:
        base_stats: Basic matchup statistics.
        win_rate_1_ci: 95% confidence interval for type 1 win rate.
        win_rate_2_ci: 95% confidence interval for type 2 win rate.
        is_significant: Whether the difference is statistically significant.
        effect_size: Cohen's h effect size for the win rate difference.
    """

    base_stats: MatchupStats
    win_rate_1_ci: tuple[float, float]
    win_rate_2_ci: tuple[float, float]
    is_significant: bool
    effect_size: float

    @property
    def advantage(self) -> str:
        """Determine which player has the advantage.

        Returns:
            Description of advantage.
        """
        if not self.is_significant:
            return "No significant advantage"

        diff = self.base_stats.win_rate_1 - self.base_stats.win_rate_2
        if abs(diff) < 0.05:
            return "Negligible advantage"

        winner = self.base_stats.type_1 if diff > 0 else self.base_stats.type_2
        magnitude = abs(diff)

        if magnitude >= 0.30:
            return f"Strong advantage: {winner}"
        elif magnitude >= 0.15:
            return f"Moderate advantage: {winner}"
        else:
            return f"Slight advantage: {winner}"

    def summary(self) -> str:
        """Generate summary of statistical matchup.

        Returns:
            Multi-line summary string.
        """
        stats = self.base_stats
        lines = [
            f"Matchup: {stats.type_1} vs {stats.type_2}",
            f"Games: {stats.games}",
            "",
            f"{stats.type_1}:",
            f"  Win Rate: {stats.win_rate_1:.1%}",
            f"  95% CI: [{self.win_rate_1_ci[0]:.1%}, {self.win_rate_1_ci[1]:.1%}]",
            "",
            f"{stats.type_2}:",
            f"  Win Rate: {stats.win_rate_2:.1%}",
            f"  95% CI: [{self.win_rate_2_ci[0]:.1%}, {self.win_rate_2_ci[1]:.1%}]",
            "",
            f"Draws: {stats.draws} ({stats.draw_rate:.1%})",
            f"Avg Game Length: {stats.avg_length:.1f} turns",
            "",
            f"Statistical Significance: {'Yes' if self.is_significant else 'No'}",
            f"Effect Size (Cohen's h): {self.effect_size:.3f}",
            f"Verdict: {self.advantage}",
        ]
        return "\n".join(lines)


def wilson_score_interval(
    successes: int,
    trials: int,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """Calculate Wilson score confidence interval for a proportion.

    More accurate than normal approximation, especially for extreme proportions.

    Args:
        successes: Number of successes.
        trials: Total number of trials.
        confidence: Confidence level (default 0.95). Supported values:
            0.80, 0.85, 0.90, 0.95, 0.99.

    Returns:
        (lower_bound, upper_bound) tuple.

    Raises:
        ValueError: If confidence level is not supported.
    """
    if trials == 0:
        return (0.0, 1.0)

    # Look up z-score for confidence level
    if confidence not in Z_SCORES:
        supported = ", ".join(str(c) for c in sorted(Z_SCORES.keys()))
        raise ValueError(
            f"Unsupported confidence level {confidence}. Supported values: {supported}"
        )
    z = Z_SCORES[confidence]

    p_hat = successes / trials
    denominator = 1 + z * z / trials

    center = (p_hat + z * z / (2 * trials)) / denominator
    margin = z * math.sqrt(p_hat * (1 - p_hat) / trials + z * z / (4 * trials * trials))
    margin = margin / denominator

    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)

    return (lower, upper)


def cohens_h(p1: float, p2: float) -> float:
    """Calculate Cohen's h effect size for two proportions.

    Interpretation:
    - 0.2: Small effect
    - 0.5: Medium effect
    - 0.8: Large effect

    Args:
        p1: First proportion.
        p2: Second proportion.

    Returns:
        Cohen's h effect size.
    """

    def arcsin_transform(p: float) -> float:
        # Clamp to valid range
        p = max(0.0, min(1.0, p))
        return 2 * math.asin(math.sqrt(p))

    return abs(arcsin_transform(p1) - arcsin_transform(p2))


def chi_square_test(
    wins_1: int,
    wins_2: int,
    draws: int,
    alpha: float = 0.05,
) -> tuple[float, bool]:
    """Perform chi-square test for independence.

    Tests whether win rates are significantly different from expected.

    Args:
        wins_1: Wins for player type 1.
        wins_2: Wins for player type 2.
        draws: Number of draws.
        alpha: Significance level (default 0.05). Supported: 0.10, 0.05, 0.01, 0.001.

    Returns:
        (chi_square_statistic, is_significant at specified alpha)

    Raises:
        ValueError: If alpha is not a supported significance level.
    """
    # Validate alpha
    if alpha not in CHI_SQUARE_CRITICAL:
        supported = ", ".join(str(a) for a in sorted(CHI_SQUARE_CRITICAL.keys()))
        raise ValueError(
            f"Unsupported alpha level {alpha}. Supported values: {supported}"
        )

    total = wins_1 + wins_2 + draws
    if total == 0:
        return (0.0, False)

    # Expected values under null hypothesis (equal win rates)
    decided_games = wins_1 + wins_2
    if decided_games == 0:
        return (0.0, False)

    expected = decided_games / 2

    # Explicit guard for division by zero
    # (defensive, since decided_games > 0 implies expected > 0)
    if expected == 0:
        return (0.0, False)

    # Chi-square statistic
    chi_sq = ((wins_1 - expected) ** 2 + (wins_2 - expected) ** 2) / expected

    # Compare against critical value from lookup table
    critical_value = CHI_SQUARE_CRITICAL[alpha]
    is_significant = chi_sq > critical_value

    return (chi_sq, is_significant)


def analyze_matchup(stats: MatchupStats) -> StatisticalMatchup:
    """Perform full statistical analysis of a matchup.

    Args:
        stats: Basic matchup statistics.

    Returns:
        StatisticalMatchup with confidence intervals and significance.
    """
    # Calculate confidence intervals
    ci_1 = wilson_score_interval(stats.wins_1, stats.games)
    ci_2 = wilson_score_interval(stats.wins_2, stats.games)

    # Statistical significance
    _, is_significant = chi_square_test(stats.wins_1, stats.wins_2, stats.draws)

    # Effect size
    # Use wins out of decided games for cleaner comparison
    decided = stats.wins_1 + stats.wins_2
    if decided > 0:
        p1 = stats.wins_1 / decided
        p2 = stats.wins_2 / decided
        effect = cohens_h(p1, p2)
    else:
        effect = 0.0

    return StatisticalMatchup(
        base_stats=stats,
        win_rate_1_ci=ci_1,
        win_rate_2_ci=ci_2,
        is_significant=is_significant,
        effect_size=effect,
    )


def analyze_match_result(
    result: "MatchResult",
    type_1: str,
    type_2: str,
) -> StatisticalMatchup:
    """Analyze a MatchResult from the simulation framework.

    Args:
        result: MatchResult from MatchRunner.
        type_1: Name of first player type.
        type_2: Name of second player type.

    Returns:
        StatisticalMatchup with full analysis.
    """
    stats = MatchupStats(
        type_1=type_1,
        type_2=type_2,
        games=result.games_played,
        wins_1=result.wins.get(type_1, 0),
        wins_2=result.wins.get(type_2, 0),
        draws=result.draws,
        avg_length=result.avg_game_length,
    )
    return analyze_matchup(stats)


@dataclass
class MatchupMatrix:
    """Matrix of all head-to-head matchups.

    Attributes:
        player_types: List of player type names.
        matchups: Dict mapping (type1, type2) to StatisticalMatchup.
    """

    player_types: list[str]
    matchups: dict[tuple[str, str], StatisticalMatchup]

    def get_matchup(self, type_1: str, type_2: str) -> StatisticalMatchup | None:
        """Get matchup between two types.

        Args:
            type_1: First player type.
            type_2: Second player type.

        Returns:
            StatisticalMatchup or None if not found.
        """
        return self.matchups.get((type_1, type_2)) or self.matchups.get(
            (type_2, type_1)
        )

    def get_rankings(self) -> list[tuple[str, float]]:
        """Calculate overall rankings based on win rates.

        Uses average win rate across all matchups.

        Returns:
            List of (player_type, avg_win_rate) sorted by win rate.
        """
        win_rates: dict[str, list[float]] = {pt: [] for pt in self.player_types}

        for (type_1, type_2), matchup in self.matchups.items():
            # Add win rate vs this opponent
            win_rates[type_1].append(matchup.base_stats.win_rate_1)
            win_rates[type_2].append(matchup.base_stats.win_rate_2)

        # Calculate averages
        rankings = []
        for ptype, rates in win_rates.items():
            if rates:
                avg = sum(rates) / len(rates)
                rankings.append((ptype, avg))

        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings

    def summary(self) -> str:
        """Generate summary of all matchups.

        Returns:
            Multi-line string with rankings and matrix.
        """
        lines = [
            "=" * 60,
            "MATCHUP MATRIX ANALYSIS",
            "=" * 60,
            "",
            "Overall Rankings:",
        ]

        for rank, (ptype, rate) in enumerate(self.get_rankings(), 1):
            lines.append(f"  {rank}. {ptype}: {rate:.1%} avg win rate")

        lines.append("")
        lines.append("Head-to-Head Summary:")

        for (type_1, type_2), matchup in sorted(self.matchups.items()):
            lines.append(f"  {type_1} vs {type_2}: {matchup.advantage}")

        return "\n".join(lines)


def create_matchup_matrix(
    results: dict[tuple[str, str], "MatchResult"],
) -> MatchupMatrix:
    """Create a matchup matrix from round-robin results.

    Args:
        results: Results dict from MatchRunner.run_round_robin().

    Returns:
        MatchupMatrix with statistical analysis of all matchups.
    """
    player_types: set[str] = set()
    matchups: dict[tuple[str, str], StatisticalMatchup] = {}

    for (type_1, type_2), result in results.items():
        player_types.add(type_1)
        player_types.add(type_2)
        matchups[(type_1, type_2)] = analyze_match_result(result, type_1, type_2)

    return MatchupMatrix(
        player_types=sorted(player_types),
        matchups=matchups,
    )
