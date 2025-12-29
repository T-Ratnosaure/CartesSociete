"""Tests for card repository.

This module tests the CardRepository class for loading and querying card data.
"""

import json
from pathlib import Path

import pytest

from src.cards.models import CardClass, CardType, Family
from src.cards.repository import CardRepository


@pytest.fixture
def sample_card_data() -> list[dict]:
    """Create sample card data for testing."""
    return [
        {
            "id": "cyborg_test_creature_1",
            "name": "Test Creature",
            "card_type": "creature",
            "level": 1,
            "movement": 1,
            "family": "Cyborg",
            "card_class": "Berseker",
            "family_abilities": {
                "scaling": [{"threshold": 3, "effect": "test effect"}]
            },
            "class_abilities": {"scaling": [{"threshold": 2, "effect": "+5 dgt"}]},
            "bonus_text": "Test bonus",
            "health": 5,
            "attack": 3,
            "image_path": "test.png",
        },
        {
            "id": "cyborg_test_creature_2",
            "name": "Test Creature 2",
            "card_type": "creature",
            "level": 2,
            "movement": 2,
            "family": "Cyborg",
            "card_class": "Dragon",
            "family_abilities": {},
            "class_abilities": {
                "conditional": [{"condition": "1 PO", "effect": "2 dgt"}]
            },
            "bonus_text": None,
            "health": 8,
            "attack": 6,
            "image_path": "test2.png",
        },
        {
            "id": "arme_test_weapon",
            "name": "Test Weapon",
            "card_type": "weapon",
            "level": None,
            "movement": 1,
            "family": "Arme",
            "card_class": "Arme",
            "family_abilities": {"passive": "Can equip"},
            "class_abilities": {},
            "bonus_text": None,
            "health": 1,
            "attack": 4,
            "image_path": "weapon.png",
            "equip_restriction": "any",
        },
        {
            "id": "demon_test_demon",
            "name": "Test Demon",
            "card_type": "demon",
            "level": None,
            "movement": 1,
            "family": "Démon",
            "card_class": "Démon",
            "family_abilities": {"passive": "Only one"},
            "class_abilities": {},
            "bonus_text": None,
            "health": 10,
            "attack": 10,
            "image_path": "demon.png",
            "summon_cost": 6,
        },
    ]


@pytest.fixture
def temp_data_dir(sample_card_data: list[dict], tmp_path: Path) -> Path:
    """Create a temporary data directory with sample cards."""
    data_path = tmp_path / "cards"
    data_path.mkdir()

    # Write sample data
    with open(data_path / "test_cards.json", "w", encoding="utf-8") as f:
        json.dump(sample_card_data, f, ensure_ascii=False)

    return data_path


class TestCardRepository:
    """Tests for CardRepository class."""

    def test_load_cards(self, temp_data_dir: Path) -> None:
        """Test loading cards from JSON files."""
        repo = CardRepository(temp_data_dir)
        repo.load()

        cards = repo.get_all()
        assert len(cards) == 4

    def test_get_by_id(self, temp_data_dir: Path) -> None:
        """Test getting a card by ID."""
        repo = CardRepository(temp_data_dir)
        repo.load()

        card = repo.get("cyborg_test_creature_1")
        assert card is not None
        assert card.name == "Test Creature"
        assert card.health == 5

    def test_get_nonexistent(self, temp_data_dir: Path) -> None:
        """Test getting a nonexistent card returns None."""
        repo = CardRepository(temp_data_dir)
        repo.load()

        card = repo.get("nonexistent")
        assert card is None

    def test_get_by_family(self, temp_data_dir: Path) -> None:
        """Test filtering cards by family."""
        repo = CardRepository(temp_data_dir)
        repo.load()

        cyborg_cards = repo.get_by_family(Family.CYBORG)
        assert len(cyborg_cards) == 2

        arme_cards = repo.get_by_family(Family.ARME)
        assert len(arme_cards) == 1

    def test_get_by_class(self, temp_data_dir: Path) -> None:
        """Test filtering cards by class."""
        repo = CardRepository(temp_data_dir)
        repo.load()

        berseker_cards = repo.get_by_class(CardClass.BERSEKER)
        assert len(berseker_cards) == 1

        dragon_cards = repo.get_by_class(CardClass.DRAGON)
        assert len(dragon_cards) == 1

    def test_get_by_level(self, temp_data_dir: Path) -> None:
        """Test filtering cards by level."""
        repo = CardRepository(temp_data_dir)
        repo.load()

        level1_cards = repo.get_by_level(1)
        assert len(level1_cards) == 1

        level2_cards = repo.get_by_level(2)
        assert len(level2_cards) == 1

    def test_get_by_type(self, temp_data_dir: Path) -> None:
        """Test filtering cards by type."""
        repo = CardRepository(temp_data_dir)
        repo.load()

        creatures = repo.get_by_type(CardType.CREATURE)
        assert len(creatures) == 2

        weapons = repo.get_by_type(CardType.WEAPON)
        assert len(weapons) == 1

        demons = repo.get_by_type(CardType.DEMON)
        assert len(demons) == 1

    def test_get_creatures(self, temp_data_dir: Path) -> None:
        """Test getting all creature cards."""
        repo = CardRepository(temp_data_dir)
        repo.load()

        creatures = repo.get_creatures()
        assert len(creatures) == 2
        assert all(c.card_type == CardType.CREATURE for c in creatures)

    def test_get_weapons(self, temp_data_dir: Path) -> None:
        """Test getting all weapon cards."""
        repo = CardRepository(temp_data_dir)
        repo.load()

        weapons = repo.get_weapons()
        assert len(weapons) == 1
        assert weapons[0].name == "Test Weapon"

    def test_get_demons(self, temp_data_dir: Path) -> None:
        """Test getting all demon cards."""
        repo = CardRepository(temp_data_dir)
        repo.load()

        demons = repo.get_demons()
        assert len(demons) == 1
        assert demons[0].name == "Test Demon"

    def test_search_by_name(self, temp_data_dir: Path) -> None:
        """Test searching cards by partial name."""
        repo = CardRepository(temp_data_dir)
        repo.load()

        results = repo.search(name="creature")
        assert len(results) == 2

        results = repo.search(name="CREATURE")  # Case insensitive
        assert len(results) == 2

    def test_search_multiple_criteria(self, temp_data_dir: Path) -> None:
        """Test searching with multiple criteria."""
        repo = CardRepository(temp_data_dir)
        repo.load()

        results = repo.search(
            family=Family.CYBORG,
            level=1,
        )
        assert len(results) == 1
        assert results[0].name == "Test Creature"

    def test_search_by_stats(self, temp_data_dir: Path) -> None:
        """Test searching by stat ranges."""
        repo = CardRepository(temp_data_dir)
        repo.load()

        # High attack cards
        results = repo.search(min_attack=6)
        assert len(results) == 2  # level 2 creature and demon

        # Low health cards
        results = repo.search(max_health=5)
        assert len(results) == 2  # level 1 creature and weapon

    def test_lazy_loading(self, temp_data_dir: Path) -> None:
        """Test that repository loads data lazily."""
        repo = CardRepository(temp_data_dir)

        # Should not be loaded yet
        assert not repo._loaded

        # This should trigger loading
        cards = repo.get_all()
        assert repo._loaded
        assert len(cards) == 4

    def test_nonexistent_directory(self) -> None:
        """Test loading from nonexistent directory raises error."""
        repo = CardRepository(Path("/nonexistent/path"))

        with pytest.raises(FileNotFoundError):
            repo.load()


class TestCardRepositoryAbilities:
    """Tests for card abilities parsing."""

    def test_scaling_abilities_parsed(self, temp_data_dir: Path) -> None:
        """Test that scaling abilities are correctly parsed."""
        repo = CardRepository(temp_data_dir)
        repo.load()

        card = repo.get("cyborg_test_creature_1")
        assert card is not None
        assert len(card.family_abilities.scaling) == 1
        assert card.family_abilities.scaling[0].threshold == 3
        assert card.family_abilities.scaling[0].effect == "test effect"

    def test_conditional_abilities_parsed(self, temp_data_dir: Path) -> None:
        """Test that conditional abilities are correctly parsed."""
        repo = CardRepository(temp_data_dir)
        repo.load()

        card = repo.get("cyborg_test_creature_2")
        assert card is not None
        assert len(card.class_abilities.conditional) == 1
        assert card.class_abilities.conditional[0].condition == "1 PO"
        assert card.class_abilities.conditional[0].effect == "2 dgt"

    def test_passive_abilities_parsed(self, temp_data_dir: Path) -> None:
        """Test that passive abilities are correctly parsed."""
        repo = CardRepository(temp_data_dir)
        repo.load()

        weapon = repo.get("arme_test_weapon")
        assert weapon is not None
        assert weapon.family_abilities.passive == "Can equip"
