"""Game actions for CartesSociete.

This module defines the actions that players can take during their turn,
including buying cards, playing cards, evolving cards, and ending turns.
"""

from dataclasses import dataclass
from enum import Enum

from src.cards.models import Card, CardType, Family

from .state import GamePhase, GameState, PlayerState


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

    if card not in state.market_cards:
        raise InvalidCardError(f"Card {card.name} is not in the market")

    if card.cost is None:
        raise InvalidCardError(f"Cannot buy card {card.name} with X cost")

    if card.cost > player.po:
        raise InsufficientPOError(
            f"Need {card.cost} PO to buy {card.name}, but only have {player.po}"
        )

    # Execute the purchase
    player.po -= card.cost
    state.market_cards.remove(card)
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

    if card not in player.hand:
        raise InvalidCardError(f"Card {card.name} is not in hand")

    # Check board limit (Lapin family can exceed limit)
    is_lapin = card.family == Family.LAPIN
    is_demon = card.card_type == CardType.DEMON
    max_board = 8

    # Demons don't count towards limit, Lapin can exceed limit
    if not is_demon and not is_lapin and not player.can_play_card(max_board):
        raise BoardFullError(
            f"Board is full ({player.get_board_count()}/{max_board}). "
            "Replace a card instead."
        )

    # Execute the play
    player.hand.remove(card)
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

    if new_card not in player.hand:
        raise InvalidCardError(f"Card {new_card.name} is not in hand")

    if old_card not in player.board:
        raise InvalidCardError(f"Card {old_card.name} is not on board")

    # Execute the replacement
    player.hand.remove(new_card)
    player.board.remove(old_card)
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
) -> ActionResult:
    """Evolve 3 matching cards into a Level 2 version.

    Evolution requires 3 cards with the exact same name.
    2 cards go to discard, 1 card is "flipped" to Level 2.
    Cards can be evolved from hand or board.

    Args:
        state: Current game state.
        player: The player evolving cards.
        cards: List of 3 cards to evolve.

    Returns:
        ActionResult with the outcome.

    Raises:
        EvolutionError: If evolution requirements are not met.
    """
    if len(cards) != 3:
        raise EvolutionError(f"Evolution requires exactly 3 cards, got {len(cards)}")

    # All cards must have the same name
    names = {card.name for card in cards}
    if len(names) != 1:
        raise EvolutionError(
            f"All cards must have the same name for evolution, got: {names}"
        )

    # All cards must be Level 1
    if not all(card.level == 1 for card in cards):
        raise EvolutionError("All cards must be Level 1 to evolve")

    # Cards can be from hand or board
    all_player_cards = player.hand + player.board
    for card in cards:
        if card not in all_player_cards:
            raise EvolutionError(f"Card {card.name} not found in hand or board")

    # Find the evolved version (Level 2)
    # For now, we just mark which card "stays" and simulate the flip
    # In a real implementation, we'd look up the Level 2 card from repository
    evolved_card = cards[0]  # The first card stays and is "flipped"
    discard_cards = cards[1:3]  # These go to discard

    # Remove all 3 cards from hand/board
    for card in cards:
        if card in player.hand:
            player.hand.remove(card)
        elif card in player.board:
            player.board.remove(card)

    # For now, we put the evolved card back
    # In real game, it would be the Level 2 version
    # TODO: Replace with actual Level 2 card lookup from repository
    player.board.append(evolved_card)

    # Discard cards go to discard pile
    state.discard_pile.extend(discard_cards)

    return ActionResult(
        success=True,
        message=f"{player.name} evolved {cards[0].name} to Level 2",
        state=state,
    )


def end_turn(state: GameState) -> ActionResult:
    """End the current turn and move to the next phase or turn.

    Args:
        state: Current game state.

    Returns:
        ActionResult with the outcome.
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

    elif phase == GamePhase.PLAY:
        # Move to combat phase
        state.phase = GamePhase.COMBAT
        return ActionResult(
            success=True,
            message="Moving to combat phase",
            state=state,
        )

    elif phase == GamePhase.COMBAT:
        # Move to end phase
        state.phase = GamePhase.END
        return ActionResult(
            success=True,
            message="Combat resolved, ending turn",
            state=state,
        )

    elif phase == GamePhase.END:
        # Start new turn
        state.turn += 1
        state.phase = GamePhase.MARKET

        # Set PO for all players
        new_po = state.get_po_for_turn()
        for player in state.players:
            player.po = new_po

        # Rotate buy order every 2 turns
        if state.turn % 2 == 1:
            state.buy_order = state.buy_order[1:] + [state.buy_order[0]]

        return ActionResult(
            success=True,
            message=f"Starting turn {state.turn}, PO: {new_po}",
            state=state,
        )

    return ActionResult(
        success=False,
        message=f"Unknown phase: {phase}",
        state=state,
    )
