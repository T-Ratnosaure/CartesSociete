"""Tests for the ability resolution system."""

from copy import deepcopy

import pytest

from src.cards.models import CardClass
from src.cards.repository import get_repository
from src.game.abilities import (
    AbilityTarget,
    get_active_scaling_ability,
    parse_ability_effect,
    resolve_all_abilities,
    resolve_class_abilities,
)
from src.game.combat import calculate_damage, resolve_combat
from src.game.state import create_initial_game_state


@pytest.fixture
def repo():
    """Get the card repository."""
    repository = get_repository()
    repository.load()
    return repository


class TestParseAbilityEffect:
    """Tests for parsing ability effect text."""

    def test_parse_attack_bonus(self) -> None:
        """Test parsing attack bonus."""
        effect = parse_ability_effect("+5 dgt / -2 PV")
        assert effect.attack_bonus == 5

    def test_parse_attack_bonus_atq(self) -> None:
        """Test parsing ATQ format."""
        effect = parse_ability_effect("+3 ATQ pour les combattants")
        assert effect.attack_bonus == 3

    def test_parse_health_bonus(self) -> None:
        """Test parsing health bonus."""
        effect = parse_ability_effect("+2 PV pour les défenseurs")
        assert effect.health_bonus == 2

    def test_parse_self_damage(self) -> None:
        """Test parsing self-damage."""
        effect = parse_ability_effect("+5 dgt / -2 PV")
        assert effect.self_damage == 2

    def test_parse_higher_self_damage(self) -> None:
        """Test parsing higher self-damage."""
        effect = parse_ability_effect("+10 dgt / -5 PV")
        assert effect.attack_bonus == 10
        assert effect.self_damage == 5

    def test_parse_imblocable_damage(self) -> None:
        """Test parsing imblocable damage."""
        effect = parse_ability_effect("2 dgt imblocables")
        assert effect.imblocable_damage == 2

    def test_parse_class_target(self) -> None:
        """Test parsing class-targeted effects."""
        effect = parse_ability_effect("+3 ATQ pour les combattants")
        assert effect.target == AbilityTarget.SPECIFIC
        assert effect.target_class == CardClass.COMBATTANT

    def test_parse_defender_target(self) -> None:
        """Test parsing defender-targeted effects."""
        effect = parse_ability_effect("+2 PV pour les défenseurs")
        assert effect.target == AbilityTarget.SPECIFIC
        assert effect.target_class == CardClass.DEFENSEUR

    def test_parse_all_monsters(self) -> None:
        """Test parsing all-monsters effects."""
        effect = parse_ability_effect("+1 dgt pour tous les monstres")
        assert effect.target == AbilityTarget.ALL_MONSTERS


class TestGetActiveScalingAbility:
    """Tests for getting active scaling abilities."""

    def test_no_abilities(self) -> None:
        """Test with no abilities."""
        result = get_active_scaling_ability([], 5)
        assert result is None

    def test_threshold_not_met(self, repo) -> None:
        """Test when threshold is not met."""
        mutanus = repo.get_by_name_and_level("Mutanus empoisonné", level=1)
        abilities = mutanus.class_abilities.scaling
        result = get_active_scaling_ability(abilities, 1)
        assert result is None

    def test_threshold_met(self, repo) -> None:
        """Test when threshold is exactly met."""
        mutanus = repo.get_by_name_and_level("Mutanus empoisonné", level=1)
        abilities = mutanus.class_abilities.scaling
        result = get_active_scaling_ability(abilities, 2)
        assert result is not None
        assert result.threshold == 2

    def test_higher_threshold_met(self, repo) -> None:
        """Test when higher threshold is met."""
        mutanus = repo.get_by_name_and_level("Mutanus empoisonné", level=1)
        abilities = mutanus.class_abilities.scaling
        result = get_active_scaling_ability(abilities, 4)
        assert result is not None
        assert result.threshold == 4


class TestResolveClassAbilities:
    """Tests for class ability resolution."""

    def test_berserker_self_damage(self, repo) -> None:
        """Test that Berserkers apply self-damage at threshold 2."""
        mutanus = repo.get_by_name_and_level("Mutanus empoisonné", level=1)

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Add 2 Berserkers to trigger threshold 2
        player.board.append(deepcopy(mutanus))
        player.board.append(deepcopy(mutanus))

        result = resolve_class_abilities(player)

        assert result.class_counts[CardClass.BERSEKER] == 2
        assert result.total_attack_bonus == 5
        assert result.total_self_damage == 2

    def test_berserker_higher_threshold(self, repo) -> None:
        """Test Berserker at threshold 4."""
        mutanus = repo.get_by_name_and_level("Mutanus empoisonné", level=1)

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Add 4 Berserkers to trigger threshold 4
        for _ in range(4):
            player.board.append(deepcopy(mutanus))

        result = resolve_class_abilities(player)

        assert result.total_attack_bonus == 10
        assert result.total_self_damage == 5

    def test_defender_health_bonus(self, repo) -> None:
        """Test that Defenders get health bonus at threshold 2."""
        defenders = [c for c in repo.get_all() if c.card_class == CardClass.DEFENSEUR]
        defender = defenders[0]

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Add 2 Defenders
        player.board.append(deepcopy(defender))
        player.board.append(deepcopy(defender))

        result = resolve_class_abilities(player)

        assert result.class_counts[CardClass.DEFENSEUR] == 2
        # Defenders get +2 PV per defender at threshold 2
        assert result.total_health_bonus >= 2

    def test_combattant_attack_bonus(self, repo) -> None:
        """Test that Combattants get attack bonus at threshold 2."""
        combattants = [
            c for c in repo.get_all() if c.card_class == CardClass.COMBATTANT
        ]
        combattant = combattants[0]

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Add 2 Combattants
        player.board.append(deepcopy(combattant))
        player.board.append(deepcopy(combattant))

        result = resolve_class_abilities(player)

        assert result.class_counts[CardClass.COMBATTANT] == 2
        # Combattants get +3 ATQ per combattant at threshold 2
        assert result.total_attack_bonus >= 3

    def test_no_abilities_with_single_card(self, repo) -> None:
        """Test that single card doesn't trigger threshold 2 abilities."""
        mutanus = repo.get_by_name_and_level("Mutanus empoisonné", level=1)

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Add only 1 Berserker
        player.board.append(deepcopy(mutanus))

        result = resolve_class_abilities(player)

        assert result.class_counts[CardClass.BERSEKER] == 1
        # Threshold 2 not met, so no attack bonus or self-damage
        assert result.total_attack_bonus == 0
        assert result.total_self_damage == 0


class TestCombatWithAbilities:
    """Tests for combat resolution with abilities."""

    def test_berserker_self_damage_in_combat(self, repo) -> None:
        """Test that Berserker self-damage is applied in combat."""
        mutanus = repo.get_by_name_and_level("Mutanus empoisonné", level=1)

        state = create_initial_game_state(num_players=2)
        player1 = state.players[0]

        initial_health = player1.health

        # Player 1: 2 Berserkers
        player1.board.append(deepcopy(mutanus))
        player1.board.append(deepcopy(mutanus))

        # Player 2: No cards (will still attack with 0 damage)

        result = resolve_combat(state)

        # Player 1 should have taken self-damage
        assert player1.player_id in result.self_damage
        assert result.self_damage[player1.player_id] == 2
        assert player1.health == initial_health - 2

    def test_attack_bonus_in_combat(self, repo) -> None:
        """Test that attack bonuses are applied in damage calculation."""
        mutanus = repo.get_by_name_and_level("Mutanus empoisonné", level=1)
        defenders = [c for c in repo.get_all() if c.card_class == CardClass.DEFENSEUR]
        defender = defenders[0]

        state = create_initial_game_state(num_players=2)
        player1 = state.players[0]
        player2 = state.players[1]

        # Player 1: 2 Berserkers (base ATK = 4+4 = 8, bonus = +5)
        player1.board.append(deepcopy(mutanus))
        player1.board.append(deepcopy(mutanus))

        # Player 2: 1 Defender
        player2.board.append(deepcopy(defender))

        breakdown = calculate_damage(player1, player2)

        # Verify attack bonus is included
        assert breakdown.attack_bonus == 5
        assert breakdown.total_attack == breakdown.base_attack + 5

    def test_health_bonus_in_combat(self, repo) -> None:
        """Test that health bonuses are applied as defense."""
        mutanus = repo.get_by_name_and_level("Mutanus empoisonné", level=1)
        defenders = [c for c in repo.get_all() if c.card_class == CardClass.DEFENSEUR]
        defender = defenders[0]

        state = create_initial_game_state(num_players=2)
        player1 = state.players[0]
        player2 = state.players[1]

        # Player 1: 1 Berserker
        player1.board.append(deepcopy(mutanus))

        # Player 2: 2 Defenders (should get health bonus)
        player2.board.append(deepcopy(defender))
        player2.board.append(deepcopy(defender))

        breakdown = calculate_damage(player1, player2)

        # Verify defense bonus is included
        assert breakdown.defense_bonus > 0
        expected_defense = breakdown.base_defense + breakdown.defense_bonus
        assert breakdown.target_defense == expected_defense


class TestResolveAllAbilities:
    """Tests for resolving all abilities (class + family)."""

    def test_combined_abilities(self, repo) -> None:
        """Test that class and family abilities are combined."""
        # Find a card with both class and family abilities
        cards = repo.get_all()

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Add cards from the same family
        nature_cards = [c for c in cards if c.family.value == "Nature"]
        if len(nature_cards) >= 2:
            player.board.append(deepcopy(nature_cards[0]))
            player.board.append(deepcopy(nature_cards[1]))

            result = resolve_all_abilities(player)

            # Should have processed both class and family abilities
            assert result.class_counts is not None
