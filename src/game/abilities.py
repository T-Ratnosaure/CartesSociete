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
        attack_penalty: Total attack penalty (negative modifier) from bonus_text.
        health_penalty: Total health penalty from bonus_text.
        on_attacked_damage: Damage dealt when this player is attacked.
        per_turn_imblocable: Per-turn imblocable damage from bonus_text.
        per_turn_pv_heal: Per-turn PV healing from bonus_text.
        per_turn_po: Per-turn PO generation from bonus_text.
        per_turn_self_damage: Per-turn PV loss from bonus_text.
        spell_damage_block: Amount of spell damage blocked.
        spell_damage: Spell damage dealt by mages.
        spell_damage_bonus: Bonus to all spell damage.
        extra_po: Extra PO generated from bonus_text effects (one-time).
        deck_reveal_atk: ATK bonus from deck reveal mechanic.
        deck_reveal_multiplier: Multiplier for deck reveal ATK.
        min_atk_floor: Minimum ATK floor for family cards.
        min_atk_family: Which family the ATK floor applies to.
        defense_multiplier: Multiplier for defense during defense phase.
        demon_imblocable_bonus: Imblocable damage bonus for summoned demon.
        demon_atk_bonus: ATK bonus for summoned demon.
        demon_pv_penalty: PV penalty for summoned demon.
        weapon_atk_bonus: ATK bonus for all equipped weapons.
        kdo_atk_bonus: Extra ATK per equipped Kdo.
        kdo_pv_bonus: Extra PV per equipped Kdo.
        diplo_atk_bonus: ATK bonus from Diplo synergy.
        diplo_pv_bonus: PV bonus from Diplo synergy.
        imblocable_scaling: Extra imblocable per X imblocable dealt.
        imblocable_scaling_ratio: How many imblocable trigger the scaling.
        enemy_high_atk_debuff: ATK debuff applied to enemy's strongest monster.
        fire_vulnerability: If True, PV = 0 when hit by fire magic.
        demons_gain_all_bonuses: If True, demons can gain normal bonuses.
        reduced_monture_threshold: Reduced threshold for Monture ability.
        pv_damage_from_healing: Damage dealt per PV healed this turn.
        gold_if_imblocable: Extra gold if imblocable damage is dealt.
        flat_imblocable_damage: Flat imblocable damage dealt (e.g., Demon Majeur).
        lifelink: If True, gain PV equal to damage dealt.
        effects: Description of active bonus_text effects.
    """

    attack_bonus: int = 0
    health_bonus: int = 0
    attack_penalty: int = 0
    health_penalty: int = 0
    on_attacked_damage: int = 0
    per_turn_imblocable: int = 0
    per_turn_pv_heal: int = 0
    per_turn_po: int = 0
    per_turn_self_damage: int = 0
    spell_damage_block: int = 0
    spell_damage: int = 0
    spell_damage_bonus: int = 0
    extra_po: int = 0
    deck_reveal_atk: int = 0
    deck_reveal_multiplier: int = 1
    min_atk_floor: int = 0
    min_atk_family: str = ""
    defense_multiplier: int = 1
    demon_imblocable_bonus: int = 0
    demon_atk_bonus: int = 0
    demon_pv_penalty: int = 0
    weapon_atk_bonus: int = 0
    kdo_atk_bonus: int = 0
    kdo_pv_bonus: int = 0
    diplo_atk_bonus: int = 0
    diplo_pv_bonus: int = 0
    imblocable_scaling: int = 0
    imblocable_scaling_ratio: int = 0
    enemy_high_atk_debuff: int = 0
    fire_vulnerability: bool = False
    demons_gain_all_bonuses: bool = False
    reduced_monture_threshold: int = 0
    pv_damage_from_healing: int = 0
    gold_if_imblocable: int = 0
    flat_imblocable_damage: int = 0
    lifelink: bool = False
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

# Patterns for bonus_text: negative ATK modifiers
_NEGATIVE_ATK_FOR_CLASS_PATTERN = re.compile(
    r"-(\d+)\s*ATQ\s+pour\s+(?:les\s+)?(\w+)", re.IGNORECASE
)

# Patterns for bonus_text: on-attacked damage
_ON_ATTACKED_DAMAGE_PATTERN = re.compile(
    r"[Ii]nflige\s+(\d+)\s+(?:points?\s+de\s+)?dgt\s+quand\s+attaqu[ée]", re.IGNORECASE
)

# Patterns for bonus_text: per-turn imblocable
_PER_TURN_IMBLOCABLE_PATTERN = re.compile(
    r"\+(\d+)\s+dgt\s+imblocable/?tour", re.IGNORECASE
)

# Patterns for bonus_text: flat imblocable damage (e.g., "10 dgt imblocable")
_FLAT_IMBLOCABLE_PATTERN = re.compile(
    r"^(\d+)\s+(?:dgt|dgts)\s+imblocable$", re.IGNORECASE
)

# Patterns for bonus_text: lifelink ("Gagne en PV le nombre de DGT qu'elle inflige")
_LIFELINK_PATTERN = re.compile(
    r"[Gg]agne\s+en\s+PV\s+le\s+nombre\s+de\s+(?:DGT|dgt)", re.IGNORECASE
)

# Patterns for bonus_text: spell damage blocking
_SPELL_DAMAGE_BLOCK_PATTERN = re.compile(
    r"[Bb]loque\s+(\d+)\s+(?:points?\s+de\s+)?(?:dgt|DGT)\s+(?:des\s+sorts|magique|par\s+sort)",
    re.IGNORECASE,
)

# Patterns for bonus_text: PO generation
_PO_PER_TURN_IF_PATTERN = re.compile(
    r"\+(\d+)\s+PO\s*/?(?:tour)?\s+si\s+(\w+)\s+(\d+)", re.IGNORECASE
)
_PO_IF_NINJA_PATTERN = re.compile(r"\+(\d+)\s+PO\s+si\s+ninja\s+choisi", re.IGNORECASE)
_PO_PER_RATONS_PATTERN = re.compile(
    r"\+(\d+)\s+PO\s+par\s+tranche\s+de\s+(\d+)\s+ratons", re.IGNORECASE
)

# Patterns for bonus_text: raccoon family bonus
_RACCOON_FAMILY_BONUS_PATTERN = re.compile(
    r"[Ll]es\s+raccoon\s+[Ff]amilly\s+gagne\s+\+(\d+)\s+ATQ", re.IGNORECASE
)

# Patterns for bonus_text: solo ninja
_SOLO_NINJA_PATTERN = re.compile(
    r"\+(\d+)\s+ATQ\s+si\s+c'?est\s+le\s+seul\s+ninja", re.IGNORECASE
)

# Patterns for bonus_text: card-specific bonuses
_BONUS_IF_JOE_PATTERN = re.compile(
    r"\+(\d+)\s+(?:dgts?|ATQ)\s+si\s+Joe\s+est\s+sur\s+plateau", re.IGNORECASE
)
_BONUS_IF_REINE_PATTERN = re.compile(
    r"\+(\d+)\s+ATQ\s+si\s+(?:la\s+)?Reine\s+est\s+en\s+jeu", re.IGNORECASE
)
_BONUS_IF_RATON_MIGNON_PATTERN = re.compile(
    r"[Gg]agne\s+\+(\d+)\s+ATQ\s+si\s+Raton\s+Mignon", re.IGNORECASE
)
_BONUS_IF_MAITRE_RAT_PATTERN = re.compile(
    r"\+(\d+)\s+ATQ/?(?:\+\d+\s+PV)?\s+si\s+ma[îi]tre\s+rat", re.IGNORECASE
)
_PV_IF_MAITRE_RAT_PATTERN = re.compile(
    r"\+(\d+)\s+PV\s+si\s+ma[îi]tre\s+rat", re.IGNORECASE
)

# Patterns for bonus_text: per-econome bonus
_ATK_PER_ENEMY_ECONOME_PATTERN = re.compile(
    r"[Gg]agne\s+\+(\d+)\s+ATQ\s+par\s+[ée]conomes?\s+sur\s+le\s+plateau\s+ennemi",
    re.IGNORECASE,
)

# Patterns for bonus_text: demon-specific
_IMBLOCABLE_FOR_DEMON_PATTERN = re.compile(
    r"\+(\d+)\s+(?:dgts?|dgt)\s+imblocable\s+pour\s+le\s+d[ée]mon", re.IGNORECASE
)
_ATK_PV_FOR_DEMON_PATTERN = re.compile(
    r"\+(\d+)\s+ATQ\s*/\s*-(\d+)\s+PV\s+pour\s+le\s+d[ée]mon", re.IGNORECASE
)

# Patterns for Lapincruste board limit expansion
_LAPIN_BOARD_EXPANSION_PATTERN = re.compile(
    r"(?:peut\s+poser|poser)\s+(\d+)\s+lapins?\s+suppl[ée]mentaires?\s+en\s+jeu",
    re.IGNORECASE,
)

# Patterns for family board expansion ("+N cartes sur le plateau")
_BOARD_EXPANSION_PATTERN = re.compile(
    r"\+(\d+)\s+cartes?\s+sur\s+le\s+plateau", re.IGNORECASE
)

# Pattern for "pour tous les [family]" effects (e.g., "+2 ATQ pour tous les lapins")
_FOR_ALL_FAMILY_PATTERN = re.compile(r"pour\s+tous\s+les\s+(\w+)", re.IGNORECASE)

# Patterns for Lapin-specific bonus_text effects
# "+X PV /tour si lapin Y" - PV per turn if lapin threshold
_PV_PER_TURN_IF_PATTERN = re.compile(
    r"\+(\d+)\s+PV\s*/?\s*tour\s+si\s+(\w+)\s+(\d+)", re.IGNORECASE
)

# "+X PO si Lapin Y / +Z PO si Lapin W" - Multi-threshold PO bonus
_MULTI_PO_IF_PATTERN = re.compile(
    r"\+(\d+)\s+PO\s+si\s+[Ll]apin\s+(\d+)\s*/\s*\+(\d+)\s+PO\s+si\s+[Ll]apin\s+(\d+)",
    re.IGNORECASE,
)

# "-X ATQ si [CardName]" - Card-conditional ATK penalty
_ATK_PENALTY_IF_CARD_PATTERN = re.compile(
    r"-(\d+)\s+ATQ\s+si\s+(.+?)(?:\s+est\s+(?:en\s+jeu|sur\s+le\s+plateau))?$",
    re.IGNORECASE,
)

# "Les [family] ont minimum X ATQ" - Minimum ATK floor
_MIN_ATK_FLOOR_PATTERN = re.compile(
    r"[Ll]es\s+(\w+)\s+ont\s+minimum\s+(\d+)\s+ATQ", re.IGNORECASE
)

# "retourner une carte de la pile, gagne son ATQ" - Deck reveal ATK bonus
_DECK_REVEAL_ATK_PATTERN: re.Pattern[str] = re.compile(
    r"retourner\s+une\s+carte\s+de\s+la\s+pile.*gagne\s+son\s+ATQ", re.IGNORECASE
)

# Deck reveal with multiplier (Yetiir Lvl 2: "x2, jusqu'à la fin du tour")
_DECK_REVEAL_MULT_PATTERN = re.compile(
    r"1/tour.*\+ATQ\s+de\s+la\s+1[èe]re\s+carte\s+de\s+la\s+pile\s*(?:x(\d+))?",
    re.IGNORECASE,
)

# === NEW PATTERNS FOR BONUS_TEXT EFFECTS ===

# Diplo synergy patterns
_DIPLO_CROSS_ATK_PATTERN = re.compile(
    r"\+(\d+)\s*ATQ\s+si\s+diplo\s+(terre|air|mer)", re.IGNORECASE
)
_DIPLO_CROSS_PV_PATTERN = re.compile(
    r"\+(\d+)\s*PV\s+si\s+Diplo\s+(terre|air|mer)", re.IGNORECASE
)
_DIPLO_COMBINED_PATTERN = re.compile(
    r"Les?\s+\+(\d+)\s+ATQ\s+si\s+diplo\s+(\w+),\s*\+(\d+)\s+PV\s+si\s+Diplo\s+(\w+)",
    re.IGNORECASE,
)

# Spell damage patterns
_SPELL_DAMAGE_PATTERN = re.compile(
    r"sorts?:\s*(\d+)\s*(?:dgt|DGT|dégâts)\s*(?:imblocables?|de\s+(?:feu|glace))?",
    re.IGNORECASE,
)
_SPELL_DAMAGE_BONUS_PATTERN = re.compile(
    r"\+(\d+)\s+(?:au\s+)?dgt\s+des\s+sorts\s+des\s+mages", re.IGNORECASE
)
_SPELL_DAMAGE_WITH_KDO_PATTERN = re.compile(
    r"sorts?:\s*(\d+)\s*dgt\s+de\s+glace\s*\+(\d+)\s*par\s+Kdo", re.IGNORECASE
)
_MAGIE_CAROTTES_PATTERN = re.compile(
    r"Magie\s+de\s+carottes\s+(\d+)\s+DGT\s+des\s+sorts", re.IGNORECASE
)

# Defense multiplier patterns
_DOUBLE_PV_DEFENSE_PATTERN = re.compile(
    r"Double\s+ses\s+PV\s+lors\s+des\s+d[ée]fenses", re.IGNORECASE
)

# ATK/PV tradeoff for class patterns
_ATK_PV_TRADEOFF_CLASS_PATTERN = re.compile(
    r"\+(\d+)\s*ATQ\s*/\s*-(\d+)\s*PV\s+pour\s+les\s+(\w+)", re.IGNORECASE
)

# Demon bonus patterns
_DEMON_IMBLOCABLE_BONUS_PATTERN = re.compile(
    r"\+(\d+)\s+dgts?\s+imblocable\s+pour\s+le\s+d[ée]mon", re.IGNORECASE
)
_DEMON_ATK_PV_PATTERN = re.compile(
    r"\+(\d+)\s*ATQ\s*/\s*-(\d+)\s*PV\s+pour\s+le\s+d[ée]mon", re.IGNORECASE
)
_DEMONS_GAIN_BONUSES_PATTERN = re.compile(
    r"[Ll]es\s+[Dd][ée]mons\s+gagnent\s+les\s+bonus\s+comme\s+les\s+autres",
    re.IGNORECASE,
)

# Weapon/Equipment patterns
_WEAPON_EQUIPPED_BONUS_PATTERN = re.compile(
    r"\+(\d+)\s*ATQ\s+si\s+[ée]quip[ée]\s+de\s+(?:la\s+)?(\w+(?:\s+\w+)*)",
    re.IGNORECASE,
)
_WEAPON_ATK_IF_NINJA_PATTERN = re.compile(
    r"[Tt]outes\s+les\s+armes\s+\+(\d+)\s*ATQ\s+si\s+ninja\s+choisi", re.IGNORECASE
)
_WEAPON_ATK_PER_RATON_PATTERN = re.compile(
    r"\+(\d+)\s*ATQ\s+sur\s+une\s+arme\s+par\s+raton\s+en\s+jeu", re.IGNORECASE
)

# Kdo (Gift) patterns
_KDO_PV_BONUS_PATTERN = re.compile(
    r"\+(\d+)\s*PV\s+par\s+Kdo\s+[ée]quip[ée]\s+sur\s+lui", re.IGNORECASE
)
_KDO_ATK_EXTRA_PATTERN = re.compile(
    r"[Ll]es\s+Kdo\s+donnent\s+\+(\d+)\s*ATQ\s+suppl[ée]mentaire", re.IGNORECASE
)

# Sacrifice patterns
_SACRIFICE_FOR_ITEM_PATTERN = re.compile(
    r"sacrifier\s+cette\s+carte,?\s+vous\s+gagnez\s+(\w+(?:\s+\w+)*)", re.IGNORECASE
)
_SACRIFICE_IF_THRESHOLD_PATTERN = re.compile(
    r"si\s+(\d+)\s+(\w+),?\s+sacrifier\s+cette\s+carte", re.IGNORECASE
)

# Imblocable scaling pattern
_IMBLOCABLE_SCALING_PATTERN = re.compile(
    r"\+(\d+)\s+dgt\s+imblocable\s+tous\s+les\s+(\d+)\s+dgt\s+imblocables?",
    re.IGNORECASE,
)

# Per-turn self-damage pattern
_PER_TURN_SELF_DAMAGE_PATTERN = re.compile(
    r"[Vv]ous\s+perdez\s+(\d+)\s+PV\s+(?:imblocables?\s+)?par\s+tour", re.IGNORECASE
)

# Enemy high ATK debuff pattern
_ENEMY_HIGH_ATK_DEBUFF_PATTERN = re.compile(
    r"-(\d+)\s*ATQ\s+pour\s+le\s+monstre\s+ennemi\s+avec\s+le\s+plus\s+d['']?ATQ",
    re.IGNORECASE,
)

# Fire vulnerability pattern
_FIRE_VULNERABILITY_PATTERN = re.compile(
    r"PV\s*=\s*0\s+si\s+magie\s+de\s+feu", re.IGNORECASE
)

# Reduced monture threshold pattern
_REDUCED_MONTURE_PATTERN = re.compile(
    r"il\s+suffit\s+de\s+(\d+)\s+montures?\s+pour\s+activer", re.IGNORECASE
)

# Gold if imblocable pattern
_GOLD_IF_IMBLOCABLE_PATTERN = re.compile(
    r"\+(\d+)\s+d['']?or\s+si\s+des?\s+dgt\s+imblocable\s+sont?\s+inflig[ée]s?",
    re.IGNORECASE,
)

# PV damage from healing pattern
_PV_DAMAGE_FROM_HEALING_PATTERN = re.compile(
    r"[Ii]nflige\s+(\d+)\s+DGT\s+par\s+PV\s+rendu\s+ce\s+tour", re.IGNORECASE
)

# Class threshold bonus pattern (e.g., "+2 ATQ si bonus Archer 2")
_CLASS_BONUS_THRESHOLD_PATTERN = re.compile(
    r"\+(\d+)\s*ATQ\s+si\s+bonus\s+(\w+)\s+(\d+)", re.IGNORECASE
)

# Family count threshold pattern (e.g., "+4 ATQ si raccoon familly 2")
_FAMILY_COUNT_THRESHOLD_PATTERN = re.compile(
    r"\+(\d+)\s*ATQ\s+(?:si|contre\s+si)\s+(?:raccoon\s+familly|lapins?|ratons?)\s+(\d+)",
    re.IGNORECASE,
)

# Hall of Win threshold pattern
_HALL_OF_WIN_THRESHOLD_PATTERN = re.compile(
    r"\+(\d+)\s*ATQ\s+si\s+Hall\s+of\s+win\s+(\d+)", re.IGNORECASE
)

# Cyborg and S-Team combined bonus pattern
_CYBORG_STEAM_BONUS_PATTERN = re.compile(
    r"\+(\d+)\s*ATQ\s+pour\s+les\s+cyborgs?\s+et\s+S-Team", re.IGNORECASE
)

# Women Atlantide bonus pattern
_WOMEN_FAMILY_BONUS_PATTERN = re.compile(
    r"\+(\d+)\s*ATQ\s+pour\s+les\s+femmes\s+(\w+)", re.IGNORECASE
)


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
    Effects like "+2 ATQ pour tous les lapins" multiply by family count.

    Args:
        player: The player whose abilities to resolve.

    Returns:
        AbilityResolutionResult with all bonuses and effects.
    """
    result = AbilityResolutionResult()
    family_counts = count_cards_by_family(player)

    # Map French family names to Family enum
    family_name_map: dict[str, Family] = {
        "lapins": Family.LAPIN,
        "lapin": Family.LAPIN,
        "cyborgs": Family.CYBORG,
        "cyborg": Family.CYBORG,
        "atlantides": Family.ATLANTIDE,
        "atlantide": Family.ATLANTIDE,
        "natures": Family.NATURE,
        "nature": Family.NATURE,
        "neiges": Family.NEIGE,
        "neige": Family.NEIGE,
        "ratons": Family.RATON,
        "raton": Family.RATON,
    }

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

                    # Check if effect targets "tous les [family]"
                    # e.g., "+2 ATQ pour tous les lapins" multiplies by count
                    for_all_match = _FOR_ALL_FAMILY_PATTERN.search(active.effect)
                    if for_all_match:
                        target_family_name = for_all_match.group(1).lower()
                        target_family = family_name_map.get(target_family_name)

                        if target_family and target_family in family_counts:
                            # Multiply bonus by number of target family cards
                            target_count = family_counts[target_family]
                            result.total_attack_bonus += (
                                effect.attack_bonus * target_count
                            )
                            result.total_health_bonus += (
                                effect.health_bonus * target_count
                            )
                            result.total_imblocable_bonus += (
                                effect.imblocable_damage * target_count
                            )
                        else:
                            # Unknown family, apply once
                            result.total_attack_bonus += effect.attack_bonus
                            result.total_health_bonus += effect.health_bonus
                            result.total_imblocable_bonus += effect.imblocable_damage
                    else:
                        # No "pour tous les X" - apply once
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


@dataclass
class LapinBoardLimitResult:
    """Result of calculating Lapin board limit.

    Attributes:
        base_limit: The base board limit (typically 8).
        lapincruste_bonus: Extra slots from Lapincruste cards on board.
        family_threshold_bonus: Extra slots from Lapin family thresholds.
        total_limit: Total board limit for Lapin cards.
    """

    base_limit: int = 8
    lapincruste_bonus: int = 0
    family_threshold_bonus: int = 0

    @property
    def total_limit(self) -> int:
        """Calculate total board limit for Lapins."""
        return self.base_limit + self.lapincruste_bonus + self.family_threshold_bonus


def calculate_lapin_board_limit(
    player: PlayerState,
    base_limit: int = 8,
) -> LapinBoardLimitResult:
    """Calculate the board limit for Lapin cards.

    Lapin cards can exceed the normal board limit through:
    1. Lapincruste Level 1: "Le joueur peut poser 2 lapins supplémentaires en jeu" (+2)
    2. Lapincruste Level 2: "Le joueur peut poser 4 lapins supplémentaires en jeu" (+4)
    3. Family threshold 3: "+1 cartes sur le plateau" (+1)
    4. Family threshold 5: "+2 cartes sur le plateau" (+2)

    Note: Family threshold bonuses are cumulative (threshold 5 includes threshold 3).
    Lapincruste bonuses stack if multiple Lapincruste cards are on board.

    Args:
        player: The player whose Lapin board limit to calculate.
        base_limit: The base board limit (default 8).

    Returns:
        LapinBoardLimitResult with breakdown of limit calculation.
    """
    result = LapinBoardLimitResult(base_limit=base_limit)

    # Count Lapin cards on board for family threshold
    lapin_count = sum(1 for card in player.board if card.family == Family.LAPIN)

    # Calculate family threshold bonus
    # These are cumulative: at 5 Lapins, you get both +1 (from 3) and +2 (from 5) = +3
    # But looking at the data, the thresholds seem to be highest-wins, not cumulative
    # Let's check: threshold 3 = "+1 cartes", threshold 5 = "+2 cartes"
    # The "+2" at threshold 5 is likely the total bonus, not additional
    # So at 5 Lapins: +2 total, at 3-4 Lapins: +1 total
    if lapin_count >= 5:
        result.family_threshold_bonus = 2
    elif lapin_count >= 3:
        result.family_threshold_bonus = 1

    # Calculate Lapincruste bonus from cards on board
    for card in player.board:
        if card.family != Family.LAPIN:
            continue

        # Check bonus_text for Lapincruste effect
        if not card.bonus_text:
            continue

        match = _LAPIN_BOARD_EXPANSION_PATTERN.search(card.bonus_text)
        if match:
            bonus = int(match.group(1))
            result.lapincruste_bonus += bonus

    return result


def can_play_lapin_card(
    player: PlayerState,
    base_limit: int = 8,
) -> bool:
    """Check if a Lapin card can be played on the board.

    Takes into account Lapincruste bonuses and family thresholds
    when determining if another Lapin card can be played.

    Args:
        player: The player attempting to play a Lapin card.
        base_limit: The base board limit (default 8).

    Returns:
        True if a Lapin card can be played, False otherwise.
    """
    limit_result = calculate_lapin_board_limit(player, base_limit)

    # Count current Lapin cards on board
    lapin_count = sum(1 for card in player.board if card.family == Family.LAPIN)

    return lapin_count < limit_result.total_limit


def resolve_bonus_text_effects(
    player: PlayerState,
    opponent: PlayerState | None = None,
) -> BonusTextResult:
    """Resolve bonus_text effects for combat.

    Parses and resolves bonus_text patterns like:
    - "+X ATQ pour les [family/class]" - attack bonus for matching cards
    - "+X ATQ si bonus [Class] Y" - attack bonus if class threshold met
    - "+X ATQ aux [family] alliés" - attack bonus to allied family
    - "-X ATQ pour les [class]" - attack penalty for class
    - "Inflige X dgt quand attaqué" - on-attacked damage
    - "+X dgt imblocable/tour" - per-turn imblocable
    - "Bloque X dgt par sort" - spell damage blocking
    - "+X PO / tour si [condition]" - PO generation
    - "Les raccoon Familly gagne +X ATQ" - raccoon family bonus
    - "+X ATQ si c'est le seul ninja" - solo ninja bonus
    - Card-specific bonuses (Joe, Reine, Raton Mignon, etc.)

    Args:
        player: The player whose bonus_text to resolve.
        opponent: Optional opponent for opponent-dependent effects.

    Returns:
        BonusTextResult with total bonuses from bonus_text.
    """
    result = BonusTextResult()
    class_counts = count_cards_by_class(player)
    family_counts = count_cards_by_family(player)

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
        "hall": Family.HALL_OF_WIN,
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

    # Helper: check if a specific card is on any board
    def card_on_any_board(card_name: str) -> bool:
        """Check if a card with the given name is on any player's board."""
        name_lower = card_name.lower()
        # Check player's board
        for c in player.board:
            if name_lower in c.name.lower():
                return True
        # Check opponent's board if available
        if opponent:
            for c in opponent.board:
                if name_lower in c.name.lower():
                    return True
        return False

    # Helper: check if a specific card is on player's board
    def card_on_player_board(card_name: str) -> bool:
        """Check if a card with the given name is on player's board."""
        name_lower = card_name.lower()
        for c in player.board:
            if name_lower in c.name.lower():
                return True
        return False

    for card in player.board:
        if card.card_type == CardType.DEMON:
            continue  # Demons can't benefit from most bonuses

        bonus = card.bonus_text
        if not bonus:
            continue

        bonus_lower = bonus.lower()

        # === NEGATIVE ATK MODIFIERS ===
        neg_match = _NEGATIVE_ATK_FOR_CLASS_PATTERN.search(bonus)
        if neg_match:
            penalty = int(neg_match.group(1))
            target_name = neg_match.group(2).lower()
            if target_name in class_map_lower:
                target_class = class_map_lower[target_name]
                matching = class_counts.get(target_class, 0)
                if matching > 0:
                    result.attack_penalty += penalty * matching
                    result.effects.append(
                        f"{card.name}: {bonus} (-{penalty * matching})"
                    )

        # === ON-ATTACKED DAMAGE ===
        on_attacked_match = _ON_ATTACKED_DAMAGE_PATTERN.search(bonus)
        if on_attacked_match:
            damage = int(on_attacked_match.group(1))
            result.on_attacked_damage += damage
            result.effects.append(f"{card.name}: {bonus}")

        # === PER-TURN IMBLOCABLE ===
        per_turn_imb_match = _PER_TURN_IMBLOCABLE_PATTERN.search(bonus)
        if per_turn_imb_match:
            imb_damage = int(per_turn_imb_match.group(1))
            result.per_turn_imblocable += imb_damage
            result.effects.append(f"{card.name}: {bonus}")

        # === FLAT IMBLOCABLE DAMAGE ===
        flat_imb_match = _FLAT_IMBLOCABLE_PATTERN.search(bonus)
        if flat_imb_match:
            imb_damage = int(flat_imb_match.group(1))
            result.flat_imblocable_damage += imb_damage
            result.effects.append(f"{card.name}: {imb_damage} imblocable")

        # === LIFELINK ===
        if _LIFELINK_PATTERN.search(bonus):
            result.lifelink = True
            result.effects.append(f"{card.name}: lifelink")

        # === SPELL DAMAGE BLOCKING ===
        spell_block_match = _SPELL_DAMAGE_BLOCK_PATTERN.search(bonus)
        if spell_block_match:
            block_amount = int(spell_block_match.group(1))
            result.spell_damage_block += block_amount
            result.effects.append(f"{card.name}: {bonus}")

        # === PO GENERATION ===
        # "+X PO / tour si [family] Y" - Per-turn PO if threshold met
        po_turn_match = _PO_PER_TURN_IF_PATTERN.search(bonus)
        if po_turn_match:
            po_bonus = int(po_turn_match.group(1))
            target_name = po_turn_match.group(2).lower()
            threshold = int(po_turn_match.group(3))
            # Check family or class threshold
            if target_name in family_map:
                target_family = family_map[target_name]
                if family_counts.get(target_family, 0) >= threshold:
                    result.per_turn_po += po_bonus
                    result.effects.append(f"{card.name}: {bonus}")
            elif target_name in class_map_lower:
                target_class = class_map_lower[target_name]
                if class_counts.get(target_class, 0) >= threshold:
                    result.per_turn_po += po_bonus
                    result.effects.append(f"{card.name}: {bonus}")

        # "+X PO par tranche de Y ratons"
        po_ratons_match = _PO_PER_RATONS_PATTERN.search(bonus)
        if po_ratons_match:
            po_per = int(po_ratons_match.group(1))
            per_count = int(po_ratons_match.group(2))
            raton_count = family_counts.get(Family.RATON, 0)
            if raton_count >= per_count:
                tranches = raton_count // per_count
                result.extra_po += po_per * tranches
                result.effects.append(f"{card.name}: {bonus} ({tranches} tranches)")

        # === RACCOON FAMILY BONUS ===
        raccoon_match = _RACCOON_FAMILY_BONUS_PATTERN.search(bonus)
        if raccoon_match:
            atk_bonus = int(raccoon_match.group(1))
            raton_count = family_counts.get(Family.RATON, 0)
            if raton_count > 0:
                result.attack_bonus += atk_bonus * raton_count
                result.effects.append(f"{card.name}: {bonus} ({raton_count} ratons)")

        # === SOLO NINJA BONUS ===
        solo_ninja_match = _SOLO_NINJA_PATTERN.search(bonus)
        if solo_ninja_match:
            atk_bonus = int(solo_ninja_match.group(1))
            ninja_count = family_counts.get(Family.NINJA, 0)
            if ninja_count == 1:
                result.attack_bonus += atk_bonus
                result.effects.append(f"{card.name}: {bonus}")

        # === CARD-SPECIFIC BONUSES ===
        # "+X dgts si Joe est sur plateau"
        joe_match = _BONUS_IF_JOE_PATTERN.search(bonus)
        if joe_match:
            atk_bonus = int(joe_match.group(1))
            if card_on_any_board("joe"):
                result.attack_bonus += atk_bonus
                result.effects.append(f"{card.name}: {bonus}")

        # "+X ATQ si la Reine est en jeu"
        reine_match = _BONUS_IF_REINE_PATTERN.search(bonus)
        if reine_match:
            atk_bonus = int(reine_match.group(1))
            if card_on_any_board("reine"):
                result.attack_bonus += atk_bonus
                result.effects.append(f"{card.name}: {bonus}")

        # "Gagne +X ATQ si Raton Mignon"
        raton_mignon_match = _BONUS_IF_RATON_MIGNON_PATTERN.search(bonus)
        if raton_mignon_match:
            atk_bonus = int(raton_mignon_match.group(1))
            # Card is actually named "Ratons Mignons" (plural)
            if card_on_player_board("ratons mignons"):
                result.attack_bonus += atk_bonus
                result.effects.append(f"{card.name}: {bonus}")

        # "+X ATQ/+Y PV si maître rat"
        maitre_rat_match = _BONUS_IF_MAITRE_RAT_PATTERN.search(bonus)
        if maitre_rat_match:
            atk_bonus = int(maitre_rat_match.group(1))
            if card_on_player_board("maître rat") or card_on_player_board("maitre rat"):
                result.attack_bonus += atk_bonus
                result.effects.append(f"{card.name}: {bonus}")
                # Also check for PV bonus
                pv_match = _PV_IF_MAITRE_RAT_PATTERN.search(bonus)
                if pv_match:
                    pv_bonus = int(pv_match.group(1))
                    result.health_bonus += pv_bonus

        # "Gagne +X ATQ par économes sur le plateau ennemi"
        econome_enemy_match = _ATK_PER_ENEMY_ECONOME_PATTERN.search(bonus)
        if econome_enemy_match and opponent:
            atk_per = int(econome_enemy_match.group(1))
            enemy_economes = sum(
                1
                for c in opponent.board
                if c.card_class == CardClass.ECONOME and c.card_type != CardType.DEMON
            )
            if enemy_economes > 0:
                result.attack_bonus += atk_per * enemy_economes
                result.effects.append(
                    f"{card.name}: {bonus} ({enemy_economes} economes)"
                )

        # === EXISTING PATTERNS ===
        # Pattern: "+X ATQ si bonus [Class] Y" (threshold-based)
        threshold_match = _BONUS_IF_THRESHOLD_PATTERN.search(bonus)
        if threshold_match:
            atk_bonus = int(threshold_match.group(1))
            target_name = threshold_match.group(2).lower()
            threshold = int(threshold_match.group(3))

            # Check if the threshold is met
            target_class = class_map_lower.get(target_name)
            target_family = family_map.get(target_name)
            if target_class and class_counts.get(target_class, 0) >= threshold:
                result.attack_bonus += atk_bonus
                result.effects.append(f"{card.name}: {bonus}")
            elif target_family and family_counts.get(target_family, 0) >= threshold:
                result.attack_bonus += atk_bonus
                result.effects.append(f"{card.name}: {bonus}")
            continue  # Don't double-process with for_match

        # Pattern: "+X ATQ pour les [target]" or "+X ATQ aux [target]"
        for_match = _BONUS_FOR_FAMILY_PATTERN.search(bonus)
        if for_match:
            atk_bonus = int(for_match.group(1))
            target_name = for_match.group(2).lower()

            # Skip if already handled by more specific patterns
            if "raccoon" in bonus_lower and "familly" in bonus_lower:
                continue  # Handled by raccoon pattern

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

        # === LAPIN-SPECIFIC PATTERNS ===

        # "+X PV /tour si [family] Y" - PV healing per turn if threshold met
        pv_turn_match = _PV_PER_TURN_IF_PATTERN.search(bonus)
        if pv_turn_match:
            pv_bonus = int(pv_turn_match.group(1))
            target_name = pv_turn_match.group(2).lower()
            threshold = int(pv_turn_match.group(3))
            # Check family threshold
            if target_name in family_map:
                target_family = family_map[target_name]
                if family_counts.get(target_family, 0) >= threshold:
                    result.per_turn_pv_heal += pv_bonus
                    result.effects.append(f"{card.name}: {bonus}")

        # "+X PO si Lapin Y / +Z PO si Lapin W" - Multi-threshold PO
        multi_po_match = _MULTI_PO_IF_PATTERN.search(bonus)
        if multi_po_match:
            po1 = int(multi_po_match.group(1))
            threshold1 = int(multi_po_match.group(2))
            po2 = int(multi_po_match.group(3))
            threshold2 = int(multi_po_match.group(4))
            lapin_count = family_counts.get(Family.LAPIN, 0)
            # Apply highest matching threshold (not cumulative)
            if lapin_count >= threshold2:
                result.per_turn_po += po2
                result.effects.append(f"{card.name}: +{po2} PO (Lapin {threshold2})")
            elif lapin_count >= threshold1:
                result.per_turn_po += po1
                result.effects.append(f"{card.name}: +{po1} PO (Lapin {threshold1})")

        # "-X ATQ si [CardName]" - Card-conditional ATK penalty
        atk_penalty_match = _ATK_PENALTY_IF_CARD_PATTERN.search(bonus)
        if atk_penalty_match:
            penalty = int(atk_penalty_match.group(1))
            card_name = atk_penalty_match.group(2).strip().lower()
            # Check if the specified card is on player's board
            if card_on_player_board(card_name):
                result.attack_penalty += penalty
                result.effects.append(f"{card.name}: -{penalty} ATQ ({card_name})")

        # "Les [family] ont minimum X ATQ" - Minimum ATK floor
        min_atk_match = _MIN_ATK_FLOOR_PATTERN.search(bonus)
        if min_atk_match:
            target_name = min_atk_match.group(1).lower()
            min_atk = int(min_atk_match.group(2))
            if target_name in family_map:
                target_family = family_map[target_name]
                # Store the floor - it will be applied during damage calculation
                if min_atk > result.min_atk_floor:
                    result.min_atk_floor = min_atk
                    result.min_atk_family = target_family.value
                    result.effects.append(f"{card.name}: {bonus}")

        # "retourner une carte de la pile, gagne son ATQ" - Deck reveal ATK
        deck_reveal_match = _DECK_REVEAL_ATK_PATTERN.search(bonus)
        if deck_reveal_match:
            # This effect reveals a card from deck and adds its ATK
            # For now, we'll use an average ATK value (3) as placeholder
            # In a full implementation, this would interact with the deck
            avg_atk = 3  # Average card ATK as approximation
            result.deck_reveal_atk += avg_atk
            result.effects.append(f"{card.name}: {bonus} (~{avg_atk} ATK)")

        # === DECK REVEAL WITH MULTIPLIER (Yetiir) ===
        deck_mult_match = _DECK_REVEAL_MULT_PATTERN.search(bonus)
        if deck_mult_match:
            avg_atk = 3  # Average card ATK
            multiplier = 1
            if deck_mult_match.group(1):
                multiplier = int(deck_mult_match.group(1))
            result.deck_reveal_atk += avg_atk
            result.deck_reveal_multiplier = max(
                result.deck_reveal_multiplier, multiplier
            )
            result.effects.append(f"{card.name}: {bonus} (~{avg_atk * multiplier} ATK)")

        # === DIPLO SYNERGY ===
        diplo_combined = _DIPLO_COMBINED_PATTERN.search(bonus)
        if diplo_combined:
            atk_bonus_val = int(diplo_combined.group(1))
            atk_diplo = diplo_combined.group(2).lower()
            pv_bonus_val = int(diplo_combined.group(3))
            pv_diplo = diplo_combined.group(4).lower()

            # Check if we have the required Diplo cards
            diplo_cards_on_board = [
                c.card_class.value.lower()
                for c in player.board
                if c.card_class == CardClass.DIPLO
            ]
            # Also check card names for Diplo-Terre, Diplo-Air, Diplo-Mer
            for c in player.board:
                name_lower = c.name.lower()
                if "diplo-terre" in name_lower or "diplo terre" in name_lower:
                    diplo_cards_on_board.append("terre")
                if "diplo-air" in name_lower or "diplo air" in name_lower:
                    diplo_cards_on_board.append("air")
                if "diplo-mer" in name_lower or "diplo mer" in name_lower:
                    diplo_cards_on_board.append("mer")

            if atk_diplo in diplo_cards_on_board:
                result.diplo_atk_bonus += atk_bonus_val
                result.effects.append(
                    f"{card.name}: +{atk_bonus_val} ATQ (Diplo {atk_diplo})"
                )
            if pv_diplo in diplo_cards_on_board:
                result.diplo_pv_bonus += pv_bonus_val
                result.effects.append(
                    f"{card.name}: +{pv_bonus_val} PV (Diplo {pv_diplo})"
                )

        # === SPELL DAMAGE ===
        spell_damage_match = _SPELL_DAMAGE_PATTERN.search(bonus)
        if spell_damage_match:
            damage = int(spell_damage_match.group(1))
            result.spell_damage += damage
            result.effects.append(f"{card.name}: sort {damage} dgt")

        spell_bonus_match = _SPELL_DAMAGE_BONUS_PATTERN.search(bonus)
        if spell_bonus_match:
            bonus_val = int(spell_bonus_match.group(1))
            result.spell_damage_bonus += bonus_val
            result.effects.append(f"{card.name}: +{bonus_val} dgt sorts")

        magie_carottes_match = _MAGIE_CAROTTES_PATTERN.search(bonus)
        if magie_carottes_match:
            damage = int(magie_carottes_match.group(1))
            result.spell_damage += damage
            result.effects.append(f"{card.name}: Magie carottes {damage} dgt")

        # === DEFENSE MULTIPLIER ===
        if _DOUBLE_PV_DEFENSE_PATTERN.search(bonus):
            result.defense_multiplier = max(result.defense_multiplier, 2)
            result.effects.append(f"{card.name}: Double PV défense")

        # === ATK/PV TRADEOFF FOR CLASS ===
        tradeoff_match = _ATK_PV_TRADEOFF_CLASS_PATTERN.search(bonus)
        if tradeoff_match:
            atk_val = int(tradeoff_match.group(1))
            pv_val = int(tradeoff_match.group(2))
            target_class_name = tradeoff_match.group(3).lower()
            if target_class_name in class_map_lower:
                target_class = class_map_lower[target_class_name]
                matching = class_counts.get(target_class, 0)
                if matching > 0:
                    result.attack_bonus += atk_val * matching
                    result.health_penalty += pv_val * matching
                    result.effects.append(
                        f"{card.name}: +{atk_val * matching} ATQ / "
                        f"-{pv_val * matching} PV ({matching} {target_class_name})"
                    )

        # === DEMON BONUSES ===
        demon_imb_match = _DEMON_IMBLOCABLE_BONUS_PATTERN.search(bonus)
        if demon_imb_match:
            imb_bonus = int(demon_imb_match.group(1))
            result.demon_imblocable_bonus += imb_bonus
            result.effects.append(f"{card.name}: +{imb_bonus} imb démon")

        demon_atk_pv_match = _DEMON_ATK_PV_PATTERN.search(bonus)
        if demon_atk_pv_match:
            atk_val = int(demon_atk_pv_match.group(1))
            pv_val = int(demon_atk_pv_match.group(2))
            result.demon_atk_bonus += atk_val
            result.demon_pv_penalty += pv_val
            result.effects.append(f"{card.name}: +{atk_val}/-{pv_val} démon")

        if _DEMONS_GAIN_BONUSES_PATTERN.search(bonus):
            result.demons_gain_all_bonuses = True
            result.effects.append(f"{card.name}: Démons gagnent tous bonus")

        # === WEAPON/EQUIPMENT ===
        weapon_ninja_match = _WEAPON_ATK_IF_NINJA_PATTERN.search(bonus)
        if weapon_ninja_match:
            # TODO: Check if ninja was chosen (requires game state tracking)
            atk_val = int(weapon_ninja_match.group(1))
            # For now, store the potential bonus
            result.weapon_atk_bonus += atk_val
            result.effects.append(f"{card.name}: +{atk_val} ATQ armes (ninja)")

        weapon_raton_match = _WEAPON_ATK_PER_RATON_PATTERN.search(bonus)
        if weapon_raton_match:
            atk_per = int(weapon_raton_match.group(1))
            raton_count = family_counts.get(Family.RATON, 0)
            if raton_count > 0:
                total_bonus = atk_per * raton_count
                result.weapon_atk_bonus += total_bonus
                result.effects.append(
                    f"{card.name}: +{total_bonus} ATQ arme ({raton_count} ratons)"
                )

        # === KDO (GIFT) BONUSES ===
        kdo_pv_match = _KDO_PV_BONUS_PATTERN.search(bonus)
        if kdo_pv_match:
            pv_per = int(kdo_pv_match.group(1))
            result.kdo_pv_bonus = max(result.kdo_pv_bonus, pv_per)
            result.effects.append(f"{card.name}: +{pv_per} PV par Kdo")

        kdo_atk_match = _KDO_ATK_EXTRA_PATTERN.search(bonus)
        if kdo_atk_match:
            atk_extra = int(kdo_atk_match.group(1))
            result.kdo_atk_bonus += atk_extra
            result.effects.append(f"{card.name}: +{atk_extra} ATQ par Kdo")

        # === IMBLOCABLE SCALING ===
        imb_scaling_match = _IMBLOCABLE_SCALING_PATTERN.search(bonus)
        if imb_scaling_match:
            extra = int(imb_scaling_match.group(1))
            ratio = int(imb_scaling_match.group(2))
            result.imblocable_scaling = extra
            result.imblocable_scaling_ratio = ratio
            result.effects.append(f"{card.name}: +{extra} imb tous les {ratio} imb")

        # === PER-TURN SELF DAMAGE ===
        per_turn_self_dmg = _PER_TURN_SELF_DAMAGE_PATTERN.search(bonus)
        if per_turn_self_dmg:
            dmg = int(per_turn_self_dmg.group(1))
            result.per_turn_self_damage += dmg
            result.effects.append(f"{card.name}: -{dmg} PV/tour")

        # === ENEMY HIGH ATK DEBUFF ===
        enemy_debuff_match = _ENEMY_HIGH_ATK_DEBUFF_PATTERN.search(bonus)
        if enemy_debuff_match:
            debuff = int(enemy_debuff_match.group(1))
            result.enemy_high_atk_debuff += debuff
            result.effects.append(f"{card.name}: -{debuff} ATQ ennemi fort")

        # === FIRE VULNERABILITY ===
        if _FIRE_VULNERABILITY_PATTERN.search(bonus):
            result.fire_vulnerability = True
            result.effects.append(f"{card.name}: Vulnérable feu")

        # === REDUCED MONTURE THRESHOLD ===
        reduced_monture_match = _REDUCED_MONTURE_PATTERN.search(bonus)
        if reduced_monture_match:
            threshold = int(reduced_monture_match.group(1))
            if (
                result.reduced_monture_threshold == 0
                or threshold < result.reduced_monture_threshold
            ):
                result.reduced_monture_threshold = threshold
            result.effects.append(f"{card.name}: Monture à {threshold}")

        # === GOLD IF IMBLOCABLE ===
        gold_imb_match = _GOLD_IF_IMBLOCABLE_PATTERN.search(bonus)
        if gold_imb_match:
            gold = int(gold_imb_match.group(1))
            result.gold_if_imblocable += gold
            result.effects.append(f"{card.name}: +{gold} or si imb")

        # === PV DAMAGE FROM HEALING ===
        pv_from_heal_match = _PV_DAMAGE_FROM_HEALING_PATTERN.search(bonus)
        if pv_from_heal_match:
            dmg_per_heal = int(pv_from_heal_match.group(1))
            result.pv_damage_from_healing = max(
                result.pv_damage_from_healing, dmg_per_heal
            )
            result.effects.append(f"{card.name}: {dmg_per_heal} dgt par PV rendu")

        # === CLASS BONUS THRESHOLD ===
        class_bonus_match = _CLASS_BONUS_THRESHOLD_PATTERN.search(bonus)
        if class_bonus_match:
            atk_val = int(class_bonus_match.group(1))
            class_name = class_bonus_match.group(2).lower()
            threshold = int(class_bonus_match.group(3))
            if class_name in class_map_lower:
                target_class = class_map_lower[class_name]
                if class_counts.get(target_class, 0) >= threshold:
                    result.attack_bonus += atk_val
                    result.effects.append(
                        f"{card.name}: +{atk_val} ATQ (bonus {class_name} {threshold})"
                    )

        # === FAMILY COUNT THRESHOLD ===
        family_count_match = _FAMILY_COUNT_THRESHOLD_PATTERN.search(bonus)
        if family_count_match:
            atk_val = int(family_count_match.group(1))
            threshold = int(family_count_match.group(2))
            # Check raccoon/lapin/raton family
            if "raccoon" in bonus_lower or "raton" in bonus_lower:
                if family_counts.get(Family.RATON, 0) >= threshold:
                    result.attack_bonus += atk_val
                    result.effects.append(
                        f"{card.name}: +{atk_val} ATQ (raton {threshold})"
                    )
            elif "lapin" in bonus_lower:
                if family_counts.get(Family.LAPIN, 0) >= threshold:
                    result.attack_bonus += atk_val
                    result.effects.append(
                        f"{card.name}: +{atk_val} ATQ (lapin {threshold})"
                    )

        # === HALL OF WIN THRESHOLD ===
        hall_match = _HALL_OF_WIN_THRESHOLD_PATTERN.search(bonus)
        if hall_match:
            atk_val = int(hall_match.group(1))
            threshold = int(hall_match.group(2))
            if family_counts.get(Family.HALL_OF_WIN, 0) >= threshold:
                result.attack_bonus += atk_val
                result.effects.append(f"{card.name}: +{atk_val} ATQ (Hall {threshold})")

        # === CYBORG AND S-TEAM COMBINED BONUS ===
        cyborg_steam_match = _CYBORG_STEAM_BONUS_PATTERN.search(bonus)
        if cyborg_steam_match:
            atk_val = int(cyborg_steam_match.group(1))
            cyborg_count = family_counts.get(Family.CYBORG, 0)
            steam_count = class_counts.get(CardClass.S_TEAM, 0)
            total = cyborg_count + steam_count
            if total > 0:
                result.attack_bonus += atk_val * total
                result.effects.append(
                    f"{card.name}: +{atk_val * total} ATQ ({total} cyborg+steam)"
                )

        # === WOMEN FAMILY BONUS ===
        # This is a placeholder - actual implementation would need gender data
        women_match = _WOMEN_FAMILY_BONUS_PATTERN.search(bonus)
        if women_match:
            atk_val = int(women_match.group(1))
            target_family_name = women_match.group(2).lower()
            if target_family_name in family_map:
                target_fam = family_map[target_family_name]
                # Approximate: count half of family as "women"
                fam_count = family_counts.get(target_fam, 0)
                women_count = fam_count // 2 + 1
                result.attack_bonus += atk_val * women_count
                result.effects.append(
                    f"{card.name}: +{atk_val * women_count} ATQ (~{women_count} femmes)"
                )

    # === DEMON-SPECIFIC EFFECTS ===
    # Demons are normally skipped, but we need to parse their own bonus_text
    # for effects like flat imblocable damage that they inherently have.
    for card in player.board:
        if card.card_type != CardType.DEMON:
            continue

        bonus = card.bonus_text
        if not bonus:
            continue

        # Flat imblocable damage (e.g., "10 dgt imblocable")
        flat_imb_match = _FLAT_IMBLOCABLE_PATTERN.search(bonus)
        if flat_imb_match:
            imb_damage = int(flat_imb_match.group(1))
            result.flat_imblocable_damage += imb_damage
            result.effects.append(f"{card.name}: {imb_damage} imblocable")

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
        total_pv_heal: Total PV healing from bonus_text effects.
        total_po_bonus: Total PO bonus from bonus_text effects.
        cards_with_effects: List of cards that have per-turn effects.
    """

    total_self_damage: int = 0
    total_pv_heal: int = 0
    total_po_bonus: int = 0
    cards_with_effects: list[str] = field(default_factory=list)


def resolve_per_turn_effects(player: PlayerState) -> PerTurnEffectResult:
    """Resolve per-turn effects for a player.

    Per-turn effects are effects that apply each turn, such as:
    - "Vous perdez X PV par tour" (you lose X HP per turn)
    - "+X PV /tour si lapin Y" (heal X HP per turn if lapin threshold)
    - "+X PO /tour si lapin Y" (gain X PO per turn if lapin threshold)

    These are separate from:
    - Combat self-damage (e.g., Berserker's -2 PV from class ability)
    - One-time effects

    Args:
        player: The player whose per-turn effects to resolve.

    Returns:
        PerTurnEffectResult with total damage, healing, PO and affected cards.
    """
    result = PerTurnEffectResult()

    # Handle per-turn self-damage from class abilities (e.g., Mutanus)
    for card in player.board:
        per_turn_dmg = card.class_abilities.per_turn_self_damage
        if per_turn_dmg > 0:
            result.total_self_damage += per_turn_dmg
            result.cards_with_effects.append(card.name)

    # Handle per-turn bonus_text effects (healing and PO)
    bonus_text_result = resolve_bonus_text_effects(player, None)
    if bonus_text_result.per_turn_pv_heal > 0:
        result.total_pv_heal += bonus_text_result.per_turn_pv_heal
    if bonus_text_result.per_turn_po > 0:
        result.total_po_bonus += bonus_text_result.per_turn_po

    return result


def apply_per_turn_effects(player: PlayerState) -> PerTurnEffectResult:
    """Apply per-turn effects to a player and return the result.

    This function both calculates and applies per-turn effects:
    - Self-damage (e.g., from Mutanus "Vous perdez X PV par tour")
    - PV healing (e.g., from "+X PV /tour si lapin Y")
    - PO bonus is calculated but NOT applied here (applied at turn start)

    Call this during the end-of-turn phase.

    Args:
        player: The player to apply per-turn effects to.

    Returns:
        PerTurnEffectResult with damage, healing, and PO bonus.
    """
    effects = resolve_per_turn_effects(player)

    # Apply self-damage
    if effects.total_self_damage > 0:
        player.health -= effects.total_self_damage

    # Apply healing (capped at maximum health if you have one, otherwise unlimited)
    if effects.total_pv_heal > 0:
        player.health += effects.total_pv_heal

    # Note: PO bonus is not applied here - it should be applied at turn start
    # via _start_turn() in the engine

    return effects
