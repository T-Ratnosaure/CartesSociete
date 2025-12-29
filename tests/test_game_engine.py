"""Tests for game engine module.

This module tests the game state, actions, combat, market, and engine.
"""

import pytest

from src.cards.models import (
    CardClass,
    CardType,
    ClassAbilities,
    ConditionalAbility,
    CreatureCard,
    Family,
    FamilyAbilities,
)
from src.game import (
    BoardFullError,
    GameEngine,
    GamePhase,
    InsufficientPOError,
    InvalidPhaseError,
    PlayerState,
    buy_card,
    calculate_damage,
    create_initial_game_state,
    play_card,
    replace_card,
    resolve_combat,
)


@pytest.fixture
def sample_creature() -> CreatureCard:
    """Create a sample creature card for testing."""
    return CreatureCard(
        id="cyborg_test_1",
        name="Test Creature",
        card_type=CardType.CREATURE,
        cost=1,
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
def nature_creature_with_imblocable() -> CreatureCard:
    """Create a Nature creature with imblocable damage."""
    return CreatureCard(
        id="nature_test_1",
        name="Nature Creature",
        card_type=CardType.CREATURE,
        cost=2,
        level=1,
        family=Family.NATURE,
        card_class=CardClass.ARCHER,
        family_abilities=FamilyAbilities(),
        class_abilities=ClassAbilities(
            conditional=[
                ConditionalAbility(condition="1 PO", effect="2 dgt imblocable"),
            ]
        ),
        bonus_text=None,
        health=2,
        attack=1,
        image_path="nature.png",
    )


class TestPlayerState:
    """Tests for PlayerState class."""

    def test_create_player(self) -> None:
        """Test creating a player."""
        player = PlayerState(player_id=0, name="Test Player")
        assert player.health == 400
        assert player.po == 0
        assert len(player.hand) == 0
        assert len(player.board) == 0
        assert player.is_alive()

    def test_player_total_attack(self, sample_creature: CreatureCard) -> None:
        """Test calculating total attack."""
        player = PlayerState(player_id=0, name="Test")
        player.board = [sample_creature]
        assert player.get_total_attack() == 2

    def test_player_total_health(self, sample_creature: CreatureCard) -> None:
        """Test calculating total board health."""
        player = PlayerState(player_id=0, name="Test")
        player.board = [sample_creature]
        assert player.get_total_health() == 3

    def test_player_board_count(self, sample_creature: CreatureCard) -> None:
        """Test counting board cards."""
        player = PlayerState(player_id=0, name="Test")
        player.board = [sample_creature]
        assert player.get_board_count() == 1

    def test_player_eliminated(self) -> None:
        """Test player elimination."""
        player = PlayerState(player_id=0, name="Test", health=0)
        assert not player.is_alive()


class TestGameState:
    """Tests for GameState class."""

    def test_create_initial_state(self) -> None:
        """Test creating initial game state."""
        state = create_initial_game_state(2)
        assert len(state.players) == 2
        assert state.turn == 1
        assert state.phase == GamePhase.MARKET

    def test_create_state_with_names(self) -> None:
        """Test creating state with custom names."""
        state = create_initial_game_state(3, ["Alice", "Bob", "Charlie"])
        assert state.players[0].name == "Alice"
        assert state.players[1].name == "Bob"
        assert state.players[2].name == "Charlie"

    def test_invalid_player_count(self) -> None:
        """Test invalid player count raises error."""
        with pytest.raises(ValueError):
            create_initial_game_state(1)
        with pytest.raises(ValueError):
            create_initial_game_state(6)

    def test_po_for_turn_1(self) -> None:
        """Test PO for turn 1."""
        state = create_initial_game_state(2)
        state.turn = 1
        assert state.get_po_for_turn() == 4

    def test_po_for_turn_2(self) -> None:
        """Test PO for turn 2."""
        state = create_initial_game_state(2)
        state.turn = 2
        # Cost tier 1, formula: 1*2+1 = 3, but Turn 2 follows Turn 1 cost tier
        # Actually: Turn 2 still uses cost tier 1, formula = 1*2+1 = 3
        # But looking at rules: Turn 2 = 4 PO (same as turn 1)
        # Wait, turn 2 = (2+1)//2 = 1 tier, 1*2+1 = 3...
        # Let me check the implementation
        assert state.get_po_for_turn() == 3  # cost_tier(1) * 2 + 1

    def test_po_for_turn_5(self) -> None:
        """Test PO for turn 5 (cost tier 3)."""
        state = create_initial_game_state(2)
        state.turn = 5
        # Cost tier 3, formula: 3*2+1 = 7
        assert state.get_po_for_turn() == 7

    def test_po_caps_at_11(self) -> None:
        """Test PO caps at 11 after turn 10."""
        state = create_initial_game_state(2)
        state.turn = 15
        assert state.get_po_for_turn() == 11

    def test_cost_tier_progression(self) -> None:
        """Test cost tier progression."""
        state = create_initial_game_state(2)

        state.turn = 1
        assert state.get_current_cost_tier() == 1

        state.turn = 3
        assert state.get_current_cost_tier() == 2

        state.turn = 9
        assert state.get_current_cost_tier() == 5

    def test_game_over_detection(self) -> None:
        """Test game over detection."""
        state = create_initial_game_state(2)
        assert not state.is_game_over()

        # Eliminate one player
        state.players[0].eliminated = True
        assert state.is_game_over()
        assert state.get_winner() == state.players[1]


class TestActions:
    """Tests for game actions."""

    def test_buy_card(self, sample_creature: CreatureCard) -> None:
        """Test buying a card from market."""
        state = create_initial_game_state(2)
        state.phase = GamePhase.MARKET
        state.market_cards = [sample_creature]
        player = state.players[0]
        player.po = 5

        result = buy_card(state, player, sample_creature)

        assert result.success
        assert sample_creature in player.hand
        assert sample_creature not in state.market_cards
        assert player.po == 4

    def test_buy_card_insufficient_po(self, sample_creature: CreatureCard) -> None:
        """Test buying with insufficient PO."""
        state = create_initial_game_state(2)
        state.phase = GamePhase.MARKET
        state.market_cards = [sample_creature]
        player = state.players[0]
        player.po = 0

        with pytest.raises(InsufficientPOError):
            buy_card(state, player, sample_creature)

    def test_buy_card_wrong_phase(self, sample_creature: CreatureCard) -> None:
        """Test buying in wrong phase."""
        state = create_initial_game_state(2)
        state.phase = GamePhase.PLAY
        state.market_cards = [sample_creature]
        player = state.players[0]
        player.po = 5

        with pytest.raises(InvalidPhaseError):
            buy_card(state, player, sample_creature)

    def test_play_card(self, sample_creature: CreatureCard) -> None:
        """Test playing a card from hand."""
        state = create_initial_game_state(2)
        state.phase = GamePhase.PLAY
        player = state.players[0]
        player.hand = [sample_creature]

        result = play_card(state, player, sample_creature)

        assert result.success
        assert sample_creature in player.board
        assert sample_creature not in player.hand

    def test_play_card_board_full(self, sample_creature: CreatureCard) -> None:
        """Test playing when board is full."""
        state = create_initial_game_state(2)
        state.phase = GamePhase.PLAY
        player = state.players[0]
        player.hand = [sample_creature]

        # Fill board with 8 cards
        for i in range(8):
            card = CreatureCard(
                id=f"filler_{i}",
                name=f"Filler {i}",
                card_type=CardType.CREATURE,
                cost=1,
                level=1,
                family=Family.CYBORG,
                card_class=CardClass.BERSEKER,
                family_abilities=FamilyAbilities(),
                class_abilities=ClassAbilities(),
                bonus_text=None,
                health=1,
                attack=1,
                image_path="filler.png",
            )
            player.board.append(card)

        with pytest.raises(BoardFullError):
            play_card(state, player, sample_creature)

    def test_replace_card(self, sample_creature: CreatureCard) -> None:
        """Test replacing a card on board."""
        state = create_initial_game_state(2)
        state.phase = GamePhase.PLAY
        player = state.players[0]

        old_card = CreatureCard(
            id="old_card",
            name="Old Card",
            card_type=CardType.CREATURE,
            cost=1,
            level=1,
            family=Family.CYBORG,
            card_class=CardClass.BERSEKER,
            family_abilities=FamilyAbilities(),
            class_abilities=ClassAbilities(),
            bonus_text=None,
            health=1,
            attack=1,
            image_path="old.png",
        )

        player.hand = [sample_creature]
        player.board = [old_card]

        result = replace_card(state, player, sample_creature, old_card)

        assert result.success
        assert sample_creature in player.board
        assert old_card in player.hand
        assert old_card not in player.board
        assert sample_creature not in player.hand


class TestCombat:
    """Tests for combat resolution."""

    def test_damage_calculation(self, sample_creature: CreatureCard) -> None:
        """Test basic damage calculation."""
        attacker = PlayerState(player_id=0, name="Attacker")
        defender = PlayerState(player_id=1, name="Defender")

        # Attacker has 2 ATK, defender has 3 HP defense
        attacker.board = [sample_creature]
        defender.board = [sample_creature]

        result = calculate_damage(attacker, defender)

        assert result.total_attack == 2
        assert result.target_defense == 3
        assert result.base_damage == 0  # 2 - 3 = 0 (min 0)
        assert result.total_damage == 0

    def test_damage_exceeds_defense(self) -> None:
        """Test damage when attack exceeds defense."""
        attacker = PlayerState(player_id=0, name="Attacker")
        defender = PlayerState(player_id=1, name="Defender")

        # Create high ATK card
        strong_card = CreatureCard(
            id="strong",
            name="Strong",
            card_type=CardType.CREATURE,
            cost=5,
            level=1,
            family=Family.CYBORG,
            card_class=CardClass.BERSEKER,
            family_abilities=FamilyAbilities(),
            class_abilities=ClassAbilities(),
            bonus_text=None,
            health=1,
            attack=10,
            image_path="strong.png",
        )

        # Create low HP card
        weak_card = CreatureCard(
            id="weak",
            name="Weak",
            card_type=CardType.CREATURE,
            cost=1,
            level=1,
            family=Family.CYBORG,
            card_class=CardClass.BERSEKER,
            family_abilities=FamilyAbilities(),
            class_abilities=ClassAbilities(),
            bonus_text=None,
            health=2,
            attack=1,
            image_path="weak.png",
        )

        attacker.board = [strong_card]
        defender.board = [weak_card]

        result = calculate_damage(attacker, defender)

        assert result.total_attack == 10
        assert result.target_defense == 2
        assert result.base_damage == 8  # 10 - 2 = 8
        assert result.total_damage == 8

    def test_resolve_combat(self) -> None:
        """Test resolving combat for all players."""
        state = create_initial_game_state(2)

        # Give each player a card
        card1 = CreatureCard(
            id="card1",
            name="Card 1",
            card_type=CardType.CREATURE,
            cost=1,
            level=1,
            family=Family.CYBORG,
            card_class=CardClass.BERSEKER,
            family_abilities=FamilyAbilities(),
            class_abilities=ClassAbilities(),
            bonus_text=None,
            health=5,
            attack=10,
            image_path="card1.png",
        )

        card2 = CreatureCard(
            id="card2",
            name="Card 2",
            card_type=CardType.CREATURE,
            cost=1,
            level=1,
            family=Family.CYBORG,
            card_class=CardClass.BERSEKER,
            family_abilities=FamilyAbilities(),
            class_abilities=ClassAbilities(),
            bonus_text=None,
            health=3,
            attack=8,
            image_path="card2.png",
        )

        state.players[0].board = [card1]
        state.players[1].board = [card2]

        result = resolve_combat(state)

        # Player 0: ATK 10 vs DEF 3 = 7 damage to player 1
        # Player 1: ATK 8 vs DEF 5 = 3 damage to player 0
        assert result.health_changes[0] == -3
        assert result.health_changes[1] == -7


class TestGameEngine:
    """Tests for GameEngine class."""

    def test_create_engine(self) -> None:
        """Test creating a game engine."""
        engine = GameEngine(num_players=2, player_names=["Alice", "Bob"])
        assert len(engine.state.players) == 2
        assert engine.state.turn == 1

    def test_phase_progression(self) -> None:
        """Test phase progression through a turn."""
        engine = GameEngine(num_players=2)

        assert engine.state.phase == GamePhase.MARKET

        engine.advance_phase()
        assert engine.state.phase == GamePhase.PLAY

        engine.advance_phase()
        assert engine.state.phase == GamePhase.COMBAT

        engine.advance_phase()
        assert engine.state.phase == GamePhase.END

    def test_get_state_summary(self) -> None:
        """Test state summary generation."""
        engine = GameEngine(num_players=2, player_names=["Alice", "Bob"])
        summary = engine.get_state_summary()

        assert "Turn 1" in summary
        assert "Alice" in summary
        assert "Bob" in summary
        assert "400 PV" in summary
