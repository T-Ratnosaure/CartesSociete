"""Game event logging for replay and analysis.

This module provides event logging capabilities for game simulations,
enabling replay, debugging, and post-game analysis.
"""

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.game.state import GamePhase


class EventType(Enum):
    """Types of game events that can be logged."""

    GAME_START = "game_start"
    TURN_START = "turn_start"
    PHASE_START = "phase_start"
    PHASE_END = "phase_end"
    CARD_BOUGHT = "card_bought"
    CARD_PLAYED = "card_played"
    CARD_REPLACED = "card_replaced"
    EVOLUTION = "evolution"
    COMBAT = "combat"
    DAMAGE_DEALT = "damage_dealt"
    PLAYER_ELIMINATED = "player_eliminated"
    GAME_END = "game_end"


@dataclass
class GameEvent:
    """A single game event for logging.

    Attributes:
        turn: The turn number when this event occurred.
        phase: The game phase during this event.
        event_type: The type of event.
        player_id: The player involved (None for global events).
        data: Additional event-specific data.
        timestamp: Unix timestamp when the event was logged.
    """

    turn: int
    phase: str  # Store as string for JSON serialization
    event_type: EventType
    player_id: int | None
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for serialization.

        Returns:
            Dictionary representation of the event.
        """
        return {
            "turn": self.turn,
            "phase": self.phase,
            "event_type": self.event_type.value,
            "player_id": self.player_id,
            "data": self.data,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameEvent":
        """Create event from dictionary.

        Args:
            data: Dictionary with event data.

        Returns:
            GameEvent instance.
        """
        return cls(
            turn=data["turn"],
            phase=data["phase"],
            event_type=EventType(data["event_type"]),
            player_id=data["player_id"],
            data=data.get("data", {}),
            timestamp=data.get("timestamp", time.time()),
        )


class GameLogger:
    """Logger for game events.

    Collects events during a game for later analysis or replay.
    Supports JSON serialization for persistent storage.

    Attributes:
        events: List of recorded game events.
    """

    def __init__(self) -> None:
        """Initialize an empty logger."""
        self._events: list[GameEvent] = []

    @property
    def events(self) -> list[GameEvent]:
        """Get all recorded events.

        Returns:
            List of game events in chronological order.
        """
        return self._events.copy()

    def log(self, event: GameEvent) -> None:
        """Record a game event.

        Args:
            event: The event to log.
        """
        self._events.append(event)

    def log_game_start(
        self,
        num_players: int,
        player_info: list[dict[str, str]],
    ) -> None:
        """Log game start event.

        Args:
            num_players: Number of players in the game.
            player_info: List of player metadata dicts.
        """
        self.log(
            GameEvent(
                turn=0,
                phase="SETUP",
                event_type=EventType.GAME_START,
                player_id=None,
                data={
                    "num_players": num_players,
                    "players": player_info,
                },
            )
        )

    def log_turn_start(self, turn: int) -> None:
        """Log turn start event.

        Args:
            turn: The turn number starting.
        """
        self.log(
            GameEvent(
                turn=turn,
                phase="TURN_START",
                event_type=EventType.TURN_START,
                player_id=None,
                data={},
            )
        )

    def log_phase_start(self, turn: int, phase: "GamePhase") -> None:
        """Log phase start event.

        Args:
            turn: Current turn number.
            phase: The phase starting.
        """
        self.log(
            GameEvent(
                turn=turn,
                phase=phase.value,
                event_type=EventType.PHASE_START,
                player_id=None,
                data={"phase": phase.value},
            )
        )

    def log_card_bought(
        self,
        turn: int,
        phase: "GamePhase",
        player_id: int,
        card_name: str,
        cost: int,
    ) -> None:
        """Log card purchase event.

        Args:
            turn: Current turn number.
            phase: Current game phase.
            player_id: Player who bought the card.
            card_name: Name of the purchased card.
            cost: Cost paid for the card.
        """
        self.log(
            GameEvent(
                turn=turn,
                phase=phase.value,
                event_type=EventType.CARD_BOUGHT,
                player_id=player_id,
                data={"card_name": card_name, "cost": cost},
            )
        )

    def log_card_played(
        self,
        turn: int,
        phase: "GamePhase",
        player_id: int,
        card_name: str,
    ) -> None:
        """Log card play event.

        Args:
            turn: Current turn number.
            phase: Current game phase.
            player_id: Player who played the card.
            card_name: Name of the played card.
        """
        self.log(
            GameEvent(
                turn=turn,
                phase=phase.value,
                event_type=EventType.CARD_PLAYED,
                player_id=player_id,
                data={"card_name": card_name},
            )
        )

    def log_evolution(
        self,
        turn: int,
        phase: "GamePhase",
        player_id: int,
        base_card_name: str,
        evolved_card_name: str,
    ) -> None:
        """Log evolution event.

        Args:
            turn: Current turn number.
            phase: Current game phase.
            player_id: Player who evolved.
            base_card_name: Name of the base card.
            evolved_card_name: Name of the evolved card.
        """
        self.log(
            GameEvent(
                turn=turn,
                phase=phase.value,
                event_type=EventType.EVOLUTION,
                player_id=player_id,
                data={
                    "base_card": base_card_name,
                    "evolved_card": evolved_card_name,
                },
            )
        )

    def log_combat(
        self,
        turn: int,
        damage_dealt: dict[int, int],
        eliminations: list[int],
    ) -> None:
        """Log combat resolution event.

        Args:
            turn: Current turn number.
            damage_dealt: Dict mapping player_id -> damage dealt.
            eliminations: List of eliminated player IDs.
        """
        self.log(
            GameEvent(
                turn=turn,
                phase="COMBAT",
                event_type=EventType.COMBAT,
                player_id=None,
                data={
                    "damage_dealt": damage_dealt,
                    "eliminations": eliminations,
                },
            )
        )

    def log_player_eliminated(
        self,
        turn: int,
        player_id: int,
    ) -> None:
        """Log player elimination event.

        Args:
            turn: Current turn number.
            player_id: ID of the eliminated player.
        """
        self.log(
            GameEvent(
                turn=turn,
                phase="COMBAT",
                event_type=EventType.PLAYER_ELIMINATED,
                player_id=player_id,
                data={},
            )
        )

    def log_game_end(
        self,
        turn: int,
        winner_id: int | None,
        reason: str = "elimination",
    ) -> None:
        """Log game end event.

        Args:
            turn: Final turn number.
            winner_id: ID of the winner (None for draw).
            reason: Reason for game end.
        """
        self.log(
            GameEvent(
                turn=turn,
                phase="END",
                event_type=EventType.GAME_END,
                player_id=winner_id,
                data={"winner_id": winner_id, "reason": reason},
            )
        )

    def get_events(self) -> list[GameEvent]:
        """Get all logged events.

        Returns:
            Copy of the events list.
        """
        return self._events.copy()

    def get_events_by_type(self, event_type: EventType) -> list[GameEvent]:
        """Filter events by type.

        Args:
            event_type: The type of events to return.

        Returns:
            List of matching events.
        """
        return [e for e in self._events if e.event_type == event_type]

    def get_events_for_player(self, player_id: int) -> list[GameEvent]:
        """Filter events by player.

        Args:
            player_id: The player ID to filter by.

        Returns:
            List of events involving that player.
        """
        return [e for e in self._events if e.player_id == player_id]

    def get_events_for_turn(self, turn: int) -> list[GameEvent]:
        """Filter events by turn.

        Args:
            turn: The turn number to filter by.

        Returns:
            List of events from that turn.
        """
        return [e for e in self._events if e.turn == turn]

    def clear(self) -> None:
        """Clear all logged events."""
        self._events.clear()

    def to_json(self, indent: int | None = 2) -> str:
        """Serialize all events to JSON.

        Args:
            indent: JSON indentation (None for compact).

        Returns:
            JSON string of all events.
        """
        return json.dumps(
            [e.to_dict() for e in self._events],
            indent=indent,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "GameLogger":
        """Create logger from JSON string.

        Args:
            json_str: JSON string of events.

        Returns:
            GameLogger with the deserialized events.
        """
        logger = cls()
        events_data = json.loads(json_str)
        for event_data in events_data:
            logger.log(GameEvent.from_dict(event_data))
        return logger

    def __len__(self) -> int:
        """Return number of logged events."""
        return len(self._events)
