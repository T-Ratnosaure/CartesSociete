"""Card repository for loading and accessing card data.

This module provides functions to load card data from JSON files and
query cards by various criteria.
"""

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from .models import (
    Card,
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
)

logger = logging.getLogger(__name__)

# Pre-compiled regex patterns for imblocable damage extraction
_IMBLOCABLE_PATTERN = re.compile(r"(\d+)\s*(?:dgt|dgts|damage)?\s*imblocable")
_IMBLOCABLE_REVERSE_PATTERN = re.compile(r"imblocable\s*(\d+)")

# Pattern for per-turn self-damage: "Vous perdez X PV ... par tour"
_PER_TURN_SELF_DMG_PATTERN = re.compile(
    r"(?:vous\s+)?perd(?:ez|s)?\s+(\d+)\s*(?:PV|pv|HP).*?par\s+tour",
    re.IGNORECASE,
)


@dataclass
class CardLoadError:
    """Represents an error that occurred while loading a card file."""

    file_path: str
    error: str


def _parse_scaling_abilities(data: list[dict]) -> list[ScalingAbility]:
    """Parse scaling abilities from JSON data."""
    return [
        ScalingAbility(threshold=item["threshold"], effect=item["effect"])
        for item in data
    ]


def _parse_conditional_abilities(data: list[dict]) -> list[ConditionalAbility]:
    """Parse conditional abilities from JSON data."""
    return [
        ConditionalAbility(condition=item["condition"], effect=item["effect"])
        for item in data
    ]


def _parse_family_abilities(data: dict) -> FamilyAbilities:
    """Parse family abilities from JSON data."""
    return FamilyAbilities(
        scaling=_parse_scaling_abilities(data.get("scaling", [])),
        passive=data.get("passive"),
    )


def _extract_imblocable_damage(conditional: list[ConditionalAbility]) -> int:
    """Extract imblocable damage value from conditional abilities.

    Parses conditional abilities looking for "imblocable" effects and
    extracts the damage value.

    Args:
        conditional: List of conditional abilities to parse.

    Returns:
        Total imblocable damage from all abilities.
    """
    total = 0
    for ability in conditional:
        effect_lower = ability.effect.lower()
        if "imblocable" in effect_lower:
            # Look for patterns like "2 dgt imblocable" or "imblocable 2"
            match = _IMBLOCABLE_PATTERN.search(effect_lower)
            if match:
                total += int(match.group(1))
            else:
                # Try reverse pattern: "imblocable 2 dgt"
                match = _IMBLOCABLE_REVERSE_PATTERN.search(effect_lower)
                if match:
                    total += int(match.group(1))
    return total


def _extract_per_turn_self_damage(bonus_text: str | None) -> int:
    """Extract per-turn self-damage from bonus text.

    Parses bonus_text looking for patterns like "Vous perdez X PV ... par tour".

    Args:
        bonus_text: The bonus text to parse (can be None).

    Returns:
        Per-turn self-damage amount, or 0 if not found.
    """
    if not bonus_text:
        return 0

    match = _PER_TURN_SELF_DMG_PATTERN.search(bonus_text)
    if match:
        return int(match.group(1))
    return 0


def _parse_class_abilities(
    data: dict,
    bonus_text: str | None = None,
) -> ClassAbilities:
    """Parse class abilities from JSON data.

    Args:
        data: Dictionary containing class abilities data.
        bonus_text: Optional bonus text to extract per-turn effects from.

    Returns:
        ClassAbilities instance with all parsed data.
    """
    conditional = _parse_conditional_abilities(data.get("conditional", []))
    imblocable = _extract_imblocable_damage(conditional)
    per_turn_self_dmg = _extract_per_turn_self_damage(bonus_text)

    return ClassAbilities(
        scaling=_parse_scaling_abilities(data.get("scaling", [])),
        conditional=conditional,
        passive=data.get("passive"),
        imblocable_damage=imblocable,
        per_turn_self_damage=per_turn_self_dmg,
    )


def _parse_card(data: dict) -> Card:
    """Parse a card from JSON data.

    Args:
        data: Dictionary containing card data.

    Returns:
        A Card instance (CreatureCard, WeaponCard, or DemonCard).

    Raises:
        ValueError: If the card data is invalid.
    """
    card_type = CardType(data["card_type"])
    family = Family(data["family"])
    card_class = CardClass(data["card_class"])
    bonus_text = data.get("bonus_text")

    base_kwargs = {
        "id": data["id"],
        "name": data["name"],
        "card_type": card_type,
        "cost": data.get("cost"),
        "level": data["level"],
        "family": family,
        "card_class": card_class,
        "family_abilities": _parse_family_abilities(data.get("family_abilities", {})),
        "class_abilities": _parse_class_abilities(
            data.get("class_abilities", {}),
            bonus_text,
        ),
        "bonus_text": bonus_text,
        "health": data["health"],
        "attack": data["attack"],
        "image_path": data["image_path"],
    }

    if card_type == CardType.CREATURE:
        return CreatureCard(**base_kwargs)
    elif card_type == CardType.WEAPON:
        return WeaponCard(
            **base_kwargs,
            equip_restriction=data.get("equip_restriction"),
        )
    elif card_type == CardType.DEMON:
        return DemonCard(
            **base_kwargs,
            summon_cost=data.get("summon_cost"),
        )
    else:
        raise ValueError(f"Unknown card type: {card_type}")


class CardRepository:
    """Repository for loading and querying card data.

    This class loads card data from JSON files and provides methods
    to query cards by various criteria.
    """

    # Files to skip when loading card data
    SKIP_FILES = frozenset(
        {
            "schema",
            "index",
            "missing_cards_template",
        }
    )

    # Prefixes to skip (templates, backups, drafts)
    SKIP_PREFIXES = ("_", "template", "backup", "draft")

    def __init__(self, data_dir: Path | None = None) -> None:
        """Initialize the repository.

        Args:
            data_dir: Path to the data/cards directory. If None, uses default location.
        """
        if data_dir is None:
            # Default to project's data/cards directory
            data_dir = Path(__file__).parent.parent.parent / "data" / "cards"
        self.data_dir = Path(data_dir)
        self._cards: dict[str, Card] = {}
        self._loaded = False
        self._load_errors: list[CardLoadError] = []

    def _should_skip_file(self, json_file: Path) -> bool:
        """Check if a file should be skipped during loading.

        Args:
            json_file: The file path to check.

        Returns:
            True if the file should be skipped.
        """
        stem = json_file.stem.lower()

        # Skip files in the explicit skip list
        if stem in self.SKIP_FILES:
            return True

        # Skip files starting with skip prefixes
        for prefix in self.SKIP_PREFIXES:
            if stem.startswith(prefix):
                return True

        # Skip files containing "template" anywhere in the name
        if "template" in stem:
            return True

        return False

    def load(self) -> None:
        """Load all card data from JSON files.

        Files are skipped if they match skip patterns (templates, schemas, etc.).
        Errors in individual files are logged but don't prevent loading other files.

        Raises:
            FileNotFoundError: If the data directory doesn't exist.
        """
        if self._loaded:
            return

        self._cards.clear()
        self._load_errors.clear()

        # Load all JSON files in the data directory
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Card data directory not found: {self.data_dir}")

        for json_file in self.data_dir.glob("**/*.json"):
            # Skip non-card files
            if self._should_skip_file(json_file):
                logger.debug(f"Skipping non-card file: {json_file}")
                continue

            try:
                self._load_file(json_file)
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                error = CardLoadError(file_path=str(json_file), error=str(e))
                self._load_errors.append(error)
                logger.warning(f"Failed to load {json_file}: {e}")
                continue

        if self._load_errors:
            logger.warning(
                f"Completed loading with {len(self._load_errors)} errors. "
                f"Successfully loaded {len(self._cards)} cards."
            )

        self._loaded = True

    def _load_file(self, json_file: Path) -> None:
        """Load cards from a single JSON file.

        Args:
            json_file: Path to the JSON file.

        Raises:
            json.JSONDecodeError: If the file contains invalid JSON.
            ValueError: If the card data is invalid.
            KeyError: If required fields are missing.
        """
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)

        # Handle both single card and list of cards
        if isinstance(data, list):
            for card_data in data:
                self._add_card(card_data, json_file)
        elif isinstance(data, dict) and "card_type" in data:
            # Single card object
            self._add_card(data, json_file)
        # Skip other JSON structures (schemas, etc.)

    def _add_card(self, card_data: dict, source_file: Path) -> None:
        """Add a card to the repository, checking for duplicates.

        Args:
            card_data: Dictionary containing card data.
            source_file: The file the card came from (for error messages).

        Raises:
            ValueError: If a card with the same ID already exists.
        """
        card = _parse_card(card_data)

        # Check for duplicate IDs
        if card.id in self._cards:
            raise ValueError(
                f"Duplicate card ID '{card.id}' in {source_file}. "
                f"First occurrence was in another file."
            )

        self._cards[card.id] = card

    @property
    def load_errors(self) -> list[CardLoadError]:
        """Get the list of errors that occurred during loading.

        Returns:
            List of CardLoadError instances.
        """
        return self._load_errors.copy()

    def get(self, card_id: str) -> Card | None:
        """Get a card by its ID.

        Args:
            card_id: The unique card identifier.

        Returns:
            The card if found, None otherwise.
        """
        if not self._loaded:
            self.load()
        return self._cards.get(card_id)

    def get_all(self) -> list[Card]:
        """Get all cards.

        Returns:
            List of all cards in the repository.
        """
        if not self._loaded:
            self.load()
        return list(self._cards.values())

    def get_by_family(self, family: Family) -> list[Card]:
        """Get all cards of a specific family.

        Args:
            family: The family to filter by.

        Returns:
            List of cards belonging to the specified family.
        """
        if not self._loaded:
            self.load()
        return [card for card in self._cards.values() if card.family == family]

    def get_by_class(self, card_class: CardClass) -> list[Card]:
        """Get all cards of a specific class.

        Args:
            card_class: The class to filter by.

        Returns:
            List of cards belonging to the specified class.
        """
        if not self._loaded:
            self.load()
        return [card for card in self._cards.values() if card.card_class == card_class]

    def get_by_level(self, level: int) -> list[Card]:
        """Get all cards of a specific tier/level.

        Args:
            level: The card tier to filter by (1 or 2).

        Returns:
            List of cards at the specified tier.
        """
        if not self._loaded:
            self.load()
        return [card for card in self._cards.values() if card.level == level]

    def get_by_cost(self, cost: int) -> list[Card]:
        """Get all cards of a specific cost.

        Args:
            cost: The cost to filter by (1-5 for creatures).

        Returns:
            List of cards with the specified cost.
        """
        if not self._loaded:
            self.load()
        return [card for card in self._cards.values() if card.cost == cost]

    def get_by_type(self, card_type: CardType) -> list[Card]:
        """Get all cards of a specific type.

        Args:
            card_type: The type to filter by.

        Returns:
            List of cards of the specified type.
        """
        if not self._loaded:
            self.load()
        return [card for card in self._cards.values() if card.card_type == card_type]

    def get_creatures(self) -> list[CreatureCard]:
        """Get all creature cards.

        Returns:
            List of all creature cards.
        """
        return [
            card
            for card in self.get_by_type(CardType.CREATURE)
            if isinstance(card, CreatureCard)
        ]

    def get_weapons(self) -> list[WeaponCard]:
        """Get all weapon cards.

        Returns:
            List of all weapon cards.
        """
        return [
            card
            for card in self.get_by_type(CardType.WEAPON)
            if isinstance(card, WeaponCard)
        ]

    def get_demons(self) -> list[DemonCard]:
        """Get all demon cards.

        Returns:
            List of all demon cards.
        """
        return [
            card
            for card in self.get_by_type(CardType.DEMON)
            if isinstance(card, DemonCard)
        ]

    def get_by_name_and_level(self, name: str, level: int) -> Card | None:
        """Get a card by exact name and level for evolution lookup.

        Args:
            name: Exact card name to match.
            level: The card level (1 or 2).

        Returns:
            The matching card, or None if not found.
        """
        if not self._loaded:
            self.load()
        for card in self._cards.values():
            if card.name == name and card.level == level:
                return card
        return None

    def search(
        self,
        name: str | None = None,
        family: Family | None = None,
        card_class: CardClass | None = None,
        cost: int | None = None,
        level: int | None = None,
        card_type: CardType | None = None,
        min_health: int | None = None,
        max_health: int | None = None,
        min_attack: int | None = None,
        max_attack: int | None = None,
    ) -> list[Card]:
        """Search for cards matching multiple criteria.

        Args:
            name: Partial name match (case-insensitive).
            family: Filter by family.
            card_class: Filter by class.
            cost: Filter by cost (1-5 for creatures).
            level: Filter by tier/level (1 or 2).
            card_type: Filter by card type.
            min_health: Minimum health.
            max_health: Maximum health.
            min_attack: Minimum attack.
            max_attack: Maximum attack.

        Returns:
            List of cards matching all specified criteria.
        """
        if not self._loaded:
            self.load()

        results = list(self._cards.values())

        if name is not None:
            name_lower = name.lower()
            results = [c for c in results if name_lower in c.name.lower()]

        if family is not None:
            results = [c for c in results if c.family == family]

        if card_class is not None:
            results = [c for c in results if c.card_class == card_class]

        if cost is not None:
            results = [c for c in results if c.cost == cost]

        if level is not None:
            results = [c for c in results if c.level == level]

        if card_type is not None:
            results = [c for c in results if c.card_type == card_type]

        if min_health is not None:
            results = [c for c in results if c.health >= min_health]

        if max_health is not None:
            results = [c for c in results if c.health <= max_health]

        if min_attack is not None:
            results = [c for c in results if c.attack >= min_attack]

        if max_attack is not None:
            results = [c for c in results if c.attack <= max_attack]

        return results


# Global repository instance for convenience
_default_repository: CardRepository | None = None


def get_repository() -> CardRepository:
    """Get the default card repository.

    Returns:
        The singleton CardRepository instance.
    """
    global _default_repository
    if _default_repository is None:
        _default_repository = CardRepository()
    return _default_repository


def reset_repository() -> None:
    """Reset the default repository singleton.

    This is primarily useful for testing to ensure a clean state.
    """
    global _default_repository
    _default_repository = None
