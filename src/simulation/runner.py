"""Game runner for complete game simulations with AI agents.

This module provides GameRunner, which orchestrates full games from start
to finish using AI player agents.
"""

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from configs import DEFAULT_CONFIG, GameConfig
from src.game.combat import CombatResult, resolve_combat
from src.game.executor import execute_action, get_legal_actions_for_player
from src.game.market import mix_decks, refresh_market, should_mix_decks
from src.game.state import GamePhase, GameState, create_initial_game_state
from src.players.action import ActionType

from .logger import GameEvent, GameLogger
from .stats import PlayerStats

if TYPE_CHECKING:
    from src.players.base import Player


@dataclass
class GameResult:
    """Result of a completed game simulation.

    Attributes:
        winner_id: ID of the winning player (None for draw/timeout).
        winner_type: Agent type of the winner.
        turns: Number of turns played.
        final_state: The final game state.
        events: List of game events (if logging enabled).
        player_stats: Statistics for each player.
    """

    winner_id: int | None
    winner_type: str | None
    turns: int
    final_state: GameState
    events: list[GameEvent] = field(default_factory=list)
    player_stats: dict[int, PlayerStats] = field(default_factory=dict)


class GameRunner:
    """Orchestrates complete game simulations with AI agents.

    The GameRunner manages the full game loop, interfacing between
    AI player agents and the game engine. It handles:
    - Turn progression (MARKET -> PLAY -> COMBAT -> END)
    - Action execution for each player
    - Event logging for analysis
    - Statistics collection

    Attributes:
        players: List of AI player agents.
        config: Game configuration.
        log_events: Whether to log events.
    """

    # Maximum turns before forcing a draw (prevent infinite games)
    MAX_TURNS: int = 100

    def __init__(
        self,
        players: list["Player"],
        config: GameConfig | None = None,
        seed: int | None = None,
        log_events: bool = True,
        max_turns: int | None = None,
    ) -> None:
        """Initialize the game runner.

        Args:
            players: List of AI player agents (2-5 players).
            config: Game configuration. Uses DEFAULT_CONFIG if None.
            seed: Random seed for reproducibility.
            log_events: Whether to log game events.
            max_turns: Maximum turns before draw. Uses MAX_TURNS if None.

        Raises:
            ValueError: If number of players is invalid.
        """
        if config is None:
            config = DEFAULT_CONFIG

        if not config.min_players <= len(players) <= config.max_players:
            raise ValueError(
                f"Number of players must be {config.min_players}-{config.max_players}, "
                f"got {len(players)}"
            )

        self.players = players
        self.config = config
        self.log_events = log_events
        self.max_turns = max_turns or self.MAX_TURNS
        self._rng = random.Random(seed)
        self._logger = GameLogger() if log_events else None

        # Track statistics
        self._stats: dict[int, PlayerStats] = {}

    def run_game(self) -> GameResult:
        """Run a complete game from start to finish.

        Executes the full game loop until a winner is determined
        or max turns is reached.

        Returns:
            GameResult with winner, statistics, and events.
        """
        # Create initial game state
        player_names = [p.name for p in self.players]
        state = create_initial_game_state(
            num_players=len(self.players),
            player_names=player_names,
            config=self.config,
        )

        # Initialize stats for each player
        for player in self.players:
            self._stats[player.player_id] = PlayerStats(
                player_id=player.player_id,
                player_type=player.info.agent_type,
            )

        # Log game start
        if self._logger is not None:
            self._logger.log_game_start(
                num_players=len(self.players),
                player_info=[
                    {
                        "id": str(p.player_id),
                        "name": p.name,
                        "type": p.info.agent_type,
                    }
                    for p in self.players
                ],
            )

        # Notify players of game start
        for player in self.players:
            player.on_game_start(state)

        # Main game loop
        while state.turn <= self.max_turns:
            if self._logger is not None:
                self._logger.log_turn_start(state.turn)

            # Notify players of turn start
            for player in self.players:
                player.on_turn_start(state, state.turn)

            # Run turn phases
            self._run_market_phase(state)
            self._run_play_phase(state)
            combat_result = self._run_combat_phase(state)
            game_over = self._run_end_phase(state, combat_result)

            if game_over:
                break

        # Determine winner
        winner_id: int | None = None
        winner_type: str | None = None
        winner = state.get_winner()

        if winner:
            winner_id = winner.player_id
            for player in self.players:
                if player.player_id == winner_id:
                    winner_type = player.info.agent_type
                    self._stats[winner_id].won = True
                    break

        # Finalize stats
        for player_id, stats in self._stats.items():
            player_state = state.players[player_id]
            stats.final_health = player_state.health
            if stats.turns_survived == 0:
                stats.turns_survived = state.turn

        # Log game end
        if self._logger is not None:
            self._logger.log_game_end(
                turn=state.turn,
                winner_id=winner_id,
                reason="elimination" if winner else "timeout",
            )

        # Notify players of game end
        for player in self.players:
            player.on_game_end(state, winner_id)

        return GameResult(
            winner_id=winner_id,
            winner_type=winner_type,
            turns=state.turn,
            final_state=state,
            events=self._logger.events if self._logger is not None else [],
            player_stats=self._stats.copy(),
        )

    def _run_market_phase(self, state: GameState) -> None:
        """Execute the market phase for all players.

        Each player takes turns buying cards until they end their phase.

        Args:
            state: Current game state.
        """
        state.phase = GamePhase.MARKET

        # Refresh market with new cards
        refresh_market(state)

        # Give PO to all players
        po = state.get_po_for_turn()
        for player_state in state.players:
            player_state.po = po

        if self._logger is not None:
            self._logger.log_phase_start(state.turn, state.phase)

        # Each player takes market actions
        for player_state in state.get_alive_players():
            player = self._get_player_agent(player_state.player_id)
            if player is None:
                continue

            # Player takes actions until END_PHASE
            while True:
                legal_actions = get_legal_actions_for_player(state, player_state)

                if not legal_actions:
                    break

                action = player.choose_market_action(state, player_state, legal_actions)

                if action.action_type == ActionType.END_PHASE:
                    break

                # Execute the action
                result = execute_action(state, player_state, action)

                # Log and track stats
                if result.success and action.action_type == ActionType.BUY_CARD:
                    self._stats[player.player_id].cards_bought += 1
                    if self._logger is not None and action.card:
                        self._logger.log_card_bought(
                            turn=state.turn,
                            phase=state.phase,
                            player_id=player.player_id,
                            card_name=action.card.name,
                            cost=action.card.cost or 0,
                        )

    def _run_play_phase(self, state: GameState) -> None:
        """Execute the play phase for all players.

        Each player plays cards from hand to board until they end their phase.

        Args:
            state: Current game state.
        """
        state.phase = GamePhase.PLAY

        if self._logger is not None:
            self._logger.log_phase_start(state.turn, state.phase)

        # Each player takes play actions
        for player_state in state.get_alive_players():
            player = self._get_player_agent(player_state.player_id)
            if player is None:
                continue

            # Player takes actions until END_PHASE
            while True:
                legal_actions = get_legal_actions_for_player(state, player_state)

                if not legal_actions:
                    break

                action = player.choose_play_action(state, player_state, legal_actions)

                if action.action_type == ActionType.END_PHASE:
                    break

                # Execute the action
                result = execute_action(state, player_state, action)

                # Log and track stats
                if result.success:
                    if action.action_type == ActionType.PLAY_CARD:
                        self._stats[player.player_id].cards_played += 1
                        if self._logger is not None and action.card:
                            self._logger.log_card_played(
                                turn=state.turn,
                                phase=state.phase,
                                player_id=player.player_id,
                                card_name=action.card.name,
                            )
                    elif action.action_type == ActionType.EVOLVE:
                        self._stats[player.player_id].evolutions += 1
                        if self._logger is not None and action.evolve_cards:
                            base_name = action.evolve_cards[0].name
                            self._logger.log_evolution(
                                turn=state.turn,
                                phase=state.phase,
                                player_id=player.player_id,
                                base_card_name=base_name,
                                evolved_card_name=f"{base_name} Lv.2",
                            )

    def _run_combat_phase(self, state: GameState) -> CombatResult:
        """Execute the combat phase.

        All players attack each other simultaneously.

        Args:
            state: Current game state.

        Returns:
            CombatResult with damage dealt and eliminations.
        """
        state.phase = GamePhase.COMBAT

        if self._logger is not None:
            self._logger.log_phase_start(state.turn, state.phase)

        # Resolve combat
        combat_result = resolve_combat(state)

        # Track damage stats
        for breakdown in combat_result.damage_dealt:
            attacker_id = breakdown.source_player.player_id
            self._stats[attacker_id].damage_dealt += breakdown.total_damage

            target_id = breakdown.target_player.player_id
            self._stats[target_id].damage_taken += breakdown.total_damage

        # Log combat
        if self._logger is not None:
            damage_dict = {
                bd.source_player.player_id: bd.total_damage
                for bd in combat_result.damage_dealt
            }
            elimination_ids = [p.player_id for p in combat_result.eliminations]
            self._logger.log_combat(
                turn=state.turn,
                damage_dealt=damage_dict,
                eliminations=elimination_ids,
            )

            # Log individual eliminations
            for eliminated in combat_result.eliminations:
                self._logger.log_player_eliminated(state.turn, eliminated.player_id)
                self._stats[eliminated.player_id].turns_survived = state.turn

        # Notify all players of combat result
        for player in self.players:
            player.on_combat_result(combat_result)

        return combat_result

    def _run_end_phase(
        self,
        state: GameState,
        combat_result: CombatResult,
    ) -> bool:
        """Execute the end phase and prepare for next turn.

        Handles deck mixing and checks for game over.

        Args:
            state: Current game state.
            combat_result: Result of combat phase.

        Returns:
            True if game is over, False otherwise.
        """
        state.phase = GamePhase.END

        # Check for game over (player elimination)
        if state.is_game_over():
            return True

        # Check for timeout (max turns reached)
        if state.turn >= self.max_turns:
            return True

        # Handle deck mixing after even turns
        if should_mix_decks(state):
            mix_decks(state)

        # Advance to next turn
        state.turn += 1

        return False

    def _get_player_agent(self, player_id: int) -> "Player | None":
        """Get the AI agent for a player ID.

        Args:
            player_id: The player's ID.

        Returns:
            The Player agent, or None if not found.
        """
        for player in self.players:
            if player.player_id == player_id:
                return player
        return None
