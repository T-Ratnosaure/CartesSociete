"""Analysis tools for game balance and statistics.

This module provides tools for analyzing game balance, player performance,
card statistics, and matchup statistics through simulation.
"""

from .balance import (
    BalanceAnalyzer,
    BalanceConfig,
    BalanceReport,
    MatchupStats,
    quick_balance_check,
)
from .card_tracker import (
    CardReport,
    CardStats,
    CardTracker,
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
    # Card tracking
    "CardReport",
    "CardStats",
    "CardTracker",
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
