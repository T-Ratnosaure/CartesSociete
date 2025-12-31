"""Analysis tools for game balance and statistics.

This module provides tools for analyzing game balance, player performance,
and matchup statistics through simulation.
"""

from .balance import (
    BalanceAnalyzer,
    BalanceConfig,
    BalanceReport,
    MatchupStats,
    quick_balance_check,
)
from .matchup import (
    CHI_SQUARE_CRITICAL,
    Z_SCORES,
    MatchupMatrix,
    StatisticalMatchup,
    analyze_match_result,
    analyze_matchup,
    chi_square_test,
    cohens_h,
    create_matchup_matrix,
    wilson_score_interval,
)

__all__ = [
    # Balance analysis
    "BalanceAnalyzer",
    "BalanceConfig",
    "BalanceReport",
    "MatchupStats",
    "quick_balance_check",
    # Matchup analysis
    "CHI_SQUARE_CRITICAL",
    "Z_SCORES",
    "MatchupMatrix",
    "StatisticalMatchup",
    "analyze_match_result",
    "analyze_matchup",
    "chi_square_test",
    "cohens_h",
    "create_matchup_matrix",
    "wilson_score_interval",
]
