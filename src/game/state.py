"""Game state management for CartesSociete.

This module defines the core game state classes including PlayerState,
GameState, and related enums for tracking game progression.
"""

from dataclasses import dataclass, field
from enum import Enum

from configs import DEFAULT_CONFIG, GameConfig
from src.cards.models import Card, CardType, DemonCard


class GamePhase(Enum):
    """Phases of a game turn."""

    MARKET = "market"  # Buy phase - players can buy cards from market
    PLAY = "play"  # Play phase - players can play/replace cards on board
    COMBAT = "combat"  # Combat phase - resolve attacks
    END = "end"  # End of turn cleanup


class InvalidPlayerError(Exception):
    """Raised when player state is invalid."""

    pass


@dataclass
class PlayerState:
    """State of a single player in the game.

    Attributes:
        player_id: Unique identifier for the player.
        name: Display name of the player.
        health: Current health points (starts at config.starting_health).
        hand: Cards in the player's hand.
        board: Cards on the player's board (max 8 for non-Lapin).
        po: Current gold/PO available this turn.
        eliminated: Whether the player has been eliminated.
    """

    player_id: int
    name: str
    health: int = DEFAULT_CONFIG.starting_health
    hand: list[Card] = field(default_factory=list)
    board: list[Card] = field(default_factory=list)
    po: int = 0
    eliminated: bool = False

    def __post_init__(self) -> None:
        """Validate player state after initialization."""
        if not self.name or not self.name.strip():
            raise InvalidPlayerError("Player name cannot be empty")
        if len(self.name) > 50:
            raise InvalidPlayerError("Player name cannot exceed 50 characters")
        # Sanitize name to prevent injection issues
        self.name = self.name.strip()

    def get_board_count(self, include_demons: bool = False) -> int:
        """Get the number of cards on the board.

        Args:
            include_demons: Whether to count demon cards (they don't count
                towards board limit by default).

        Returns:
            Number of cards on the board.
        """
        if include_demons:
            return len(self.board)
        return sum(1 for card in self.board if card.card_type != CardType.DEMON)

    def get_total_attack(self) -> int:
        """Calculate the total attack value of all cards on the board.

        Returns:
            Sum of attack values of all board cards.
        """
        return sum(card.attack for card in self.board)

    def get_total_health(self) -> int:
        """Calculate the total health (defense) of all cards on the board.

        Returns:
            Sum of health values of all board cards.
        """
        return sum(card.health for card in self.board)

    def can_play_card(self, max_board_size: int | None = None) -> bool:
        """Check if the player can play a card on the board.

        Args:
            max_board_size: Maximum board size (default from config).

        Returns:
            True if the player can play a card.
        """
        if max_board_size is None:
            max_board_size = DEFAULT_CONFIG.max_board_size
        return self.get_board_count() < max_board_size

    def is_alive(self) -> bool:
        """Check if the player is still alive.

        Returns:
            True if player health > 0 and not eliminated.
        """
        return self.health > 0 and not self.eliminated


class InvalidGameStateError(Exception):
    """Raised when game state is invalid."""

    pass


@dataclass
class GameState:
    """Complete state of a CartesSociete game.

    Attributes:
        players: List of player states.
        turn: Current turn number (1-indexed).
        phase: Current game phase.
        active_player_index: Index of the currently active player.
        buy_order: Order in which players buy from market this turn.
        market_cards: Cards currently available in the market.
        cost_1_deck: Deck of cost-1 cards.
        cost_2_deck: Deck of cost-2 cards.
        cost_3_deck: Deck of cost-3 cards.
        cost_4_deck: Deck of cost-4 cards.
        cost_5_deck: Deck of cost-5 cards.
        weapon_deck: Deck of weapon cards.
        demon_deck: Deck of demon cards.
        discard_pile: Discarded cards that can be recycled.
        config: Game configuration values.
    """

    players: list[PlayerState]
    turn: int = 1
    phase: GamePhase = GamePhase.MARKET
    active_player_index: int = 0
    buy_order: list[int] = field(default_factory=list)
    market_cards: list[Card] = field(default_factory=list)
    cost_1_deck: list[Card] = field(default_factory=list)
    cost_2_deck: list[Card] = field(default_factory=list)
    cost_3_deck: list[Card] = field(default_factory=list)
    cost_4_deck: list[Card] = field(default_factory=list)
    cost_5_deck: list[Card] = field(default_factory=list)
    weapon_deck: list[Card] = field(default_factory=list)
    demon_deck: list[DemonCard] = field(default_factory=list)
    discard_pile: list[Card] = field(default_factory=list)
    config: GameConfig = field(default_factory=lambda: DEFAULT_CONFIG)

    def get_current_cost_tier(self) -> int:
        """Get the current cost tier based on turn number.

        Returns:
            The current cost tier (1-5).
        """
        return self.config.get_cost_tier_for_turn(self.turn)

    def get_po_for_turn(self) -> int:
        """Calculate PO available for the current turn.

        Returns:
            PO available this turn.
        """
        return self.config.get_po_for_turn(self.turn)

    def get_active_player(self) -> PlayerState:
        """Get the currently active player.

        Returns:
            The active player's state.

        Raises:
            InvalidGameStateError: If active_player_index is out of bounds.
        """
        if not 0 <= self.active_player_index < len(self.players):
            raise InvalidGameStateError(
                f"Invalid active_player_index {self.active_player_index} "
                f"for {len(self.players)} players"
            )
        return self.players[self.active_player_index]

    def get_alive_players(self) -> list[PlayerState]:
        """Get all players who are still alive.

        Returns:
            List of alive players.
        """
        return [p for p in self.players if p.is_alive()]

    def get_opponents(self, player: PlayerState) -> list[PlayerState]:
        """Get all alive opponents of a player.

        Args:
            player: The player whose opponents to find.

        Returns:
            List of alive players excluding the given player.
        """
        return [p for p in self.get_alive_players() if p.player_id != player.player_id]

    def is_game_over(self) -> bool:
        """Check if the game is over.

        Game ends when only one player remains alive.

        Returns:
            True if the game is over.
        """
        return len(self.get_alive_players()) <= 1

    def get_winner(self) -> PlayerState | None:
        """Get the winning player if the game is over.

        Returns:
            The winning player, or None if game is not over.
        """
        alive = self.get_alive_players()
        if len(alive) == 1:
            return alive[0]
        return None

    def get_deck_for_tier(self, tier: int) -> list[Card]:
        """Get the deck for a specific cost tier.

        Args:
            tier: The cost tier (1-5).

        Returns:
            Reference to the specified tier's deck.

        Raises:
            ValueError: If tier is not between 1 and 5.
        """
        if not 1 <= tier <= 5:
            raise ValueError(f"Invalid cost tier {tier}, must be 1-5")
        decks = {
            1: self.cost_1_deck,
            2: self.cost_2_deck,
            3: self.cost_3_deck,
            4: self.cost_4_deck,
            5: self.cost_5_deck,
        }
        return decks[tier]

    def get_current_deck(self) -> list[Card]:
        """Get the deck corresponding to the current cost tier.

        Returns:
            Reference to the current cost tier's deck.
        """
        return self.get_deck_for_tier(self.get_current_cost_tier())


def create_initial_game_state(
    num_players: int,
    player_names: list[str] | None = None,
    config: GameConfig | None = None,
) -> GameState:
    """Create an initial game state for a new game.

    Args:
        num_players: Number of players (2-5).
        player_names: Optional list of player names.
        config: Optional game configuration. Uses DEFAULT_CONFIG if not provided.

    Returns:
        A new GameState ready for play.

    Raises:
        ValueError: If num_players is not between min and max from config.
    """
    if config is None:
        config = DEFAULT_CONFIG

    if not config.min_players <= num_players <= config.max_players:
        raise ValueError(
            f"Number of players must be {config.min_players}-{config.max_players}, "
            f"got {num_players}"
        )

    if player_names is None:
        player_names = [f"Player {i + 1}" for i in range(num_players)]
    elif len(player_names) != num_players:
        raise ValueError(
            f"Number of names ({len(player_names)}) must match "
            f"number of players ({num_players})"
        )

    players = [
        PlayerState(player_id=i, name=name, health=config.starting_health)
        for i, name in enumerate(player_names)
    ]

    # Initial buy order is just player order
    buy_order = list(range(num_players))

    return GameState(
        players=players,
        buy_order=buy_order,
        config=config,
    )
