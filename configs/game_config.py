"""Game configuration for CartesSociete.

This module centralizes all game constants and configuration values.
Modify these values to adjust game balance without changing game logic.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class GameConfig:
    """Configuration values for the game engine.

    All game constants are defined here to avoid hardcoding values
    throughout the codebase.
    """

    # Player settings
    starting_health: int = 400
    max_board_size: int = 8
    min_players: int = 2
    max_players: int = 5

    # Market settings
    cards_per_reveal: int = 5
    copies_per_card: int = 5

    # PO (gold) settings
    turn_1_po: int = 4
    max_po: int = 11

    # Turn settings
    max_cost_tier: int = 5
    deck_mix_end_turn: int = 10  # Stop mixing after this turn
    max_turns: int = 100  # For simulation timeout

    # Evolution settings
    cards_required_for_evolution: int = 3

    def get_po_for_turn(self, turn: int) -> int:
        """Calculate PO available for a given turn.

        Formula: card_cost × 2 + 1 (exception: Turn 1 = turn_1_po)

        Args:
            turn: The turn number (1-indexed).

        Returns:
            PO available for the turn.
        """
        if turn == 1:
            return self.turn_1_po
        cost_tier = self.get_cost_tier_for_turn(turn)
        return min(cost_tier * 2 + 1, self.max_po)

    def get_cost_tier_for_turn(self, turn: int) -> int:
        """Get the cost tier for a given turn.

        Turns 1-2: Cost 1, Turns 3-4: Cost 2, etc.

        Args:
            turn: The turn number (1-indexed).

        Returns:
            The cost tier (1-5).
        """
        return min((turn + 1) // 2, self.max_cost_tier)

    def should_mix_decks(self, turn: int) -> bool:
        """Check if decks should be mixed after the given turn.

        Deck mixing occurs after every even turn until deck_mix_end_turn.

        Args:
            turn: The turn number.

        Returns:
            True if decks should be mixed.
        """
        return turn % 2 == 0 and turn < self.deck_mix_end_turn


# Default configuration instance
DEFAULT_CONFIG = GameConfig()
