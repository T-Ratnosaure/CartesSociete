"""Card data models for CartesSociete.

This module defines the core data structures for representing cards in the game,
including creatures, weapons, and demons. All models use dataclasses with full
type hints for type safety and IDE support.
"""

import unicodedata
from dataclasses import dataclass, field
from enum import Enum


class Family(Enum):
    """Card families representing different factions in the game."""

    CYBORG = "Cyborg"
    NATURE = "Nature"
    ATLANTIDE = "Atlantide"
    NINJA = "Ninja"
    NEIGE = "Neige"
    LAPIN = "Lapin"
    RATON = "Raton"
    HALL_OF_WIN = "Hall of win"
    ARME = "Arme"
    DEMON = "Démon"


class CardClass(Enum):
    """Card classes representing different roles/archetypes."""

    ARCHER = "Archer"
    BERSEKER = "Berseker"
    COMBATTANT = "Combattant"
    DEFENSEUR = "Défenseur"
    DIPLO = "Diplo"
    DRAGON = "Dragon"
    ECONOME = "Econome"
    ENVOUTEUR = "Envouteur"
    FORGERON = "Forgeron"
    INVOCATEUR = "Invocateur"
    MAGE = "Mage"
    MONTURE = "Monture"
    PROTECTEUR = "Protecteur"
    S_TEAM = "S-Team"
    ARME = "Arme"
    DEMON = "Démon"


class CardType(Enum):
    """Types of cards in the game."""

    CREATURE = "creature"
    WEAPON = "weapon"
    DEMON = "demon"


class Gender(Enum):
    """Gender of card characters for Women family bonus calculation.

    Used by cards with "+X ATQ pour les femmes [family]" bonus text.
    """

    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"  # Default for cards without specified gender


@dataclass(frozen=True)
class ScalingAbility:
    """An ability that scales with the number of family/class members.

    Attributes:
        threshold: The number required to activate this tier.
        effect: Description of the effect at this tier.
    """

    threshold: int
    effect: str


@dataclass(frozen=True)
class ConditionalAbility:
    """An ability that triggers under specific conditions.

    Attributes:
        condition: The condition that must be met (e.g., "1 PO" for 1 action point).
        effect: Description of the effect when condition is met.
    """

    condition: str
    effect: str


@dataclass
class FamilyAbilities:
    """Abilities granted by a card's family affiliation.

    Family abilities typically scale with the number of family members on the board.
    Common thresholds are 2, 3, 4, 5, 6, 8.
    """

    scaling: list[ScalingAbility] = field(default_factory=list)
    passive: str | None = None


@dataclass
class ClassAbilities:
    """Abilities granted by a card's class.

    Class abilities can be scaling (based on class count) or conditional
    (based on action points, board state, etc.).

    Attributes:
        scaling: Abilities that scale with class count.
        conditional: Abilities that trigger on conditions.
        passive: Always-active passive ability text.
        imblocable_damage: Fixed imblocable damage dealt (bypasses defense).
        per_turn_self_damage: Damage dealt to self each turn (from bonus_text).
    """

    scaling: list[ScalingAbility] = field(default_factory=list)
    conditional: list[ConditionalAbility] = field(default_factory=list)
    passive: str | None = None
    imblocable_damage: int = 0  # Structured field for imblocable damage
    per_turn_self_damage: int = 0  # Self-damage applied each turn


@dataclass
class Card:
    """Base class for all cards in the game.

    Attributes:
        id: Unique identifier for the card (e.g., "cyborg_lolo_le_gorille").
        name: Display name of the card.
        card_type: Type of card (creature, weapon, demon).
        cost: Card cost to play (1-5 for creatures, None for weapons/demons).
        level: Card tier (1 or 2, indicates Level 1 or Level 2 version).
        family: Card's family affiliation.
        card_class: Card's class/role.
        family_abilities: Abilities from family.
        class_abilities: Abilities from class.
        bonus_text: Special bonus effect text.
        health: Health points (PV).
        attack: Attack points (ATQ).
        image_path: Relative path to the card image file.
        gender: Gender of the card character (for Women family bonus).
    """

    id: str
    name: str
    card_type: CardType
    cost: int | None  # None for X-cost cards (weapons, demons)
    level: int  # 1 or 2 (card tier)
    family: Family
    card_class: CardClass
    family_abilities: FamilyAbilities
    class_abilities: ClassAbilities
    bonus_text: str | None
    health: int
    attack: int
    image_path: str
    gender: Gender = Gender.UNKNOWN  # Default to unknown for backward compatibility


@dataclass
class CreatureCard(Card):
    """A creature card that can be played on the board.

    Creature cards have a cost (1-5), belong to a family and class,
    and can attack and defend.
    """

    def __post_init__(self) -> None:
        """Validate creature card constraints."""
        if self.card_type != CardType.CREATURE:
            raise ValueError(
                f"CreatureCard must have card_type CREATURE, got {self.card_type}"
            )
        # S-Team cards have cost X (None), others must have cost 1-5
        if self.card_class == CardClass.S_TEAM:
            if self.cost is not None:
                raise ValueError(
                    f"S-Team cards must have cost None (X), got {self.cost}"
                )
        elif self.cost is None or not (1 <= self.cost <= 5):
            raise ValueError(f"CreatureCard cost must be 1-5, got {self.cost}")
        # Level must be 1 or 2 (card tier)
        if self.level not in (1, 2):
            raise ValueError(f"CreatureCard level must be 1 or 2, got {self.level}")


@dataclass
class WeaponCard(Card):
    """A weapon card that can be equipped to creatures.

    Weapons add their ATQ and PV to the equipped creature.
    They have level X (represented as None).
    """

    equip_restriction: str | None = None  # e.g., "n'importe quel monstre"

    def __post_init__(self) -> None:
        """Validate weapon card constraints."""
        if self.card_type != CardType.WEAPON:
            raise ValueError(
                f"WeaponCard must have card_type WEAPON, got {self.card_type}"
            )
        if self.family != Family.ARME:
            raise ValueError(f"WeaponCard must have family ARME, got {self.family}")


@dataclass
class DemonCard(Card):
    """A demon card that can be summoned by Invocateurs.

    Demons have special restrictions and cannot gain most bonuses.
    They have level X (represented as None).
    """

    summon_cost: int | None = None  # Invocateur threshold to summon

    def __post_init__(self) -> None:
        """Validate demon card constraints."""
        if self.card_type != CardType.DEMON:
            raise ValueError(
                f"DemonCard must have card_type DEMON, got {self.card_type}"
            )
        if self.family != Family.DEMON:
            raise ValueError(f"DemonCard must have family DEMON, got {self.family}")


def _normalize_to_ascii(text: str) -> str:
    """Normalize text to ASCII by removing accents and special characters.

    Uses Unicode NFD normalization to decompose characters, then removes
    combining marks (accents) to get the base characters.

    Args:
        text: The text to normalize.

    Returns:
        ASCII-compatible text with accents removed.
    """
    # NFD decomposes characters (e.g., "é" -> "e" + combining accent)
    normalized = unicodedata.normalize("NFD", text.lower())
    # Filter out combining characters (category "Mn" = Mark, Nonspacing)
    ascii_text = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    return ascii_text


def create_card_id(family: Family, name: str, level: int | None = None) -> str:
    """Generate a unique card ID from family, name, and level.

    Args:
        family: The card's family.
        name: The card's display name.
        level: The card's level (optional for weapons/demons).

    Returns:
        A snake_case identifier like "cyborg_lolo_le_gorille_1".
    """
    # Normalize name to snake_case with ASCII characters
    normalized = _normalize_to_ascii(name)
    normalized = normalized.replace(" ", "_")
    normalized = normalized.replace("'", "")
    normalized = normalized.replace("-", "_")

    # Normalize family prefix
    family_prefix = _normalize_to_ascii(family.value).replace(" ", "_")

    if level is not None:
        return f"{family_prefix}_{normalized}_{level}"
    return f"{family_prefix}_{normalized}"
