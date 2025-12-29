"""Tests for balance and matchup analysis tools."""

import pytest

from src.analysis import (
    BalanceAnalyzer,
    BalanceConfig,
    BalanceReport,
    MatchupStats,
    StatisticalMatchup,
    analyze_matchup,
    cohens_h,
    quick_balance_check,
    wilson_score_interval,
)
from src.players import GreedyPlayer, RandomPlayer


class TestBalanceConfig:
    """Tests for BalanceConfig."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = BalanceConfig()
        assert config.games_per_matchup == 100
        assert config.dominance_threshold == 0.70
        assert config.base_seed == 42

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = BalanceConfig(
            games_per_matchup=50,
            dominance_threshold=0.65,
            base_seed=123,
        )
        assert config.games_per_matchup == 50
        assert config.dominance_threshold == 0.65
        assert config.base_seed == 123

    def test_invalid_games_per_matchup(self) -> None:
        """Test that invalid games_per_matchup is rejected."""
        with pytest.raises(ValueError, match="games_per_matchup"):
            BalanceConfig(games_per_matchup=0)

        with pytest.raises(ValueError, match="games_per_matchup"):
            BalanceConfig(games_per_matchup=2000)

    def test_invalid_dominance_threshold(self) -> None:
        """Test that invalid dominance_threshold is rejected."""
        with pytest.raises(ValueError, match="dominance_threshold"):
            BalanceConfig(dominance_threshold=0.3)

        with pytest.raises(ValueError, match="dominance_threshold"):
            BalanceConfig(dominance_threshold=1.5)


class TestMatchupStats:
    """Tests for MatchupStats."""

    def test_create_stats(self) -> None:
        """Test creating matchup stats."""
        stats = MatchupStats(
            type_1="random",
            type_2="greedy",
            games=100,
            wins_1=40,
            wins_2=55,
            draws=5,
            avg_length=15.0,
        )
        assert stats.games == 100
        assert stats.wins_1 == 40
        assert stats.wins_2 == 55

    def test_win_rates(self) -> None:
        """Test win rate calculations."""
        stats = MatchupStats(
            type_1="a",
            type_2="b",
            games=100,
            wins_1=60,
            wins_2=30,
            draws=10,
            avg_length=10.0,
        )
        assert stats.win_rate_1 == 0.60
        assert stats.win_rate_2 == 0.30
        assert stats.draw_rate == 0.10

    def test_zero_games(self) -> None:
        """Test win rates with zero games."""
        stats = MatchupStats(
            type_1="a",
            type_2="b",
            games=0,
            wins_1=0,
            wins_2=0,
            draws=0,
            avg_length=0.0,
        )
        assert stats.win_rate_1 == 0.0
        assert stats.win_rate_2 == 0.0


class TestWilsonScore:
    """Tests for Wilson score confidence interval."""

    def test_basic_interval(self) -> None:
        """Test basic confidence interval calculation."""
        lower, upper = wilson_score_interval(50, 100)
        assert 0.0 <= lower < upper <= 1.0
        # 50% should have interval roughly around 0.4-0.6
        assert lower > 0.35
        assert upper < 0.65

    def test_zero_successes(self) -> None:
        """Test interval with zero successes."""
        lower, upper = wilson_score_interval(0, 100)
        assert lower == 0.0 or lower > 0  # May be slightly > 0
        assert upper < 0.1

    def test_all_successes(self) -> None:
        """Test interval with all successes."""
        lower, upper = wilson_score_interval(100, 100)
        assert lower > 0.9
        assert upper == 1.0 or upper < 1.0  # May be slightly < 1

    def test_zero_trials(self) -> None:
        """Test interval with zero trials."""
        lower, upper = wilson_score_interval(0, 0)
        assert lower == 0.0
        assert upper == 1.0


class TestCohensH:
    """Tests for Cohen's h effect size."""

    def test_equal_proportions(self) -> None:
        """Test effect size with equal proportions."""
        h = cohens_h(0.5, 0.5)
        assert h == 0.0

    def test_different_proportions(self) -> None:
        """Test effect size with different proportions."""
        h = cohens_h(0.7, 0.3)
        assert h > 0.5  # Should be medium-large effect

    def test_extreme_proportions(self) -> None:
        """Test effect size with extreme proportions."""
        h = cohens_h(1.0, 0.0)
        assert h > 1.5  # Very large effect


class TestAnalyzeMatchup:
    """Tests for analyze_matchup function."""

    def test_analyze_balanced_matchup(self) -> None:
        """Test analysis of a balanced matchup."""
        stats = MatchupStats(
            type_1="a",
            type_2="b",
            games=100,
            wins_1=48,
            wins_2=47,
            draws=5,
            avg_length=15.0,
        )
        result = analyze_matchup(stats)

        assert isinstance(result, StatisticalMatchup)
        assert result.base_stats == stats
        assert not result.is_significant  # Nearly equal wins

    def test_analyze_dominant_matchup(self) -> None:
        """Test analysis of a dominant matchup."""
        stats = MatchupStats(
            type_1="strong",
            type_2="weak",
            games=100,
            wins_1=80,
            wins_2=15,
            draws=5,
            avg_length=12.0,
        )
        result = analyze_matchup(stats)

        assert result.is_significant
        assert result.effect_size > 0.5  # Large effect
        assert "strong" in result.advantage.lower()


class TestBalanceAnalyzer:
    """Tests for BalanceAnalyzer."""

    def test_create_analyzer(self) -> None:
        """Test creating a balance analyzer."""
        analyzer = BalanceAnalyzer()
        assert analyzer.config is not None

    def test_create_analyzer_with_config(self) -> None:
        """Test creating analyzer with custom config."""
        config = BalanceConfig(games_per_matchup=20)
        analyzer = BalanceAnalyzer(config)
        assert analyzer.config.games_per_matchup == 20

    def test_run_matchup(self) -> None:
        """Test running a single matchup."""
        config = BalanceConfig(games_per_matchup=5, base_seed=42)
        analyzer = BalanceAnalyzer(config)

        def factory_1(pid: int) -> RandomPlayer:
            return RandomPlayer(player_id=pid, seed=pid)

        def factory_2(pid: int) -> RandomPlayer:
            return RandomPlayer(player_id=pid, seed=pid + 100)

        stats = analyzer.run_matchup(factory_1, factory_2, num_games=5)

        assert stats.games == 5
        assert stats.wins_1 + stats.wins_2 + stats.draws == 5

    def test_run_analysis(self) -> None:
        """Test running full analysis."""
        config = BalanceConfig(games_per_matchup=3, base_seed=42)
        analyzer = BalanceAnalyzer(config)

        factories = [
            lambda pid: RandomPlayer(player_id=pid, seed=pid),
            lambda pid: GreedyPlayer(player_id=pid),
        ]

        report = analyzer.run_analysis(factories)

        assert isinstance(report, BalanceReport)
        assert report.total_games > 0
        # Two different player types: random and greedy
        assert len(report.win_rates) >= 1  # At least one type has wins

    def test_analysis_requires_two_players(self) -> None:
        """Test that analysis requires at least 2 players."""
        analyzer = BalanceAnalyzer()

        with pytest.raises(ValueError, match="at least 2"):
            analyzer.run_analysis([lambda pid: RandomPlayer(pid)])


class TestQuickBalanceCheck:
    """Tests for quick_balance_check convenience function."""

    def test_quick_check(self) -> None:
        """Test quick balance check."""
        factories = [
            lambda pid: RandomPlayer(player_id=pid, seed=pid),
            lambda pid: GreedyPlayer(player_id=pid),
        ]

        report = quick_balance_check(factories, games_per_matchup=3, seed=42)

        assert isinstance(report, BalanceReport)
        assert report.total_games == 3


class TestBalanceReport:
    """Tests for BalanceReport."""

    def test_report_summary(self) -> None:
        """Test generating report summary."""
        report = BalanceReport(
            total_games=100,
            win_rates={"random": 0.4, "greedy": 0.6},
            matchup_results={},
            avg_game_length=15.0,
            dominance_warnings=["greedy appears dominant"],
        )

        summary = report.summary()
        assert "100" in summary
        assert "random" in summary.lower()
        assert "greedy" in summary.lower()
        assert "dominant" in summary.lower()


class TestMatchupMatrix:
    """Tests for MatchupMatrix."""

    def test_create_empty_matrix(self) -> None:
        """Test matrix with no matchups."""
        from src.analysis.matchup import MatchupMatrix

        matrix = MatchupMatrix(player_types=[], matchups={})
        assert matrix.get_rankings() == []

    def test_get_rankings(self) -> None:
        """Test getting rankings from matrix."""
        from src.analysis.matchup import MatchupMatrix

        # Create a simple matchup
        stats = MatchupStats(
            type_1="a",
            type_2="b",
            games=10,
            wins_1=7,
            wins_2=2,
            draws=1,
            avg_length=10.0,
        )
        statistical = analyze_matchup(stats)

        matrix = MatchupMatrix(
            player_types=["a", "b"],
            matchups={("a", "b"): statistical},
        )

        rankings = matrix.get_rankings()
        assert len(rankings) == 2
        # "a" should rank higher with 70% win rate
        assert rankings[0][0] == "a"
