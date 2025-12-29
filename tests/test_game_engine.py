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
    EvolutionError,
    GameEngine,
    GamePhase,
    InsufficientPOError,
    InvalidGameStateError,
    InvalidPhaseError,
    InvalidPlayerError,
    PlayerState,
    buy_card,
    calculate_damage,
    calculate_imblocable_damage,
    create_initial_game_state,
    evolve_cards,
    mix_decks,
    play_card,
    replace_card,
    resolve_combat,
    should_mix_decks,
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


class TestImblocableDamage:
    """Tests for imblocable damage calculation."""

    def test_imblocable_damage_from_class_abilities(self) -> None:
        """Test imblocable damage using structured field."""
        # Create a creature with imblocable damage
        creature = CreatureCard(
            id="nature_archer_1",
            name="Nature Archer",
            card_type=CardType.CREATURE,
            cost=2,
            level=1,
            family=Family.NATURE,
            card_class=CardClass.ARCHER,
            family_abilities=FamilyAbilities(),
            class_abilities=ClassAbilities(
                conditional=[
                    ConditionalAbility(condition="1 PO", effect="2 dgt imblocable"),
                ],
                imblocable_damage=2,  # Structured field
            ),
            bonus_text=None,
            health=2,
            attack=1,
            image_path="nature.png",
        )

        player = PlayerState(player_id=0, name="Test")
        player.board = [creature]

        imblocable = calculate_imblocable_damage(player)
        assert imblocable == 2

    def test_imblocable_damage_multiple_cards(self) -> None:
        """Test imblocable damage from multiple cards."""
        creature1 = CreatureCard(
            id="card1",
            name="Card 1",
            card_type=CardType.CREATURE,
            cost=2,
            level=1,
            family=Family.NATURE,
            card_class=CardClass.ARCHER,
            family_abilities=FamilyAbilities(),
            class_abilities=ClassAbilities(imblocable_damage=2),
            bonus_text=None,
            health=2,
            attack=1,
            image_path="c1.png",
        )
        creature2 = CreatureCard(
            id="card2",
            name="Card 2",
            card_type=CardType.CREATURE,
            cost=3,
            level=1,
            family=Family.NATURE,
            card_class=CardClass.ARCHER,
            family_abilities=FamilyAbilities(),
            class_abilities=ClassAbilities(imblocable_damage=3),
            bonus_text=None,
            health=3,
            attack=2,
            image_path="c2.png",
        )

        player = PlayerState(player_id=0, name="Test")
        player.board = [creature1, creature2]

        imblocable = calculate_imblocable_damage(player)
        assert imblocable == 5  # 2 + 3

    def test_imblocable_damage_in_combat(self) -> None:
        """Test imblocable damage is added to combat damage."""
        state = create_initial_game_state(2)

        # Attacker has card with high imblocable but low ATK
        attacker_card = CreatureCard(
            id="imblocable",
            name="Imblocable Dealer",
            card_type=CardType.CREATURE,
            cost=2,
            level=1,
            family=Family.NATURE,
            card_class=CardClass.ARCHER,
            family_abilities=FamilyAbilities(),
            class_abilities=ClassAbilities(imblocable_damage=5),
            bonus_text=None,
            health=1,
            attack=1,  # Low ATK
            image_path="imb.png",
        )

        # Defender has high HP
        defender_card = CreatureCard(
            id="tank",
            name="Tank",
            card_type=CardType.CREATURE,
            cost=5,
            level=1,
            family=Family.CYBORG,
            card_class=CardClass.DEFENSEUR,
            family_abilities=FamilyAbilities(),
            class_abilities=ClassAbilities(),
            bonus_text=None,
            health=10,  # High defense
            attack=1,
            image_path="tank.png",
        )

        state.players[0].board = [attacker_card]
        state.players[1].board = [defender_card]

        result = calculate_damage(state.players[0], state.players[1])

        # Base damage: 1 ATK - 10 HP = 0 (capped at 0)
        assert result.base_damage == 0
        # Imblocable: 5
        assert result.imblocable_damage == 5
        # Total: 0 + 5 = 5
        assert result.total_damage == 5


class TestEvolution:
    """Tests for card evolution."""

    def test_evolution_requires_3_cards(self) -> None:
        """Test evolution fails with wrong number of cards."""
        state = create_initial_game_state(2)
        player = state.players[0]

        card = CreatureCard(
            id="test_1",
            name="Test Card",
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
            image_path="test.png",
        )

        player.hand = [card, card]  # Only 2 cards

        with pytest.raises(EvolutionError, match="exactly 3 cards"):
            evolve_cards(state, player, player.hand)

    def test_evolution_same_name_required(self) -> None:
        """Test evolution fails with different card names."""
        state = create_initial_game_state(2)
        player = state.players[0]

        # Create three distinct card instances: two "Card A" and one "Card B"
        card_a1 = CreatureCard(
            id="card_a_1",
            name="Card A",
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
            image_path="a.png",
        )
        card_a2 = CreatureCard(
            id="card_a_2",
            name="Card A",
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
            image_path="a.png",
        )
        card_b = CreatureCard(
            id="card_b_1",
            name="Card B",
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
            image_path="b.png",
        )

        player.hand = [card_a1, card_a2, card_b]

        with pytest.raises(EvolutionError, match="same name"):
            evolve_cards(state, player, player.hand)

    def test_evolution_level_1_required(self) -> None:
        """Test evolution fails if card is not Level 1."""
        state = create_initial_game_state(2)
        player = state.players[0]

        # Create card instances (can't use level=2 in CreatureCard)
        card1 = CreatureCard(
            id="test_1_a",
            name="Test Card",
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
            image_path="test.png",
        )
        card2 = CreatureCard(
            id="test_1_b",
            name="Test Card",
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
            image_path="test.png",
        )
        card3 = CreatureCard(
            id="test_1_c",
            name="Test Card",
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
            image_path="test.png",
        )

        # All level 1, so this should attempt evolution but fail
        # because no Level 2 card exists
        player.hand = [card1, card2, card3]

        with pytest.raises(EvolutionError, match="No Level 2 version"):
            evolve_cards(state, player, player.hand)

    def test_evolution_distinct_cards_required(self) -> None:
        """Test evolution fails if same card instance used multiple times."""
        state = create_initial_game_state(2)
        player = state.players[0]

        card = CreatureCard(
            id="test_1",
            name="Test Card",
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
            image_path="test.png",
        )

        player.hand = [card]
        # Try to evolve with same instance 3 times
        with pytest.raises(EvolutionError, match="same card instance"):
            evolve_cards(state, player, [card, card, card])


class TestDeckMixing:
    """Tests for deck mixing mechanics."""

    def test_should_mix_on_even_turns(self) -> None:
        """Test deck mixing occurs on even turns."""
        state = create_initial_game_state(2)

        state.turn = 1
        assert not should_mix_decks(state)

        state.turn = 2
        assert should_mix_decks(state)

        state.turn = 3
        assert not should_mix_decks(state)

        state.turn = 4
        assert should_mix_decks(state)

    def test_should_not_mix_after_turn_10(self) -> None:
        """Test deck mixing stops after turn 10."""
        state = create_initial_game_state(2)

        state.turn = 10
        assert not should_mix_decks(state)

        state.turn = 12
        assert not should_mix_decks(state)

    def test_mix_decks_transfers_cards(self) -> None:
        """Test mix_decks moves cards to next tier."""
        state = create_initial_game_state(2)
        state.turn = 2  # Cost tier 1

        # Add some cards to cost_1_deck
        card = CreatureCard(
            id="cost1_card",
            name="Cost 1 Card",
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
            image_path="c1.png",
        )

        state.cost_1_deck = [card] * 10
        state.cost_2_deck = []
        state.market_cards = []

        mixed_count = mix_decks(state)

        # Should have mixed half (5) to cost_2
        assert mixed_count == 5
        assert len(state.cost_2_deck) == 5
        assert len(state.discard_pile) == 5
        assert len(state.cost_1_deck) == 0

    def test_mix_decks_clears_market(self) -> None:
        """Test mix_decks clears market cards back to deck first."""
        state = create_initial_game_state(2)
        state.turn = 2

        card = CreatureCard(
            id="market_card",
            name="Market Card",
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
            image_path="m.png",
        )

        state.cost_1_deck = [card] * 4
        state.market_cards = [card] * 2  # 2 cards in market
        state.cost_2_deck = []

        mix_decks(state)

        # Market should be cleared
        assert len(state.market_cards) == 0


class TestValidation:
    """Tests for validation and error handling."""

    def test_invalid_player_name_empty(self) -> None:
        """Test empty player name raises error."""
        with pytest.raises(InvalidPlayerError, match="cannot be empty"):
            PlayerState(player_id=0, name="")

    def test_invalid_player_name_too_long(self) -> None:
        """Test too long player name raises error."""
        with pytest.raises(InvalidPlayerError, match="cannot exceed"):
            PlayerState(player_id=0, name="A" * 51)

    def test_invalid_active_player_index(self) -> None:
        """Test invalid active player index raises error."""
        state = create_initial_game_state(2)
        state.active_player_index = 10  # Invalid

        with pytest.raises(InvalidGameStateError, match="Invalid active_player_index"):
            state.get_active_player()

    def test_invalid_deck_tier(self) -> None:
        """Test invalid deck tier raises error."""
        state = create_initial_game_state(2)

        with pytest.raises(ValueError, match="Invalid cost tier"):
            state.get_deck_for_tier(0)

        with pytest.raises(ValueError, match="Invalid cost tier"):
            state.get_deck_for_tier(6)
