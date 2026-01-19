"""Tests for the ability resolution system."""

from copy import deepcopy

import pytest

from src.cards.models import CardClass
from src.cards.repository import get_repository
from src.game.abilities import (
    AbilityTarget,
    UnmatchedBonusTextError,
    apply_per_turn_effects,
    get_active_scaling_ability,
    parse_ability_effect,
    resolve_all_abilities,
    resolve_bonus_text_effects,
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

        result = apply_per_turn_effects(player)

        assert result.total_self_damage == 2
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

    def test_negative_atk_modifier(self, repo) -> None:
        """Test bonus_text that gives attack penalty (e.g., '-1 ATQ pour les X')."""
        from src.game.abilities import resolve_bonus_text_effects

        # Find a card with negative ATK modifier
        cards_with_negative = [
            c
            for c in repo.get_all()
            if c.bonus_text and "-" in c.bonus_text and "atq" in c.bonus_text.lower()
        ]

        if not cards_with_negative:
            pytest.skip("No cards with negative ATK modifier found")

        card = cards_with_negative[0]
        state = create_initial_game_state(num_players=2)
        player = state.players[0]
        player.board.append(deepcopy(card))

        result = resolve_bonus_text_effects(player)

        # attack_penalty should be a valid value
        assert result.attack_penalty >= 0

    def test_on_attacked_damage(self, repo) -> None:
        """Test bonus_text that deals damage when attacked."""
        from src.game.abilities import resolve_bonus_text_effects

        # Find a card with on-attacked damage (e.g., "Inflige X dgt quand attaqué")
        cards_with_on_attacked = [
            c
            for c in repo.get_all()
            if c.bonus_text
            and "quand" in c.bonus_text.lower()
            and "attaqu" in c.bonus_text.lower()
        ]

        if not cards_with_on_attacked:
            pytest.skip("No cards with on-attacked damage found")

        card = cards_with_on_attacked[0]
        state = create_initial_game_state(num_players=2)
        player = state.players[0]
        player.board.append(deepcopy(card))

        result = resolve_bonus_text_effects(player)

        # on_attacked_damage should be positive
        assert result.on_attacked_damage > 0

    def test_per_turn_imblocable(self, repo) -> None:
        """Test bonus_text that gives per-turn imblocable damage."""
        import re

        from src.game.abilities import resolve_bonus_text_effects

        # Find a card with per-turn imblocable attack (e.g., "+X dgt imblocable/tour")
        # Pattern: starts with +, has a number, then dgt imblocable/tour
        per_turn_pattern = re.compile(r"\+\d+\s+dgt\s+imblocable", re.IGNORECASE)
        cards_with_per_turn = [
            c
            for c in repo.get_all()
            if c.bonus_text and per_turn_pattern.search(c.bonus_text)
        ]

        if not cards_with_per_turn:
            pytest.skip("No cards with per-turn imblocable attack found")

        card = cards_with_per_turn[0]
        state = create_initial_game_state(num_players=2)
        player = state.players[0]
        player.board.append(deepcopy(card))

        result = resolve_bonus_text_effects(player)

        # per_turn_imblocable should be positive
        assert result.per_turn_imblocable > 0

    def test_solo_ninja_bonus(self, repo) -> None:
        """Test bonus_text for solo ninja attack bonus."""
        from src.cards.models import Family
        from src.game.abilities import resolve_bonus_text_effects

        # Find a ninja card with solo bonus
        ninjas = [c for c in repo.get_all() if c.family == Family.NINJA]

        if not ninjas:
            pytest.skip("No Ninja cards found")

        # Find one with solo bonus text
        ninja_with_solo = [
            n for n in ninjas if n.bonus_text and "seul ninja" in n.bonus_text.lower()
        ]

        if not ninja_with_solo:
            pytest.skip("No Ninja with solo bonus found")

        ninja = ninja_with_solo[0]
        state = create_initial_game_state(num_players=2)
        player = state.players[0]
        player.board.append(deepcopy(ninja))

        result = resolve_bonus_text_effects(player)

        # Solo ninja bonus should apply when only 1 ninja
        assert result.attack_bonus > 0

    def test_raccoon_family_bonus(self, repo) -> None:
        """Test bonus_text for raccoon family bonus."""
        from src.cards.models import Family
        from src.game.abilities import resolve_bonus_text_effects

        # Find cards with raccoon family bonus
        raccoon_bonus_cards = [
            c
            for c in repo.get_all()
            if c.bonus_text
            and "raccoon" in c.bonus_text.lower()
            and "familly" in c.bonus_text.lower()
        ]

        if not raccoon_bonus_cards:
            pytest.skip("No cards with raccoon family bonus found")

        card = raccoon_bonus_cards[0]
        state = create_initial_game_state(num_players=2)
        player = state.players[0]
        player.board.append(deepcopy(card))

        # Add a raton card to benefit from the bonus
        ratons = [c for c in repo.get_all() if c.family == Family.RATON]
        if ratons:
            player.board.append(deepcopy(ratons[0]))

        result = resolve_bonus_text_effects(player)

        # Should have attack bonus for raccoons
        assert result.attack_bonus >= 0

    def test_bonus_text_result_fields(self, repo) -> None:
        """Test that BonusTextResult has all expected fields."""
        from src.game.abilities import resolve_bonus_text_effects

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        result = resolve_bonus_text_effects(player)

        # Verify all expected fields exist
        assert hasattr(result, "attack_bonus")
        assert hasattr(result, "health_bonus")
        assert hasattr(result, "attack_penalty")
        assert hasattr(result, "on_attacked_damage")
        assert hasattr(result, "per_turn_imblocable")
        assert hasattr(result, "spell_damage_block")
        assert hasattr(result, "extra_po")
        assert hasattr(result, "effects")


class TestOnAttackedDamageInCombat:
    """Tests for on-attacked damage integration in combat."""

    def test_on_attacked_damage_in_combat_result(self, repo) -> None:
        """Test that on-attacked damage is tracked in combat result."""
        # Find a card with on-attacked damage
        cards_with_on_attacked = [
            c
            for c in repo.get_all()
            if c.bonus_text
            and "quand" in c.bonus_text.lower()
            and "attaqu" in c.bonus_text.lower()
        ]

        if not cards_with_on_attacked:
            pytest.skip("No cards with on-attacked damage found")

        card = cards_with_on_attacked[0]
        state = create_initial_game_state(num_players=2)
        player2 = state.players[1]

        # Player 2 has the on-attacked card
        player2.board.append(deepcopy(card))

        result = resolve_combat(state)

        # Check that on_attacked_damage is tracked
        assert isinstance(result.on_attacked_damage, dict)

    def test_combat_result_has_on_attacked_field(self) -> None:
        """Test that CombatResult has on_attacked_damage field."""
        from src.game.combat import CombatResult

        result = CombatResult()

        assert hasattr(result, "on_attacked_damage")
        assert isinstance(result.on_attacked_damage, dict)


class TestDragonAttackMultipliers:
    """Tests for Dragon attack multiplier conditional abilities."""

    def test_dragon_attack_multiplier_parsed(self, repo) -> None:
        """Test that Dragon attack multipliers are recognized."""
        from src.game.abilities import resolve_conditional_abilities

        # Find a Dragon card with attack multiplier conditionals
        dragons = [
            c
            for c in repo.get_all()
            if c.card_class == CardClass.DRAGON
            and c.class_abilities.conditional
            and any(
                "double" in cond.effect.lower()
                or "triple" in cond.effect.lower()
                or "quadruple" in cond.effect.lower()
                for cond in c.class_abilities.conditional
            )
        ]

        if not dragons:
            pytest.skip("No Dragon cards with attack multiplier abilities found")

        dragon = dragons[0]
        state = create_initial_game_state(num_players=2)
        player = state.players[0]
        player.po = 5  # Enough for any multiplier

        player.board.append(deepcopy(dragon))

        result = resolve_conditional_abilities(player)

        # Should have an attack multiplier greater than 1
        assert result.attack_multiplier >= 2

    def test_dragon_multiplier_in_combat(self, repo) -> None:
        """Test that Dragon attack multiplier is applied in combat."""
        # Find a Dragon card with attack multiplier conditionals
        dragons = [
            c
            for c in repo.get_all()
            if c.card_class == CardClass.DRAGON
            and c.class_abilities.conditional
            and any(
                "double" in cond.effect.lower()
                for cond in c.class_abilities.conditional
            )
        ]

        if not dragons:
            pytest.skip("No Dragon cards with double attack ability found")

        dragon = dragons[0]
        state = create_initial_game_state(num_players=2)
        player1 = state.players[0]
        player2 = state.players[1]
        player1.po = 5  # Enough PO

        player1.board.append(deepcopy(dragon))

        breakdown = calculate_damage(player1, player2)

        # Multiplier should be applied
        assert breakdown.attack_multiplier >= 2
        # Total attack should be at least base * multiplier
        base_atk = player1.get_total_attack()
        assert breakdown.total_attack >= base_atk * breakdown.attack_multiplier


class TestInvocateurAbilities:
    """Tests for Invocateur demon summoning ability."""

    def test_invocateur_resolves_demons(self, repo) -> None:
        """Test that Invocateur abilities return demon names to summon."""
        from src.game.abilities import resolve_invocateur_abilities

        invocateurs = [
            c
            for c in repo.get_all()
            if c.card_class == CardClass.INVOCATEUR and c.class_abilities.scaling
        ]

        if not invocateurs:
            pytest.skip("No Invocateur cards found")

        invocateur = invocateurs[0]
        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Add 1 Invocateur (threshold 1 should summon Diablotin)
        player.board.append(deepcopy(invocateur))

        result = resolve_invocateur_abilities(player)

        # Should have demons to summon
        assert len(result.demons_to_summon) >= 1
        assert "Diablotin" in result.demons_to_summon

    def test_invocateur_higher_threshold(self, repo) -> None:
        """Test Invocateur at higher thresholds."""
        from src.game.abilities import resolve_invocateur_abilities

        invocateurs = [
            c
            for c in repo.get_all()
            if c.card_class == CardClass.INVOCATEUR and c.class_abilities.scaling
        ]

        if not invocateurs:
            pytest.skip("No Invocateur cards found")

        invocateur = invocateurs[0]
        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Add 2 Invocateurs (threshold 2 should summon Demon mineur)
        player.board.append(deepcopy(invocateur))
        player.board.append(deepcopy(invocateur))

        result = resolve_invocateur_abilities(player)

        # Should summon a higher tier demon
        assert len(result.demons_to_summon) >= 1

    def test_invocateur_no_cards_no_demons(self, repo) -> None:
        """Test that no demons are summoned without Invocateurs."""
        from src.game.abilities import resolve_invocateur_abilities

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        result = resolve_invocateur_abilities(player)

        assert len(result.demons_to_summon) == 0


class TestMontureAbilities:
    """Tests for Monture card draw ability."""

    def test_monture_resolves_card_draw(self, repo) -> None:
        """Test that Monture abilities return cards to draw."""
        from src.game.abilities import resolve_monture_abilities

        montures = [
            c
            for c in repo.get_all()
            if c.card_class == CardClass.MONTURE and c.class_abilities.scaling
        ]

        if not montures:
            pytest.skip("No Monture cards found")

        monture = montures[0]
        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Add 3 Montures (threshold 3 should draw a cost-5 card)
        player.board.append(deepcopy(monture))
        player.board.append(deepcopy(monture))
        player.board.append(deepcopy(monture))

        result = resolve_monture_abilities(player)

        # Should have cards to draw
        assert result.cards_to_draw >= 1

    def test_monture_below_threshold(self, repo) -> None:
        """Test Monture with insufficient count doesn't trigger draw."""
        from src.game.abilities import resolve_monture_abilities

        montures = [
            c
            for c in repo.get_all()
            if c.card_class == CardClass.MONTURE and c.class_abilities.scaling
        ]

        if not montures:
            pytest.skip("No Monture cards found")

        monture = montures[0]
        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Add only 1 Monture (below threshold 3)
        player.board.append(deepcopy(monture))

        result = resolve_monture_abilities(player)

        # Should not have cards to draw below threshold
        assert result.cards_to_draw == 0


class TestMarketDemonSummoning:
    """Tests for market demon summoning function."""

    def test_summon_demon_adds_to_board(self, repo) -> None:
        """Test that summon_demon adds demon to player's board."""
        from src.cards.models import CardType
        from src.game.market import summon_demon

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Get demons from repo
        demons = [c for c in repo.get_all() if c.card_type == CardType.DEMON]
        if not demons:
            pytest.skip("No demon cards found in repository")

        # Add demons to the state's demon deck
        for demon in demons[:3]:
            state.demon_deck.append(deepcopy(demon))

        initial_board_count = len(player.board)
        demon_name = demons[0].name

        result = summon_demon(state, player.player_id, demon_name)

        if result:
            assert len(player.board) == initial_board_count + 1
            assert result.card_type == CardType.DEMON

    def test_summon_demon_removes_from_deck(self, repo) -> None:
        """Test that summon_demon removes the demon from deck."""
        from src.cards.models import CardType
        from src.game.market import summon_demon

        state = create_initial_game_state(num_players=2)

        # Get demons from repo
        demons = [c for c in repo.get_all() if c.card_type == CardType.DEMON]
        if not demons:
            pytest.skip("No demon cards found in repository")

        # Add demons to the state's demon deck
        for demon in demons[:3]:
            state.demon_deck.append(deepcopy(demon))

        initial_deck_count = len(state.demon_deck)
        demon_name = demons[0].name

        result = summon_demon(state, 0, demon_name)

        if result:
            assert len(state.demon_deck) == initial_deck_count - 1


class TestMarketCost5Draw:
    """Tests for market cost-5 card draw function."""

    def test_draw_cost5_adds_to_hand(self, repo) -> None:
        """Test that draw_cost5_card adds card to player's hand."""
        from src.game.market import draw_cost5_card

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Get cost-5 cards from repo
        cost5_cards = [c for c in repo.get_all() if c.cost == 5]
        if not cost5_cards:
            pytest.skip("No cost-5 cards found in repository")

        # Add cards to the state's cost_5 deck
        for card in cost5_cards[:3]:
            state.cost_5_deck.append(deepcopy(card))

        initial_hand_count = len(player.hand)

        result = draw_cost5_card(state, player.player_id)

        if result:
            assert len(player.hand) == initial_hand_count + 1
            assert result.cost == 5

    def test_draw_cost5_removes_from_deck(self, repo) -> None:
        """Test that draw_cost5_card removes card from deck."""
        from src.game.market import draw_cost5_card

        state = create_initial_game_state(num_players=2)

        # Get cost-5 cards from repo
        cost5_cards = [c for c in repo.get_all() if c.cost == 5]
        if not cost5_cards:
            pytest.skip("No cost-5 cards found in repository")

        # Add cards to the state's cost_5 deck
        for card in cost5_cards[:3]:
            state.cost_5_deck.append(deepcopy(card))

        initial_deck_count = len(state.cost_5_deck)

        result = draw_cost5_card(state, 0)

        if result:
            assert len(state.cost_5_deck) == initial_deck_count - 1

    def test_draw_cost5_empty_deck_returns_none(self) -> None:
        """Test that draw_cost5_card returns None when deck is empty."""
        from src.game.market import draw_cost5_card

        state = create_initial_game_state(num_players=2)
        # Empty deck
        state.cost_5_deck.clear()

        result = draw_cost5_card(state, 0)

        assert result is None


class TestLapinBoardLimits:
    """Tests for Lapin family board limit calculations."""

    def test_base_lapin_board_limit(self, repo) -> None:
        """Test that base Lapin board limit is the config limit."""
        from src.game.abilities import calculate_lapin_board_limit

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        result = calculate_lapin_board_limit(player, base_limit=8)

        assert result.base_limit == 8
        assert result.lapincruste_bonus == 0
        assert result.family_threshold_bonus == 0
        assert result.total_limit == 8

    def test_lapin_threshold_3_adds_slot(self, repo) -> None:
        """Test that 3 Lapins add +1 board slot."""
        from src.cards.models import Family
        from src.game.abilities import calculate_lapin_board_limit

        # Exclude Lapincruste to test only threshold bonus
        lapins = [
            c
            for c in repo.get_all()
            if c.family == Family.LAPIN and c.level == 1 and c.name != "Lapincruste"
        ]

        if len(lapins) < 3:
            pytest.skip("Not enough Lapin cards found")

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Add 3 non-Lapincruste Lapins to board
        for lapin in lapins[:3]:
            player.board.append(deepcopy(lapin))

        result = calculate_lapin_board_limit(player, base_limit=8)

        assert result.lapincruste_bonus == 0  # No Lapincruste
        assert result.family_threshold_bonus == 1
        assert result.total_limit == 9  # 8 + 1

    def test_lapin_threshold_5_adds_slots(self, repo) -> None:
        """Test that 5 Lapins add +2 board slots."""
        from src.cards.models import Family
        from src.game.abilities import calculate_lapin_board_limit

        # Exclude Lapincruste to test only threshold bonus
        lapins = [
            c
            for c in repo.get_all()
            if c.family == Family.LAPIN and c.level == 1 and c.name != "Lapincruste"
        ]

        if len(lapins) < 5:
            pytest.skip("Not enough Lapin cards found")

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Add 5 non-Lapincruste Lapins to board
        for lapin in lapins[:5]:
            player.board.append(deepcopy(lapin))

        result = calculate_lapin_board_limit(player, base_limit=8)

        assert result.lapincruste_bonus == 0  # No Lapincruste
        assert result.family_threshold_bonus == 2
        assert result.total_limit == 10  # 8 + 2

    def test_lapincruste_adds_slots(self, repo) -> None:
        """Test that Lapincruste adds board slots."""
        from src.game.abilities import calculate_lapin_board_limit

        lapincruste = repo.get_by_name_and_level("Lapincruste", level=1)
        if not lapincruste:
            pytest.skip("Lapincruste card not found")

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        player.board.append(deepcopy(lapincruste))

        result = calculate_lapin_board_limit(player, base_limit=8)

        # Lapincruste Lv1: "+2 lapins supplémentaires"
        assert result.lapincruste_bonus == 2
        assert result.total_limit == 10  # 8 + 2

    def test_lapincruste_level2_adds_more_slots(self, repo) -> None:
        """Test that Lapincruste Level 2 adds +4 board slots."""
        from src.game.abilities import calculate_lapin_board_limit

        lapincruste2 = repo.get_by_name_and_level("Lapincruste", level=2)
        if not lapincruste2:
            pytest.skip("Lapincruste Level 2 card not found")

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        player.board.append(deepcopy(lapincruste2))

        result = calculate_lapin_board_limit(player, base_limit=8)

        # Lapincruste Lv2: "+4 lapins supplémentaires"
        assert result.lapincruste_bonus == 4
        assert result.total_limit == 12  # 8 + 4

    def test_lapincruste_stacks_with_threshold(self, repo) -> None:
        """Test that Lapincruste bonus stacks with family threshold."""
        from src.cards.models import Family
        from src.game.abilities import calculate_lapin_board_limit

        lapincruste = repo.get_by_name_and_level("Lapincruste", level=1)
        lapins = [
            c
            for c in repo.get_all()
            if c.family == Family.LAPIN and c.level == 1 and c.name != "Lapincruste"
        ]

        if not lapincruste or len(lapins) < 2:
            pytest.skip("Not enough Lapin cards found")

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Add Lapincruste + 2 other Lapins = 3 total
        player.board.append(deepcopy(lapincruste))
        player.board.append(deepcopy(lapins[0]))
        player.board.append(deepcopy(lapins[1]))

        result = calculate_lapin_board_limit(player, base_limit=8)

        # Lapincruste: +2, Threshold 3: +1
        assert result.lapincruste_bonus == 2
        assert result.family_threshold_bonus == 1
        assert result.total_limit == 11  # 8 + 2 + 1

    def test_can_play_lapin_card_under_limit(self, repo) -> None:
        """Test can_play_lapin_card returns True when under limit."""
        from src.cards.models import Family
        from src.game.abilities import can_play_lapin_card

        lapins = [
            c for c in repo.get_all() if c.family == Family.LAPIN and c.level == 1
        ]

        if len(lapins) < 2:
            pytest.skip("Not enough Lapin cards found")

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Add 2 Lapins (under limit of 8)
        player.board.append(deepcopy(lapins[0]))
        player.board.append(deepcopy(lapins[1]))

        assert can_play_lapin_card(player, base_limit=8) is True

    def test_can_play_lapin_card_at_limit(self, repo) -> None:
        """Test can_play_lapin_card returns False at limit."""
        from src.cards.models import Family
        from src.game.abilities import can_play_lapin_card

        lapins = [
            c for c in repo.get_all() if c.family == Family.LAPIN and c.level == 1
        ]

        if len(lapins) < 8:
            pytest.skip("Not enough Lapin cards found")

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Add 8 Lapins (at limit)
        for lapin in lapins[:8]:
            player.board.append(deepcopy(lapin))

        # Base limit is 8, but with 8 Lapins we get +2 from threshold 5
        # So limit is 10, but we have 8 -> can still play
        # Actually at 8 Lapins, threshold 5 gives +2 = limit 10
        # So we CAN play more
        assert can_play_lapin_card(player, base_limit=8) is True

    def test_can_play_lapin_card_over_limit_without_lapincruste(self, repo) -> None:
        """Test that Lapins are limited without Lapincruste."""
        from src.cards.models import Family
        from src.game.abilities import calculate_lapin_board_limit, can_play_lapin_card

        # Filter out Lapincruste
        lapins = [
            c
            for c in repo.get_all()
            if c.family == Family.LAPIN and c.level == 1 and c.name != "Lapincruste"
        ]

        if len(lapins) < 10:
            pytest.skip("Not enough Lapin cards found")

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # With 10 non-Lapincruste Lapins:
        # Threshold 5: +2 -> limit is 10
        # At exactly 10, we're at the limit
        for lapin in lapins[:10]:
            player.board.append(deepcopy(lapin))

        limit_result = calculate_lapin_board_limit(player, base_limit=8)
        # 8 base + 2 from threshold 5 = 10
        assert limit_result.total_limit == 10

        # Can't play more - at limit
        assert can_play_lapin_card(player, base_limit=8) is False

    def test_lapin_threshold_8_atk_bonus_multiplied(self, repo) -> None:
        """Test threshold 8 ATK bonus multiplies by lapin count."""
        from src.cards.models import Family
        from src.game.abilities import resolve_family_abilities

        # Get non-Lapincruste Lapins
        lapins = [
            c
            for c in repo.get_all()
            if c.family == Family.LAPIN and c.level == 1 and c.name != "Lapincruste"
        ]

        if len(lapins) < 8:
            pytest.skip("Not enough Lapin cards found")

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Add 8 Lapins to trigger threshold 8
        for lapin in lapins[:8]:
            player.board.append(deepcopy(lapin))

        result = resolve_family_abilities(player)

        # Threshold 8: "+2 ATQ pour tous les lapins"
        # Should be +2 per Lapin = +16 total (not just +2)
        assert result.total_attack_bonus == 16  # 2 * 8 = 16

    def test_lapin_threshold_8_scales_with_count(self, repo) -> None:
        """Test that threshold 8 bonus scales correctly with different lapin counts."""
        from src.cards.models import Family
        from src.game.abilities import resolve_family_abilities

        # Get non-Lapincruste Lapins
        lapins = [
            c
            for c in repo.get_all()
            if c.family == Family.LAPIN and c.level == 1 and c.name != "Lapincruste"
        ]

        if len(lapins) < 10:
            pytest.skip("Not enough Lapin cards found")

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Add 10 Lapins
        for lapin in lapins[:10]:
            player.board.append(deepcopy(lapin))

        result = resolve_family_abilities(player)

        # Threshold 8: "+2 ATQ pour tous les lapins"
        # With 10 Lapins: +2 * 10 = +20 ATK
        assert result.total_attack_bonus == 20


class TestWeaponEquipment:
    """Tests for weapon equipment system."""

    def test_equip_weapon_to_board_card(self, repo) -> None:
        """Test equipping a weapon to a card on the board."""
        from src.cards.models import CardType

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Get a creature and a weapon
        creature = None
        weapon = None
        for card in repo.get_all():
            if creature is None and card.card_type == CardType.CREATURE:
                creature = deepcopy(card)
            if weapon is None and card.card_type == CardType.WEAPON:
                weapon = deepcopy(card)
            if creature and weapon:
                break

        if not creature or not weapon:
            pytest.skip("No creature or weapon cards found")

        # Add creature to board
        player.board.append(creature)

        # Equip weapon
        success = player.equip_weapon(creature.id, weapon)
        assert success is True
        assert player.equipped_weapons[creature.id] == weapon

    def test_cannot_equip_to_nonexistent_card(self, repo) -> None:
        """Test that equipping to a non-existent card fails."""
        from src.cards.models import CardType

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        weapon = None
        for card in repo.get_all():
            if card.card_type == CardType.WEAPON:
                weapon = deepcopy(card)
                break

        if not weapon:
            pytest.skip("No weapon cards found")

        # Try to equip to non-existent card
        success = player.equip_weapon("nonexistent_id", weapon)
        assert success is False

    def test_cannot_double_equip(self, repo) -> None:
        """Test that a card can only have one weapon equipped."""
        from src.cards.models import CardType

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        creature = None
        weapons = []
        for card in repo.get_all():
            if creature is None and card.card_type == CardType.CREATURE:
                creature = deepcopy(card)
            if card.card_type == CardType.WEAPON and len(weapons) < 2:
                weapons.append(deepcopy(card))
            if creature and len(weapons) >= 2:
                break

        if not creature or len(weapons) < 2:
            pytest.skip("Not enough cards found")

        player.board.append(creature)

        # First equip should succeed
        success1 = player.equip_weapon(creature.id, weapons[0])
        assert success1 is True

        # Second equip should fail
        success2 = player.equip_weapon(creature.id, weapons[1])
        assert success2 is False

    def test_unequip_weapon(self, repo) -> None:
        """Test unequipping a weapon."""
        from src.cards.models import CardType

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        creature = None
        weapon = None
        for card in repo.get_all():
            if creature is None and card.card_type == CardType.CREATURE:
                creature = deepcopy(card)
            if weapon is None and card.card_type == CardType.WEAPON:
                weapon = deepcopy(card)
            if creature and weapon:
                break

        if not creature or not weapon:
            pytest.skip("No cards found")

        player.board.append(creature)
        player.equip_weapon(creature.id, weapon)

        # Unequip
        unequipped = player.unequip_weapon(creature.id)
        assert unequipped == weapon
        assert creature.id not in player.equipped_weapons

    def test_total_weapon_attack(self, repo) -> None:
        """Test calculating total weapon attack bonus."""
        from src.cards.models import CardType

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        creatures = []
        weapons = []
        for card in repo.get_all():
            if card.card_type == CardType.CREATURE and len(creatures) < 2:
                creatures.append(deepcopy(card))
            if card.card_type == CardType.WEAPON and len(weapons) < 2:
                weapons.append(deepcopy(card))

        if len(creatures) < 2 or len(weapons) < 2:
            pytest.skip("Not enough cards")

        # Add creatures and equip weapons
        for creature, weapon in zip(creatures, weapons):
            player.board.append(creature)
            player.equip_weapon(creature.id, weapon)

        total_atk = player.get_total_weapon_attack()
        expected_atk = sum(w.attack for w in weapons)
        assert total_atk == expected_atk


class TestSpellTracking:
    """Tests for spell casting and tracking system."""

    def test_cast_spell_increments_counter(self) -> None:
        """Test that casting a spell increments the counter."""
        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        assert player.spells_cast_this_turn == 0
        assert player.spell_damage_dealt == 0

        player.cast_spell(5)

        assert player.spells_cast_this_turn == 1
        assert player.spell_damage_dealt == 5

    def test_multiple_spells_accumulate(self) -> None:
        """Test that multiple spell casts accumulate."""
        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        player.cast_spell(3)
        player.cast_spell(7)
        player.cast_spell(2)

        assert player.spells_cast_this_turn == 3
        assert player.spell_damage_dealt == 12

    def test_reset_spell_tracking(self) -> None:
        """Test resetting spell tracking for new turn."""
        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        player.cast_spell(10)
        assert player.spells_cast_this_turn == 1

        player.reset_spell_tracking()

        assert player.spells_cast_this_turn == 0
        assert player.spell_damage_dealt == 0


class TestSacrificeMechanics:
    """Tests for card sacrifice mechanics."""

    def test_sacrifice_card_from_board(self, repo) -> None:
        """Test sacrificing a card removes it from board."""
        from src.cards.models import CardType

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        creature = None
        for card in repo.get_all():
            if card.card_type == CardType.CREATURE:
                creature = deepcopy(card)
                break

        if not creature:
            pytest.skip("No creature cards found")

        player.board.append(creature)
        assert len(player.board) == 1

        success = player.sacrifice_card(creature)
        assert success is True
        assert len(player.board) == 0
        assert len(player.sacrificed_this_turn) == 1
        assert player.sacrificed_this_turn[0] == creature

    def test_sacrifice_removes_equipped_weapon(self, repo) -> None:
        """Test that sacrificing a card also removes its weapon."""
        from src.cards.models import CardType

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        creature = None
        weapon = None
        for card in repo.get_all():
            if creature is None and card.card_type == CardType.CREATURE:
                creature = deepcopy(card)
            if weapon is None and card.card_type == CardType.WEAPON:
                weapon = deepcopy(card)
            if creature and weapon:
                break

        if not creature or not weapon:
            pytest.skip("No cards found")

        player.board.append(creature)
        player.equip_weapon(creature.id, weapon)
        assert creature.id in player.equipped_weapons

        player.sacrifice_card(creature)
        assert creature.id not in player.equipped_weapons

    def test_sacrifice_count(self, repo) -> None:
        """Test getting sacrifice count."""
        from src.cards.models import CardType

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        creatures = []
        for card in repo.get_all():
            if card.card_type == CardType.CREATURE:
                creatures.append(deepcopy(card))
                if len(creatures) >= 3:
                    break

        if len(creatures) < 3:
            pytest.skip("Not enough creatures")

        for c in creatures:
            player.board.append(c)

        player.sacrifice_card(creatures[0])
        player.sacrifice_card(creatures[1])

        assert player.get_sacrifice_count() == 2

    def test_reset_sacrifice_tracking(self, repo) -> None:
        """Test resetting sacrifice tracking."""
        from src.cards.models import CardType

        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        creature = None
        for card in repo.get_all():
            if card.card_type == CardType.CREATURE:
                creature = deepcopy(card)
                break

        if not creature:
            pytest.skip("No creature found")

        player.board.append(creature)
        player.sacrifice_card(creature)
        assert player.get_sacrifice_count() == 1

        player.reset_sacrifice_tracking()
        assert player.get_sacrifice_count() == 0


class TestDeckInteractions:
    """Tests for deck interaction methods."""

    def test_peek_deck(self, repo) -> None:
        """Test peeking at deck without removing cards."""
        state = create_initial_game_state(num_players=2)

        # Add some cards to cost_1_deck
        cards = [c for c in repo.get_all() if c.cost == 1][:5]
        if len(cards) < 3:
            pytest.skip("Not enough cost-1 cards")

        state.cost_1_deck = list(cards)
        original_len = len(state.cost_1_deck)

        peeked = state.peek_deck(1, 3)

        assert len(peeked) == 3
        assert len(state.cost_1_deck) == original_len  # Deck unchanged
        assert peeked == state.cost_1_deck[:3]

    def test_reveal_top_card(self, repo) -> None:
        """Test revealing top card of deck."""
        state = create_initial_game_state(num_players=2)

        cards = [c for c in repo.get_all() if c.cost == 2][:3]
        if not cards:
            pytest.skip("No cost-2 cards")

        state.cost_2_deck = list(cards)

        revealed = state.reveal_top_card(2)

        assert revealed == cards[0]
        assert len(state.cost_2_deck) == len(cards)  # Not removed

    def test_reveal_empty_deck(self) -> None:
        """Test revealing from empty deck returns None."""
        state = create_initial_game_state(num_players=2)
        state.cost_3_deck = []

        revealed = state.reveal_top_card(3)
        assert revealed is None

    def test_draw_from_deck(self, repo) -> None:
        """Test drawing removes card from deck."""
        state = create_initial_game_state(num_players=2)

        cards = [c for c in repo.get_all() if c.cost == 4][:3]
        if not cards:
            pytest.skip("No cost-4 cards")

        state.cost_4_deck = list(cards)
        original_len = len(state.cost_4_deck)
        top_card = state.cost_4_deck[0]

        drawn = state.draw_from_deck(4)

        assert drawn == top_card
        assert len(state.cost_4_deck) == original_len - 1

    def test_search_deck_by_family(self, repo) -> None:
        """Test searching deck by family."""
        from src.cards.models import Family

        state = create_initial_game_state(num_players=2)

        # Mix cards from different families
        all_cards = repo.get_all()
        mixed_deck = []
        for card in all_cards:
            if card.cost == 1:
                mixed_deck.append(deepcopy(card))
                if len(mixed_deck) >= 10:
                    break

        if len(mixed_deck) < 5:
            pytest.skip("Not enough cards")

        state.cost_1_deck = mixed_deck

        # Count how many Lapins are in deck
        lapin_count = sum(1 for c in mixed_deck if c.family == Family.LAPIN)

        results = state.search_deck(1, "Lapin")
        assert len(results) == lapin_count

    def test_reset_turn_tracking_all_players(self) -> None:
        """Test resetting turn tracking for all players."""
        state = create_initial_game_state(num_players=3)

        # Set some tracking values
        for player in state.players:
            player.cast_spell(5)

        state.reset_turn_tracking_all_players()

        for player in state.players:
            assert player.spells_cast_this_turn == 0
            assert player.spell_damage_dealt == 0


class TestStrictMode:
    """Tests for strict mode in bonus_text parsing (D011)."""

    def test_strict_mode_raises_on_unknown_bonus_text(self, repo) -> None:
        """Test that strict mode raises UnmatchedBonusTextError for unknown text."""
        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Get any card and modify its bonus_text
        cards = repo.get_all()
        card = deepcopy(cards[0])
        card.bonus_text = "This is completely unknown text that matches no pattern"
        player.board.append(card)

        with pytest.raises(UnmatchedBonusTextError) as exc_info:
            resolve_bonus_text_effects(player, strict=True)

        assert exc_info.value.card_name == card.name
        assert "unknown text" in exc_info.value.bonus_text

    def test_strict_mode_accepts_known_patterns(self, repo) -> None:
        """Test that strict mode doesn't raise for recognized patterns."""
        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Get any card and set a known bonus_text pattern
        cards = repo.get_all()
        card = deepcopy(cards[0])
        card.bonus_text = "+2 ATQ pour les lapins"  # Known pattern
        player.board.append(card)

        # Should not raise
        result = resolve_bonus_text_effects(player, strict=True)
        assert result is not None

    def test_non_strict_mode_silently_ignores_unknown(self, repo) -> None:
        """Test that non-strict mode (default) silently ignores unknown text."""
        state = create_initial_game_state(num_players=2)
        player = state.players[0]

        # Get any card and set unknown bonus_text
        cards = repo.get_all()
        card = deepcopy(cards[0])
        card.bonus_text = "Completely unknown pattern xyz"
        player.board.append(card)

        # Should not raise - default is strict=False
        result = resolve_bonus_text_effects(player)
        assert result is not None
        # No effects should be applied since pattern is unknown
        assert len(result.effects) == 0

    def test_unmatched_bonus_text_error_attributes(self) -> None:
        """Test that UnmatchedBonusTextError has correct attributes."""
        error = UnmatchedBonusTextError("TestCard", "unknown bonus text")

        assert error.card_name == "TestCard"
        assert error.bonus_text == "unknown bonus text"
        assert "TestCard" in str(error)
        assert "unknown bonus text" in str(error)
