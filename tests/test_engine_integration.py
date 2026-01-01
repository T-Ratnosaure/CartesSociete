"""Tests for engine integration of weapon, sacrifice, and turn tracking systems.

These tests verify that the new action types (EQUIP_WEAPON, SACRIFICE_CARD)
work correctly in the game flow.
"""

import pytest

from src.cards.models import CardType
from src.cards.repository import CardRepository
from src.game.actions import (
    InvalidCardError,
    InvalidPhaseError,
    equip_weapon,
    sacrifice_card,
)
from src.game.executor import execute_action, get_legal_actions_for_player
from src.game.state import GamePhase, create_initial_game_state
from src.players.action import Action, ActionType


@pytest.fixture
def repo() -> CardRepository:
    """Create a card repository with all cards loaded."""
    return CardRepository()


# === Tests for equip_weapon action ===


class TestEquipWeaponAction:
    """Test the equip_weapon action function."""

    def test_equip_weapon_success(self, repo: CardRepository) -> None:
        """Test successfully equipping a weapon to a board card."""
        state = create_initial_game_state(2, ["P1", "P2"])
        state.phase = GamePhase.PLAY
        player = state.players[0]

        # Get a creature and weapon
        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        weapons = repo.get_by_type(CardType.WEAPON)
        if not creatures or not weapons:
            pytest.skip("Need creature and weapon cards")

        creature = creatures[0]
        weapon = weapons[0]

        # Set up player state
        player.board.append(creature)
        player.hand.append(weapon)

        # Equip weapon
        result = equip_weapon(state, player, weapon, creature)

        assert result.success is True
        assert weapon not in player.hand
        assert player.get_weapon_for_card(creature.id) == weapon
        assert player.get_total_weapon_attack() == weapon.attack

    def test_equip_weapon_wrong_phase(self, repo: CardRepository) -> None:
        """Test that equipping in wrong phase raises error."""
        state = create_initial_game_state(2, ["P1", "P2"])
        state.phase = GamePhase.MARKET  # Wrong phase
        player = state.players[0]

        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        weapons = repo.get_by_type(CardType.WEAPON)
        if not creatures or not weapons:
            pytest.skip("Need creature and weapon cards")

        player.board.append(creatures[0])
        player.hand.append(weapons[0])

        with pytest.raises(InvalidPhaseError):
            equip_weapon(state, player, weapons[0], creatures[0])

    def test_equip_weapon_not_in_hand(self, repo: CardRepository) -> None:
        """Test that equipping weapon not in hand raises error."""
        state = create_initial_game_state(2, ["P1", "P2"])
        state.phase = GamePhase.PLAY
        player = state.players[0]

        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        weapons = repo.get_by_type(CardType.WEAPON)
        if not creatures or not weapons:
            pytest.skip("Need creature and weapon cards")

        player.board.append(creatures[0])
        # Don't add weapon to hand

        with pytest.raises(InvalidCardError):
            equip_weapon(state, player, weapons[0], creatures[0])

    def test_equip_weapon_target_not_on_board(self, repo: CardRepository) -> None:
        """Test that equipping to card not on board raises error."""
        state = create_initial_game_state(2, ["P1", "P2"])
        state.phase = GamePhase.PLAY
        player = state.players[0]

        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        weapons = repo.get_by_type(CardType.WEAPON)
        if not creatures or not weapons:
            pytest.skip("Need creature and weapon cards")

        # Don't add creature to board
        player.hand.append(weapons[0])

        with pytest.raises(InvalidCardError):
            equip_weapon(state, player, weapons[0], creatures[0])

    def test_equip_weapon_already_equipped(self, repo: CardRepository) -> None:
        """Test that equipping to card with weapon raises error."""
        state = create_initial_game_state(2, ["P1", "P2"])
        state.phase = GamePhase.PLAY
        player = state.players[0]

        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        weapons = repo.get_by_type(CardType.WEAPON)
        if not creatures or len(weapons) < 2:
            pytest.skip("Need creature and 2 weapon cards")

        creature = creatures[0]
        player.board.append(creature)
        player.hand.extend([weapons[0], weapons[1]])

        # Equip first weapon
        equip_weapon(state, player, weapons[0], creature)

        # Try to equip second weapon to same card
        with pytest.raises(InvalidCardError):
            equip_weapon(state, player, weapons[1], creature)


# === Tests for sacrifice_card action ===


class TestSacrificeCardAction:
    """Test the sacrifice_card action function."""

    def test_sacrifice_card_success(self, repo: CardRepository) -> None:
        """Test successfully sacrificing a card from board."""
        state = create_initial_game_state(2, ["P1", "P2"])
        state.phase = GamePhase.PLAY
        player = state.players[0]

        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        if not creatures:
            pytest.skip("Need creature cards")

        creature = creatures[0]
        player.board.append(creature)

        result = sacrifice_card(state, player, creature)

        assert result.success is True
        assert creature not in player.board
        assert creature in player.sacrificed_this_turn
        assert creature in state.discard_pile
        assert player.get_sacrifice_count() == 1

    def test_sacrifice_card_wrong_phase(self, repo: CardRepository) -> None:
        """Test that sacrificing in wrong phase raises error."""
        state = create_initial_game_state(2, ["P1", "P2"])
        state.phase = GamePhase.COMBAT  # Wrong phase
        player = state.players[0]

        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        if not creatures:
            pytest.skip("Need creature cards")

        player.board.append(creatures[0])

        with pytest.raises(InvalidPhaseError):
            sacrifice_card(state, player, creatures[0])

    def test_sacrifice_card_not_on_board(self, repo: CardRepository) -> None:
        """Test that sacrificing card not on board raises error."""
        state = create_initial_game_state(2, ["P1", "P2"])
        state.phase = GamePhase.PLAY
        player = state.players[0]

        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        if not creatures:
            pytest.skip("Need creature cards")

        # Don't add to board

        with pytest.raises(InvalidCardError):
            sacrifice_card(state, player, creatures[0])

    def test_sacrifice_removes_weapon(self, repo: CardRepository) -> None:
        """Test that sacrificing a card removes its equipped weapon."""
        state = create_initial_game_state(2, ["P1", "P2"])
        state.phase = GamePhase.PLAY
        player = state.players[0]

        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        weapons = repo.get_by_type(CardType.WEAPON)
        if not creatures or not weapons:
            pytest.skip("Need creature and weapon cards")

        creature = creatures[0]
        weapon = weapons[0]

        player.board.append(creature)
        player.hand.append(weapon)

        # Equip weapon first
        equip_weapon(state, player, weapon, creature)
        assert player.get_total_weapon_attack() == weapon.attack

        # Sacrifice the card
        sacrifice_card(state, player, creature)

        # Weapon should be gone
        assert player.get_total_weapon_attack() == 0
        assert player.get_weapon_for_card(creature.id) is None


# === Tests for execute_action with new types ===


class TestExecuteActionNewTypes:
    """Test execute_action with new action types."""

    def test_execute_equip_weapon(self, repo: CardRepository) -> None:
        """Test executing EQUIP_WEAPON action."""
        state = create_initial_game_state(2, ["P1", "P2"])
        state.phase = GamePhase.PLAY
        player = state.players[0]

        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        weapons = repo.get_by_type(CardType.WEAPON)
        if not creatures or not weapons:
            pytest.skip("Need creature and weapon cards")

        creature = creatures[0]
        weapon = weapons[0]

        player.board.append(creature)
        player.hand.append(weapon)

        action = Action.equip_weapon(weapon, creature)
        result = execute_action(state, player, action)

        assert result.success is True
        assert player.get_weapon_for_card(creature.id) == weapon

    def test_execute_sacrifice(self, repo: CardRepository) -> None:
        """Test executing SACRIFICE_CARD action."""
        state = create_initial_game_state(2, ["P1", "P2"])
        state.phase = GamePhase.PLAY
        player = state.players[0]

        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        if not creatures:
            pytest.skip("Need creature cards")

        creature = creatures[0]
        player.board.append(creature)

        action = Action.sacrifice(creature)
        result = execute_action(state, player, action)

        assert result.success is True
        assert creature not in player.board
        assert player.get_sacrifice_count() == 1


# === Tests for get_legal_actions with new types ===


class TestLegalActionsNewTypes:
    """Test get_legal_actions_for_player includes new action types."""

    def test_legal_actions_include_equip_weapon(self, repo: CardRepository) -> None:
        """Test that legal actions include equip weapon options."""
        state = create_initial_game_state(2, ["P1", "P2"])
        state.phase = GamePhase.PLAY
        player = state.players[0]

        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        weapons = repo.get_by_type(CardType.WEAPON)
        if not creatures or not weapons:
            pytest.skip("Need creature and weapon cards")

        creature = creatures[0]
        weapon = weapons[0]

        player.board.append(creature)
        player.hand.append(weapon)

        actions = get_legal_actions_for_player(state, player)

        equip_actions = [a for a in actions if a.action_type == ActionType.EQUIP_WEAPON]
        assert len(equip_actions) == 1
        assert equip_actions[0].card == weapon
        assert equip_actions[0].target_card == creature

    def test_legal_actions_no_equip_if_already_equipped(
        self, repo: CardRepository
    ) -> None:
        """Test that no equip action if card already has weapon."""
        state = create_initial_game_state(2, ["P1", "P2"])
        state.phase = GamePhase.PLAY
        player = state.players[0]

        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        weapons = repo.get_by_type(CardType.WEAPON)
        if not creatures or len(weapons) < 2:
            pytest.skip("Need creature and 2 weapon cards")

        creature = creatures[0]
        player.board.append(creature)
        player.equip_weapon(creature.id, weapons[0])  # Already equipped
        player.hand.append(weapons[1])

        actions = get_legal_actions_for_player(state, player)

        equip_actions = [a for a in actions if a.action_type == ActionType.EQUIP_WEAPON]
        # Should be 0 because creature already has weapon
        assert len(equip_actions) == 0

    def test_legal_actions_include_sacrifice(self, repo: CardRepository) -> None:
        """Test that legal actions include sacrifice options."""
        state = create_initial_game_state(2, ["P1", "P2"])
        state.phase = GamePhase.PLAY
        player = state.players[0]

        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        if len(creatures) < 2:
            pytest.skip("Need at least 2 creature cards")

        player.board.extend([creatures[0], creatures[1]])

        actions = get_legal_actions_for_player(state, player)

        sacrifice_actions = [
            a for a in actions if a.action_type == ActionType.SACRIFICE_CARD
        ]
        assert len(sacrifice_actions) == 2  # One for each board card


# === Tests for turn tracking reset ===


class TestTurnTrackingReset:
    """Test that per-turn tracking resets correctly."""

    def test_simulation_completes_with_new_actions(self, repo: CardRepository) -> None:
        """Test that simulation runs with new action types available."""
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

        # Spells should always be 0 (reset happens, and no spell casting yet)
        for player in result.final_state.players:
            assert player.spells_cast_this_turn == 0

    def test_reset_turn_tracking_manually(self) -> None:
        """Test that reset_turn_tracking_all_players works correctly."""
        state = create_initial_game_state(2, ["P1", "P2"])

        # Set up some tracking
        state.players[0].cast_spell(damage=5)
        state.players[0].sacrificed_this_turn.append(None)  # type: ignore
        state.players[1].cast_spell(damage=10)

        # Verify tracking is set
        assert state.players[0].spells_cast_this_turn == 1
        assert state.players[0].get_sacrifice_count() == 1
        assert state.players[1].spells_cast_this_turn == 1

        # Reset
        state.reset_turn_tracking_all_players()

        # Verify reset
        for player in state.players:
            assert player.spells_cast_this_turn == 0
            assert player.spell_damage_dealt == 0
            assert player.get_sacrifice_count() == 0


# === Tests for Action repr ===


class TestActionRepr:
    """Test Action repr for new action types."""

    def test_equip_weapon_repr(self, repo: CardRepository) -> None:
        """Test EQUIP_WEAPON action repr."""
        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        weapons = repo.get_by_type(CardType.WEAPON)
        if not creatures or not weapons:
            pytest.skip("Need creature and weapon cards")

        action = Action.equip_weapon(weapons[0], creatures[0])
        repr_str = repr(action)

        assert "EQUIP" in repr_str
        assert weapons[0].name in repr_str
        assert creatures[0].name in repr_str

    def test_sacrifice_repr(self, repo: CardRepository) -> None:
        """Test SACRIFICE_CARD action repr."""
        creatures = [c for c in repo.get_all() if c.card_type == CardType.CREATURE]
        if not creatures:
            pytest.skip("Need creature cards")

        action = Action.sacrifice(creatures[0])
        repr_str = repr(action)

        assert "SACRIFICE" in repr_str
        assert creatures[0].name in repr_str
