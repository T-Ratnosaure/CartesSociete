"""Match and tournament runner for batch game simulations.

This module provides MatchRunner for running multiple games between
AI agents and aggregating statistics.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from configs import DEFAULT_CONFIG, GameConfig

from .runner import GameResult, GameRunner
from .stats import StatsCollector

if TYPE_CHECKING:
    from src.players.base import Player


@dataclass
class MatchConfig:
    """Configuration for a match (series of games).

    Attributes:
        num_games: Number of games to play.
        player_factories: Functions that create new player instances.
        rotate_positions: Whether to swap player order between games.
        game_config: Configuration for individual games.
        base_seed: Base random seed (each game uses base_seed + game_index).
        log_events: Whether to log events for each game.
        verbose: Whether to print progress during the match.
    """

    num_games: int = 100
    player_factories: list[Callable[[int], "Player"]] = field(default_factory=list)
    rotate_positions: bool = True
    game_config: GameConfig | None = None
    base_seed: int | None = None
    log_events: bool = False
    verbose: bool = False

    # Maximum bounds
    MAX_GAMES: int = field(default=10000, repr=False, init=False)

    def __post_init__(self) -> None:
        """Validate configuration."""
        if not 1 <= self.num_games <= self.MAX_GAMES:
            raise ValueError(
                f"num_games must be between 1 and {self.MAX_GAMES}, "
                f"got {self.num_games}"
            )
        if len(self.player_factories) < 2:
            raise ValueError("At least 2 player factories required")


@dataclass
class MatchResult:
    """Result of a match (series of games).

    Attributes:
        games_played: Total number of games played.
        results: Individual game results.
        wins: Win count per player type.
        draws: Number of draws/timeouts.
        avg_game_length: Average turns per game.
        win_rates: Win rate per player type.
        stats: Detailed statistics from StatsCollector.
    """

    games_played: int
    results: list[GameResult]
    wins: dict[str, int]
    draws: int
    avg_game_length: float
    win_rates: dict[str, float]
    stats: StatsCollector

    def summary(self) -> str:
        """Generate a human-readable summary of match results.

        Returns:
            Multi-line string with match statistics.
        """
        lines = [
            "=== Match Results ===",
            f"Games Played: {self.games_played}",
            f"Average Game Length: {self.avg_game_length:.1f} turns",
            f"Draws/Timeouts: {self.draws}",
            "",
            "Win Rates:",
        ]

        for player_type, rate in sorted(
            self.win_rates.items(), key=lambda x: x[1], reverse=True
        ):
            wins = self.wins.get(player_type, 0)
            lines.append(f"  {player_type}: {rate:.1%} ({wins} wins)")

        return "\n".join(lines)


class MatchRunner:
    """Runs batch game simulations between AI agents.

    The MatchRunner executes multiple games, optionally rotating
    player positions, and aggregates statistics for analysis.

    Attributes:
        config: Match configuration.
        collector: Statistics collector for aggregation.
    """

    def __init__(self, config: MatchConfig | None = None) -> None:
        """Initialize the match runner.

        Args:
            config: Match configuration. Required.
        """
        self.config = config
        self._collector = StatsCollector()

    def run_match(self, config: MatchConfig | None = None) -> MatchResult:
        """Run a complete match (series of games).

        Args:
            config: Match configuration. Uses self.config if not provided.

        Returns:
            MatchResult with aggregate statistics.

        Raises:
            ValueError: If no configuration is provided.
        """
        match_config = config or self.config
        if match_config is None:
            raise ValueError("Match configuration required")

        self._collector.clear()
        results: list[GameResult] = []

        for game_index in range(match_config.num_games):
            # Create players for this game
            players = self._create_players(match_config, game_index)

            # Determine seed for this game
            seed = None
            if match_config.base_seed is not None:
                seed = match_config.base_seed + game_index

            # Run the game
            runner = GameRunner(
                players=players,
                config=match_config.game_config or DEFAULT_CONFIG,
                seed=seed,
                log_events=match_config.log_events,
            )
            result = runner.run_game()
            results.append(result)

            # Record statistics
            self._collector.record_game(
                turns=result.turns,
                winner_id=result.winner_id,
                winner_type=result.winner_type,
                player_stats=result.player_stats,
            )

            # Progress output
            if match_config.verbose and (game_index + 1) % 10 == 0:
                print(f"Completed {game_index + 1}/{match_config.num_games} games")

        # Calculate results
        aggregate = self._collector.aggregate

        return MatchResult(
            games_played=aggregate.games_played,
            results=results,
            wins=aggregate.wins_by_type.copy(),
            draws=aggregate.draws,
            avg_game_length=aggregate.avg_game_length,
            win_rates=aggregate.win_rates(),
            stats=self._collector,
        )

    def _create_players(
        self,
        config: MatchConfig,
        game_index: int,
    ) -> list["Player"]:
        """Create player instances for a game.

        Handles position rotation if enabled.

        Args:
            config: Match configuration.
            game_index: Index of the current game.

        Returns:
            List of player instances with appropriate IDs.
        """
        num_players = len(config.player_factories)

        # Determine player order for this game
        if config.rotate_positions:
            # Rotate based on game index
            rotation = game_index % num_players
            factory_order = list(range(num_players))
            factory_order = factory_order[rotation:] + factory_order[:rotation]
        else:
            factory_order = list(range(num_players))

        # Create players with correct IDs
        players: list["Player"] = []  # noqa: UP037
        for player_id, factory_index in enumerate(factory_order):
            factory = config.player_factories[factory_index]
            player = factory(player_id)
            players.append(player)

        return players

    def run_round_robin(
        self,
        player_factories: list[Callable[[int], "Player"]],
        games_per_matchup: int = 10,
        game_config: GameConfig | None = None,
        base_seed: int | None = None,
        verbose: bool = False,
    ) -> dict[tuple[str, str], MatchResult]:
        """Run a round-robin tournament between all player types.

        Each pair of player types plays games_per_matchup games.

        Args:
            player_factories: List of player factory functions.
            games_per_matchup: Games per pair of players.
            game_config: Configuration for games.
            base_seed: Base random seed.
            verbose: Whether to print progress.

        Returns:
            Dict mapping (type1, type2) to MatchResult.
        """
        results: dict[tuple[str, str], MatchResult] = {}

        num_types = len(player_factories)
        matchup_index = 0

        for i in range(num_types):
            for j in range(i + 1, num_types):
                # Get player types for naming
                p1 = player_factories[i](0)
                p2 = player_factories[j](1)
                type1 = p1.info.agent_type
                type2 = p2.info.agent_type

                if verbose:
                    print(f"Running matchup: {type1} vs {type2}")

                # Run the matchup
                matchup_config = MatchConfig(
                    num_games=games_per_matchup,
                    player_factories=[player_factories[i], player_factories[j]],
                    rotate_positions=True,
                    game_config=game_config,
                    base_seed=(
                        base_seed + matchup_index * games_per_matchup
                        if base_seed
                        else None
                    ),
                    log_events=False,
                    verbose=verbose,
                )

                result = self.run_match(matchup_config)
                results[(type1, type2)] = result
                matchup_index += 1

        return results

    def get_round_robin_summary(
        self,
        results: dict[tuple[str, str], MatchResult],
    ) -> str:
        """Generate a summary table of round-robin results.

        Args:
            results: Results from run_round_robin.

        Returns:
            Multi-line string with tournament summary.
        """
        # Collect all player types
        types: set[str] = set()
        for type1, type2 in results.keys():
            types.add(type1)
            types.add(type2)

        type_list = sorted(types)

        # Build summary
        lines = [
            "=== Round Robin Tournament Results ===",
            "",
        ]

        # Overall stats per type
        total_wins: dict[str, int] = {t: 0 for t in type_list}
        total_games: dict[str, int] = {t: 0 for t in type_list}

        for (type1, type2), result in results.items():
            total_wins[type1] += result.wins.get(type1, 0)
            total_wins[type2] += result.wins.get(type2, 0)
            total_games[type1] += result.games_played
            total_games[type2] += result.games_played

        lines.append("Overall Performance:")
        for t in type_list:
            if total_games[t] > 0:
                rate = total_wins[t] / total_games[t]
                lines.append(f"  {t}: {rate:.1%} ({total_wins[t]}/{total_games[t]})")

        lines.append("")
        lines.append("Head-to-Head Results:")

        for (type1, type2), result in sorted(results.items()):
            wins1 = result.wins.get(type1, 0)
            wins2 = result.wins.get(type2, 0)
            draws = result.draws
            lines.append(f"  {type1} vs {type2}: {wins1}-{wins2} (draws: {draws})")

        return "\n".join(lines)
