"""Class and family ability resolution for CartesSociete.

This module provides the ability resolution system that processes
scaling abilities, conditional abilities, and passive effects based
on card counts and game state.
"""

import re
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum

from src.cards.models import (
    CardClass,
    CardType,
    ConditionalAbility,
    Family,
    ScalingAbility,
)

from .state import PlayerState


class PassiveType(Enum):
    """Types of passive abilities."""

    S_TEAM_NOT_MONSTER = "s_team_not_monster"  # Doesn't count as monster
    ECONOME_PO = "econome_po"  # Generates extra PO
    DEMON_RESTRICTION = "demon_restriction"  # Demons can't gain most bonuses
    FORGERON_DRAW = "forgeron_draw"  # Draw weapon cards


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


@dataclass
class ConditionalAbilityResult:
    """Result of resolving conditional abilities (e.g., Dragon PO spending).

    Attributes:
        total_imblocable_damage: Imblocable damage from conditional abilities.
        total_attack_bonus: Attack bonus from conditional abilities.
        total_health_bonus: Health bonus from conditional abilities.
        attack_multiplier: Attack multiplier (e.g., 2 for double, 3 for triple).
        po_spent: Total PO spent on conditional abilities.
        effects: List of activated conditional effects.
    """

    total_imblocable_damage: int = 0
    total_attack_bonus: int = 0
    total_health_bonus: int = 0
    attack_multiplier: int = 1  # Default is 1x (no multiplier)
    po_spent: int = 0
    effects: list[str] = field(default_factory=list)


@dataclass
class PassiveAbilityResult:
    """Result of resolving passive abilities.

    Attributes:
        extra_po: Additional PO generated (from Econome).
        cards_excluded_from_count: Cards that don't count as monsters (S-Team).
        weapons_to_draw: Number of weapons to draw (from Forgeron).
    """

    extra_po: int = 0
    cards_excluded_from_count: list[str] = field(default_factory=list)
    weapons_to_draw: int = 0


@dataclass
class BonusTextResult:
    """Result of parsing bonus_text effects.

    Attributes:
        attack_bonus: Total attack bonus from bonus_text.
        health_bonus: Total health bonus from bonus_text.
        effects: Description of active bonus_text effects.
    """

    attack_bonus: int = 0
    health_bonus: int = 0
    effects: list[str] = field(default_factory=list)


@dataclass
class InvocateurAbilityResult:
    """Result of resolving Invocateur demon summoning.

    Attributes:
        demons_to_summon: List of demon names to summon.
        effects: Description of summoning effects.
    """

    demons_to_summon: list[str] = field(default_factory=list)
    effects: list[str] = field(default_factory=list)


@dataclass
class MontureAbilityResult:
    """Result of resolving Monture card draw ability.

    Attributes:
        cards_to_draw: Number of cost-5 cards to draw.
        effects: Description of draw effects.
    """

    cards_to_draw: int = 0
    effects: list[str] = field(default_factory=list)


# Regex patterns for parsing ability effects
_ATK_PATTERN = re.compile(r"\+(\d+)\s*(?:ATQ|dgt|atq)", re.IGNORECASE)
_PV_PATTERN = re.compile(r"\+(\d+)\s*(?:PV|pv|HP)", re.IGNORECASE)
_SELF_DAMAGE_PATTERN = re.compile(r"-(\d+)\s*(?:PV|pv)", re.IGNORECASE)
_IMBLOCABLE_PATTERN = re.compile(r"(\d+)\s*(?:dgt|dgts)?\s*imblocable", re.IGNORECASE)

# Patterns for conditional ability conditions
_PO_CONDITION_PATTERN = re.compile(r"(\d+)\s*PO", re.IGNORECASE)

# Patterns for Dragon conditional effects
_DOUBLE_ATTACK_PATTERN = re.compile(r"double\s+son\s+attaque", re.IGNORECASE)
_TRIPLE_ATTACK_PATTERN = re.compile(r"triple\s+son\s+attaque", re.IGNORECASE)
_QUADRUPLE_ATTACK_PATTERN = re.compile(r"quadruple\s+son\s+attaque", re.IGNORECASE)
_PER_CARD_BONUS_PATTERN = re.compile(
    r"\+(\d+)\s*(?:ATQ|dgt)\s+par\s+(\w+)", re.IGNORECASE
)
_BONUS_TO_CLASS_PATTERN = re.compile(
    r"\+(\d+)\s*(?:ATQ|dgt)\s+aux\s+(\w+)", re.IGNORECASE
)

# Patterns for Invocateur demon summoning
_SUMMON_DIABLOTIN_PATTERN = re.compile(r"invoque\s+un\s+diablotin", re.IGNORECASE)
_SUMMON_DEMON_MINEUR_PATTERN = re.compile(r"d[ée]mon\s+mineur", re.IGNORECASE)
_SUMMON_SUCCUBE_PATTERN = re.compile(r"une?\s+succube", re.IGNORECASE)
_SUMMON_DEMON_MAJEUR_PATTERN = re.compile(r"d[ée]mon\s+majeur", re.IGNORECASE)

# Patterns for Monture card draw
_DRAW_COST_5_PATTERN = re.compile(r"piocher\s+une\s+carte\s+co[uû]t\s*5", re.IGNORECASE)

# Patterns for bonus_text effects
_BONUS_FOR_FAMILY_PATTERN = re.compile(
    r"\+(\d+)\s*(?:ATQ|dgt|atq)\s+(?:pour|aux)\s+(?:les\s+)?(\w+)",
    re.IGNORECASE,
)
_BONUS_FOR_CLASS_PATTERN = re.compile(
    r"\+(\d+)\s*(?:ATQ|dgt|atq)\s+(?:pour|aux)\s+(?:les\s+)?(\w+)",
    re.IGNORECASE,
)
_BONUS_IF_THRESHOLD_PATTERN = re.compile(
    r"\+(\d+)\s*(?:ATQ|dgt|atq)\s+si\s+(?:bonus\s+)?(\w+)\s+(\d+)",
    re.IGNORECASE,
)

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


def resolve_conditional_abilities(
    player: PlayerState,
    po_to_spend: int | None = None,
) -> ConditionalAbilityResult:
    """Resolve conditional abilities (e.g., Dragon PO spending).

    Dragon class cards have conditional abilities like:
    - "1 PO": "2 dgt imblocable" (imblocable damage)
    - "1 PO": "double son attaque" (attack multiplier)
    - "1 PO": "+3 ATQ" (attack bonus)
    - "2 PO": "et +3 PV" (health bonus, cumulative)
    - "1 PO": "+1 ATQ par raton" (per-card bonus)

    This function determines which conditional abilities to activate based on
    available PO and returns all effects. Dragon conditionals are CUMULATIVE -
    spending 2 PO activates both the 1 PO and 2 PO effects if marked with "et".

    Args:
        player: The player whose abilities to resolve.
        po_to_spend: Optional PO amount to spend. If None, uses player's full PO.

    Returns:
        ConditionalAbilityResult with all bonuses and PO spent.
    """
    result = ConditionalAbilityResult()
    available_po = po_to_spend if po_to_spend is not None else player.po

    # Count cards by family for per-card bonuses
    family_counts: dict[Family, int] = {}
    for c in player.board:
        if c.card_type != CardType.DEMON:
            family_counts[c.family] = family_counts.get(c.family, 0) + 1

    # Map family names (French) to Family enum
    family_name_map = {
        "raton": Family.RATON,
        "ratons": Family.RATON,
        "lapin": Family.LAPIN,
        "lapins": Family.LAPIN,
        "cyborg": Family.CYBORG,
        "cyborgs": Family.CYBORG,
        "nature": Family.NATURE,
        "atlantide": Family.ATLANTIDE,
        "ninja": Family.NINJA,
        "ninjas": Family.NINJA,
        "neige": Family.NEIGE,
    }

    # Find all Dragon cards with conditional abilities
    for card in player.board:
        if card.card_class != CardClass.DRAGON:
            continue
        if card.card_type == CardType.DEMON:
            continue  # Demons can't use most abilities

        conditionals = card.class_abilities.conditional
        if not conditionals:
            continue

        # Collect all affordable abilities (Dragon conditionals are cumulative)
        # Sort by PO cost to apply in order
        affordable: list[tuple[int, ConditionalAbility]] = []
        for ability in conditionals:
            match = _PO_CONDITION_PATTERN.search(ability.condition)
            if match:
                po_cost = int(match.group(1))
                if po_cost <= available_po:
                    affordable.append((po_cost, ability))

        # Sort by cost and apply cumulative effects
        affordable.sort(key=lambda x: x[0])

        max_po_spent = 0
        for po_cost, ability in affordable:
            effect = ability.effect
            effect_applied = False

            # Check for attack multiplier
            if _QUADRUPLE_ATTACK_PATTERN.search(effect):
                result.attack_multiplier = max(result.attack_multiplier, 4)
                effect_applied = True
            elif _TRIPLE_ATTACK_PATTERN.search(effect):
                result.attack_multiplier = max(result.attack_multiplier, 3)
                effect_applied = True
            elif _DOUBLE_ATTACK_PATTERN.search(effect):
                result.attack_multiplier = max(result.attack_multiplier, 2)
                effect_applied = True

            # Check for imblocable damage
            imblocable_match = _IMBLOCABLE_PATTERN.search(effect)
            if imblocable_match:
                result.total_imblocable_damage += int(imblocable_match.group(1))
                effect_applied = True

            # Check for attack bonus
            atk_match = _ATK_PATTERN.search(effect)
            if atk_match:
                result.total_attack_bonus += int(atk_match.group(1))
                effect_applied = True

            # Check for health bonus
            pv_match = _PV_PATTERN.search(effect)
            if pv_match:
                result.total_health_bonus += int(pv_match.group(1))
                effect_applied = True

            # Check for per-card bonus (e.g., "+1 ATQ par raton")
            per_card_match = _PER_CARD_BONUS_PATTERN.search(effect)
            if per_card_match:
                bonus_per = int(per_card_match.group(1))
                family_name = per_card_match.group(2).lower()
                target_family = family_name_map.get(family_name)
                if target_family:
                    count = family_counts.get(target_family, 0)
                    result.total_attack_bonus += bonus_per * count
                    effect_applied = True

            # Check for class/family bonus (e.g., "+3 ATQ aux dragons")
            to_class_match = _BONUS_TO_CLASS_PATTERN.search(effect)
            if to_class_match:
                bonus = int(to_class_match.group(1))
                target_name = to_class_match.group(2).lower()
                # Count matching cards
                if target_name in ("dragons", "dragon"):
                    dragon_count = sum(
                        1
                        for c in player.board
                        if c.card_class == CardClass.DRAGON
                        and c.card_type != CardType.DEMON
                    )
                    result.total_attack_bonus += bonus * dragon_count
                    effect_applied = True
                elif target_name in family_name_map:
                    target_family = family_name_map[target_name]
                    count = family_counts.get(target_family, 0)
                    result.total_attack_bonus += bonus * count
                    effect_applied = True

            if effect_applied:
                max_po_spent = max(max_po_spent, po_cost)
                result.effects.append(f"{card.name}: {effect} ({po_cost} PO)")

        if max_po_spent > 0:
            result.po_spent += max_po_spent
            available_po -= max_po_spent

    return result


def resolve_passive_abilities(player: PlayerState) -> PassiveAbilityResult:
    """Resolve passive abilities for a player.

    Passive abilities are always-active effects:
    - S-Team: "Ne compte pas comme un monstre du plateau"
    - Econome: "les économes apportent 1- nb d'économes PO/Tour"

    Args:
        player: The player whose passive abilities to resolve.

    Returns:
        PassiveAbilityResult with all passive effects.
    """
    result = PassiveAbilityResult()
    econome_count = 0

    for card in player.board:
        passive = card.class_abilities.passive

        if not passive:
            # Check family passive
            passive = card.family_abilities.passive

        if not passive:
            continue

        passive_lower = passive.lower()

        # S-Team: doesn't count as monster
        if "ne compte pas comme un monstre" in passive_lower:
            result.cards_excluded_from_count.append(card.id)

        # Econome: extra PO generation
        if (
            "économes apportent" in passive_lower
            or "economes apportent" in passive_lower
        ):
            econome_count += 1

    # Econome passive: each Econome adds 1 extra PO
    # Text says "les économes apportent 1- nb d'économes PO/Tour"
    # This means 1 PO per Econome
    if econome_count > 0:
        result.extra_po = econome_count

    return result


def resolve_forgeron_abilities(player: PlayerState) -> int:
    """Resolve Forgeron weapon draw ability.

    Forgeron class abilities allow drawing weapons:
    - Threshold 1: "Piocher une arme" (draw 1 weapon)
    - Threshold 2: "2 armes" (draw 2 weapons)
    - Threshold 3: "3 armes" (draw 3 weapons)

    Args:
        player: The player whose Forgeron abilities to resolve.

    Returns:
        Number of weapons to draw.
    """
    forgeron_count = sum(
        1
        for card in player.board
        if card.card_class == CardClass.FORGERON and card.card_type != CardType.DEMON
    )

    if forgeron_count == 0:
        return 0

    # Find a Forgeron card to get its scaling abilities
    for card in player.board:
        if card.card_class != CardClass.FORGERON:
            continue
        if card.card_type == CardType.DEMON:
            continue

        scaling = card.class_abilities.scaling
        if not scaling:
            continue

        # Get the active scaling ability
        active = get_active_scaling_ability(scaling, forgeron_count)
        if not active:
            continue

        # Parse the number of weapons to draw
        effect_lower = active.effect.lower()
        if "piocher une arme" in effect_lower:
            return 1
        elif "2 armes" in effect_lower:
            return 2
        elif "3 armes" in effect_lower:
            return 3

    return 0


def resolve_invocateur_abilities(player: PlayerState) -> InvocateurAbilityResult:
    """Resolve Invocateur demon summoning ability.

    Invocateur class abilities summon demons based on threshold:
    - Threshold 1: "invoque un diablotin" (summon Diablotin)
    - Threshold 2: "démon mineur" (summon Demon mineur)
    - Threshold 4: "une succube" (summon Succube)
    - Threshold 6: "un démon majeur" (summon Demon Majeur)

    Args:
        player: The player whose Invocateur abilities to resolve.

    Returns:
        InvocateurAbilityResult with demons to summon.
    """
    result = InvocateurAbilityResult()

    invocateur_count = sum(
        1
        for card in player.board
        if card.card_class == CardClass.INVOCATEUR and card.card_type != CardType.DEMON
    )

    if invocateur_count == 0:
        return result

    # Find an Invocateur card to get its scaling abilities
    for card in player.board:
        if card.card_class != CardClass.INVOCATEUR:
            continue
        if card.card_type == CardType.DEMON:
            continue

        scaling = card.class_abilities.scaling
        if not scaling:
            continue

        # Get the active scaling ability based on Invocateur count
        active = get_active_scaling_ability(scaling, invocateur_count)
        if not active:
            continue

        effect = active.effect

        # Determine which demon to summon (cumulative - summon highest tier)
        if _SUMMON_DEMON_MAJEUR_PATTERN.search(effect):
            result.demons_to_summon.append("Demon Majeur")
            result.effects.append(
                f"Invocateur threshold {active.threshold}: Summon Demon Majeur"
            )
        elif _SUMMON_SUCCUBE_PATTERN.search(effect):
            result.demons_to_summon.append("Succube")
            result.effects.append(
                f"Invocateur threshold {active.threshold}: Summon Succube"
            )
        elif _SUMMON_DEMON_MINEUR_PATTERN.search(effect):
            result.demons_to_summon.append("Demon mineur")
            result.effects.append(
                f"Invocateur threshold {active.threshold}: Summon Demon mineur"
            )
        elif _SUMMON_DIABLOTIN_PATTERN.search(effect):
            result.demons_to_summon.append("Diablotin")
            result.effects.append(
                f"Invocateur threshold {active.threshold}: Summon Diablotin"
            )

        break  # Only process one Invocateur's abilities

    return result


def resolve_monture_abilities(player: PlayerState) -> MontureAbilityResult:
    """Resolve Monture card draw ability.

    Monture class abilities draw cards:
    - Threshold 3: "piocher une carte coût 5 dans la pile (au hasard)"

    Args:
        player: The player whose Monture abilities to resolve.

    Returns:
        MontureAbilityResult with cards to draw.
    """
    result = MontureAbilityResult()

    monture_count = sum(
        1
        for card in player.board
        if card.card_class == CardClass.MONTURE and card.card_type != CardType.DEMON
    )

    if monture_count == 0:
        return result

    # Find a Monture card to get its scaling abilities
    for card in player.board:
        if card.card_class != CardClass.MONTURE:
            continue
        if card.card_type == CardType.DEMON:
            continue

        scaling = card.class_abilities.scaling
        if not scaling:
            continue

        # Get the active scaling ability based on Monture count
        active = get_active_scaling_ability(scaling, monture_count)
        if not active:
            continue

        effect = active.effect

        # Check for cost-5 card draw
        if _DRAW_COST_5_PATTERN.search(effect):
            result.cards_to_draw = 1
            result.effects.append(
                f"Monture threshold {active.threshold}: Draw 1 cost-5 card"
            )

        break  # Only process one Monture's abilities

    return result


def count_board_monsters(player: PlayerState) -> int:
    """Count monsters on board, excluding S-Team and demons.

    S-Team cards have the passive "Ne compte pas comme un monstre du plateau"
    and should be excluded from the board count for limit purposes.

    Args:
        player: The player whose board to count.

    Returns:
        Number of monsters counting towards board limit.
    """
    passives = resolve_passive_abilities(player)
    excluded_ids = set(passives.cards_excluded_from_count)

    count = 0
    for card in player.board:
        if card.card_type == CardType.DEMON:
            continue  # Demons don't count towards board limit
        if card.id in excluded_ids:
            continue  # S-Team cards don't count
        count += 1

    return count


def resolve_bonus_text_effects(
    player: PlayerState,
    opponent: PlayerState | None = None,
) -> BonusTextResult:
    """Resolve bonus_text effects for combat.

    Parses and resolves bonus_text patterns like:
    - "+X ATQ pour les [family/class]" - attack bonus for matching cards
    - "+X ATQ si bonus [Class] Y" - attack bonus if class threshold met
    - "+X ATQ aux [family] alliés" - attack bonus to allied family

    Args:
        player: The player whose bonus_text to resolve.
        opponent: Optional opponent for opponent-dependent effects.

    Returns:
        BonusTextResult with total bonuses from bonus_text.
    """
    result = BonusTextResult()
    class_counts = count_cards_by_class(player)

    # Map for French names to Family/Class
    family_map = {
        "cyborg": Family.CYBORG,
        "cyborgs": Family.CYBORG,
        "nature": Family.NATURE,
        "atlantide": Family.ATLANTIDE,
        "ninja": Family.NINJA,
        "ninjas": Family.NINJA,
        "neige": Family.NEIGE,
        "lapin": Family.LAPIN,
        "lapins": Family.LAPIN,
        "raton": Family.RATON,
        "ratons": Family.RATON,
        "raccoon": Family.RATON,
    }

    class_map_lower = {
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
        "s-team": CardClass.S_TEAM,
        "econome": CardClass.ECONOME,
        "économes": CardClass.ECONOME,
        "economes": CardClass.ECONOME,
    }

    for card in player.board:
        if card.card_type == CardType.DEMON:
            continue  # Demons can't benefit from most bonuses

        bonus = card.bonus_text
        if not bonus:
            continue

        # Pattern: "+X ATQ si bonus [Class] Y" (threshold-based)
        threshold_match = _BONUS_IF_THRESHOLD_PATTERN.search(bonus)
        if threshold_match:
            atk_bonus = int(threshold_match.group(1))
            target_name = threshold_match.group(2).lower()
            threshold = int(threshold_match.group(3))

            # Check if the threshold is met
            target_class = class_map_lower.get(target_name)
            if target_class and class_counts.get(target_class, 0) >= threshold:
                result.attack_bonus += atk_bonus
                result.effects.append(f"{card.name}: {bonus}")
            continue  # Don't double-process

        # Pattern: "+X ATQ pour les [target]" or "+X ATQ aux [target]"
        for_match = _BONUS_FOR_FAMILY_PATTERN.search(bonus)
        if for_match:
            atk_bonus = int(for_match.group(1))
            target_name = for_match.group(2).lower()

            # Check if it's a family
            if target_name in family_map:
                target_family = family_map[target_name]
                # Count cards of that family
                matching = sum(
                    1
                    for c in player.board
                    if c.family == target_family and c.card_type != CardType.DEMON
                )
                if matching > 0:
                    result.attack_bonus += atk_bonus * matching
                    result.effects.append(f"{card.name}: {bonus} ({matching} cards)")
            # Check if it's a class
            elif target_name in class_map_lower:
                target_class = class_map_lower[target_name]
                matching = class_counts.get(target_class, 0)
                if matching > 0:
                    result.attack_bonus += atk_bonus * matching
                    result.effects.append(f"{card.name}: {bonus} ({matching} cards)")

    return result


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
