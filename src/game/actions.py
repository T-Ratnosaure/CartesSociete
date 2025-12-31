"""Game actions for CartesSociete.

This module defines the actions that players can take during their turn,
including buying cards, playing cards, evolving cards, and ending turns.
"""

from dataclasses import dataclass
from enum import Enum
from typing import NoReturn

from src.cards.models import Card, CardType, Family
from src.cards.repository import CardRepository, get_repository

from .state import GamePhase, GameState, PlayerState


def _remove_by_identity(lst: list, item: object) -> None:
    """Remove an item from a list using identity comparison (is), not equality (==).

    This is necessary because Card objects compare equal by value (same name/stats),
    but we need to remove specific card instances when the same card exists as
    multiple copies.

    Falls back to equality comparison if identity match fails. This handles the case
    where MCTS simulations use cloned states with different card objects.

    Args:
        lst: The list to remove from.
        item: The item to remove (by identity, or by equality as fallback).

    Raises:
        ValueError: If the item is not found by identity or equality.
    """
    # First try identity match
    for i, elem in enumerate(lst):
        if elem is item:
            del lst[i]
            return

    # Fall back to equality match (for MCTS cloned states)
    for i, elem in enumerate(lst):
        if elem == item:
            del lst[i]
            return

    raise ValueError(f"Item not found by identity or equality in list")


def _assert_never(value: NoReturn) -> NoReturn:
    """Assert that a value is never reached (for exhaustive matching)."""
    raise AssertionError(f"Unhandled value: {value!r}")


class ActionType(Enum):
    """Types of player actions."""

    BUY_CARD = "buy_card"
    PLAY_CARD = "play_card"
    REPLACE_CARD = "replace_card"
    EVOLVE = "evolve"
    END_TURN = "end_turn"


class ActionError(Exception):
    """Base exception for action-related errors."""

    pass


class InsufficientPOError(ActionError):
    """Raised when player doesn't have enough PO to buy a card."""

    pass


class BoardFullError(ActionError):
    """Raised when player's board is full and cannot play more cards."""

    pass


class InvalidCardError(ActionError):
    """Raised when a card cannot be played or used in this context."""

    pass


class InvalidPhaseError(ActionError):
    """Raised when an action is attempted in the wrong game phase."""

    pass


class EvolutionError(ActionError):
    """Raised when evolution cannot be performed."""

    pass


@dataclass
class ActionResult:
    """Result of executing an action.

    Attributes:
        success: Whether the action succeeded.
        message: Description of what happened.
        state: The updated game state.
    """

    success: bool
    message: str
    state: GameState


def buy_card(
    state: GameState,
    player: PlayerState,
    card: Card,
) -> ActionResult:
    """Buy a card from the market.

    Args:
        state: Current game state.
        player: The player buying the card.
        card: The card to buy.

    Returns:
        ActionResult with the outcome.

    Raises:
        InvalidPhaseError: If not in market phase.
        InsufficientPOError: If player doesn't have enough PO.
        InvalidCardError: If card is not in market.
    """
    if state.phase != GamePhase.MARKET:
        raise InvalidPhaseError(f"Cannot buy cards in {state.phase.value} phase")

    # Use identity comparison, falling back to equality for MCTS cloned states
    if not any(c is card for c in state.market_cards) and card not in state.market_cards:
        raise InvalidCardError(f"Card {card.name} is not in the market")

    if card.cost is None:
        raise InvalidCardError(f"Cannot buy card {card.name} with X cost")

    if card.cost > player.po:
        raise InsufficientPOError(
            f"Need {card.cost} PO to buy {card.name}, but only have {player.po}"
        )

    # Execute the purchase
    player.po -= card.cost
    # Use identity-based removal since cards compare equal by value
    _remove_by_identity(state.market_cards, card)
    player.hand.append(card)

    return ActionResult(
        success=True,
        message=f"{player.name} bought {card.name} for {card.cost} PO",
        state=state,
    )


def play_card(
    state: GameState,
    player: PlayerState,
    card: Card,
) -> ActionResult:
    """Play a card from hand to the board.

    Args:
        state: Current game state.
        player: The player playing the card.
        card: The card to play.

    Returns:
        ActionResult with the outcome.

    Raises:
        InvalidPhaseError: If not in play phase.
        InvalidCardError: If card is not in hand.
        BoardFullError: If board is full.
    """
    if state.phase != GamePhase.PLAY:
        raise InvalidPhaseError(f"Cannot play cards in {state.phase.value} phase")

    # Use identity comparison, falling back to equality for MCTS cloned states
    if not any(c is card for c in player.hand) and card not in player.hand:
        raise InvalidCardError(f"Card {card.name} is not in hand")

    # Check board limit (Lapin family can exceed limit)
    is_lapin = card.family == Family.LAPIN
    is_demon = card.card_type == CardType.DEMON
    max_board = state.config.max_board_size

    # Demons don't count towards limit, Lapin can exceed limit
    if not is_demon and not is_lapin and not player.can_play_card(max_board):
        raise BoardFullError(
            f"Board is full ({player.get_board_count()}/{max_board}). "
            "Replace a card instead."
        )

    # Execute the play
    # Use identity-based removal since cards compare equal by value
    _remove_by_identity(player.hand, card)
    player.board.append(card)

    return ActionResult(
        success=True,
        message=f"{player.name} played {card.name}",
        state=state,
    )


def replace_card(
    state: GameState,
    player: PlayerState,
    new_card: Card,
    old_card: Card,
) -> ActionResult:
    """Replace a card on the board with a card from hand.

    Args:
        state: Current game state.
        player: The player replacing the card.
        new_card: The card from hand to play.
        old_card: The card on board to replace.

    Returns:
        ActionResult with the outcome.

    Raises:
        InvalidPhaseError: If not in play phase.
        InvalidCardError: If cards are not in correct locations.
    """
    if state.phase != GamePhase.PLAY:
        raise InvalidPhaseError(f"Cannot replace cards in {state.phase.value} phase")

    # Use identity comparison, falling back to equality for MCTS cloned states
    if not any(c is new_card for c in player.hand) and new_card not in player.hand:
        raise InvalidCardError(f"Card {new_card.name} is not in hand")

    if not any(c is old_card for c in player.board) and old_card not in player.board:
        raise InvalidCardError(f"Card {old_card.name} is not on board")

    # Execute the replacement
    # Use identity-based removal since cards compare equal by value
    _remove_by_identity(player.hand, new_card)
    _remove_by_identity(player.board, old_card)
    player.board.append(new_card)
    player.hand.append(old_card)  # Old card goes to hand

    return ActionResult(
        success=True,
        message=f"{player.name} replaced {old_card.name} with {new_card.name}",
        state=state,
    )


def evolve_cards(
    state: GameState,
    player: PlayerState,
    cards: list[Card],
    repository: CardRepository | None = None,
) -> ActionResult:
    """Evolve 3 matching cards into a Level 2 version.

    Evolution requires 3 cards with the exact same name.
    2 cards go to discard, 1 card is "flipped" to Level 2.
    Cards can be evolved from hand or board.

    Args:
        state: Current game state.
        player: The player evolving cards.
        cards: List of 3 cards to evolve.
        repository: Card repository for Level 2 lookup. Uses default if not provided.

    Returns:
        ActionResult with the outcome.

    Raises:
        EvolutionError: If evolution requirements are not met.
    """
    required_cards = state.config.cards_required_for_evolution

    if len(cards) != required_cards:
        raise EvolutionError(
            f"Evolution requires exactly {required_cards} cards, got {len(cards)}"
        )

    # Verify cards are distinct instances (not the same card reference 3 times)
    card_ids = [id(card) for card in cards]
    if len(set(card_ids)) != len(cards):
        raise EvolutionError("Cannot evolve the same card instance multiple times")

    # All cards must have the same name
    names = {card.name for card in cards}
    if len(names) != 1:
        raise EvolutionError(
            f"All cards must have the same name for evolution, got: {names}"
        )

    # All cards must be Level 1
    if not all(card.level == 1 for card in cards):
        raise EvolutionError("All cards must be Level 1 to evolve")

    # Cards must be from hand or board - check each card individually
    # Use identity comparison, falling back to equality for MCTS cloned states
    for card in cards:
        in_hand = any(c is card for c in player.hand) or card in player.hand
        in_board = any(c is card for c in player.board) or card in player.board
        if not in_hand and not in_board:
            raise EvolutionError(f"Card {card.name} not found in hand or board")

    # Get the card repository for Level 2 lookup
    if repository is None:
        repository = get_repository()

    # Look up the Level 2 version
    card_name = cards[0].name
    evolved_card = repository.get_by_name_and_level(card_name, level=2)

    if evolved_card is None:
        raise EvolutionError(
            f"No Level 2 version found for '{card_name}'. This card cannot be evolved."
        )

    # Remove all 3 cards from hand/board
    # Use identity-based removal, falling back to equality for MCTS cloned states
    for card in cards:
        in_hand_identity = any(c is card for c in player.hand)
        in_hand_equality = card in player.hand
        if in_hand_identity or in_hand_equality:
            _remove_by_identity(player.hand, card)
        elif any(c is card for c in player.board) or card in player.board:
            _remove_by_identity(player.board, card)

    # Add the evolved Level 2 card to board
    player.board.append(evolved_card)

    # Discard the Level 1 cards (all 3 go to discard, Level 2 is new)
    state.discard_pile.extend(cards)

    return ActionResult(
        success=True,
        message=f"{player.name} evolved {card_name} to Level 2",
        state=state,
    )


def end_turn(state: GameState) -> ActionResult:
    """End the current turn and move to the next phase or turn.

    Args:
        state: Current game state.

    Returns:
        ActionResult with the outcome.

    Raises:
        AssertionError: If an unhandled phase is encountered.
    """
    phase = state.phase

    if phase == GamePhase.MARKET:
        # Move to play phase
        state.phase = GamePhase.PLAY
        return ActionResult(
            success=True,
            message="Moving to play phase",
            state=state,
        )

    if phase == GamePhase.PLAY:
        # Move to combat phase
        state.phase = GamePhase.COMBAT
        return ActionResult(
            success=True,
            message="Moving to combat phase",
            state=state,
        )

    if phase == GamePhase.COMBAT:
        # Move to end phase
        state.phase = GamePhase.END
        return ActionResult(
            success=True,
            message="Combat resolved, ending turn",
            state=state,
        )

    if phase == GamePhase.END:
        # Start new turn
        state.turn += 1
        state.phase = GamePhase.MARKET

        # Set PO for all players
        new_po = state.get_po_for_turn()
        for player in state.players:
            player.po = new_po

        # Rotate buy order every 2 turns (per game rules)
        if state.turn % 2 == 1 and state.buy_order:
            state.buy_order = state.buy_order[1:] + [state.buy_order[0]]

        return ActionResult(
            success=True,
            message=f"Starting turn {state.turn}, PO: {new_po}",
            state=state,
        )

    # This should never be reached - ensures exhaustive matching
    _assert_never(phase)  # type: ignore[arg-type]
