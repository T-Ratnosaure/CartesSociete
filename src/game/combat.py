"""Combat resolution for CartesSociete.

This module handles the combat phase, including damage calculation,
special damage types (imblocable), and applying damage to players.
"""

from dataclasses import dataclass, field

from .abilities import (
    resolve_all_abilities,
    resolve_bonus_text_effects,
    resolve_conditional_abilities,
)
from .state import GameState, PlayerState


@dataclass
class DamageBreakdown:
    """Breakdown of damage dealt to a player.

    Attributes:
        source_player: The player dealing damage.
        target_player: The player receiving damage.
        base_attack: Base attack from card stats.
        attack_bonus: Attack bonus from class/family abilities.
        bonus_text_attack: Attack bonus from bonus_text effects.
        diplo_attack_bonus: Attack bonus from Diplo synergy.
        conditional_attack_bonus: Attack bonus from conditional abilities (Dragon).
        attack_multiplier: Attack multiplier from conditional abilities (Dragon).
        total_attack: Total attack value (base + bonuses) * multiplier.
        base_defense: Base defense from card stats.
        defense_bonus: Defense bonus from class/family abilities.
        defense_multiplier: Multiplier from bonus_text (e.g., "Double PV défense").
        target_defense: Total defense (base + bonus) * multiplier.
        base_damage: Normal damage (attack - defense, min 0).
        imblocable_damage: Damage that bypasses defense.
        conditional_imblocable: Imblocable from Dragon conditional abilities.
        spell_damage: Damage from spells (mage abilities).
        total_damage: Total damage dealt to target's PV.
    """

    source_player: PlayerState
    target_player: PlayerState
    base_attack: int
    attack_bonus: int
    bonus_text_attack: int
    diplo_attack_bonus: int
    conditional_attack_bonus: int
    attack_multiplier: int
    total_attack: int
    base_defense: int
    defense_bonus: int
    defense_multiplier: int
    target_defense: int
    base_damage: int
    imblocable_damage: int
    conditional_imblocable: int
    spell_damage: int
    total_damage: int


@dataclass
class CombatResult:
    """Result of combat resolution for a turn.

    Attributes:
        damage_dealt: List of damage breakdowns for each attacker-target pair.
        eliminations: List of players eliminated this combat.
        health_changes: Dict mapping player_id to health change.
        self_damage: Dict mapping player_id to self-damage (e.g., Berserker).
        on_attacked_damage: Dict mapping player_id to damage from on-attacked effects.
        spell_damage: Dict mapping player_id to spell damage dealt.
        health_penalty: Dict mapping player_id to HP penalty from bonus_text.
        diplo_bonuses: Dict mapping player_id to Diplo ATK/PV bonuses applied.
    """

    damage_dealt: list[DamageBreakdown] = field(default_factory=list)
    eliminations: list[PlayerState] = field(default_factory=list)
    health_changes: dict[int, int] = field(default_factory=dict)
    self_damage: dict[int, int] = field(default_factory=dict)
    on_attacked_damage: dict[int, int] = field(default_factory=dict)
    spell_damage: dict[int, int] = field(default_factory=dict)
    health_penalty: dict[int, int] = field(default_factory=dict)
    diplo_bonuses: dict[int, tuple[int, int]] = field(default_factory=dict)


def calculate_imblocable_damage(player: PlayerState) -> int:
    """Calculate imblocable damage from cards with imblocable abilities.

    Imblocable damage bypasses the normal combat formula (ATK - HP).
    This is primarily a Nature family ability but can appear on other cards.

    Args:
        player: The player whose imblocable damage to calculate.

    Returns:
        Total imblocable damage from all cards on the board.
    """
    imblocable = 0

    for card in player.board:
        # Use the structured imblocable_damage field from ClassAbilities
        # This is pre-parsed during card loading for reliability
        imblocable += card.class_abilities.imblocable_damage

    return imblocable


def calculate_damage(
    attacker: PlayerState,
    defender: PlayerState,
) -> DamageBreakdown:
    """Calculate damage from one player to another.

    Combat formula:
    1. Calculate attacker's total attack (base + ability bonuses + bonus_text + diplo)
    2. Calculate defender's total HP/defense (base + ability bonuses) * multiplier
    3. Base damage = attack - defense (min 0)
    4. Add imblocable damage (bypasses defense)
    5. Add conditional imblocable (Dragon PO abilities)
    6. Add spell damage (from mage abilities)
    7. Total damage = base + imblocable + conditional + spell

    Args:
        attacker: The attacking player.
        defender: The defending player.

    Returns:
        DamageBreakdown with full calculation details.
    """
    # Resolve abilities for both players
    attacker_abilities = resolve_all_abilities(attacker)
    defender_abilities = resolve_all_abilities(defender)

    # Resolve bonus_text effects for both players
    attacker_bonus_text = resolve_bonus_text_effects(attacker, defender)
    defender_bonus_text = resolve_bonus_text_effects(defender, attacker)

    # Resolve conditional abilities (Dragon PO spending)
    conditional_result = resolve_conditional_abilities(attacker)

    # Calculate attack with all bonuses
    base_attack = attacker.get_total_attack()

    # Apply minimum ATK floor if applicable (e.g., "Les lapins ont minimum 4 ATQ")
    if attacker_bonus_text.min_atk_floor > 0 and attacker_bonus_text.min_atk_family:
        from src.cards.models import Family

        target_family = Family(attacker_bonus_text.min_atk_family)
        # Add attack bonus to bring cards below floor up to minimum
        min_atk_bonus = 0
        for card in attacker.board:
            if (
                card.family == target_family
                and card.attack < attacker_bonus_text.min_atk_floor
            ):
                min_atk_bonus += attacker_bonus_text.min_atk_floor - card.attack
        base_attack += min_atk_bonus

    attack_bonus = attacker_abilities.total_attack_bonus
    bonus_text_attack = attacker_bonus_text.attack_bonus
    # Add Diplo synergy ATK bonus
    diplo_attack_bonus = attacker_bonus_text.diplo_atk_bonus
    # Add deck reveal ATK bonus (from Lapindomptable)
    deck_reveal_atk = attacker_bonus_text.deck_reveal_atk
    # Apply attack penalty from attacker's bonus_text (e.g., "-1 ATQ pour les cyborgs")
    attack_penalty = attacker_bonus_text.attack_penalty
    # Apply enemy high ATK debuff from defender's bonus_text
    enemy_debuff = defender_bonus_text.enemy_high_atk_debuff
    conditional_attack_bonus = conditional_result.total_attack_bonus
    attack_multiplier = conditional_result.attack_multiplier

    # Apply multiplier to base attack, then add bonuses minus penalties
    # Multiplier only affects base attack (from Dragon conditional abilities)
    total_attack = max(
        0,
        (base_attack * attack_multiplier)
        + attack_bonus
        + bonus_text_attack
        + diplo_attack_bonus
        + deck_reveal_atk
        + conditional_attack_bonus
        - attack_penalty
        - enemy_debuff,
    )

    # Calculate defense with ability bonuses and multiplier
    base_defense = defender.get_total_health()
    defense_bonus = defender_abilities.total_health_bonus
    # Add Diplo PV bonus to defense
    diplo_pv_bonus = defender_bonus_text.diplo_pv_bonus
    # Apply defense multiplier (e.g., "Double PV défense")
    defense_multiplier = defender_bonus_text.defense_multiplier
    target_defense = (
        base_defense + defense_bonus + diplo_pv_bonus
    ) * defense_multiplier

    # Base damage: attack minus defense, minimum 0
    base_damage = max(0, total_attack - target_defense)

    # Imblocable damage bypasses defense entirely
    # Includes both pre-parsed imblocable and ability bonuses
    imblocable_damage = (
        calculate_imblocable_damage(attacker)
        + attacker_abilities.total_imblocable_bonus
    )

    # Conditional imblocable from Dragon PO abilities
    conditional_imblocable = conditional_result.total_imblocable_damage

    # Spell damage (from mage abilities, subject to spell_damage_block)
    spell_damage = max(
        0,
        attacker_bonus_text.spell_damage
        + attacker_bonus_text.spell_damage_bonus
        - defender_bonus_text.spell_damage_block,
    )

    total_damage = (
        base_damage + imblocable_damage + conditional_imblocable + spell_damage
    )

    return DamageBreakdown(
        source_player=attacker,
        target_player=defender,
        base_attack=base_attack,
        attack_bonus=attack_bonus,
        bonus_text_attack=bonus_text_attack,
        diplo_attack_bonus=diplo_attack_bonus,
        conditional_attack_bonus=conditional_attack_bonus,
        attack_multiplier=attack_multiplier,
        total_attack=total_attack,
        base_defense=base_defense,
        defense_bonus=defense_bonus,
        defense_multiplier=defense_multiplier,
        target_defense=target_defense,
        base_damage=base_damage,
        imblocable_damage=imblocable_damage,
        conditional_imblocable=conditional_imblocable,
        spell_damage=spell_damage,
        total_damage=total_damage,
    )


def resolve_combat(state: GameState) -> CombatResult:
    """Resolve combat for all players simultaneously.

    In CartesSociete, all players attack all opponents simultaneously.
    Damage is calculated for each attacker-defender pair, then applied.
    Self-damage from abilities (e.g., Berserker) is also applied.
    On-attacked damage is dealt back to attackers by defenders.
    Spell damage, health penalties, and Diplo bonuses are tracked.

    Args:
        state: Current game state.

    Returns:
        CombatResult with all damage dealt and eliminations.
    """
    result = CombatResult()
    alive_players = state.get_alive_players()

    # Calculate all damage first (simultaneous combat)
    damage_to_apply: dict[int, int] = {p.player_id: 0 for p in alive_players}

    for attacker in alive_players:
        for defender in alive_players:
            if attacker.player_id != defender.player_id:
                breakdown = calculate_damage(attacker, defender)
                result.damage_dealt.append(breakdown)
                damage_to_apply[defender.player_id] += breakdown.total_damage

                # Track spell damage
                if breakdown.spell_damage > 0:
                    if attacker.player_id not in result.spell_damage:
                        result.spell_damage[attacker.player_id] = 0
                    result.spell_damage[attacker.player_id] += breakdown.spell_damage

                # Track Diplo bonuses
                if breakdown.diplo_attack_bonus > 0:
                    atk, pv = result.diplo_bonuses.get(attacker.player_id, (0, 0))
                    result.diplo_bonuses[attacker.player_id] = (
                        atk + breakdown.diplo_attack_bonus,
                        pv,
                    )

    # Calculate on-attacked damage (defenders damage attackers when attacked)
    # This is separate from the main damage calculation
    for defender in alive_players:
        defender_bonus_text = resolve_bonus_text_effects(defender, None)
        if defender_bonus_text.on_attacked_damage > 0:
            # Defender deals this damage to all attackers (other players)
            for attacker in alive_players:
                if attacker.player_id != defender.player_id:
                    damage_to_apply[attacker.player_id] += (
                        defender_bonus_text.on_attacked_damage
                    )
            result.on_attacked_damage[defender.player_id] = (
                defender_bonus_text.on_attacked_damage
            )

        # Add per-turn imblocable from bonus_text to damage
        if defender_bonus_text.per_turn_imblocable > 0:
            # Per-turn imblocable damages all opponents
            for opponent in alive_players:
                if opponent.player_id != defender.player_id:
                    damage_to_apply[opponent.player_id] += (
                        defender_bonus_text.per_turn_imblocable
                    )

        # Track Diplo PV bonuses
        if defender_bonus_text.diplo_pv_bonus > 0:
            atk, pv = result.diplo_bonuses.get(defender.player_id, (0, 0))
            result.diplo_bonuses[defender.player_id] = (
                atk,
                pv + defender_bonus_text.diplo_pv_bonus,
            )

        # Track health penalty from bonus_text (e.g., ATK/PV tradeoff)
        if defender_bonus_text.health_penalty > 0:
            result.health_penalty[defender.player_id] = (
                defender_bonus_text.health_penalty
            )

    # Calculate self-damage from abilities (e.g., Berserker)
    for player in alive_players:
        abilities = resolve_all_abilities(player)
        if abilities.total_self_damage > 0:
            result.self_damage[player.player_id] = abilities.total_self_damage
            damage_to_apply[player.player_id] += abilities.total_self_damage

    # Apply all damage simultaneously
    for player in alive_players:
        damage = damage_to_apply[player.player_id]
        if damage > 0:
            player.health -= damage
            result.health_changes[player.player_id] = -damage

            # Check for elimination
            if player.health <= 0:
                player.eliminated = True
                result.eliminations.append(player)

    return result


def get_combat_summary(result: CombatResult) -> str:
    """Generate a human-readable summary of combat results.

    Args:
        result: The combat result to summarize.

    Returns:
        Multi-line string describing the combat outcome.
    """
    lines = ["=== Combat Resolution ==="]

    # Group damage by attacker
    by_attacker: dict[int, list[DamageBreakdown]] = {}
    for breakdown in result.damage_dealt:
        attacker_id = breakdown.source_player.player_id
        if attacker_id not in by_attacker:
            by_attacker[attacker_id] = []
        by_attacker[attacker_id].append(breakdown)

    for attacker_id, breakdowns in by_attacker.items():
        attacker = breakdowns[0].source_player
        bd = breakdowns[0]
        lines.append(f"\n{attacker.name} attacks:")

        # Show attack breakdown with all bonuses
        attack_parts = [f"{bd.base_attack} base"]
        if bd.attack_multiplier > 1:
            attack_parts[0] = f"{bd.base_attack}x{bd.attack_multiplier} base"
        if bd.attack_bonus > 0:
            attack_parts.append(f"{bd.attack_bonus} ability")
        if bd.bonus_text_attack > 0:
            attack_parts.append(f"{bd.bonus_text_attack} bonus_text")
        if bd.diplo_attack_bonus > 0:
            attack_parts.append(f"{bd.diplo_attack_bonus} diplo")
        if bd.conditional_attack_bonus > 0:
            attack_parts.append(f"{bd.conditional_attack_bonus} conditional")
        if len(attack_parts) > 1:
            lines.append(f"  ATK: {' + '.join(attack_parts)} = {bd.total_attack}")
        else:
            lines.append(f"  ATK: {bd.total_attack}")

        for bd in breakdowns:
            # Show defense breakdown with bonuses and multiplier
            if bd.defense_multiplier > 1:
                base_def = bd.base_defense + bd.defense_bonus
                mult = bd.defense_multiplier
                defense_str = f"(DEF: {base_def}x{mult}={bd.target_defense})"
            elif bd.defense_bonus > 0:
                defense_str = (
                    f"(DEF: {bd.base_defense}+{bd.defense_bonus}={bd.target_defense})"
                )
            else:
                defense_str = f"(DEF: {bd.target_defense})"

            # Build imblocable string
            if bd.conditional_imblocable > 0:
                imblocable_str = (
                    f"{bd.imblocable_damage}+{bd.conditional_imblocable} "
                    f"(Dragon) imblocable"
                )
            else:
                imblocable_str = f"{bd.imblocable_damage} imblocable"

            # Build spell damage string
            spell_str = f" + {bd.spell_damage} spell" if bd.spell_damage > 0 else ""

            lines.append(
                f"  vs {bd.target_player.name} {defense_str}: "
                f"{bd.base_damage} base + {imblocable_str}{spell_str} = "
                f"{bd.total_damage} damage"
            )

    # Self-damage from abilities (e.g., Berserker)
    if result.self_damage:
        lines.append("\nSelf-damage (Berserker abilities):")
        for player_id, damage in result.self_damage.items():
            # Find player name
            for bd in result.damage_dealt:
                if bd.source_player.player_id == player_id:
                    lines.append(f"  {bd.source_player.name}: {damage} self-damage")
                    break

    # On-attacked damage (from bonus_text effects)
    if result.on_attacked_damage:
        lines.append("\nOn-attacked damage (dealt by defenders):")
        for player_id, damage in result.on_attacked_damage.items():
            # Find player name
            for bd in result.damage_dealt:
                if bd.target_player.player_id == player_id:
                    name = bd.target_player.name
                    lines.append(f"  {name}: deals {damage} damage when attacked")
                    break

    # Spell damage
    if result.spell_damage:
        lines.append("\nSpell damage (mage abilities):")
        for player_id, damage in result.spell_damage.items():
            # Find player name
            for bd in result.damage_dealt:
                if bd.source_player.player_id == player_id:
                    lines.append(f"  {bd.source_player.name}: {damage} spell damage")
                    break

    # Diplo bonuses
    if result.diplo_bonuses:
        lines.append("\nDiplo synergy bonuses:")
        for player_id, (atk, pv) in result.diplo_bonuses.items():
            # Find player name
            for bd in result.damage_dealt:
                if bd.source_player.player_id == player_id:
                    parts = []
                    if atk > 0:
                        parts.append(f"+{atk} ATK")
                    if pv > 0:
                        parts.append(f"+{pv} PV")
                    if parts:
                        lines.append(f"  {bd.source_player.name}: {', '.join(parts)}")
                    break

    # Health changes
    lines.append("\nHealth changes:")
    for player_id, change in result.health_changes.items():
        # Find player name
        for bd in result.damage_dealt:
            if bd.target_player.player_id == player_id:
                lines.append(
                    f"  {bd.target_player.name}: {change:+d} "
                    f"(now {bd.target_player.health} PV)"
                )
                break

    # Eliminations
    if result.eliminations:
        lines.append("\nEliminations:")
        for player in result.eliminations:
            lines.append(f"  {player.name} has been eliminated!")

    return "\n".join(lines)
