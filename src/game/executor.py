"""Action executor for player agents.

This module bridges player Action objects with the game action functions,
allowing the engine to execute player decisions.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.players.action import Action

from src.cards.models import CardType, Family

from .abilities import can_play_lapin_card
from .actions import (
    ActionResult,
    buy_card,
    equip_weapon,
    evolve_cards,
    play_card,
    replace_card,
    sacrifice_card,
)
from .state import GameState, PlayerState


class InvalidActionError(Exception):
    """Raised when an action cannot be executed."""

    pass


def execute_action(
    state: GameState,
    player: PlayerState,
    action: "Action",
) -> ActionResult:
    """Execute a player action on the game state.

    This function translates player Action objects into calls to the
    appropriate action functions from the actions module.

    Args:
        state: Current game state.
        player: The player taking the action.
        action: The action to execute.

    Returns:
        ActionResult indicating success/failure and updated state.

    Raises:
        InvalidActionError: If the action is malformed.
        Various action errors: If the action is invalid for the current state.
    """
    from src.players.action import ActionType

    if action.action_type == ActionType.BUY_CARD:
        if action.card is None:
            raise InvalidActionError("BUY_CARD action requires a card")
        return buy_card(state, player, action.card)

    elif action.action_type == ActionType.PLAY_CARD:
        if action.card is None:
            raise InvalidActionError("PLAY_CARD action requires a card")
        return play_card(state, player, action.card)

    elif action.action_type == ActionType.REPLACE_CARD:
        if action.card is None or action.target_card is None:
            raise InvalidActionError(
                "REPLACE_CARD action requires card and target_card"
            )
        return replace_card(state, player, action.card, action.target_card)

    elif action.action_type == ActionType.EVOLVE:
        if action.evolve_cards is None:
            raise InvalidActionError("EVOLVE action requires evolve_cards")
        return evolve_cards(state, player, list(action.evolve_cards))

    elif action.action_type == ActionType.EQUIP_WEAPON:
        if action.card is None or action.target_card is None:
            raise InvalidActionError(
                "EQUIP_WEAPON action requires card (weapon) and target_card"
            )
        return equip_weapon(state, player, action.card, action.target_card)

    elif action.action_type == ActionType.SACRIFICE_CARD:
        if action.card is None:
            raise InvalidActionError("SACRIFICE_CARD action requires a card")
        return sacrifice_card(state, player, action.card)

    elif action.action_type == ActionType.END_PHASE:
        return ActionResult(
            success=True,
            message=f"{player.name} ends phase",
            state=state,
        )

    raise InvalidActionError(f"Unknown action type: {action.action_type}")


def get_legal_actions_for_player(
    state: GameState,
    player: PlayerState,
) -> list["Action"]:
    """Get all legal actions for a player in the current state.

    This function generates Action objects for all valid moves.

    Args:
        state: Current game state.
        player: The player whose actions to enumerate.

    Returns:
        List of valid Action objects.
    """
    from src.players.action import Action

    from .state import GamePhase

    actions: list[Action] = []

    if state.phase == GamePhase.MARKET:
        # Can buy affordable cards from market
        for card in state.market_cards:
            if card.cost is not None and card.cost <= player.po:
                actions.append(Action.buy(card))

        # Can always end phase
        actions.append(Action.end_phase())

    elif state.phase == GamePhase.PLAY:
        max_board = state.config.max_board_size

        # Can play cards from hand if board not full
        for card in player.hand:
            # Demons bypass board limit
            if card.card_type == CardType.DEMON:
                actions.append(Action.play(card))
            # Lapins have special board limit rules
            elif card.family == Family.LAPIN:
                if can_play_lapin_card(player, max_board):
                    actions.append(Action.play(card))
            # Normal cards use standard limit
            elif player.can_play_card(max_board):
                actions.append(Action.play(card))

        # Can replace cards on board
        for hand_card in player.hand:
            for board_card in player.board:
                actions.append(Action.replace(hand_card, board_card))

        # Check for evolution opportunities
        from collections import Counter

        name_counts: Counter[str] = Counter()
        cards_by_name: dict[str, list] = {}

        for card in player.hand + player.board:
            if card.level == 1:
                name_counts[card.name] += 1
                if card.name not in cards_by_name:
                    cards_by_name[card.name] = []
                cards_by_name[card.name].append(card)

        for name, count in name_counts.items():
            if count >= 3:
                # Can evolve - take first 3 cards
                evolve_set = cards_by_name[name][:3]
                actions.append(Action.evolve(evolve_set))

        # Can equip weapons from hand to board cards
        weapons_in_hand = [c for c in player.hand if c.card_type == CardType.WEAPON]
        for weapon in weapons_in_hand:
            for board_card in player.board:
                # Can only equip if card doesn't already have a weapon
                if board_card.id not in player.equipped_weapons:
                    actions.append(Action.equip_weapon(weapon, board_card))

        # Can sacrifice cards from board
        for board_card in player.board:
            actions.append(Action.sacrifice(board_card))

        # Can always end phase
        actions.append(Action.end_phase())

    return actions
