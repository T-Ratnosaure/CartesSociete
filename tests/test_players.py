"""Tests for player agents module.

This module tests the AI player implementations including RandomPlayer,
GreedyPlayer, HeuristicPlayer, and MCTSPlayer.
"""

import pytest

from src.cards.models import (
    CardClass,
    CardType,
    ClassAbilities,
    CreatureCard,
    Family,
    FamilyAbilities,
)
from src.game import GamePhase, create_initial_game_state
from src.game.executor import get_legal_actions_for_player
from src.players import (
    Action,
    ActionType,
    GreedyPlayer,
    HeuristicPlayer,
    MCTSPlayer,
    RandomPlayer,
    calculate_base_value,
    calculate_evolution_potential,
    calculate_family_synergy,
    calculate_imblocable_bonus,
    evaluate_card_for_purchase,
)


@pytest.fixture
def sample_creature() -> CreatureCard:
    """Create a sample creature for testing."""
    return CreatureCard(
        id="test_1",
        name="Test Creature",
        card_type=CardType.CREATURE,
        cost=2,
        level=1,
        family=Family.CYBORG,
        card_class=CardClass.BERSEKER,
        family_abilities=FamilyAbilities(),
        class_abilities=ClassAbilities(),
        bonus_text=None,
        health=3,
        attack=2,
        image_path="test.png",
    )


@pytest.fixture
def high_value_creature() -> CreatureCard:
    """Create a high-value creature for testing."""
    return CreatureCard(
        id="high_1",
        name="High Value",
        card_type=CardType.CREATURE,
        cost=3,
        level=1,
        family=Family.NATURE,
        card_class=CardClass.ARCHER,
        family_abilities=FamilyAbilities(),
        class_abilities=ClassAbilities(imblocable_damage=2),
        bonus_text=None,
        health=4,
        attack=5,
        image_path="high.png",
    )


class TestAction:
    """Tests for Action dataclass."""

    def test_buy_action(self, sample_creature: CreatureCard) -> None:
        """Test creating a buy action."""
        action = Action.buy(sample_creature)
        assert action.action_type == ActionType.BUY_CARD
        assert action.card == sample_creature
        assert action.target_card is None
        assert action.evolve_cards is None

    def test_play_action(self, sample_creature: CreatureCard) -> None:
        """Test creating a play action."""
        action = Action.play(sample_creature)
        assert action.action_type == ActionType.PLAY_CARD
        assert action.card == sample_creature

    def test_replace_action(
        self, sample_creature: CreatureCard, high_value_creature: CreatureCard
    ) -> None:
        """Test creating a replace action."""
        action = Action.replace(high_value_creature, sample_creature)
        assert action.action_type == ActionType.REPLACE_CARD
        assert action.card == high_value_creature
        assert action.target_card == sample_creature

    def test_evolve_action(self, sample_creature: CreatureCard) -> None:
        """Test creating an evolve action."""
        cards = [sample_creature, sample_creature, sample_creature]
        action = Action.evolve(cards)
        assert action.action_type == ActionType.EVOLVE
        assert len(action.evolve_cards) == 3

    def test_end_phase_action(self) -> None:
        """Test creating an end phase action."""
        action = Action.end_phase()
        assert action.action_type == ActionType.END_PHASE
        assert action.card is None

    def test_action_repr(self, sample_creature: CreatureCard) -> None:
        """Test action string representation."""
        buy = Action.buy(sample_creature)
        assert "BUY" in repr(buy)
        assert sample_creature.name in repr(buy)

        end = Action.end_phase()
        assert "END_PHASE" in repr(end)


class TestEvaluation:
    """Tests for card evaluation functions."""

    def test_base_value(self, sample_creature: CreatureCard) -> None:
        """Base value is ATK + HP."""
        value = calculate_base_value(sample_creature)
        assert value == 5.0  # 2 ATK + 3 HP

    def test_family_synergy_empty_board(self, sample_creature: CreatureCard) -> None:
        """No synergy with empty board."""
        state = create_initial_game_state(2)
        player = state.players[0]
        player.board = []

        synergy = calculate_family_synergy(sample_creature, player)
        assert synergy == 0.0

    def test_family_synergy_with_match(self, sample_creature: CreatureCard) -> None:
        """Synergy bonus when board has matching family."""
        state = create_initial_game_state(2)
        player = state.players[0]

        # Add a Cyborg to board
        board_card = CreatureCard(
            id="board_1",
            name="Board Card",
            card_type=CardType.CREATURE,
            cost=1,
            level=1,
            family=Family.CYBORG,
            card_class=CardClass.DEFENSEUR,
            family_abilities=FamilyAbilities(),
            class_abilities=ClassAbilities(),
            bonus_text=None,
            health=2,
            attack=1,
            image_path="board.png",
        )
        player.board = [board_card]

        synergy = calculate_family_synergy(sample_creature, player)
        assert synergy > 0

    def test_evolution_potential_no_copies(self, sample_creature: CreatureCard) -> None:
        """No evolution potential without copies."""
        state = create_initial_game_state(2)
        player = state.players[0]
        player.hand = []
        player.board = []

        potential = calculate_evolution_potential(sample_creature, player)
        assert potential == 0.0

    def test_evolution_potential_two_copies(
        self, sample_creature: CreatureCard
    ) -> None:
        """High evolution potential with 2 copies."""
        state = create_initial_game_state(2)
        player = state.players[0]

        # Add 2 copies of the same card
        copy1 = CreatureCard(
            id="copy_1",
            name="Test Creature",
            card_type=CardType.CREATURE,
            cost=2,
            level=1,
            family=Family.CYBORG,
            card_class=CardClass.BERSEKER,
            family_abilities=FamilyAbilities(),
            class_abilities=ClassAbilities(),
            bonus_text=None,
            health=3,
            attack=2,
            image_path="test.png",
        )
        copy2 = CreatureCard(
            id="copy_2",
            name="Test Creature",
            card_type=CardType.CREATURE,
            cost=2,
            level=1,
            family=Family.CYBORG,
            card_class=CardClass.BERSEKER,
            family_abilities=FamilyAbilities(),
            class_abilities=ClassAbilities(),
            bonus_text=None,
            health=3,
            attack=2,
            image_path="test.png",
        )
        player.hand = [copy1, copy2]

        potential = calculate_evolution_potential(sample_creature, player)
        assert potential >= 3.0  # High bonus when 2 copies exist

    def test_imblocable_bonus(self, high_value_creature: CreatureCard) -> None:
        """Imblocable damage has significant bonus."""
        bonus = calculate_imblocable_bonus(high_value_creature)
        assert bonus == 5.0  # 2 * 2.5

    def test_evaluate_card_for_purchase(self, sample_creature: CreatureCard) -> None:
        """Comprehensive evaluation combines all factors."""
        state = create_initial_game_state(2)
        player = state.players[0]

        score = evaluate_card_for_purchase(sample_creature, player, state)
        assert score > 0
        assert isinstance(score, float)


class TestRandomPlayer:
    """Tests for RandomPlayer."""

    def test_create_random_player(self) -> None:
        """Test creating a random player."""
        player = RandomPlayer(player_id=0)
        assert player.player_id == 0
        assert player.info.agent_type == "random"

    def test_random_player_with_name(self) -> None:
        """Test random player with custom name."""
        player = RandomPlayer(player_id=1, name="TestBot")
        assert player.name == "TestBot"

    def test_random_player_always_returns_legal_action(self) -> None:
        """Random player always returns a legal action."""
        player = RandomPlayer(player_id=0, seed=42)
        state = create_initial_game_state(2)
        player_state = state.players[0]

        # Create some legal actions
        legal_actions = [Action.end_phase()]
        action = player.choose_market_action(state, player_state, legal_actions)

        assert action in legal_actions

    def test_random_player_reproducible_with_seed(self) -> None:
        """Same seed produces same choices."""
        state = create_initial_game_state(2)
        player_state = state.players[0]

        # Create multiple actions to choose from
        actions = [Action.end_phase(), Action.end_phase()]  # Identical for simplicity

        p1 = RandomPlayer(player_id=0, seed=12345)
        p2 = RandomPlayer(player_id=0, seed=12345)

        # With same seed and same actions, should make same choice
        choice1 = p1.choose_market_action(state, player_state, actions)
        choice2 = p2.choose_market_action(state, player_state, actions)

        assert choice1.action_type == choice2.action_type


class TestGreedyPlayer:
    """Tests for GreedyPlayer."""

    def test_create_greedy_player(self) -> None:
        """Test creating a greedy player."""
        player = GreedyPlayer(player_id=0)
        assert player.info.agent_type == "greedy"

    def test_greedy_ends_phase_when_no_buys(self) -> None:
        """Ends phase when no buy actions available."""
        player = GreedyPlayer(player_id=0)
        state = create_initial_game_state(2)
        player_state = state.players[0]
        player_state.po = 0  # No money

        legal_actions = [Action.end_phase()]
        action = player.choose_market_action(state, player_state, legal_actions)

        assert action.action_type == ActionType.END_PHASE

    def test_greedy_buys_high_value_card(
        self, sample_creature: CreatureCard, high_value_creature: CreatureCard
    ) -> None:
        """Greedy player buys highest value card."""
        player = GreedyPlayer(player_id=0)
        state = create_initial_game_state(2)
        player_state = state.players[0]
        player_state.po = 10

        # Offer both cards
        legal_actions = [
            Action.buy(sample_creature),
            Action.buy(high_value_creature),
            Action.end_phase(),
        ]

        action = player.choose_market_action(state, player_state, legal_actions)

        # Should buy high value creature (more ATK + HP + imblocable)
        assert action.action_type == ActionType.BUY_CARD
        assert action.card == high_value_creature


class TestHeuristicPlayer:
    """Tests for HeuristicPlayer."""

    def test_create_heuristic_player(self) -> None:
        """Test creating a heuristic player."""
        player = HeuristicPlayer(player_id=0)
        assert player.info.agent_type == "heuristic"

    def test_custom_weights(self) -> None:
        """Test custom weight configuration."""
        player = HeuristicPlayer(
            player_id=0,
            evolution_weight=5.0,
            synergy_weight=0.5,
            aggression=2.0,
        )
        assert player.evolution_weight == 5.0
        assert player.synergy_weight == 0.5
        assert player.aggression == 2.0

    def test_on_game_start_clears_state(self) -> None:
        """on_game_start resets tracking state."""
        player = HeuristicPlayer(player_id=0)
        player._evolution_targets.add("test")

        state = create_initial_game_state(2)
        player.on_game_start(state)

        assert len(player._evolution_targets) == 0

    def test_evolve_prioritized(self) -> None:
        """Heuristic player prioritizes evolution actions."""
        player = HeuristicPlayer(player_id=0)
        state = create_initial_game_state(2)
        state.phase = GamePhase.PLAY
        player_state = state.players[0]

        # Create 3 identical cards for evolution
        cards = []
        for i in range(3):
            card = CreatureCard(
                id=f"evo_{i}",
                name="Evolvable",
                card_type=CardType.CREATURE,
                cost=1,
                level=1,
                family=Family.CYBORG,
                card_class=CardClass.BERSEKER,
                family_abilities=FamilyAbilities(),
                class_abilities=ClassAbilities(),
                bonus_text=None,
                health=2,
                attack=2,
                image_path="evo.png",
            )
            cards.append(card)

        # Offer evolve and play actions
        legal_actions = [
            Action.evolve(cards),
            Action.play(cards[0]),
            Action.end_phase(),
        ]

        action = player.choose_play_action(state, player_state, legal_actions)

        # Should choose evolve
        assert action.action_type == ActionType.EVOLVE


class TestMCTSPlayer:
    """Tests for MCTSPlayer."""

    def test_create_mcts_player(self) -> None:
        """Test creating an MCTS player."""
        player = MCTSPlayer(player_id=0)
        assert player.info.agent_type == "mcts"
        assert player.info.version == "1.0.0"

    def test_full_mcts_mode_default(self) -> None:
        """MCTS defaults to full implementation (not stub)."""
        player = MCTSPlayer(player_id=0)
        assert player.config.use_stub is False

    def test_stub_mode_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Stub mode logs a warning when explicitly enabled."""
        import logging

        from src.players.mcts_player import MCTSConfig

        with caplog.at_level(logging.WARNING):
            MCTSPlayer(player_id=0, config=MCTSConfig(use_stub=True))

        assert "STUB mode" in caplog.text

    def test_mcts_chooses_valid_action(self) -> None:
        """MCTS chooses a valid action from legal actions."""
        from src.players.mcts_player import MCTSConfig

        # Use low sim count for speed
        config = MCTSConfig(num_simulations=5, max_rollout_depth=3)
        player = MCTSPlayer(player_id=0, config=config, seed=42)
        state = create_initial_game_state(2)
        player_state = state.players[0]

        legal_actions = [Action.end_phase()]
        action = player.choose_market_action(state, player_state, legal_actions)

        assert action in legal_actions


class TestExecutor:
    """Tests for action executor."""

    def test_get_legal_actions_market_phase(self) -> None:
        """Get legal actions in market phase."""
        state = create_initial_game_state(2)
        state.phase = GamePhase.MARKET
        player = state.players[0]
        player.po = 5

        # Add a card to market
        card = CreatureCard(
            id="market_1",
            name="Market Card",
            card_type=CardType.CREATURE,
            cost=2,
            level=1,
            family=Family.CYBORG,
            card_class=CardClass.DEFENSEUR,
            family_abilities=FamilyAbilities(),
            class_abilities=ClassAbilities(),
            bonus_text=None,
            health=2,
            attack=2,
            image_path="market.png",
        )
        state.market_cards = [card]

        actions = get_legal_actions_for_player(state, player)

        # Should have buy action and end phase
        action_types = [a.action_type for a in actions]
        assert ActionType.BUY_CARD in action_types
        assert ActionType.END_PHASE in action_types

    def test_get_legal_actions_play_phase(self) -> None:
        """Get legal actions in play phase."""
        state = create_initial_game_state(2)
        state.phase = GamePhase.PLAY
        player = state.players[0]

        # Add a card to hand
        card = CreatureCard(
            id="hand_1",
            name="Hand Card",
            card_type=CardType.CREATURE,
            cost=2,
            level=1,
            family=Family.CYBORG,
            card_class=CardClass.DEFENSEUR,
            family_abilities=FamilyAbilities(),
            class_abilities=ClassAbilities(),
            bonus_text=None,
            health=2,
            attack=2,
            image_path="hand.png",
        )
        player.hand = [card]
        player.board = []

        actions = get_legal_actions_for_player(state, player)

        # Should have play action and end phase
        action_types = [a.action_type for a in actions]
        assert ActionType.PLAY_CARD in action_types
        assert ActionType.END_PHASE in action_types
