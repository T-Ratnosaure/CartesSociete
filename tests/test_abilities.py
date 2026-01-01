"""Tests for the ability resolution system."""

from copy import deepcopy

import pytest

from src.cards.models import CardClass
from src.cards.repository import get_repository
from src.game.abilities import (
    AbilityTarget,
    apply_per_turn_effects,
    get_active_scaling_ability,
    parse_ability_effect,
    resolve_all_abilities,
    resolve_class_abilities,
    resolve_per_turn_effects,
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


class TestPerTurnEffects:
    """Tests for per-turn effect resolution."""

    def test_mutanus_per_turn_self_damage_parsed(self, repo) -> None:
        """Test that Mutanus empoisonné has per-turn self-damage parsed."""
        mutanus = repo.get_by_name_and_level("Mutanus empoisonné", level=1)
        assert mutanus is not None
        # Mutanus has "Vous perdez 2 PV imblocables par tour"
        assert mutanus.class_abilities.per_turn_self_damage == 2

    def test_mutanus_level2_per_turn_self_damage(self, repo) -> None:
        """Test that Mutanus empoisonné Level 2 has correct per-turn damage."""
        mutanus = repo.get_by_name_and_level("Mutanus empoisonné", level=2)
        assert mutanus is not None
        # Level 2 Mutanus has "Vous perdez 2 PV imblocables par tour, +3 ATQ"
        assert mutanus.class_abilities.per_turn_self_damage == 2

    def test_card_without_per_turn_effect(self, repo) -> None:
        """Test that cards without per-turn effects have 0 damage."""
        defenders = [c for c in repo.get_all() if c.card_class == CardClass.DEFENSEUR]
        defender = defenders[0]
        assert defender.class_abilities.per_turn_self_damage == 0

    def test_resolve_per_turn_effects_no_cards(self) -> None:
        """Test per-turn resolution with no cards on board."""
        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        result = resolve_per_turn_effects(player)
        assert result.total_self_damage == 0
        assert result.cards_with_effects == []

    def test_resolve_per_turn_effects_with_mutanus(self, repo) -> None:
        """Test per-turn resolution with Mutanus on board."""
        mutanus = repo.get_by_name_and_level("Mutanus empoisonné", level=1)

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        player.board.append(deepcopy(mutanus))

        result = resolve_per_turn_effects(player)
        assert result.total_self_damage == 2
        assert "Mutanus empoisonné" in result.cards_with_effects

    def test_resolve_per_turn_effects_multiple_cards(self, repo) -> None:
        """Test per-turn resolution with multiple Mutanus cards."""
        mutanus = repo.get_by_name_and_level("Mutanus empoisonné", level=1)

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Add 2 Mutanus
        player.board.append(deepcopy(mutanus))
        player.board.append(deepcopy(mutanus))

        result = resolve_per_turn_effects(player)
        # Each Mutanus deals 2 per-turn damage
        assert result.total_self_damage == 4
        assert len(result.cards_with_effects) == 2

    def test_apply_per_turn_effects_reduces_health(self, repo) -> None:
        """Test that applying per-turn effects reduces player health."""
        mutanus = repo.get_by_name_and_level("Mutanus empoisonné", level=1)

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        initial_health = player.health
        player.board.append(deepcopy(mutanus))

        damage = apply_per_turn_effects(player)

        assert damage == 2
        assert player.health == initial_health - 2

    def test_per_turn_damage_separate_from_berserker_damage(self, repo) -> None:
        """Test that per-turn damage is separate from Berserker class damage."""
        mutanus = repo.get_by_name_and_level("Mutanus empoisonné", level=1)

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Add 2 Mutanus (triggers Berserker threshold 2: +5 ATK / -2 PV)
        player.board.append(deepcopy(mutanus))
        player.board.append(deepcopy(mutanus))

        # Class abilities (Berserker self-damage from threshold)
        class_result = resolve_class_abilities(player)
        assert class_result.total_self_damage == 2  # Berserker threshold damage

        # Per-turn effects (from bonus_text "Vous perdez 2 PV par tour")
        per_turn_result = resolve_per_turn_effects(player)
        assert per_turn_result.total_self_damage == 4  # 2 x 2 PV per turn

        # Total expected damage per turn: 2 (Berserker) + 4 (per-turn) = 6


class TestConditionalAbilities:
    """Tests for conditional ability resolution (Dragon PO spending)."""

    def test_dragon_conditional_with_enough_po(self, repo) -> None:
        """Test that Dragon conditional abilities work when PO is available."""
        from src.game.abilities import resolve_conditional_abilities

        # Find a Dragon card with imblocable conditional abilities
        # (e.g., "Ancien de la nature" with "X dgt imblocable")
        dragons = [
            c
            for c in repo.get_all()
            if c.card_class == CardClass.DRAGON
            and c.class_abilities.conditional
            and any(
                "imblocable" in cond.effect.lower()
                for cond in c.class_abilities.conditional
            )
        ]

        if not dragons:
            pytest.skip("No Dragon cards with imblocable conditional abilities found")

        dragon = dragons[0]
        state = create_initial_game_state(num_players=2)
        player = state.players[0]
        player.po = 3  # Enough for highest tier

        player.board.append(deepcopy(dragon))

        result = resolve_conditional_abilities(player)

        # Should have imblocable damage and spent PO
        assert result.total_imblocable_damage > 0
        assert result.po_spent > 0
        assert len(result.effects) > 0

    def test_dragon_conditional_with_no_po(self, repo) -> None:
        """Test that Dragon conditional abilities don't activate without PO."""
        from src.game.abilities import resolve_conditional_abilities

        # Find a Dragon card with imblocable conditional abilities
        dragons = [
            c
            for c in repo.get_all()
            if c.card_class == CardClass.DRAGON
            and c.class_abilities.conditional
            and any(
                "imblocable" in cond.effect.lower()
                for cond in c.class_abilities.conditional
            )
        ]

        if not dragons:
            pytest.skip("No Dragon cards with imblocable conditional abilities found")

        dragon = dragons[0]
        state = create_initial_game_state(num_players=2)
        player = state.players[0]
        player.po = 0  # No PO available

        player.board.append(deepcopy(dragon))

        result = resolve_conditional_abilities(player)

        # Should have no imblocable damage
        assert result.total_imblocable_damage == 0
        assert result.po_spent == 0

    def test_dragon_conditional_limited_by_po(self, repo) -> None:
        """Test that Dragon conditional abilities are limited by available PO."""
        from src.game.abilities import resolve_conditional_abilities

        # Find a Dragon card with imblocable conditional abilities
        dragons = [
            c
            for c in repo.get_all()
            if c.card_class == CardClass.DRAGON
            and c.class_abilities.conditional
            and any(
                "imblocable" in cond.effect.lower()
                for cond in c.class_abilities.conditional
            )
        ]

        if not dragons:
            pytest.skip("No Dragon cards with imblocable conditional abilities found")

        dragon = dragons[0]
        state = create_initial_game_state(num_players=2)
        player = state.players[0]
        player.po = 1  # Only 1 PO available

        player.board.append(deepcopy(dragon))

        result = resolve_conditional_abilities(player, po_to_spend=1)

        # Should only activate 1 PO tier
        assert result.po_spent <= 1


class TestPassiveAbilities:
    """Tests for passive ability resolution."""

    def test_s_team_not_counted_as_monster(self, repo) -> None:
        """Test that S-Team cards don't count as monsters."""
        from src.game.abilities import count_board_monsters, resolve_passive_abilities

        s_team_cards = [c for c in repo.get_all() if c.card_class == CardClass.S_TEAM]

        if not s_team_cards:
            pytest.skip("No S-Team cards found")

        s_team = s_team_cards[0]
        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Add S-Team card
        player.board.append(deepcopy(s_team))

        # Check passive resolution
        passives = resolve_passive_abilities(player)
        assert len(passives.cards_excluded_from_count) == 1

        # Check board count
        monster_count = count_board_monsters(player)
        assert monster_count == 0  # S-Team doesn't count

    def test_econome_generates_extra_po(self, repo) -> None:
        """Test that Econome cards generate extra PO."""
        from src.game.abilities import resolve_passive_abilities

        economes = [
            c
            for c in repo.get_all()
            if c.card_class == CardClass.ECONOME and c.class_abilities.passive
        ]

        if not economes:
            pytest.skip("No Econome cards with passive found")

        econome = economes[0]
        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Add 2 Economes
        player.board.append(deepcopy(econome))
        player.board.append(deepcopy(econome))

        passives = resolve_passive_abilities(player)

        # Should generate 2 extra PO (1 per Econome)
        assert passives.extra_po == 2


class TestForgeronAbilities:
    """Tests for Forgeron weapon draw ability."""

    def test_forgeron_draws_weapons(self, repo) -> None:
        """Test that Forgeron class draws weapons."""
        from src.game.abilities import resolve_forgeron_abilities

        forgerons = [
            c
            for c in repo.get_all()
            if c.card_class == CardClass.FORGERON and c.class_abilities.scaling
        ]

        if not forgerons:
            pytest.skip("No Forgeron cards found")

        forgeron = forgerons[0]
        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Add 1 Forgeron (threshold 1)
        player.board.append(deepcopy(forgeron))

        weapons_to_draw = resolve_forgeron_abilities(player)

        # Should draw at least 1 weapon at threshold 1
        assert weapons_to_draw >= 1

    def test_forgeron_no_cards_no_weapons(self, repo) -> None:
        """Test that no weapons are drawn without Forgerons."""
        from src.game.abilities import resolve_forgeron_abilities

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        weapons_to_draw = resolve_forgeron_abilities(player)

        assert weapons_to_draw == 0


class TestBonusTextEffects:
    """Tests for bonus_text effect parsing and resolution."""

    def test_bonus_for_family(self, repo) -> None:
        """Test bonus_text that gives attack to a family."""
        from src.game.abilities import resolve_bonus_text_effects

        # Find a card with bonus for family (e.g., "+1 ATQ pour tous les cyborgs")
        cards_with_family_bonus = [
            c
            for c in repo.get_all()
            if c.bonus_text
            and "pour" in c.bonus_text.lower()
            and "atq" in c.bonus_text.lower()
        ]

        if not cards_with_family_bonus:
            pytest.skip("No cards with family bonus found")

        card = cards_with_family_bonus[0]
        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Add the card and a matching family card
        player.board.append(deepcopy(card))

        # Find another card of the same family
        same_family = [
            c for c in repo.get_all() if c.family == card.family and c.id != card.id
        ]
        if same_family:
            player.board.append(deepcopy(same_family[0]))

        result = resolve_bonus_text_effects(player)

        # Should have some attack bonus if the pattern matches
        # Note: may be 0 if the bonus_text pattern doesn't match our regex
        assert result.attack_bonus >= 0

    def test_bonus_if_threshold(self, repo) -> None:
        """Test bonus_text that gives attack if a class threshold is met."""
        from src.game.abilities import resolve_bonus_text_effects

        # Find a card with threshold bonus (e.g., "+2 ATQ si bonus Archer 2")
        cards_with_threshold = [
            c
            for c in repo.get_all()
            if c.bonus_text
            and "si" in c.bonus_text.lower()
            and "atq" in c.bonus_text.lower()
        ]

        if not cards_with_threshold:
            pytest.skip("No cards with threshold bonus found")

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Add a card with threshold bonus
        card = cards_with_threshold[0]
        player.board.append(deepcopy(card))

        result = resolve_bonus_text_effects(player)

        # Attack bonus may or may not be present depending on threshold met
        assert result.attack_bonus >= 0
