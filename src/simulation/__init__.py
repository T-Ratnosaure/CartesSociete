"""Game simulation framework for CartesSociete.

This module provides tools for running complete game simulations
with AI agents, collecting statistics, and enabling balance analysis.

Main components:
- GameRunner: Orchestrates single game simulations
- MatchRunner: Runs batch simulations and tournaments
- GameLogger: Records game events for replay/analysis
- StatsCollector: Aggregates statistics across games
"""

from .logger import EventType, GameEvent, GameLogger
from .match import MatchConfig, MatchResult, MatchRunner
from .runner import GameResult, GameRunner
from .stats import AggregateStats, GameStats, PlayerStats, StatsCollector

__all__ = [
    # Runner
    "GameRunner",
    "GameResult",
    # Match
    "MatchRunner",
    "MatchConfig",
    "MatchResult",
    # Logger
    "GameLogger",
    "GameEvent",
    "EventType",
    # Stats
    "StatsCollector",
    "PlayerStats",
    "GameStats",
    "AggregateStats",
]
