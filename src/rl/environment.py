"""Gymnasium environment for CartesSociete.

This module provides a Gymnasium-compatible environment for training
reinforcement learning agents to play CartesSociete.
"""

from dataclasses import dataclass
from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from configs import DEFAULT_CONFIG, GameConfig
from src.cards.models import Card, CardClass, Family
from src.cards.repository import CardRepository
from src.game.combat import resolve_combat
from src.game.executor import execute_action, get_legal_actions_for_player
from src.game.market import refresh_market, setup_decks
from src.game.state import GamePhase, GameState, PlayerState, create_initial_game_state
from src.players.action import Action, ActionType
from src.players.base import Player, PlayerInfo


@dataclass
class RewardConfig:
    """Configuration for reward shaping in the RL environment.

    These parameters control how different game events contribute to the
    reward signal during training. Making these configurable allows
    experimentation with different reward shaping strategies.

    Attributes:
        win: Reward for winning the game.
        lose: Reward (typically negative) for losing the game.
        draw: Reward for drawing the game.
        damage_dealt: Reward per point of damage dealt to opponent.
        damage_taken: Reward (typically negative) per point of damage taken.
        card_bought: Reward for buying a card.
        evolution: Reward for evolving a card.
    """

    win: float = 10.0
    lose: float = -10.0
    draw: float = 0.0
    damage_dealt: float = 0.1
    damage_taken: float = -0.05
    card_bought: float = 0.05
    evolution: float = 0.3


# Default reward configuration (matches original hardcoded values)
DEFAULT_REWARD_CONFIG = RewardConfig()


class RLPlayer(Player):
    """Placeholder player for RL agent integration.

    This player is controlled by external RL actions passed to the environment.
    """

    def __init__(self, player_id: int, name: str | None = None) -> None:
        """Initialize the RL player."""
        super().__init__(player_id, name)
        self._pending_action: Action | None = None

    @property
    def info(self) -> PlayerInfo:
        """Return metadata about this player agent."""
        return PlayerInfo(
            name=self._name or f"rl_agent_{self.player_id}",
            agent_type="rl",
            version="1.0.0",
        )

    def set_action(self, action: Action) -> None:
        """Set the action to take on next turn."""
        self._pending_action = action

    def choose_market_action(
        self,
        state: GameState,
        player_state: PlayerState,
        legal_actions: list[Action],
    ) -> Action:
        """Return the pending action or end phase."""
        if self._pending_action is not None:
            action = self._pending_action
            self._pending_action = None
            return action
        return Action.end_phase()

    def choose_play_action(
        self,
        state: GameState,
        player_state: PlayerState,
        legal_actions: list[Action],
    ) -> Action:
        """Return the pending action or end phase."""
        if self._pending_action is not None:
            action = self._pending_action
            self._pending_action = None
            return action
        return Action.end_phase()


class CartesSocieteEnv(gym.Env):
    """Gymnasium environment for CartesSociete card game.

    This environment provides:
    - Observation: Encoded game state (player stats, cards, market)
    - Action: Index into legal actions list
    - Reward: Based on damage dealt, health changes, and game outcome

    The environment runs a 2-player game where player 0 is the RL agent
    and player 1 is an opponent (configurable).

    Attributes:
        config: Game configuration.
        max_cards: Maximum cards to encode in observations.
        card_dim: Dimension of card feature vector.
    """

    # Environment configuration
    MAX_CARDS_HAND: int = 20
    MAX_CARDS_BOARD: int = 10
    MAX_CARDS_MARKET: int = 10
    CARD_FEATURE_DIM: int = 6  # cost, attack, health, level, family, class

    # Family and class index mappings for encoding
    FAMILY_TO_IDX: dict[Family, int] = {family: i for i, family in enumerate(Family)}
    CLASS_TO_IDX: dict[CardClass, int] = {
        card_class: i for i, card_class in enumerate(CardClass)
    }

    def __init__(
        self,
        opponent_factory: Any = None,
        config: GameConfig | None = None,
        max_actions: int = 50,
        seed: int | None = None,
        reward_config: RewardConfig | None = None,
    ) -> None:
        """Initialize the environment.

        Args:
            opponent_factory: Factory function to create opponent player.
                If None, uses a RandomPlayer.
            config: Game configuration. Uses default if None.
            max_actions: Maximum actions per turn (to bound action space).
            seed: Random seed for reproducibility.
            reward_config: Reward shaping configuration. Uses DEFAULT_REWARD_CONFIG
                if None. See RewardConfig for available parameters.
        """
        super().__init__()

        self.config = config or DEFAULT_CONFIG
        self.reward_config = reward_config or DEFAULT_REWARD_CONFIG
        self.max_actions = max_actions
        self._seed = seed
        self._rng = np.random.default_rng(seed)

        # Import here to avoid circular imports
        from src.players import RandomPlayer

        self._opponent_factory = opponent_factory or (
            lambda pid: RandomPlayer(pid, seed=seed)
        )

        # Load card data for encoding
        self._repository = CardRepository()
        self._all_cards = self._repository.get_all()
        self._card_name_to_idx = {
            card.name: i for i, card in enumerate(self._all_cards)
        }
        self._num_unique_cards = len(self._all_cards)

        # Define observation space
        # Format: [player_stats, hand_cards, board_cards, opp_board, market_cards]
        obs_dim = self._calculate_obs_dim()
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(obs_dim,),
            dtype=np.float32,
        )

        # Action space: index into legal actions (variable size, use max)
        self.action_space = spaces.Discrete(max_actions)

        # Internal state
        self._state: GameState | None = None
        self._rl_player: RLPlayer | None = None
        self._opponent: Player | None = None
        self._legal_actions: list[Action] = []
        self._current_player_state: PlayerState | None = None
        self._episode_reward: float = 0.0
        self._step_count: int = 0
        self._max_steps: int = 500

    def _calculate_obs_dim(self) -> int:
        """Calculate observation space dimension."""
        # Player stats: health, po, board_count, hand_size, turn
        player_stats = 5

        # Cards: each encoded as CARD_FEATURE_DIM features
        hand_cards = self.MAX_CARDS_HAND * self.CARD_FEATURE_DIM
        board_cards = self.MAX_CARDS_BOARD * self.CARD_FEATURE_DIM
        opp_board = self.MAX_CARDS_BOARD * self.CARD_FEATURE_DIM
        market_cards = self.MAX_CARDS_MARKET * self.CARD_FEATURE_DIM

        # Legal action mask (optional - for action masking)
        # action_mask = self.max_actions

        return player_stats + hand_cards + board_cards + opp_board + market_cards

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        """Reset the environment to initial state.

        Args:
            seed: Optional seed for RNG.
            options: Additional options (unused).

        Returns:
            Tuple of (observation, info_dict).
        """
        super().reset(seed=seed)
        if seed is not None:
            self._rng = np.random.default_rng(seed)

        # Create players
        self._rl_player = RLPlayer(0, "RL Agent")
        self._opponent = self._opponent_factory(1)
        players = [self._rl_player, self._opponent]

        # Create game state
        self._state = create_initial_game_state(
            num_players=2,
            player_names=[p.name for p in players],
            config=self.config,
        )

        # Setup decks
        if self._all_cards:
            decks = setup_decks(self._all_cards, copies_per_card=3)
            self._state.cost_1_deck = list(decks[0])
            self._state.cost_2_deck = list(decks[1])
            self._state.cost_3_deck = list(decks[2])
            self._state.cost_4_deck = list(decks[3])
            self._state.cost_5_deck = list(decks[4])
            self._state.weapon_deck = list(decks[5])
            self._state.demon_deck = list(decks[6])

            # Shuffle with our RNG
            for deck in [
                self._state.cost_1_deck,
                self._state.cost_2_deck,
                self._state.cost_3_deck,
                self._state.cost_4_deck,
                self._state.cost_5_deck,
            ]:
                self._rng.shuffle(deck)

            # Reveal initial market
            refresh_market(self._state)

        # Notify players
        for player in players:
            player.on_game_start(self._state)

        # Start market phase and get legal actions
        self._state.phase = GamePhase.MARKET
        po = self._state.get_po_for_turn()
        for ps in self._state.players:
            ps.po = po

        self._current_player_state = self._state.players[0]
        self._legal_actions = get_legal_actions_for_player(
            self._state, self._current_player_state
        )

        self._episode_reward = 0.0
        self._step_count = 0

        obs = self._get_observation()
        info = self._get_info()

        return obs, info

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        """Execute one step in the environment.

        Args:
            action: Index into legal actions list.

        Returns:
            Tuple of (observation, reward, terminated, truncated, info).
        """
        assert self._state is not None
        assert self._rl_player is not None
        assert self._current_player_state is not None

        self._step_count += 1
        reward = 0.0

        # Get the action from legal actions
        if not self._legal_actions:
            # No legal actions - use end phase
            selected_action = Action.end_phase()
        elif action >= len(self._legal_actions):
            # Invalid action index - default to last legal action (usually end_phase)
            selected_action = self._legal_actions[-1]
        else:
            selected_action = self._legal_actions[action]

        # Execute the action
        prev_health = self._state.players[0].health
        prev_opp_health = self._state.players[1].health

        result = execute_action(
            self._state, self._current_player_state, selected_action
        )

        # Reward for action success
        if result.success:
            if selected_action.action_type == ActionType.BUY_CARD:
                reward += self.reward_config.card_bought
            elif selected_action.action_type == ActionType.EVOLVE:
                reward += self.reward_config.evolution

        # Check if we should end phase and progress game
        game_over = False
        if selected_action.action_type == ActionType.END_PHASE:
            # Progress through phases
            game_over, phase_reward = self._progress_game()
            reward += phase_reward

        # Update legal actions for next step
        if not game_over and self._state.phase in (GamePhase.MARKET, GamePhase.PLAY):
            self._current_player_state = self._state.players[0]
            self._legal_actions = get_legal_actions_for_player(
                self._state, self._current_player_state
            )
        else:
            self._legal_actions = []

        # Calculate reward from health changes
        health_delta = self._state.players[0].health - prev_health
        opp_health_delta = self._state.players[1].health - prev_opp_health
        if opp_health_delta < 0:
            reward += abs(opp_health_delta) * self.reward_config.damage_dealt
        if health_delta < 0:
            reward += abs(health_delta) * self.reward_config.damage_taken

        # Terminal rewards
        terminated = game_over or self._state.is_game_over()
        if terminated:
            winner = self._state.get_winner()
            if winner and winner.player_id == 0:
                reward += self.reward_config.win
            elif winner and winner.player_id == 1:
                reward += self.reward_config.lose
            else:
                reward += self.reward_config.draw

        # Truncation (max steps reached)
        truncated = self._step_count >= self._max_steps

        self._episode_reward += reward
        obs = self._get_observation()
        info = self._get_info()

        return obs, reward, terminated, truncated, info

    def _progress_game(self) -> tuple[bool, float]:
        """Progress game through phases after end_phase action.

        Returns:
            Tuple of (game_over, reward).
        """
        assert self._state is not None
        assert self._opponent is not None

        reward = 0.0

        # Let opponent take their actions for current phase
        opp_state = self._state.players[1]

        if self._state.phase == GamePhase.MARKET:
            # Opponent market phase
            while opp_state.is_alive():
                opp_legal = get_legal_actions_for_player(self._state, opp_state)
                if not opp_legal:
                    break
                opp_action = self._opponent.choose_market_action(
                    self._state, opp_state, opp_legal
                )
                if opp_action.action_type == ActionType.END_PHASE:
                    break
                execute_action(self._state, opp_state, opp_action)

            # Move to play phase
            self._state.phase = GamePhase.PLAY

        elif self._state.phase == GamePhase.PLAY:
            # Opponent play phase
            while opp_state.is_alive():
                opp_legal = get_legal_actions_for_player(self._state, opp_state)
                if not opp_legal:
                    break
                opp_action = self._opponent.choose_play_action(
                    self._state, opp_state, opp_legal
                )
                if opp_action.action_type == ActionType.END_PHASE:
                    break
                execute_action(self._state, opp_state, opp_action)

            # Move to combat
            self._state.phase = GamePhase.COMBAT
            combat_result = resolve_combat(self._state)

            # Calculate damage reward
            for breakdown in combat_result.damage_dealt:
                if breakdown.source_player.player_id == 0:
                    reward += breakdown.total_damage * self.reward_config.damage_dealt

            # Check for game over
            if self._state.is_game_over():
                return True, reward

            # Start next turn
            self._state.turn += 1
            self._state.phase = GamePhase.MARKET

            # Give PO to all players
            po = self._state.get_po_for_turn()
            for ps in self._state.players:
                ps.po = po

            # Refresh market
            refresh_market(self._state)

        return False, reward

    def _get_observation(self) -> np.ndarray:
        """Encode the current game state as an observation.

        Returns:
            Numpy array of shape (obs_dim,).
        """
        if self._state is None:
            return np.zeros(self.observation_space.shape, dtype=np.float32)

        player = self._state.players[0]
        opponent = self._state.players[1]

        obs_parts = []

        # Player stats (5 values)
        obs_parts.append(
            [
                player.health / 100.0,  # Normalize
                player.po / 10.0,
                len(player.board) / self.MAX_CARDS_BOARD,
                len(player.hand) / self.MAX_CARDS_HAND,
                self._state.turn / 20.0,
            ]
        )

        # Hand cards
        obs_parts.append(self._encode_cards(player.hand, self.MAX_CARDS_HAND))

        # Board cards
        obs_parts.append(self._encode_cards(player.board, self.MAX_CARDS_BOARD))

        # Opponent board cards
        obs_parts.append(self._encode_cards(opponent.board, self.MAX_CARDS_BOARD))

        # Market cards
        obs_parts.append(
            self._encode_cards(self._state.market_cards, self.MAX_CARDS_MARKET)
        )

        # Flatten and concatenate
        obs = np.concatenate([np.array(part).flatten() for part in obs_parts])
        return obs.astype(np.float32)

    def _encode_cards(self, cards: list[Card], max_cards: int) -> np.ndarray:
        """Encode a list of cards as feature vectors.

        Args:
            cards: List of cards to encode.
            max_cards: Maximum cards to encode (pad with zeros).

        Returns:
            Array of shape (max_cards * CARD_FEATURE_DIM,).
        """
        encoded = np.zeros((max_cards, self.CARD_FEATURE_DIM), dtype=np.float32)

        num_families = len(self.FAMILY_TO_IDX)
        num_classes = len(self.CLASS_TO_IDX)

        for i, card in enumerate(cards[:max_cards]):
            # Normalize features
            encoded[i, 0] = (card.cost or 0) / 5.0  # Cost 1-5
            encoded[i, 1] = card.attack / 10.0
            encoded[i, 2] = card.health / 10.0
            encoded[i, 3] = card.level / 2.0  # Level 1-2
            # Encode family as normalized index
            family_idx = self.FAMILY_TO_IDX.get(card.family, 0)
            encoded[i, 4] = family_idx / num_families if card.family else 0
            # Encode class as normalized index
            class_idx = self.CLASS_TO_IDX.get(card.card_class, 0)
            encoded[i, 5] = class_idx / num_classes if card.card_class else 0

        return encoded.flatten()

    def _get_info(self) -> dict[str, Any]:
        """Get additional information about the environment state.

        Returns:
            Dict with debug/analysis info.
        """
        return {
            "episode_reward": self._episode_reward,
            "step_count": self._step_count,
            "turn": self._state.turn if self._state else 0,
            "phase": self._state.phase.value if self._state else "",
            "num_legal_actions": len(self._legal_actions),
            "player_health": self._state.players[0].health if self._state else 0,
            "opponent_health": self._state.players[1].health if self._state else 0,
        }

    def action_masks(self) -> np.ndarray:
        """Get mask of valid actions (SB3-compatible method name).

        This method is called by MaskablePPO to get valid actions.

        Returns:
            Boolean array where True indicates a valid action.
        """
        mask = np.zeros(self.max_actions, dtype=bool)
        for i in range(min(len(self._legal_actions), self.max_actions)):
            mask[i] = True
        return mask

    def get_action_mask(self) -> np.ndarray:
        """Alias for action_masks() for backwards compatibility."""
        return self.action_masks()

    def render(self) -> None:
        """Render the environment (text mode)."""
        if self._state is None:
            print("No game in progress")
            return

        player = self._state.players[0]
        opponent = self._state.players[1]

        print(f"\n=== Turn {self._state.turn} - {self._state.phase.value} ===")
        print(
            f"Player: HP={player.health}, PO={player.po}, "
            f"Hand={len(player.hand)}, Board={len(player.board)}"
        )
        print(f"Opponent: HP={opponent.health}, Board={len(opponent.board)}")
        print(f"Market: {len(self._state.market_cards)} cards")
        print(f"Legal actions: {len(self._legal_actions)}")

    def close(self) -> None:
        """Clean up resources."""
        pass
