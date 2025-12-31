"""Market system for CartesSociete.

This module handles the card market including deck management,
card revealing, deck mixing, and market refreshing.
"""

import copy
import random

from src.cards.models import Card, CardType, CreatureCard, DemonCard, WeaponCard

from .state import GameState


def setup_decks(
    all_cards: list[Card],
    copies_per_card: int = 5,
) -> tuple[
    list[Card],  # cost_1
    list[Card],  # cost_2
    list[Card],  # cost_3
    list[Card],  # cost_4
    list[Card],  # cost_5
    list[WeaponCard],  # weapons
    list[DemonCard],  # demons
]:
    """Set up the game decks from a card pool.

    Creates copies of each card and sorts them into appropriate decks
    based on cost and type.

    Args:
        all_cards: List of unique cards to use.
        copies_per_card: Number of copies of each card.

    Returns:
        Tuple of (cost_1, cost_2, cost_3, cost_4, cost_5, weapons, demons) decks.
    """
    cost_decks: dict[int, list[Card]] = {i: [] for i in range(1, 6)}
    weapons: list[WeaponCard] = []
    demons: list[DemonCard] = []

    for card in all_cards:
        # Create copies of each card
        for _ in range(copies_per_card):
            # Deep copy to ensure each card is a unique instance
            card_copy = copy.deepcopy(card)
            if card_copy.card_type == CardType.WEAPON:
                if isinstance(card_copy, WeaponCard):
                    weapons.append(card_copy)
            elif card_copy.card_type == CardType.DEMON:
                if isinstance(card_copy, DemonCard):
                    demons.append(card_copy)
            elif card_copy.card_type == CardType.CREATURE:
                if isinstance(card_copy, CreatureCard) and card_copy.cost is not None:
                    # Only add Level 1 cards to decks (Level 2 comes from evolution)
                    if card_copy.level == 1:
                        cost_decks[card_copy.cost].append(card_copy)

    # Shuffle all decks
    for deck in cost_decks.values():
        random.shuffle(deck)
    random.shuffle(weapons)
    random.shuffle(demons)

    return (
        cost_decks[1],
        cost_decks[2],
        cost_decks[3],
        cost_decks[4],
        cost_decks[5],
        weapons,
        demons,
    )


def reveal_market_cards(
    state: GameState,
    count: int = 5,
) -> list[Card]:
    """Reveal cards from the current cost tier deck to the market.

    Args:
        state: Current game state.
        count: Number of cards to reveal.

    Returns:
        List of newly revealed cards.
    """
    current_deck = state.get_current_deck()
    revealed: list[Card] = []

    for _ in range(count):
        if current_deck:
            card = current_deck.pop()
            revealed.append(card)
            state.market_cards.append(card)

    return revealed


def mix_decks(state: GameState) -> int:
    """Mix remaining cards from current deck into the next tier.

    Called after every even turn. Takes remaining cards from current
    tier's deck, shuffles them, splits roughly in half, mixes one half
    into the next tier deck, and discards the other half.

    Args:
        state: Current game state.

    Returns:
        Number of cards mixed into next tier.
    """
    current_tier = state.get_current_cost_tier()
    max_tier = state.config.max_cost_tier

    # Can't mix if we're at max tier
    if current_tier >= max_tier:
        return 0

    current_deck = state.get_current_deck()
    next_deck = state.get_deck_for_tier(current_tier + 1)

    if not current_deck:
        return 0

    # Clear market cards back to current deck first
    current_deck.extend(state.market_cards)
    state.market_cards.clear()

    # Shuffle remaining cards
    random.shuffle(current_deck)

    # Split roughly in half
    half = len(current_deck) // 2
    to_mix = current_deck[:half]
    to_discard = current_deck[half:]

    # Mix into next tier
    next_deck.extend(to_mix)
    random.shuffle(next_deck)

    # Discard the other half
    state.discard_pile.extend(to_discard)

    # Clear current deck
    current_deck.clear()

    return len(to_mix)


def should_mix_decks(state: GameState) -> bool:
    """Check if decks should be mixed after the current turn.

    Deck mixing occurs after every even turn until deck_mix_end_turn.

    Args:
        state: Current game state.

    Returns:
        True if decks should be mixed.
    """
    return state.config.should_mix_decks(state.turn)


def refresh_market(state: GameState, count: int | None = None) -> list[Card]:
    """Refresh the market for a new turn.

    Clears any remaining market cards (they stay unbought until mixing)
    and reveals new cards from the current tier deck.

    Args:
        state: Current game state.
        count: Number of cards to reveal. Uses config default if not provided.

    Returns:
        List of newly revealed cards.
    """
    if count is None:
        count = state.config.cards_per_reveal

    # Keep unbought cards in market until mixing
    # Only reveal up to the difference
    current_count = len(state.market_cards)
    to_reveal = max(0, count - current_count)

    if to_reveal > 0:
        return reveal_market_cards(state, to_reveal)
    return []


def get_market_summary(state: GameState) -> str:
    """Generate a summary of the current market state.

    Args:
        state: Current game state.

    Returns:
        Multi-line string describing the market.
    """
    tier = state.get_current_cost_tier()
    lines = [
        f"=== Market (Turn {state.turn}, Cost Tier {tier}) ===",
        f"PO Available: {state.get_po_for_turn()}",
        "",
        "Available Cards:",
    ]

    if not state.market_cards:
        lines.append("  (empty)")
    else:
        for i, card in enumerate(state.market_cards, 1):
            cost_str = str(card.cost) if card.cost else "X"
            lines.append(
                f"  {i}. {card.name} "
                f"(Cost {cost_str}, ATK {card.attack}, HP {card.health})"
            )

    return "\n".join(lines)
