"""Combat resolution for CartesSociete.

This module handles the combat phase, including damage calculation,
special damage types (imblocable), and applying damage to players.
"""

from dataclasses import dataclass, field

from .abilities import resolve_all_abilities
from .state import GameState, PlayerState


@dataclass
class DamageBreakdown:
    """Breakdown of damage dealt to a player.

    Attributes:
        source_player: The player dealing damage.
        target_player: The player receiving damage.
        base_attack: Base attack from card stats.
        attack_bonus: Attack bonus from class/family abilities.
        total_attack: Total attack value (base + bonus).
        base_defense: Base defense from card stats.
        defense_bonus: Defense bonus from class/family abilities.
        target_defense: Total defense (base + bonus).
        base_damage: Normal damage (attack - defense, min 0).
        imblocable_damage: Damage that bypasses defense.
        total_damage: Total damage dealt to target's PV.
    """

    source_player: PlayerState
    target_player: PlayerState
    base_attack: int
    attack_bonus: int
    total_attack: int
    base_defense: int
    defense_bonus: int
    target_defense: int
    base_damage: int
    imblocable_damage: int
    total_damage: int


@dataclass
class CombatResult:
    """Result of combat resolution for a turn.

    Attributes:
        damage_dealt: List of damage breakdowns for each attacker-target pair.
        eliminations: List of players eliminated this combat.
        health_changes: Dict mapping player_id to health change.
        self_damage: Dict mapping player_id to self-damage (e.g., Berserker).
    """

    damage_dealt: list[DamageBreakdown] = field(default_factory=list)
    eliminations: list[PlayerState] = field(default_factory=list)
    health_changes: dict[int, int] = field(default_factory=dict)
    self_damage: dict[int, int] = field(default_factory=dict)


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
    1. Calculate attacker's total attack (base + ability bonuses)
    2. Calculate defender's total HP/defense (base + ability bonuses)
    3. Base damage = attack - defense (min 0)
    4. Add imblocable damage (bypasses defense)
    5. Total damage = base + imblocable

    Args:
        attacker: The attacking player.
        defender: The defending player.

    Returns:
        DamageBreakdown with full calculation details.
    """
    # Resolve abilities for both players
    attacker_abilities = resolve_all_abilities(attacker)
    defender_abilities = resolve_all_abilities(defender)

    # Calculate attack with ability bonuses
    base_attack = attacker.get_total_attack()
    attack_bonus = attacker_abilities.total_attack_bonus
    total_attack = base_attack + attack_bonus

    # Calculate defense with ability bonuses
    base_defense = defender.get_total_health()
    defense_bonus = defender_abilities.total_health_bonus
    target_defense = base_defense + defense_bonus

    # Base damage: attack minus defense, minimum 0
    base_damage = max(0, total_attack - target_defense)

    # Imblocable damage bypasses defense entirely
    # Includes both pre-parsed imblocable and ability bonuses
    imblocable_damage = (
        calculate_imblocable_damage(attacker)
        + attacker_abilities.total_imblocable_bonus
    )

    total_damage = base_damage + imblocable_damage

    return DamageBreakdown(
        source_player=attacker,
        target_player=defender,
        base_attack=base_attack,
        attack_bonus=attack_bonus,
        total_attack=total_attack,
        base_defense=base_defense,
        defense_bonus=defense_bonus,
        target_defense=target_defense,
        base_damage=base_damage,
        imblocable_damage=imblocable_damage,
        total_damage=total_damage,
    )


def resolve_combat(state: GameState) -> CombatResult:
    """Resolve combat for all players simultaneously.

    In CartesSociete, all players attack all opponents simultaneously.
    Damage is calculated for each attacker-defender pair, then applied.
    Self-damage from abilities (e.g., Berserker) is also applied.

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

        # Show attack breakdown with bonuses
        if bd.attack_bonus > 0:
            lines.append(
                f"  ATK: {bd.base_attack} base + {bd.attack_bonus} bonus = "
                f"{bd.total_attack}"
            )
        else:
            lines.append(f"  ATK: {bd.total_attack}")

        for bd in breakdowns:
            # Show defense breakdown with bonuses
            if bd.defense_bonus > 0:
                defense_str = (
                    f"(DEF: {bd.base_defense}+{bd.defense_bonus}={bd.target_defense})"
                )
            else:
                defense_str = f"(DEF: {bd.target_defense})"

            lines.append(
                f"  vs {bd.target_player.name} {defense_str}: "
                f"{bd.base_damage} base + {bd.imblocable_damage} imblocable = "
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
