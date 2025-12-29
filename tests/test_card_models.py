"""Tests for card data models.

This module tests the Card, CreatureCard, WeaponCard, and DemonCard models
to ensure they correctly validate and store card data.
"""

import pytest

from src.cards.models import (
    CardClass,
    CardType,
    ClassAbilities,
    ConditionalAbility,
    CreatureCard,
    DemonCard,
    Family,
    FamilyAbilities,
    ScalingAbility,
    WeaponCard,
    create_card_id,
)


class TestScalingAbility:
    """Tests for ScalingAbility dataclass."""

    def test_create_scaling_ability(self) -> None:
        """Test creating a scaling ability."""
        ability = ScalingAbility(threshold=3, effect="+5 damage")
        assert ability.threshold == 3
        assert ability.effect == "+5 damage"

    def test_scaling_ability_is_frozen(self) -> None:
        """Test that scaling ability is immutable."""
        ability = ScalingAbility(threshold=3, effect="+5 damage")
        with pytest.raises(AttributeError):
            ability.threshold = 5  # type: ignore


class TestConditionalAbility:
    """Tests for ConditionalAbility dataclass."""

    def test_create_conditional_ability(self) -> None:
        """Test creating a conditional ability."""
        ability = ConditionalAbility(condition="1 PO", effect="2 dgt imblocable")
        assert ability.condition == "1 PO"
        assert ability.effect == "2 dgt imblocable"


class TestFamilyAbilities:
    """Tests for FamilyAbilities dataclass."""

    def test_empty_family_abilities(self) -> None:
        """Test creating empty family abilities."""
        abilities = FamilyAbilities()
        assert abilities.scaling == []
        assert abilities.passive is None

    def test_family_abilities_with_scaling(self) -> None:
        """Test creating family abilities with scaling."""
        scaling = [
            ScalingAbility(threshold=2, effect="+2 ATQ"),
            ScalingAbility(threshold=4, effect="+4 ATQ"),
        ]
        abilities = FamilyAbilities(scaling=scaling)
        assert len(abilities.scaling) == 2
        assert abilities.scaling[0].threshold == 2

    def test_family_abilities_with_passive(self) -> None:
        """Test creating family abilities with passive."""
        abilities = FamilyAbilities(passive="Un seul demon peut apparaitre")
        assert abilities.passive == "Un seul demon peut apparaitre"


class TestClassAbilities:
    """Tests for ClassAbilities dataclass."""

    def test_empty_class_abilities(self) -> None:
        """Test creating empty class abilities."""
        abilities = ClassAbilities()
        assert abilities.scaling == []
        assert abilities.conditional == []
        assert abilities.passive is None

    def test_class_abilities_with_conditional(self) -> None:
        """Test creating class abilities with conditional effects."""
        conditional = [
            ConditionalAbility(condition="1 PO", effect="2 dgt imblocable"),
            ConditionalAbility(condition="2 PO", effect="3 dgt imblocable"),
        ]
        abilities = ClassAbilities(conditional=conditional)
        assert len(abilities.conditional) == 2


class TestCreatureCard:
    """Tests for CreatureCard dataclass."""

    def test_create_valid_creature(self) -> None:
        """Test creating a valid creature card."""
        card = CreatureCard(
            id="cyborg_lolo_le_gorille_1",
            name="Lolo le gorille",
            card_type=CardType.CREATURE,
            level=1,
            movement=1,
            family=Family.CYBORG,
            card_class=CardClass.BERSEKER,
            family_abilities=FamilyAbilities(),
            class_abilities=ClassAbilities(),
            bonus_text="+4 ATQ si raccoon familly 2",
            health=3,
            attack=0,
            image_path="Cyborg lvl 1/Lolo le gorille.png",
        )
        assert card.name == "Lolo le gorille"
        assert card.level == 1
        assert card.family == Family.CYBORG
        assert card.health == 3

    def test_creature_invalid_type(self) -> None:
        """Test that creature card must have CREATURE type."""
        with pytest.raises(
            ValueError, match="CreatureCard must have card_type CREATURE"
        ):
            CreatureCard(
                id="test",
                name="Test",
                card_type=CardType.WEAPON,
                level=1,
                movement=1,
                family=Family.CYBORG,
                card_class=CardClass.BERSEKER,
                family_abilities=FamilyAbilities(),
                class_abilities=ClassAbilities(),
                bonus_text=None,
                health=1,
                attack=1,
                image_path="test.png",
            )

    def test_creature_invalid_level_none(self) -> None:
        """Test that creature card must have a level."""
        with pytest.raises(ValueError, match="CreatureCard level must be 1-5"):
            CreatureCard(
                id="test",
                name="Test",
                card_type=CardType.CREATURE,
                level=None,
                movement=1,
                family=Family.CYBORG,
                card_class=CardClass.BERSEKER,
                family_abilities=FamilyAbilities(),
                class_abilities=ClassAbilities(),
                bonus_text=None,
                health=1,
                attack=1,
                image_path="test.png",
            )

    def test_creature_invalid_level_out_of_range(self) -> None:
        """Test that creature card level must be 1-5."""
        with pytest.raises(ValueError, match="CreatureCard level must be 1-5"):
            CreatureCard(
                id="test",
                name="Test",
                card_type=CardType.CREATURE,
                level=6,
                movement=1,
                family=Family.CYBORG,
                card_class=CardClass.BERSEKER,
                family_abilities=FamilyAbilities(),
                class_abilities=ClassAbilities(),
                bonus_text=None,
                health=1,
                attack=1,
                image_path="test.png",
            )


class TestWeaponCard:
    """Tests for WeaponCard dataclass."""

    def test_create_valid_weapon(self) -> None:
        """Test creating a valid weapon card."""
        card = WeaponCard(
            id="arme_hache_runique",
            name="Hache Runique",
            card_type=CardType.WEAPON,
            level=None,
            movement=1,
            family=Family.ARME,
            card_class=CardClass.ARME,
            family_abilities=FamilyAbilities(passive="Equip restriction"),
            class_abilities=ClassAbilities(),
            bonus_text="Ajoute l'ATQ au monstre equipe",
            health=1,
            attack=5,
            image_path="Hache runique.png",
            equip_restriction="n'importe quel monstre",
        )
        assert card.name == "Hache Runique"
        assert card.level is None
        assert card.equip_restriction == "n'importe quel monstre"

    def test_weapon_invalid_type(self) -> None:
        """Test that weapon card must have WEAPON type."""
        with pytest.raises(ValueError, match="WeaponCard must have card_type WEAPON"):
            WeaponCard(
                id="test",
                name="Test",
                card_type=CardType.CREATURE,
                level=None,
                movement=1,
                family=Family.ARME,
                card_class=CardClass.ARME,
                family_abilities=FamilyAbilities(),
                class_abilities=ClassAbilities(),
                bonus_text=None,
                health=1,
                attack=1,
                image_path="test.png",
            )

    def test_weapon_invalid_family(self) -> None:
        """Test that weapon card must have ARME family."""
        with pytest.raises(ValueError, match="WeaponCard must have family ARME"):
            WeaponCard(
                id="test",
                name="Test",
                card_type=CardType.WEAPON,
                level=None,
                movement=1,
                family=Family.CYBORG,
                card_class=CardClass.ARME,
                family_abilities=FamilyAbilities(),
                class_abilities=ClassAbilities(),
                bonus_text=None,
                health=1,
                attack=1,
                image_path="test.png",
            )


class TestDemonCard:
    """Tests for DemonCard dataclass."""

    def test_create_valid_demon(self) -> None:
        """Test creating a valid demon card."""
        card = DemonCard(
            id="demon_demon_majeur",
            name="Demon Majeur",
            card_type=CardType.DEMON,
            level=None,
            movement=1,
            family=Family.DEMON,
            card_class=CardClass.DEMON,
            family_abilities=FamilyAbilities(),
            class_abilities=ClassAbilities(),
            bonus_text="10 dgt imblocable",
            health=10,
            attack=10,
            image_path="Demon Majeur.png",
            summon_cost=6,
        )
        assert card.name == "Demon Majeur"
        assert card.summon_cost == 6

    def test_demon_invalid_type(self) -> None:
        """Test that demon card must have DEMON type."""
        with pytest.raises(ValueError, match="DemonCard must have card_type DEMON"):
            DemonCard(
                id="test",
                name="Test",
                card_type=CardType.CREATURE,
                level=None,
                movement=1,
                family=Family.DEMON,
                card_class=CardClass.DEMON,
                family_abilities=FamilyAbilities(),
                class_abilities=ClassAbilities(),
                bonus_text=None,
                health=1,
                attack=1,
                image_path="test.png",
            )


class TestCreateCardId:
    """Tests for create_card_id function."""

    def test_simple_name(self) -> None:
        """Test generating ID for simple name."""
        card_id = create_card_id(Family.CYBORG, "Test Card", level=1)
        assert card_id == "cyborg_test_card_1"

    def test_name_with_accents(self) -> None:
        """Test generating ID with French accents."""
        card_id = create_card_id(Family.NATURE, "Ancien de la nature", level=1)
        assert card_id == "nature_ancien_de_la_nature_1"

    def test_name_with_special_chars(self) -> None:
        """Test generating ID with special characters."""
        card_id = create_card_id(Family.ATLANTIDE, "Archère des flots", level=1)
        assert card_id == "atlantide_archere_des_flots_1"

    def test_weapon_without_level(self) -> None:
        """Test generating ID for weapon without level."""
        card_id = create_card_id(Family.ARME, "Hache Runique")
        assert card_id == "arme_hache_runique"

    def test_hall_of_win_family(self) -> None:
        """Test generating ID for Hall of win family."""
        card_id = create_card_id(Family.HALL_OF_WIN, "Chevalier", level=1)
        assert card_id == "hall_of_win_chevalier_1"


class TestEnums:
    """Tests for enum classes."""

    def test_family_values(self) -> None:
        """Test that all expected families exist."""
        families = {f.value for f in Family}
        assert "Cyborg" in families
        assert "Nature" in families
        assert "Atlantide" in families
        assert "Ninja" in families
        assert "Neige" in families
        assert "Lapin" in families
        assert "Raton" in families
        assert "Hall of win" in families
        assert "Arme" in families
        assert "Demon" in families or "Démon" in families  # Handle accented version

    def test_card_class_values(self) -> None:
        """Test that all expected classes exist."""
        classes = {c.value for c in CardClass}
        assert "Archer" in classes
        assert "Berseker" in classes
        assert "Combattant" in classes
        assert (
            "Defenseur" in classes or "Défenseur" in classes
        )  # Handle accented version
        assert "Dragon" in classes
        assert "Invocateur" in classes
        assert "Mage" in classes
        assert "Monture" in classes
        assert "S-Team" in classes
        assert "Arme" in classes
        assert "Demon" in classes or "Démon" in classes  # Handle accented version

    def test_card_type_values(self) -> None:
        """Test that all expected card types exist."""
        types = {t.value for t in CardType}
        assert "creature" in types
        assert "weapon" in types
        assert "demon" in types
