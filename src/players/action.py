"""Action representation for player decisions.

This module defines the Action dataclass used by AI players to communicate
their decisions to the game engine.
"""

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.cards.models import Card


class ActionType(Enum):
    """Types of actions a player can take."""

    BUY_CARD = "buy_card"
    PLAY_CARD = "play_card"
    REPLACE_CARD = "replace_card"
    EVOLVE = "evolve"
    END_PHASE = "end_phase"


@dataclass(frozen=True)
class Action:
    """Represents a player action.

    Actions are immutable and describe what a player wants to do.
    The game engine validates and executes them.

    Attributes:
        action_type: The type of action.
        card: The primary card involved (for buy/play).
        target_card: The card to replace (for replace action).
        evolve_cards: The 3 cards to evolve (for evolve action).
    """

    action_type: ActionType
    card: "Card | None" = None
    target_card: "Card | None" = None
    evolve_cards: tuple["Card", ...] | None = None

    @classmethod
    def buy(cls, card: "Card") -> "Action":
        """Create a buy action.

        Args:
            card: The card to buy from the market.

        Returns:
            A buy action for the specified card.
        """
        return cls(action_type=ActionType.BUY_CARD, card=card)

    @classmethod
    def play(cls, card: "Card") -> "Action":
        """Create a play action.

        Args:
            card: The card to play from hand to board.

        Returns:
            A play action for the specified card.
        """
        return cls(action_type=ActionType.PLAY_CARD, card=card)

    @classmethod
    def replace(cls, new_card: "Card", old_card: "Card") -> "Action":
        """Create a replace action.

        Args:
            new_card: The card from hand to play.
            old_card: The card on board to replace.

        Returns:
            A replace action swapping the cards.
        """
        return cls(
            action_type=ActionType.REPLACE_CARD,
            card=new_card,
            target_card=old_card,
        )

    @classmethod
    def evolve(cls, cards: list["Card"]) -> "Action":
        """Create an evolve action.

        Args:
            cards: The 3 cards to evolve into a Level 2 card.

        Returns:
            An evolve action for the specified cards.
        """
        return cls(action_type=ActionType.EVOLVE, evolve_cards=tuple(cards))

    @classmethod
    def end_phase(cls) -> "Action":
        """Create an end phase action.

        Returns:
            An action to end the current phase.
        """
        return cls(action_type=ActionType.END_PHASE)

    def __repr__(self) -> str:
        """Return a readable string representation."""
        if self.action_type == ActionType.END_PHASE:
            return "Action(END_PHASE)"
        elif self.action_type == ActionType.BUY_CARD:
            name = self.card.name if self.card else "None"
            return f"Action(BUY: {name})"
        elif self.action_type == ActionType.PLAY_CARD:
            name = self.card.name if self.card else "None"
            return f"Action(PLAY: {name})"
        elif self.action_type == ActionType.REPLACE_CARD:
            new_name = self.card.name if self.card else "None"
            old_name = self.target_card.name if self.target_card else "None"
            return f"Action(REPLACE: {old_name} -> {new_name})"
        elif self.action_type == ActionType.EVOLVE:
            names = [c.name for c in self.evolve_cards] if self.evolve_cards else []
            return f"Action(EVOLVE: {names})"
        return f"Action({self.action_type})"
