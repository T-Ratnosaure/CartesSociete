"""Integration tests for weapon, spell, sacrifice, and deck systems.

These tests verify the end-to-end flow of the new game systems
implemented in Phases 3-5 of the bonus_text effects plan.
"""

import pytest

from src.cards.models import CardType, Family
from src.cards.repository import CardRepository
from src.game.combat import calculate_damage, resolve_combat
from src.game.state import (
    GameState,
    create_initial_game_state,
)

# === Fixtures ===


@pytest.fixture
def repo() -> CardRepository:
    """Create a card repository with all cards loaded."""
    return CardRepository()


@pytest.fixture
def two_player_state() -> GameState:
    """Create a game state with two players."""
    return create_initial_game_state(
        num_players=2,
        player_names=["Player 1", "Player 2"],
    )


# === Integration Tests: Weapon Equipment in Combat ===


class TestWeaponEquipmentCombatIntegration:
    """Test weapon equipment affects combat calculations."""

    def test_weapon_attack_bonus_in_combat(
        self, two_player_state: GameState, repo: CardRepository
    ) -> None:
        """Verify equipped weapons add attack in combat."""
        p1 = two_player_state.players[0]
        p2 = two_player_state.players[1]

        # Get a real creature card for player 1
        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        if not creatures:
            pytest.skip("No creature cards in repository")
        creature = creatures[0]

        # Get a weapon card
        weapons = repo.get_by_type(CardType.WEAPON)
        if not weapons:
            pytest.skip("No weapon cards in repository")
        weapon = weapons[0]

        p1.board.append(creature)
        p2.board.append(creatures[1] if len(creatures) > 1 else creature)

        # Calculate damage without weapon
        breakdown_no_weapon = calculate_damage(p1, p2)
        base_weapon_attack = breakdown_no_weapon.weapon_attack

        # Equip weapon to player 1's card
        p1.equip_weapon(creature.id, weapon)

        # Calculate damage with weapon
        breakdown_with_weapon = calculate_damage(p1, p2)

        # Weapon should add to attack
        assert breakdown_with_weapon.weapon_attack == base_weapon_attack + weapon.attack

    def test_weapon_defense_bonus_in_combat(
        self, two_player_state: GameState, repo: CardRepository
    ) -> None:
        """Verify equipped weapons add defense in combat."""
        p1 = two_player_state.players[0]
        p2 = two_player_state.players[1]

        # Get creature cards
        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        if len(creatures) < 2:
            pytest.skip("Not enough creature cards in repository")

        # Get a weapon with health
        weapons = [w for w in repo.get_by_type(CardType.WEAPON) if w.health > 0]
        if not weapons:
            pytest.skip("No weapon cards with HP in repository")
        weapon = weapons[0]

        p1.board.append(creatures[0])
        p2.board.append(creatures[1])

        # Calculate damage without weapon on defender
        breakdown_no_weapon = calculate_damage(p1, p2)
        base_weapon_defense = breakdown_no_weapon.weapon_defense

        # Equip weapon to player 2's card (defender)
        p2.equip_weapon(creatures[1].id, weapon)

        # Calculate damage with weapon on defender
        breakdown_with_weapon = calculate_damage(p1, p2)

        # Weapon should add to defense
        expected_defense = base_weapon_defense + weapon.health
        assert breakdown_with_weapon.weapon_defense == expected_defense

    def test_multiple_weapons_stack(
        self, two_player_state: GameState, repo: CardRepository
    ) -> None:
        """Verify multiple equipped weapons stack their bonuses."""
        p1 = two_player_state.players[0]
        p2 = two_player_state.players[1]

        # Get creature cards
        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        if len(creatures) < 3:
            pytest.skip("Not enough creature cards in repository")

        # Get weapon cards
        weapons = repo.get_by_type(CardType.WEAPON)
        if len(weapons) < 2:
            pytest.skip("Not enough weapon cards in repository")

        p1.board.extend([creatures[0], creatures[1]])
        p2.board.append(creatures[2])

        # Equip both weapons to different cards
        p1.equip_weapon(creatures[0].id, weapons[0])
        p1.equip_weapon(creatures[1].id, weapons[1])

        # Calculate total weapon attack
        total_weapon_atk = p1.get_total_weapon_attack()
        expected = weapons[0].attack + weapons[1].attack

        assert total_weapon_atk == expected

    def test_weapon_removed_on_card_sacrifice(
        self, two_player_state: GameState, repo: CardRepository
    ) -> None:
        """Verify weapon is removed when card is sacrificed."""
        p1 = two_player_state.players[0]

        # Get a creature and weapon
        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        weapons = repo.get_by_type(CardType.WEAPON)
        if not creatures or not weapons:
            pytest.skip("Need creature and weapon cards")

        creature = creatures[0]
        weapon = weapons[0]

        p1.board.append(creature)
        p1.equip_weapon(creature.id, weapon)

        assert p1.get_total_weapon_attack() == weapon.attack

        # Sacrifice the card
        p1.sacrifice_card(creature)

        # Weapon should be removed
        assert p1.get_total_weapon_attack() == 0
        assert creature.id not in p1.equipped_weapons


# === Integration Tests: Spell Tracking in Game Flow ===


class TestSpellTrackingIntegration:
    """Test spell tracking persists correctly through game phases."""

    def test_spell_tracking_accumulates_in_turn(
        self, two_player_state: GameState
    ) -> None:
        """Verify spell tracking accumulates correctly in a turn."""
        p1 = two_player_state.players[0]

        # Cast multiple spells
        p1.cast_spell(damage=5)
        p1.cast_spell(damage=3)
        p1.cast_spell(damage=2)

        assert p1.spells_cast_this_turn == 3
        assert p1.spell_damage_dealt == 10

    def test_spell_tracking_resets_on_new_turn(
        self, two_player_state: GameState
    ) -> None:
        """Verify spell tracking resets correctly between turns."""
        p1 = two_player_state.players[0]

        # Cast spells
        p1.cast_spell(damage=5)
        p1.cast_spell(damage=3)
        assert p1.spells_cast_this_turn == 2
        assert p1.spell_damage_dealt == 8

        # Reset for new turn
        p1.reset_turn_tracking()

        assert p1.spells_cast_this_turn == 0
        assert p1.spell_damage_dealt == 0

    def test_spell_tracking_independent_per_player(
        self, two_player_state: GameState
    ) -> None:
        """Verify spell tracking is independent per player."""
        p1 = two_player_state.players[0]
        p2 = two_player_state.players[1]

        p1.cast_spell(damage=5)
        p2.cast_spell(damage=10)
        p2.cast_spell(damage=10)

        assert p1.spells_cast_this_turn == 1
        assert p1.spell_damage_dealt == 5
        assert p2.spells_cast_this_turn == 2
        assert p2.spell_damage_dealt == 20

    def test_reset_turn_tracking_all_players(self, two_player_state: GameState) -> None:
        """Verify GameState.reset_turn_tracking_all_players() works."""
        p1 = two_player_state.players[0]
        p2 = two_player_state.players[1]

        p1.cast_spell(damage=5)
        p2.cast_spell(damage=10)

        two_player_state.reset_turn_tracking_all_players()

        assert p1.spells_cast_this_turn == 0
        assert p2.spells_cast_this_turn == 0


# === Integration Tests: Sacrifice Mechanics ===


class TestSacrificeMechanicsIntegration:
    """Test sacrifice mechanics in game context."""

    def test_sacrifice_removes_card_from_board(
        self, two_player_state: GameState, repo: CardRepository
    ) -> None:
        """Verify sacrifice removes card from board."""
        p1 = two_player_state.players[0]

        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        if not creatures:
            pytest.skip("No creature cards")

        creature = creatures[0]
        p1.board.append(creature)

        assert len(p1.board) == 1

        result = p1.sacrifice_card(creature)

        assert result is True
        assert len(p1.board) == 0
        assert creature in p1.sacrificed_this_turn

    def test_sacrifice_count_tracked(
        self, two_player_state: GameState, repo: CardRepository
    ) -> None:
        """Verify sacrifice count is tracked correctly."""
        p1 = two_player_state.players[0]

        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        if len(creatures) < 3:
            pytest.skip("Need at least 3 creature cards")

        p1.board.extend(creatures[:3])

        # Sacrifice two cards
        p1.sacrifice_card(creatures[0])
        p1.sacrifice_card(creatures[1])

        assert p1.get_sacrifice_count() == 2
        assert len(p1.board) == 1

    def test_sacrifice_with_weapon_removes_both(
        self, two_player_state: GameState, repo: CardRepository
    ) -> None:
        """Verify sacrificing a card with weapon removes both."""
        p1 = two_player_state.players[0]

        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        weapons = repo.get_by_type(CardType.WEAPON)
        if not creatures or not weapons:
            pytest.skip("Need creature and weapon cards")

        creature = creatures[0]
        weapon = weapons[0]

        p1.board.append(creature)
        p1.equip_weapon(creature.id, weapon)

        # Verify weapon is equipped
        assert p1.get_weapon_for_card(creature.id) == weapon

        # Sacrifice
        p1.sacrifice_card(creature)

        # Both should be gone
        assert len(p1.board) == 0
        assert p1.get_weapon_for_card(creature.id) is None
        assert p1.get_sacrifice_count() == 1

    def test_sacrifice_tracking_resets(
        self, two_player_state: GameState, repo: CardRepository
    ) -> None:
        """Verify sacrifice tracking resets on new turn."""
        p1 = two_player_state.players[0]

        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        if not creatures:
            pytest.skip("No creature cards")

        creature = creatures[0]
        p1.board.append(creature)
        p1.sacrifice_card(creature)

        assert p1.get_sacrifice_count() == 1

        p1.reset_turn_tracking()

        assert p1.get_sacrifice_count() == 0


# === Integration Tests: Deck Interactions ===


class TestDeckInteractionsIntegration:
    """Test deck interaction methods in game context."""

    def test_peek_deck_does_not_remove(
        self, two_player_state: GameState, repo: CardRepository
    ) -> None:
        """Verify peek_deck doesn't remove cards."""
        state = two_player_state

        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        if not creatures:
            pytest.skip("No creature cards")

        state.cost_1_deck = [creatures[0]]

        peeked = state.peek_deck(tier=1, count=1)

        assert len(peeked) == 1
        assert peeked[0] == creatures[0]
        assert len(state.cost_1_deck) == 1  # Card still in deck

    def test_reveal_top_card_for_bonuses(
        self, two_player_state: GameState, repo: CardRepository
    ) -> None:
        """Verify reveal_top_card works for bonus calculations."""
        state = two_player_state

        # Get a Lapin card
        lapins = [
            c
            for c in repo.get_all()
            if c.card_type == CardType.CREATURE and c.family == Family.LAPIN
        ]
        if not lapins:
            pytest.skip("No Lapin cards in repository")

        state.cost_1_deck = [lapins[0]]

        revealed = state.reveal_top_card(tier=1)

        assert revealed is not None
        assert revealed.family == Family.LAPIN
        # Card still in deck
        assert len(state.cost_1_deck) == 1

    def test_draw_from_deck_removes_card(
        self, two_player_state: GameState, repo: CardRepository
    ) -> None:
        """Verify draw_from_deck removes the card."""
        state = two_player_state

        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        if len(creatures) < 2:
            pytest.skip("Need at least 2 creature cards")

        state.cost_1_deck = [creatures[0], creatures[1]]

        drawn = state.draw_from_deck(tier=1)

        assert drawn == creatures[0]
        assert len(state.cost_1_deck) == 1
        assert state.cost_1_deck[0] == creatures[1]

    def test_search_deck_by_family(
        self, two_player_state: GameState, repo: CardRepository
    ) -> None:
        """Verify search_deck finds cards by family."""
        state = two_player_state

        # Get Lapin and non-Lapin cards
        lapins = [
            c
            for c in repo.get_all()
            if c.card_type == CardType.CREATURE and c.family == Family.LAPIN
        ]
        non_lapins = [
            c
            for c in repo.get_all()
            if c.card_type == CardType.CREATURE and c.family != Family.LAPIN
        ]

        if not lapins or not non_lapins:
            pytest.skip("Need both Lapin and non-Lapin cards")

        state.cost_2_deck = [lapins[0], non_lapins[0]]

        found_lapins = state.search_deck(tier=2, family="Lapin")

        assert len(found_lapins) == 1
        assert found_lapins[0].family == Family.LAPIN

    def test_peek_current_deck(
        self, two_player_state: GameState, repo: CardRepository
    ) -> None:
        """Verify peek_current_deck uses current cost tier."""
        state = two_player_state
        state.turn = 1  # Turn 1 = tier 1

        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        if not creatures:
            pytest.skip("No creature cards")

        state.cost_1_deck = [creatures[0]]

        peeked = state.peek_current_deck(count=1)

        assert len(peeked) == 1
        assert peeked[0] == creatures[0]

    def test_draw_from_empty_deck_returns_none(
        self, two_player_state: GameState
    ) -> None:
        """Verify drawing from empty deck returns None."""
        state = two_player_state
        state.cost_1_deck = []

        drawn = state.draw_from_deck(tier=1)

        assert drawn is None

    def test_reveal_empty_deck_returns_none(self, two_player_state: GameState) -> None:
        """Verify revealing from empty deck returns None."""
        state = two_player_state
        state.cost_1_deck = []

        revealed = state.reveal_top_card(tier=1)

        assert revealed is None


# === Integration Tests: Full Combat with All Systems ===


class TestFullCombatIntegration:
    """Test full combat resolution with all new systems."""

    def test_combat_with_weapons_both_sides(
        self, two_player_state: GameState, repo: CardRepository
    ) -> None:
        """Test combat where both players have weapons equipped."""
        p1 = two_player_state.players[0]
        p2 = two_player_state.players[1]

        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        weapons = repo.get_by_type(CardType.WEAPON)

        if len(creatures) < 2 or len(weapons) < 2:
            pytest.skip("Need at least 2 creatures and 2 weapons")

        # Set up player 1
        p1.board.append(creatures[0])
        p1.equip_weapon(creatures[0].id, weapons[0])

        # Set up player 2
        p2.board.append(creatures[1])
        p2.equip_weapon(creatures[1].id, weapons[1])

        # Resolve combat
        result = resolve_combat(two_player_state)

        # Check damage breakdowns include weapon stats
        for breakdown in result.damage_dealt:
            if breakdown.source_player == p1:
                assert breakdown.weapon_attack == weapons[0].attack
                assert breakdown.weapon_defense == weapons[1].health
            elif breakdown.source_player == p2:
                assert breakdown.weapon_attack == weapons[1].attack
                assert breakdown.weapon_defense == weapons[0].health

    def test_combat_after_sacrifice(
        self, two_player_state: GameState, repo: CardRepository
    ) -> None:
        """Test combat after a player sacrifices a card."""
        p1 = two_player_state.players[0]
        p2 = two_player_state.players[1]

        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        if len(creatures) < 3:
            pytest.skip("Need at least 3 creature cards")

        # Give player 1 two cards
        p1.board.extend([creatures[0], creatures[1]])
        p2.board.append(creatures[2])

        # Calculate attack before sacrifice
        total_atk_before = p1.get_total_attack()

        # Sacrifice one card
        sacrificed = creatures[0]
        p1.sacrifice_card(sacrificed)
        assert p1.get_sacrifice_count() == 1

        # Calculate attack after sacrifice
        total_atk_after = p1.get_total_attack()
        assert total_atk_after == total_atk_before - sacrificed.attack

        # Combat should use reduced attack
        breakdown = calculate_damage(p1, p2)
        assert breakdown.base_attack == total_atk_after


# === Integration Tests: Full Simulation ===


class TestFullSimulationIntegration:
    """Test full game simulation with new systems."""

    def test_game_simulation_completes(self, repo: CardRepository) -> None:
        """Run a brief simulation verifying systems don't break gameplay."""
        from src.players import RandomPlayer
        from src.simulation import GameRunner

        players = [
            RandomPlayer(player_id=0, seed=42),
            RandomPlayer(player_id=1, seed=43),
        ]

        runner = GameRunner(players=players, seed=100, max_turns=10)
        result = runner.run_game()

        # Game should complete without errors
        assert result.turns > 0
        assert result.final_state is not None
        assert len(result.final_state.players) == 2

    def test_multiple_games_stable(self, repo: CardRepository) -> None:
        """Run multiple simulations to verify stability."""
        from src.players import RandomPlayer
        from src.simulation import GameRunner

        for i in range(5):
            players = [
                RandomPlayer(player_id=0, seed=i * 100),
                RandomPlayer(player_id=1, seed=i * 100 + 1),
            ]
            runner = GameRunner(players=players, seed=i, max_turns=20)
            result = runner.run_game()

            # Each game should complete
            assert result.turns > 0
            assert result.final_state is not None
