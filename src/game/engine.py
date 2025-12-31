"""Game engine for CartesSociete.

This module provides the main game loop and orchestrates all game
components including state management, actions, combat, and market.
"""

from dataclasses import dataclass, field

from src.cards.models import Card

from .abilities import apply_per_turn_effects
from .actions import end_turn
from .combat import CombatResult, resolve_combat
from .market import mix_decks, refresh_market, setup_decks, should_mix_decks
from .state import GamePhase, PlayerState, create_initial_game_state


@dataclass
class TurnResult:
    """Result of executing a complete turn.

    Attributes:
        turn_number: The turn that was executed.
        combat_result: Result of combat resolution.
        per_turn_damage: Per-turn self-damage applied (e.g., from Mutanus).
        eliminated_players: Players eliminated this turn.
        game_over: Whether the game ended this turn.
        winner: The winning player if game is over.
    """

    turn_number: int
    combat_result: CombatResult | None = None
    per_turn_damage: dict[int, int] = field(default_factory=dict)
    eliminated_players: list[PlayerState] = field(default_factory=list)
    game_over: bool = False
    winner: PlayerState | None = None


class GameEngine:
    """Main game engine that orchestrates a CartesSociete game.

    The engine manages the game loop, processes player actions,
    and handles phase transitions.

    Attributes:
        state: Current game state.
        config: Game configuration.
    """

    def __init__(
        self,
        num_players: int,
        player_names: list[str] | None = None,
        all_cards: list[Card] | None = None,
    ) -> None:
        """Initialize a new game.

        Args:
            num_players: Number of players (2-5).
            player_names: Optional list of player names.
            all_cards: Optional list of cards to use. If None, uses empty decks.
        """
        self.state = create_initial_game_state(num_players, player_names)

        # Set up decks if cards provided
        if all_cards:
            (
                self.state.cost_1_deck,
                self.state.cost_2_deck,
                self.state.cost_3_deck,
                self.state.cost_4_deck,
                self.state.cost_5_deck,
                self.state.weapon_deck,
                self.state.demon_deck,
            ) = setup_decks(all_cards)

        # Initialize first turn
        self._start_turn()

    def _start_turn(self) -> None:
        """Initialize a new turn."""
        # Set PO for all players
        po = self.state.get_po_for_turn()
        for player in self.state.players:
            player.po = po

        # Reveal market cards
        refresh_market(self.state)

        # Set phase to market
        self.state.phase = GamePhase.MARKET

    def advance_phase(self) -> GamePhase:
        """Advance to the next game phase.

        Returns:
            The new game phase.
        """
        end_turn(self.state)
        return self.state.phase

    def execute_combat(self) -> CombatResult:
        """Execute the combat phase.

        Returns:
            Combat result with damage dealt and eliminations.
        """
        if self.state.phase != GamePhase.COMBAT:
            self.state.phase = GamePhase.COMBAT

        result = resolve_combat(self.state)
        return result

    def end_turn(self) -> TurnResult:
        """Complete the current turn and prepare for the next.

        Handles combat resolution, per-turn effects, deck mixing, and turn
        transition.

        Returns:
            TurnResult with turn outcome.
        """
        turn_number = self.state.turn

        # Resolve combat if in combat phase
        combat_result = None
        if self.state.phase == GamePhase.COMBAT:
            combat_result = self.execute_combat()

        # Move to end phase
        self.state.phase = GamePhase.END

        # Apply per-turn effects (e.g., Mutanus "Vous perdez X PV par tour")
        per_turn_damage: dict[int, int] = {}
        all_eliminations: list[PlayerState] = []

        if combat_result:
            all_eliminations = list(combat_result.eliminations)

        for player in self.state.get_alive_players():
            damage = apply_per_turn_effects(player)
            if damage > 0:
                per_turn_damage[player.player_id] = damage
                # Check for elimination from per-turn damage
                if player.health <= 0 and not player.eliminated:
                    player.eliminated = True
                    all_eliminations.append(player)

        # Check for game over
        if self.state.is_game_over():
            return TurnResult(
                turn_number=turn_number,
                combat_result=combat_result,
                per_turn_damage=per_turn_damage,
                eliminated_players=all_eliminations,
                game_over=True,
                winner=self.state.get_winner(),
            )

        # Handle deck mixing after even turns
        if should_mix_decks(self.state):
            mix_decks(self.state)

        # Start new turn
        self.state.turn += 1
        self._start_turn()

        return TurnResult(
            turn_number=turn_number,
            combat_result=combat_result,
            per_turn_damage=per_turn_damage,
            eliminated_players=all_eliminations,
            game_over=False,
        )

    def run_turn(self) -> TurnResult:
        """Run a complete turn from start to finish.

        This method assumes no player interaction (for simulation).
        In a real game, you'd pause for player input between phases.

        Returns:
            TurnResult with turn outcome.
        """
        # Market phase (players buy cards)
        self.state.phase = GamePhase.MARKET
        # ... player actions would go here

        # Play phase (players play/replace cards)
        self.state.phase = GamePhase.PLAY
        # ... player actions would go here

        # Combat phase
        self.state.phase = GamePhase.COMBAT
        self.execute_combat()

        # End turn
        return self.end_turn()

    def simulate_game(self, max_turns: int = 100) -> PlayerState | None:
        """Simulate a complete game with random/no actions.

        This is a basic simulation that just advances turns without
        player actions. Useful for testing the game loop.

        Args:
            max_turns: Maximum turns before forcing a draw.

        Returns:
            The winning player, or None if max turns reached.
        """
        while self.state.turn <= max_turns:
            result = self.run_turn()
            if result.game_over:
                return result.winner

        return None  # Draw/timeout

    def get_legal_actions(self, player: PlayerState) -> list[str]:
        """Get a list of legal actions for a player in the current phase.

        Args:
            player: The player to check.

        Returns:
            List of action descriptions.
        """
        actions: list[str] = []

        if self.state.phase == GamePhase.MARKET:
            # Can buy affordable cards from market
            for card in self.state.market_cards:
                if card.cost is not None and card.cost <= player.po:
                    actions.append(f"buy:{card.id}")

            actions.append("end_market")

        elif self.state.phase == GamePhase.PLAY:
            # Can play cards from hand
            can_play = player.can_play_card()
            for card in player.hand:
                if can_play:
                    actions.append(f"play:{card.id}")
                # Can always replace
                for board_card in player.board:
                    actions.append(f"replace:{card.id}:{board_card.id}")

            actions.append("end_play")

        return actions

    def get_state_summary(self) -> str:
        """Get a summary of the current game state.

        Returns:
            Multi-line string describing the game state.
        """
        lines = [
            f"=== Turn {self.state.turn} - {self.state.phase.value} phase ===",
            f"Cost Tier: {self.state.get_current_cost_tier()}",
            f"PO: {self.state.get_po_for_turn()}",
            "",
            "Players:",
        ]

        for player in self.state.players:
            status = "ALIVE" if player.is_alive() else "ELIMINATED"
            lines.append(
                f"  {player.name}: {player.health} PV, "
                f"{len(player.hand)} hand, {len(player.board)} board [{status}]"
            )
            if player.board:
                total_atk = player.get_total_attack()
                total_hp = player.get_total_health()
                lines.append(f"    Board: ATK={total_atk}, HP={total_hp}")

        lines.append(f"\nMarket: {len(self.state.market_cards)} cards")

        return "\n".join(lines)
