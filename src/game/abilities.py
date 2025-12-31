"""Class and family ability resolution for CartesSociete.

This module provides the ability resolution system that processes
scaling abilities, conditional abilities, and passive effects based
on card counts and game state.
"""

import re
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum

from src.cards.models import CardClass, CardType, Family, ScalingAbility

from .state import PlayerState


class AbilityTarget(Enum):
    """Target for an ability effect."""

    SELF = "self"  # Affects only this card/player
    CLASS = "class"  # Affects all cards of the same class
    FAMILY = "family"  # Affects all cards of the same family
    ALL_MONSTERS = "all_monsters"  # Affects all monsters
    SPECIFIC = "specific"  # Affects a specific target (e.g., "defenseurs")


@dataclass
class AbilityEffect:
    """A resolved ability effect.

    Attributes:
        attack_bonus: Bonus attack damage.
        health_bonus: Bonus health/defense.
        self_damage: Damage to self (negative effect, e.g., Berserker).
        self_defense_loss: Defense loss to self (negative effect).
        imblocable_damage: Additional imblocable damage.
        target: Who the effect applies to.
        target_class: Specific class target (if target is SPECIFIC).
        description: Human-readable description.
    """

    attack_bonus: int = 0
    health_bonus: int = 0
    self_damage: int = 0
    self_defense_loss: int = 0
    imblocable_damage: int = 0
    target: AbilityTarget = AbilityTarget.SELF
    target_class: CardClass | None = None
    description: str = ""


@dataclass
class AbilityResolutionResult:
    """Result of resolving all abilities for a player.

    Attributes:
        total_attack_bonus: Total attack bonus from all abilities.
        total_health_bonus: Total health bonus from all abilities.
        total_self_damage: Total self-damage from abilities (e.g., Berserker).
        total_imblocable_bonus: Additional imblocable damage from abilities.
        effects: List of individual effects for debugging/display.
        class_counts: Count of cards per class (for reference).
    """

    total_attack_bonus: int = 0
    total_health_bonus: int = 0
    total_self_damage: int = 0
    total_imblocable_bonus: int = 0
    effects: list[AbilityEffect] = field(default_factory=list)
    class_counts: dict[CardClass, int] = field(default_factory=dict)


# Regex patterns for parsing ability effects
_ATK_PATTERN = re.compile(r"\+(\d+)\s*(?:ATQ|dgt|atq)", re.IGNORECASE)
_PV_PATTERN = re.compile(r"\+(\d+)\s*(?:PV|pv|HP)", re.IGNORECASE)
_SELF_DAMAGE_PATTERN = re.compile(r"-(\d+)\s*(?:PV|pv)", re.IGNORECASE)
_IMBLOCABLE_PATTERN = re.compile(r"(\d+)\s*(?:dgt|dgts)?\s*imblocable", re.IGNORECASE)

# Patterns for conditional targeting
_FOR_CLASS_PATTERN = re.compile(r"pour (?:les |tous les )?(\w+)", re.IGNORECASE)
_IF_DEFENDERS_PATTERN = re.compile(r"si (?:\d+ )?d[ée]fenseurs?", re.IGNORECASE)


def count_cards_by_class(player: PlayerState) -> Counter[CardClass]:
    """Count cards on board by class.

    Args:
        player: The player whose board to count.

    Returns:
        Counter mapping CardClass to count.
    """
    counter: Counter[CardClass] = Counter()
    for card in player.board:
        if card.card_type != CardType.DEMON:  # Demons may have restrictions
            counter[card.card_class] += 1
    return counter


def count_cards_by_family(player: PlayerState) -> Counter[Family]:
    """Count cards on board by family.

    Args:
        player: The player whose board to count.

    Returns:
        Counter mapping Family to count.
    """
    counter: Counter[Family] = Counter()
    for card in player.board:
        counter[card.family] += 1
    return counter


def parse_ability_effect(effect_text: str) -> AbilityEffect:
    """Parse an ability effect string into structured data.

    Handles patterns like:
    - "+5 dgt / -2 PV" (Berserker: attack bonus with self-damage)
    - "+3 ATQ pour les combattants" (attack bonus for class)
    - "+2 PV pour les défenseurs" (health bonus for class)
    - "+4 dgt si 2 défenseurs" (conditional attack bonus)

    Args:
        effect_text: The effect description to parse.

    Returns:
        AbilityEffect with parsed values.
    """
    effect = AbilityEffect(description=effect_text)

    # Parse attack bonus
    atk_match = _ATK_PATTERN.search(effect_text)
    if atk_match:
        effect.attack_bonus = int(atk_match.group(1))

    # Parse health bonus
    pv_match = _PV_PATTERN.search(effect_text)
    if pv_match:
        effect.health_bonus = int(pv_match.group(1))

    # Parse self-damage (negative PV like "-2 PV")
    self_dmg_match = _SELF_DAMAGE_PATTERN.search(effect_text)
    if self_dmg_match:
        effect.self_damage = int(self_dmg_match.group(1))

    # Parse imblocable damage
    imb_match = _IMBLOCABLE_PATTERN.search(effect_text)
    if imb_match:
        effect.imblocable_damage = int(imb_match.group(1))

    # Parse target (for class-specific bonuses)
    for_match = _FOR_CLASS_PATTERN.search(effect_text)
    if for_match:
        target_name = for_match.group(1).lower()
        # Map common French names to CardClass
        class_map = {
            "combattants": CardClass.COMBATTANT,
            "combattant": CardClass.COMBATTANT,
            "défenseurs": CardClass.DEFENSEUR,
            "defenseurs": CardClass.DEFENSEUR,
            "défenseur": CardClass.DEFENSEUR,
            "defenseur": CardClass.DEFENSEUR,
            "mages": CardClass.MAGE,
            "mage": CardClass.MAGE,
            "archers": CardClass.ARCHER,
            "archer": CardClass.ARCHER,
            "dragons": CardClass.DRAGON,
            "dragon": CardClass.DRAGON,
            "monstres": None,  # All monsters
        }
        if target_name in class_map:
            if class_map[target_name] is None:
                effect.target = AbilityTarget.ALL_MONSTERS
            else:
                effect.target = AbilityTarget.SPECIFIC
                effect.target_class = class_map[target_name]

    # Check for conditional on defenders
    if _IF_DEFENDERS_PATTERN.search(effect_text):
        effect.target = AbilityTarget.SPECIFIC
        effect.target_class = CardClass.DEFENSEUR

    return effect


def get_active_scaling_ability(
    abilities: list[ScalingAbility],
    count: int,
) -> ScalingAbility | None:
    """Get the highest active scaling ability for a given count.

    Scaling abilities activate at thresholds (e.g., 2, 4, 6 cards).
    Only the highest threshold that is met applies.

    Args:
        abilities: List of scaling abilities to check.
        count: Current count of matching cards.

    Returns:
        The highest applicable ScalingAbility, or None if none apply.
    """
    active = None
    for ability in abilities:
        if count >= ability.threshold:
            if active is None or ability.threshold > active.threshold:
                active = ability
    return active


def resolve_class_abilities(player: PlayerState) -> AbilityResolutionResult:
    """Resolve all class abilities for a player.

    Counts cards by class and applies scaling bonuses based on thresholds.
    Handles special cases like Berserker self-damage.

    Args:
        player: The player whose abilities to resolve.

    Returns:
        AbilityResolutionResult with all bonuses and effects.
    """
    result = AbilityResolutionResult()
    class_counts = count_cards_by_class(player)
    result.class_counts = dict(class_counts)

    # Track which classes we've already processed (avoid double-counting)
    processed_effects: set[str] = set()

    for card in player.board:
        if card.card_type == CardType.DEMON:
            continue  # Demons have restrictions on bonuses

        card_class = card.card_class
        class_count = class_counts[card_class]

        # Get the active scaling ability for this class
        if card.class_abilities.scaling:
            active = get_active_scaling_ability(
                card.class_abilities.scaling,
                class_count,
            )

            if active:
                # Create a unique key to avoid processing same ability multiple times
                effect_key = f"{card_class.value}_{active.threshold}_{active.effect}"

                if effect_key not in processed_effects:
                    processed_effects.add(effect_key)
                    effect = parse_ability_effect(active.effect)

                    # Apply the effect based on target
                    if effect.target == AbilityTarget.SELF:
                        # Effect applies once for the class
                        result.total_attack_bonus += effect.attack_bonus
                        result.total_health_bonus += effect.health_bonus
                        result.total_self_damage += effect.self_damage
                        result.total_imblocable_bonus += effect.imblocable_damage
                    elif effect.target == AbilityTarget.SPECIFIC:
                        # Effect applies per matching card
                        if effect.target_class:
                            target_count = class_counts.get(effect.target_class, 0)
                            result.total_attack_bonus += (
                                effect.attack_bonus * target_count
                            )
                            result.total_health_bonus += (
                                effect.health_bonus * target_count
                            )
                    elif effect.target == AbilityTarget.ALL_MONSTERS:
                        # Effect applies to all monsters
                        total_monsters = sum(class_counts.values())
                        result.total_attack_bonus += (
                            effect.attack_bonus * total_monsters
                        )
                        result.total_health_bonus += (
                            effect.health_bonus * total_monsters
                        )

                    result.effects.append(effect)

    return result


def resolve_family_abilities(player: PlayerState) -> AbilityResolutionResult:
    """Resolve all family abilities for a player.

    Family abilities scale with the number of same-family cards.

    Args:
        player: The player whose abilities to resolve.

    Returns:
        AbilityResolutionResult with all bonuses and effects.
    """
    result = AbilityResolutionResult()
    family_counts = count_cards_by_family(player)

    # Track processed effects
    processed_effects: set[str] = set()

    for card in player.board:
        family = card.family
        family_count = family_counts[family]

        if card.family_abilities.scaling:
            active = get_active_scaling_ability(
                card.family_abilities.scaling,
                family_count,
            )

            if active:
                effect_key = f"{family.value}_{active.threshold}_{active.effect}"

                if effect_key not in processed_effects:
                    processed_effects.add(effect_key)
                    effect = parse_ability_effect(active.effect)

                    # Family abilities typically apply once
                    result.total_attack_bonus += effect.attack_bonus
                    result.total_health_bonus += effect.health_bonus
                    result.total_imblocable_bonus += effect.imblocable_damage

                    result.effects.append(effect)

    return result


def resolve_all_abilities(player: PlayerState) -> AbilityResolutionResult:
    """Resolve all abilities (class and family) for a player.

    Args:
        player: The player whose abilities to resolve.

    Returns:
        Combined AbilityResolutionResult.
    """
    class_result = resolve_class_abilities(player)
    family_result = resolve_family_abilities(player)

    # Combine results
    combined = AbilityResolutionResult(
        total_attack_bonus=class_result.total_attack_bonus
        + family_result.total_attack_bonus,
        total_health_bonus=class_result.total_health_bonus
        + family_result.total_health_bonus,
        total_self_damage=class_result.total_self_damage
        + family_result.total_self_damage,
        total_imblocable_bonus=class_result.total_imblocable_bonus
        + family_result.total_imblocable_bonus,
        effects=class_result.effects + family_result.effects,
        class_counts=class_result.class_counts,
    )

    return combined


def get_player_attack_with_abilities(player: PlayerState) -> int:
    """Get total attack including ability bonuses.

    Args:
        player: The player to calculate attack for.

    Returns:
        Total attack value.
    """
    base_attack = player.get_total_attack()
    abilities = resolve_all_abilities(player)
    return base_attack + abilities.total_attack_bonus


def get_player_health_with_abilities(player: PlayerState) -> int:
    """Get total health including ability bonuses.

    Args:
        player: The player to calculate health for.

    Returns:
        Total health value.
    """
    base_health = player.get_total_health()
    abilities = resolve_all_abilities(player)
    return base_health + abilities.total_health_bonus


def get_ability_summary(player: PlayerState) -> str:
    """Generate a human-readable summary of a player's active abilities.

    Args:
        player: The player to summarize.

    Returns:
        Multi-line string describing active abilities.
    """
    result = resolve_all_abilities(player)

    lines = [f"=== Ability Summary for {player.name} ==="]
    lines.append(f"Cards on board: {len(player.board)}")

    if result.class_counts:
        lines.append("\nClass counts:")
        for card_class, count in sorted(
            result.class_counts.items(), key=lambda x: -x[1]
        ):
            if count > 0:
                lines.append(f"  {card_class.value}: {count}")

    if result.effects:
        lines.append("\nActive effects:")
        for effect in result.effects:
            parts = []
            if effect.attack_bonus:
                parts.append(f"+{effect.attack_bonus} ATK")
            if effect.health_bonus:
                parts.append(f"+{effect.health_bonus} HP")
            if effect.self_damage:
                parts.append(f"-{effect.self_damage} self-damage")
            if effect.imblocable_damage:
                parts.append(f"+{effect.imblocable_damage} imblocable")

            if parts:
                lines.append(f"  {', '.join(parts)} ({effect.description})")

    lines.append("\nTotal bonuses:")
    lines.append(f"  Attack: +{result.total_attack_bonus}")
    lines.append(f"  Health: +{result.total_health_bonus}")
    if result.total_self_damage:
        lines.append(f"  Self-damage: {result.total_self_damage}")
    if result.total_imblocable_bonus:
        lines.append(f"  Imblocable: +{result.total_imblocable_bonus}")

    return "\n".join(lines)


@dataclass
class PerTurnEffectResult:
    """Result of resolving per-turn effects for a player.

    Attributes:
        total_self_damage: Total self-damage from per-turn effects.
        cards_with_effects: List of cards that have per-turn effects.
    """

    total_self_damage: int = 0
    cards_with_effects: list[str] = field(default_factory=list)


def resolve_per_turn_effects(player: PlayerState) -> PerTurnEffectResult:
    """Resolve per-turn effects for a player.

    Per-turn effects are effects that apply each turn, such as
    "Vous perdez X PV par tour" (you lose X HP per turn).

    These are separate from:
    - Combat self-damage (e.g., Berserker's -2 PV from class ability)
    - One-time effects

    Args:
        player: The player whose per-turn effects to resolve.

    Returns:
        PerTurnEffectResult with total damage and affected cards.
    """
    result = PerTurnEffectResult()

    for card in player.board:
        per_turn_dmg = card.class_abilities.per_turn_self_damage
        if per_turn_dmg > 0:
            result.total_self_damage += per_turn_dmg
            result.cards_with_effects.append(card.name)

    return result


def apply_per_turn_effects(player: PlayerState) -> int:
    """Apply per-turn effects to a player and return damage dealt.

    This function both calculates and applies per-turn damage.
    Call this during the end-of-turn phase.

    Args:
        player: The player to apply per-turn effects to.

    Returns:
        Total self-damage dealt to the player.
    """
    effects = resolve_per_turn_effects(player)

    if effects.total_self_damage > 0:
        player.health -= effects.total_self_damage

    return effects.total_self_damage
