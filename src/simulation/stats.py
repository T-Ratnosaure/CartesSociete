"""Statistics collection and aggregation for game simulations.

This module provides data structures and collectors for tracking
game statistics, enabling balance analysis and performance comparison.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .logger import GameLogger


@dataclass
class PlayerStats:
    """Statistics for a single player in a game.

    Attributes:
        player_id: The player's ID.
        player_type: The type of AI agent.
        cards_bought: Number of cards purchased.
        cards_played: Number of cards played to board.
        evolutions: Number of evolutions performed.
        damage_dealt: Total damage dealt to opponents.
        damage_taken: Total damage received.
        final_health: Health at game end.
        turns_survived: Number of turns the player survived.
        won: Whether this player won the game.
    """

    player_id: int
    player_type: str
    cards_bought: int = 0
    cards_played: int = 0
    evolutions: int = 0
    damage_dealt: int = 0
    damage_taken: int = 0
    final_health: int = 0
    turns_survived: int = 0
    won: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert stats to dictionary.

        Returns:
            Dictionary representation of stats.
        """
        return {
            "player_id": self.player_id,
            "player_type": self.player_type,
            "cards_bought": self.cards_bought,
            "cards_played": self.cards_played,
            "evolutions": self.evolutions,
            "damage_dealt": self.damage_dealt,
            "damage_taken": self.damage_taken,
            "final_health": self.final_health,
            "turns_survived": self.turns_survived,
            "won": self.won,
        }


@dataclass
class GameStats:
    """Statistics for a single game.

    Attributes:
        turns: Total number of turns in the game.
        winner_id: ID of the winning player (None for draw).
        winner_type: Type of the winning player agent.
        player_stats: Stats for each player.
        total_cards_bought: Total cards bought across all players.
        total_evolutions: Total evolutions across all players.
    """

    turns: int
    winner_id: int | None
    winner_type: str | None
    player_stats: dict[int, PlayerStats]
    total_cards_bought: int = 0
    total_evolutions: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert game stats to dictionary.

        Returns:
            Dictionary representation of game stats.
        """
        return {
            "turns": self.turns,
            "winner_id": self.winner_id,
            "winner_type": self.winner_type,
            "player_stats": {
                pid: stats.to_dict() for pid, stats in self.player_stats.items()
            },
            "total_cards_bought": self.total_cards_bought,
            "total_evolutions": self.total_evolutions,
        }


@dataclass
class AggregateStats:
    """Aggregated statistics across multiple games.

    Attributes:
        games_played: Total number of games.
        wins_by_type: Win count per player type.
        total_turns: Sum of turns across all games.
        total_cards_bought: Sum of cards bought.
        total_evolutions: Sum of evolutions.
        draws: Number of games ending in draw.
    """

    games_played: int = 0
    wins_by_type: dict[str, int] = field(default_factory=dict)
    total_turns: int = 0
    total_cards_bought: int = 0
    total_evolutions: int = 0
    draws: int = 0

    @property
    def avg_game_length(self) -> float:
        """Calculate average game length in turns.

        Returns:
            Average turns per game.
        """
        if self.games_played == 0:
            return 0.0
        return self.total_turns / self.games_played

    @property
    def avg_cards_per_game(self) -> float:
        """Calculate average cards bought per game.

        Returns:
            Average cards bought per game.
        """
        if self.games_played == 0:
            return 0.0
        return self.total_cards_bought / self.games_played

    @property
    def avg_evolutions_per_game(self) -> float:
        """Calculate average evolutions per game.

        Returns:
            Average evolutions per game.
        """
        if self.games_played == 0:
            return 0.0
        return self.total_evolutions / self.games_played

    def win_rate(self, player_type: str) -> float:
        """Calculate win rate for a player type.

        Args:
            player_type: The player type to check.

        Returns:
            Win rate as a float between 0 and 1.
        """
        if self.games_played == 0:
            return 0.0
        wins = self.wins_by_type.get(player_type, 0)
        return wins / self.games_played

    def win_rates(self) -> dict[str, float]:
        """Calculate win rates for all player types.

        Returns:
            Dict mapping player type to win rate.
        """
        if self.games_played == 0:
            return {}
        return {
            ptype: wins / self.games_played for ptype, wins in self.wins_by_type.items()
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert aggregate stats to dictionary.

        Returns:
            Dictionary representation of aggregate stats.
        """
        return {
            "games_played": self.games_played,
            "wins_by_type": self.wins_by_type,
            "win_rates": self.win_rates(),
            "draws": self.draws,
            "avg_game_length": self.avg_game_length,
            "avg_cards_per_game": self.avg_cards_per_game,
            "avg_evolutions_per_game": self.avg_evolutions_per_game,
            "total_turns": self.total_turns,
            "total_cards_bought": self.total_cards_bought,
            "total_evolutions": self.total_evolutions,
        }


class StatsCollector:
    """Collects and aggregates statistics across multiple games.

    This class provides methods to record game results and compute
    aggregate statistics for balance analysis.

    Attributes:
        game_stats: List of individual game statistics.
        aggregate: Running aggregate statistics.
    """

    def __init__(self) -> None:
        """Initialize an empty stats collector."""
        self._game_stats: list[GameStats] = []
        self._aggregate = AggregateStats()

    @property
    def game_stats(self) -> list[GameStats]:
        """Get all recorded game stats.

        Returns:
            List of game statistics.
        """
        return self._game_stats.copy()

    @property
    def aggregate(self) -> AggregateStats:
        """Get aggregate statistics.

        Returns:
            Aggregated statistics across all games.
        """
        return self._aggregate

    def record_game(
        self,
        turns: int,
        winner_id: int | None,
        winner_type: str | None,
        player_stats: dict[int, PlayerStats],
    ) -> GameStats:
        """Record statistics from a completed game.

        Args:
            turns: Number of turns in the game.
            winner_id: ID of the winner (None for draw).
            winner_type: Type of winning player.
            player_stats: Statistics for each player.

        Returns:
            The recorded GameStats object.
        """
        total_bought = sum(ps.cards_bought for ps in player_stats.values())
        total_evos = sum(ps.evolutions for ps in player_stats.values())

        game_stat = GameStats(
            turns=turns,
            winner_id=winner_id,
            winner_type=winner_type,
            player_stats=player_stats,
            total_cards_bought=total_bought,
            total_evolutions=total_evos,
        )
        self._game_stats.append(game_stat)

        # Update aggregates
        self._aggregate.games_played += 1
        self._aggregate.total_turns += turns
        self._aggregate.total_cards_bought += total_bought
        self._aggregate.total_evolutions += total_evos

        if winner_type is not None:
            self._aggregate.wins_by_type[winner_type] = (
                self._aggregate.wins_by_type.get(winner_type, 0) + 1
            )
        else:
            self._aggregate.draws += 1

        return game_stat

    def record_from_logger(
        self,
        logger: "GameLogger",
        player_types: dict[int, str],
        final_health: dict[int, int],
    ) -> GameStats:
        """Record statistics from a game logger.

        Extracts statistics from logged events.

        Args:
            logger: The game logger with recorded events.
            player_types: Dict mapping player_id to player type.
            final_health: Dict mapping player_id to final health.

        Returns:
            The recorded GameStats object.
        """
        from .logger import EventType

        player_stats: dict[int, PlayerStats] = {}

        # Initialize stats for each player
        for pid, ptype in player_types.items():
            player_stats[pid] = PlayerStats(
                player_id=pid,
                player_type=ptype,
                final_health=final_health.get(pid, 0),
            )

        # Process events
        turns = 0
        winner_id: int | None = None
        winner_type: str | None = None

        for event in logger.events:
            turns = max(turns, event.turn)

            if (
                event.event_type == EventType.CARD_BOUGHT
                and event.player_id is not None
            ):
                player_stats[event.player_id].cards_bought += 1

            elif (
                event.event_type == EventType.CARD_PLAYED
                and event.player_id is not None
            ):
                player_stats[event.player_id].cards_played += 1

            elif (
                event.event_type == EventType.EVOLUTION and event.player_id is not None
            ):
                player_stats[event.player_id].evolutions += 1

            elif event.event_type == EventType.COMBAT:
                damage_dealt = event.data.get("damage_dealt", {})
                for pid_str, damage in damage_dealt.items():
                    pid = int(pid_str) if isinstance(pid_str, str) else pid_str
                    if pid in player_stats:
                        player_stats[pid].damage_dealt += damage

            elif (
                event.event_type == EventType.PLAYER_ELIMINATED
                and event.player_id is not None
            ):
                player_stats[event.player_id].turns_survived = event.turn

            elif event.event_type == EventType.GAME_END:
                winner_id = event.data.get("winner_id")
                if winner_id is not None:
                    winner_type = player_types.get(winner_id)
                    player_stats[winner_id].won = True

        # Set turns_survived for survivors
        for pid, stats in player_stats.items():
            if stats.turns_survived == 0:
                stats.turns_survived = turns

        return self.record_game(turns, winner_id, winner_type, player_stats)

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of all collected statistics.

        Returns:
            Dictionary with aggregate statistics.
        """
        return self._aggregate.to_dict()

    def get_win_rates(self) -> dict[str, float]:
        """Get win rates for all player types.

        Returns:
            Dict mapping player type to win rate.
        """
        return self._aggregate.win_rates()

    def get_matchup_stats(
        self,
        player_type_1: str,
        player_type_2: str,
    ) -> dict[str, Any]:
        """Get head-to-head statistics between two player types.

        Args:
            player_type_1: First player type.
            player_type_2: Second player type.

        Returns:
            Dictionary with matchup statistics.
        """
        relevant_games = [
            gs
            for gs in self._game_stats
            if {player_type_1, player_type_2}
            == {ps.player_type for ps in gs.player_stats.values()}
        ]

        if not relevant_games:
            return {
                "games": 0,
                "wins_1": 0,
                "wins_2": 0,
                "draws": 0,
                "win_rate_1": 0.0,
                "win_rate_2": 0.0,
            }

        wins_1 = sum(1 for gs in relevant_games if gs.winner_type == player_type_1)
        wins_2 = sum(1 for gs in relevant_games if gs.winner_type == player_type_2)
        draws = sum(1 for gs in relevant_games if gs.winner_id is None)

        total = len(relevant_games)
        return {
            "games": total,
            "wins_1": wins_1,
            "wins_2": wins_2,
            "draws": draws,
            "win_rate_1": wins_1 / total,
            "win_rate_2": wins_2 / total,
        }

    def clear(self) -> None:
        """Clear all recorded statistics."""
        self._game_stats.clear()
        self._aggregate = AggregateStats()

    def __len__(self) -> int:
        """Return number of recorded games."""
        return len(self._game_stats)
