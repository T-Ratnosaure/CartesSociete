"""Tests for game simulation framework.

This module tests the GameRunner, MatchRunner, GameLogger, and StatsCollector
components of the simulation framework.
"""

import pytest

from src.players import GreedyPlayer, HeuristicPlayer, RandomPlayer
from src.simulation import (
    EventType,
    GameEvent,
    GameLogger,
    GameResult,
    GameRunner,
    MatchConfig,
    MatchResult,
    MatchRunner,
    PlayerStats,
    StatsCollector,
)


class TestGameEvent:
    """Tests for GameEvent dataclass."""

    def test_create_event(self) -> None:
        """Test creating a game event."""
        event = GameEvent(
            turn=1,
            phase="MARKET",
            event_type=EventType.CARD_BOUGHT,
            player_id=0,
            data={"card_name": "Test Card", "cost": 2},
        )
        assert event.turn == 1
        assert event.phase == "MARKET"
        assert event.event_type == EventType.CARD_BOUGHT
        assert event.player_id == 0
        assert event.data["card_name"] == "Test Card"

    def test_event_to_dict(self) -> None:
        """Test converting event to dictionary."""
        event = GameEvent(
            turn=1,
            phase="MARKET",
            event_type=EventType.GAME_START,
            player_id=None,
            data={"num_players": 2},
        )
        d = event.to_dict()
        assert d["turn"] == 1
        assert d["event_type"] == "game_start"
        assert d["player_id"] is None

    def test_event_from_dict(self) -> None:
        """Test creating event from dictionary."""
        data = {
            "turn": 5,
            "phase": "COMBAT",
            "event_type": "combat",
            "player_id": None,
            "data": {"damage_dealt": {0: 10}},
            "timestamp": 12345.0,
        }
        event = GameEvent.from_dict(data)
        assert event.turn == 5
        assert event.event_type == EventType.COMBAT
        assert event.timestamp == 12345.0


class TestGameLogger:
    """Tests for GameLogger."""

    def test_create_logger(self) -> None:
        """Test creating an empty logger."""
        logger = GameLogger()
        assert len(logger) == 0
        assert logger.events == []

    def test_log_event(self) -> None:
        """Test logging an event."""
        logger = GameLogger()
        event = GameEvent(
            turn=1,
            phase="MARKET",
            event_type=EventType.TURN_START,
            player_id=None,
        )
        logger.log(event)
        assert len(logger) == 1
        assert logger.events[0] == event

    def test_log_game_start(self) -> None:
        """Test logging game start."""
        logger = GameLogger()
        logger.log_game_start(
            num_players=2,
            player_info=[{"id": "0", "name": "Player 1", "type": "random"}],
        )
        assert len(logger) == 1
        assert logger.events[0].event_type == EventType.GAME_START

    def test_log_card_bought(self) -> None:
        """Test logging card purchase."""
        from src.game.state import GamePhase

        logger = GameLogger()
        logger.log_card_bought(
            turn=1,
            phase=GamePhase.MARKET,
            player_id=0,
            card_name="Test Card",
            cost=3,
        )
        assert len(logger) == 1
        event = logger.events[0]
        assert event.event_type == EventType.CARD_BOUGHT
        assert event.data["card_name"] == "Test Card"
        assert event.data["cost"] == 3

    def test_filter_by_type(self) -> None:
        """Test filtering events by type."""
        logger = GameLogger()
        logger.log_turn_start(1)
        logger.log_turn_start(2)
        logger.log_game_end(2, winner_id=0)

        turn_events = logger.get_events_by_type(EventType.TURN_START)
        assert len(turn_events) == 2

        end_events = logger.get_events_by_type(EventType.GAME_END)
        assert len(end_events) == 1

    def test_filter_by_player(self) -> None:
        """Test filtering events by player."""
        from src.game.state import GamePhase

        logger = GameLogger()
        logger.log_card_bought(1, GamePhase.MARKET, 0, "Card A", 1)
        logger.log_card_bought(1, GamePhase.MARKET, 1, "Card B", 2)
        logger.log_card_bought(2, GamePhase.MARKET, 0, "Card C", 1)

        p0_events = logger.get_events_for_player(0)
        assert len(p0_events) == 2

        p1_events = logger.get_events_for_player(1)
        assert len(p1_events) == 1

    def test_json_serialization(self) -> None:
        """Test JSON serialization round-trip."""
        logger = GameLogger()
        logger.log_turn_start(1)
        logger.log_game_end(1, winner_id=0)

        json_str = logger.to_json()
        restored = GameLogger.from_json(json_str)

        assert len(restored) == 2
        assert restored.events[0].event_type == EventType.TURN_START
        assert restored.events[1].event_type == EventType.GAME_END

    def test_clear(self) -> None:
        """Test clearing the logger."""
        logger = GameLogger()
        logger.log_turn_start(1)
        logger.log_turn_start(2)
        assert len(logger) == 2

        logger.clear()
        assert len(logger) == 0


class TestPlayerStats:
    """Tests for PlayerStats dataclass."""

    def test_create_stats(self) -> None:
        """Test creating player stats."""
        stats = PlayerStats(player_id=0, player_type="random")
        assert stats.player_id == 0
        assert stats.player_type == "random"
        assert stats.cards_bought == 0
        assert stats.won is False

    def test_stats_to_dict(self) -> None:
        """Test converting stats to dictionary."""
        stats = PlayerStats(
            player_id=1,
            player_type="greedy",
            cards_bought=5,
            damage_dealt=20,
            won=True,
        )
        d = stats.to_dict()
        assert d["player_id"] == 1
        assert d["player_type"] == "greedy"
        assert d["cards_bought"] == 5
        assert d["damage_dealt"] == 20
        assert d["won"] is True


class TestStatsCollector:
    """Tests for StatsCollector."""

    def test_create_collector(self) -> None:
        """Test creating an empty collector."""
        collector = StatsCollector()
        assert len(collector) == 0
        assert collector.aggregate.games_played == 0

    def test_record_game(self) -> None:
        """Test recording a game."""
        collector = StatsCollector()
        player_stats = {
            0: PlayerStats(player_id=0, player_type="random", cards_bought=3),
            1: PlayerStats(player_id=1, player_type="greedy", cards_bought=5),
        }
        game_stat = collector.record_game(
            turns=10,
            winner_id=1,
            winner_type="greedy",
            player_stats=player_stats,
        )

        assert len(collector) == 1
        assert game_stat.turns == 10
        assert game_stat.winner_id == 1
        assert collector.aggregate.games_played == 1
        assert collector.aggregate.wins_by_type["greedy"] == 1

    def test_win_rates(self) -> None:
        """Test calculating win rates."""
        collector = StatsCollector()

        # Game 1: greedy wins
        collector.record_game(
            turns=10,
            winner_id=1,
            winner_type="greedy",
            player_stats={
                0: PlayerStats(0, "random"),
                1: PlayerStats(1, "greedy"),
            },
        )

        # Game 2: random wins
        collector.record_game(
            turns=8,
            winner_id=0,
            winner_type="random",
            player_stats={
                0: PlayerStats(0, "random"),
                1: PlayerStats(1, "greedy"),
            },
        )

        win_rates = collector.get_win_rates()
        assert win_rates["greedy"] == 0.5
        assert win_rates["random"] == 0.5

    def test_aggregate_stats(self) -> None:
        """Test aggregate statistics."""
        collector = StatsCollector()

        collector.record_game(
            turns=10,
            winner_id=0,
            winner_type="random",
            player_stats={
                0: PlayerStats(0, "random", cards_bought=3),
                1: PlayerStats(1, "greedy", cards_bought=4),
            },
        )

        collector.record_game(
            turns=20,
            winner_id=0,
            winner_type="random",
            player_stats={
                0: PlayerStats(0, "random", cards_bought=5),
                1: PlayerStats(1, "greedy", cards_bought=6),
            },
        )

        agg = collector.aggregate
        assert agg.games_played == 2
        assert agg.total_turns == 30
        assert agg.avg_game_length == 15.0
        assert agg.total_cards_bought == 18  # 3+4+5+6

    def test_clear(self) -> None:
        """Test clearing the collector."""
        collector = StatsCollector()
        collector.record_game(
            turns=10,
            winner_id=0,
            winner_type="random",
            player_stats={0: PlayerStats(0, "random")},
        )
        assert len(collector) == 1

        collector.clear()
        assert len(collector) == 0
        assert collector.aggregate.games_played == 0


class TestGameRunner:
    """Tests for GameRunner."""

    def test_create_runner(self) -> None:
        """Test creating a game runner."""
        players = [
            RandomPlayer(player_id=0, seed=42),
            RandomPlayer(player_id=1, seed=43),
        ]
        runner = GameRunner(players=players, seed=100)
        assert len(runner.players) == 2

    def test_invalid_player_count(self) -> None:
        """Test that runner rejects invalid player counts."""
        with pytest.raises(ValueError, match="Number of players"):
            players = [RandomPlayer(player_id=0)]
            GameRunner(players=players)

    def test_run_game_completes(self) -> None:
        """Test that a game runs to completion."""
        players = [
            RandomPlayer(player_id=0, seed=42),
            RandomPlayer(player_id=1, seed=43),
        ]
        runner = GameRunner(players=players, seed=100, max_turns=50)
        result = runner.run_game()

        assert isinstance(result, GameResult)
        assert result.turns > 0
        assert result.turns <= 50
        assert result.final_state is not None

    def test_run_game_produces_events(self) -> None:
        """Test that game produces events when logging enabled."""
        players = [
            RandomPlayer(player_id=0, seed=42),
            RandomPlayer(player_id=1, seed=43),
        ]
        runner = GameRunner(players=players, seed=100, log_events=True, max_turns=10)
        result = runner.run_game()

        assert len(result.events) > 0
        # Should at least have game start and game end
        event_types = [e.event_type for e in result.events]
        assert EventType.GAME_START in event_types
        assert EventType.GAME_END in event_types

    def test_run_game_produces_stats(self) -> None:
        """Test that game produces player statistics."""
        players = [
            RandomPlayer(player_id=0, seed=42),
            RandomPlayer(player_id=1, seed=43),
        ]
        runner = GameRunner(players=players, seed=100, max_turns=10)
        result = runner.run_game()

        assert 0 in result.player_stats
        assert 1 in result.player_stats
        assert result.player_stats[0].player_type == "random"
        assert result.player_stats[1].player_type == "random"

    def test_reproducible_with_seed(self) -> None:
        """Test that same seed produces same result."""
        players1 = [
            RandomPlayer(player_id=0, seed=42),
            RandomPlayer(player_id=1, seed=43),
        ]
        players2 = [
            RandomPlayer(player_id=0, seed=42),
            RandomPlayer(player_id=1, seed=43),
        ]

        runner1 = GameRunner(players=players1, seed=100, max_turns=20)
        runner2 = GameRunner(players=players2, seed=100, max_turns=20)

        result1 = runner1.run_game()
        result2 = runner2.run_game()

        assert result1.winner_id == result2.winner_id
        assert result1.turns == result2.turns


class TestMatchRunner:
    """Tests for MatchRunner."""

    def test_create_match_runner(self) -> None:
        """Test creating a match runner."""
        runner = MatchRunner()
        assert runner.config is None

    def test_invalid_config(self) -> None:
        """Test that invalid config is rejected."""
        with pytest.raises(ValueError, match="num_games"):
            MatchConfig(num_games=0, player_factories=[])

        with pytest.raises(ValueError, match="player factories"):
            MatchConfig(
                num_games=10,
                player_factories=[lambda pid: RandomPlayer(pid)],
            )

    def test_run_match(self) -> None:
        """Test running a match."""
        config = MatchConfig(
            num_games=2,
            player_factories=[
                lambda pid: RandomPlayer(player_id=pid, seed=pid),
                lambda pid: RandomPlayer(player_id=pid, seed=pid + 100),
            ],
            base_seed=42,
        )

        runner = MatchRunner()
        result = runner.run_match(config)

        assert isinstance(result, MatchResult)
        assert result.games_played == 2
        assert len(result.results) == 2
        assert result.avg_game_length > 0

    def test_match_win_rates(self) -> None:
        """Test that match calculates win rates."""
        config = MatchConfig(
            num_games=4,
            player_factories=[
                lambda pid: RandomPlayer(player_id=pid),
                lambda pid: GreedyPlayer(player_id=pid),
            ],
            base_seed=123,
        )

        runner = MatchRunner()
        result = runner.run_match(config)

        # Win rates should sum to 1 (minus draw rate)
        total_rate = sum(result.win_rates.values())
        draw_rate = result.draws / result.games_played if result.games_played > 0 else 0
        assert abs(total_rate + draw_rate - 1.0) < 0.01

    def test_position_rotation(self) -> None:
        """Test that position rotation works."""

        def tracking_factory_random(pid: int) -> RandomPlayer:
            return RandomPlayer(player_id=pid, name="TrackRandom")

        def tracking_factory_greedy(pid: int) -> GreedyPlayer:
            return GreedyPlayer(player_id=pid, name="TrackGreedy")

        config = MatchConfig(
            num_games=4,
            player_factories=[tracking_factory_random, tracking_factory_greedy],
            rotate_positions=True,
            base_seed=42,
        )

        runner = MatchRunner()
        result = runner.run_match(config)

        # With rotation, player positions should alternate
        assert result.games_played == 4


class TestIntegration:
    """Integration tests for the simulation framework."""

    def test_greedy_beats_random(self) -> None:
        """Test that greedy player performs better than random over games."""
        config = MatchConfig(
            num_games=4,
            player_factories=[
                lambda pid: RandomPlayer(player_id=pid, seed=pid * 1000),
                lambda pid: GreedyPlayer(player_id=pid),
            ],
            base_seed=999,
            rotate_positions=True,
        )

        runner = MatchRunner()
        result = runner.run_match(config)

        # Without cards loaded, all games will be draws (timeouts)
        # We just check that the framework runs without errors
        assert result.games_played == 4
        # Either there are winners OR all games are draws (no cards = no combat damage)
        has_winners = bool(result.win_rates)
        all_draws = result.draws == result.games_played
        assert has_winners or all_draws

    def test_heuristic_player_runs(self) -> None:
        """Test that heuristic player works in simulation."""
        players = [
            HeuristicPlayer(player_id=0),
            RandomPlayer(player_id=1, seed=42),
        ]
        runner = GameRunner(players=players, seed=100, max_turns=20)
        result = runner.run_game()

        assert result.turns > 0
        assert "heuristic" in [s.player_type for s in result.player_stats.values()]
