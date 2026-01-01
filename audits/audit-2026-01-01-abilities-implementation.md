# Regulatory Audit Report
**Auditor**: Wealon, Regulatory Team
**Date**: 2026-01-01
**Scope**: Class Abilities, Family Abilities, Passive Effects, bonus_text Implementation
**Verdict**: ~~MAJOR~~ **RESOLVED** (Updated 2026-01-01)

---

## Resolution Summary

All critical and major issues from this audit have been addressed:

- **PR #18** (`feat/class-abilities-and-ppo-training`): Implemented conditional abilities, passive abilities, Forgeron/Invocateur/Monture class effects, Econome PO generation, S-Team board exclusion
- **PR #19** (`feat/bonus-text-effects`): Implemented comprehensive bonus_text effect resolution including attack penalties, on-attacked damage, per-turn imblocable, and 15+ effect patterns

**Remaining**: 2 low-priority items (family ability tests, ability documentation)

---

## Executive Summary

*Sigh*. Once again, I find myself documenting what should have been obvious during development. The abilities system in this codebase is... let's call it "aspirational." While the foundational structure exists, I've discovered significant gaps between what is defined and what is actually used during gameplay. The passive effects are decorative at best, the conditional abilities from bonus_text are largely ignored, and there are orphaned helper functions collecting dust. Per regulatory requirements, I must note that "implementing something halfway" does not count as implementing it at all.

---

## Critical Issues

### CRIT-001: Conditional Abilities NOT Resolved in Game Logic
**Location**: `C:\Users\larai\CartesSociete\src\game\abilities.py`
**Lines**: 212-282 (resolve_class_abilities function)

The `ClassAbilities.conditional` field is parsed and stored on cards (e.g., Dragon class's "1 PO" -> "2 dgt imblocable"), but the `resolve_class_abilities()` function ONLY processes `scaling` abilities. Conditional abilities are completely ignored during ability resolution.

```python
# Line 239-280 - ONLY scaling abilities are processed
if card.class_abilities.scaling:
    active = get_active_scaling_ability(
        card.class_abilities.scaling,
        class_count,
    )
# NO CODE EXISTS TO PROCESS card.class_abilities.conditional
```

**Cards Affected**:
- `nature_ancien_de_la_nature_1` (Dragon): Has `conditional: [{"condition": "1 PO", "effect": "2 dgt imblocable"}, ...]`
- All Dragon-class cards with PO-based conditional effects

**Impact**: Dragon class abilities requiring PO expenditure are DEAD CODE. They render in the UI but do nothing.

---

### CRIT-002: Passive Abilities NOT Applied in Game Logic
**Location**: `C:\Users\larai\CartesSociete\src\game\abilities.py`
**Lines**: 285-326 (resolve_family_abilities), 212-282 (resolve_class_abilities)

Both `FamilyAbilities.passive` and `ClassAbilities.passive` fields exist and are populated on cards, but NEITHER function reads or processes them.

**Examples of Ignored Passives**:
- `class_abilities.passive: "Ne compte pas comme un monstre du plateau"` (S-Team cards)
- `class_abilities.passive: "les economes apportent 1- nb d'economes PO/Tour"` (Econome class)
- `family_abilities.passive` (if any cards have this)

**Evidence**: Searching for `family_abilities.passive` in `src/game/` returns NO matches. The passive field is:
- Defined in models.py:92, 112
- Parsed in repository.py:68, 140
- Rendered in renderer.py:96-98, 107-109, 169-171, 182-184
- **NEVER used in game logic**

---

### CRIT-003: bonus_text Effects Mostly Ignored
**Location**: Various
**Severity**: CRITICAL

The `bonus_text` field contains many gameplay effects that are NOT implemented:

| Card | bonus_text | Status |
|------|-----------|--------|
| `nature_mutanus_empoisonne_1` | "Vous perdez 2 PV imblocables par tour" | IMPLEMENTED (per_turn_self_damage) |
| `nature_cameleor_1` | "+1 d'or si des dgt imblocable sont infligés" | NOT IMPLEMENTED |
| `nature_golem_de_combat_1` | "Bloque 1 dgt par sort" | NOT IMPLEMENTED |
| `cyborg_cyberpique_1` | "Inflige 1 dgt quand attaque" | NOT IMPLEMENTED |
| `cyborg_naingenieur_1` | "+1 ATQ pour tous les cyborgs" | NOT IMPLEMENTED |
| `cyborg_hydre_steam_1` | "-1 ATQ pour les cyborgs (pas en dessous de 0)" | NOT IMPLEMENTED |
| `atlantide_chanteuse_des_flots_1` | "+1 ATQ pour les Atlantide" | NOT IMPLEMENTED |
| `atlantide_rathon_1` | "Les raccoon Familly gagne +2 ATQ" | NOT IMPLEMENTED |

Only ONE pattern is extracted from bonus_text: "Vous perdez X PV ... par tour" for per-turn self-damage (repository.py:34-37, 100-117).

---

## Major Issues

### MAJ-001: Dead Code - Unused Helper Functions
**Location**: `C:\Users\larai\CartesSociete\src\game\abilities.py`
**Lines**: 358-383

The functions `get_player_attack_with_abilities()` and `get_player_health_with_abilities()` are defined but NEVER called anywhere in the codebase.

```python
# Lines 358-369 - DEAD CODE
def get_player_attack_with_abilities(player: PlayerState) -> int:
    """Get total attack including ability bonuses."""
    base_attack = player.get_total_attack()
    abilities = resolve_all_abilities(player)
    return base_attack + abilities.total_attack_bonus
```

**Evidence**: `grep -r "get_player_attack_with_abilities" src/` only returns abilities.py itself.

---

### MAJ-002: Imblocable Damage from Family Abilities Not Calculated
**Location**: `C:\Users\larai\CartesSociete\src\game\combat.py`
**Lines**: 61-80 (calculate_imblocable_damage function)

The function only reads `card.class_abilities.imblocable_damage`. However, Nature family has imblocable damage in their FAMILY abilities:

```json
// nature.json - ALL Nature cards
"family_abilities": {
  "scaling": [
    {"threshold": 2, "effect": "2 dgt imblocables"},
    {"threshold": 4, "effect": "5 dgt imblocables"},
    {"threshold": 6, "effect": "8 dgt imblocables"}
  ]
}
```

This imblocable damage from family scaling is captured in `resolve_family_abilities()` -> `total_imblocable_bonus`, and IS included in combat.py:122-125. So this is not as broken as I initially suspected - the family imblocable goes through the ability resolution, while card-specific imblocable goes through the structured field. How... creative.

**Status**: Partially mitigated, but the separation is confusing.

---

### MAJ-003: S-Team "Ne compte pas comme un monstre du plateau" Passive Not Implemented
**Location**: `C:\Users\larai\CartesSociete\src\game\state.py`
**Lines**: 60-72 (get_board_count function)

The S-Team class has passive: "Ne compte pas comme un monstre du plateau", but:
1. This passive is never read
2. `get_board_count()` only checks for Demons (card_type == CardType.DEMON), not S-Team class

```python
# state.py:60-72 - Does NOT handle S-Team
def get_board_count(self, include_demons: bool = False) -> int:
    if include_demons:
        return len(self.board)
    return sum(1 for card in self.board if card.card_type != CardType.DEMON)
    # NO CHECK FOR CardClass.S_TEAM
```

---

### MAJ-004: Econome PO Generation Not Implemented
**Location**: Nowhere (missing implementation)

Econome class has passive: "les economes apportent 1- nb d'economes PO/Tour"

This economy mechanic is completely unimplemented. There is no code that:
1. Counts Econome cards
2. Modifies PO based on Econome count
3. Applies this during any phase

---

### MAJ-005: Forgeron Weapon Draw Not Implemented
**Location**: Nowhere (missing implementation)

Forgeron class scaling: "Piocher une arme" at threshold 1, "2 armes" at 2, etc.

This is parsed but never executed. The `resolve_class_abilities()` function:
1. Returns numeric bonuses (attack_bonus, health_bonus, etc.)
2. Has no mechanism for "draw card" effects
3. Is never integrated with the weapon_deck

---

## Minor Issues

### MIN-001: Test Coverage Gap for Family Abilities
**Location**: `C:\Users\larai\CartesSociete\tests\test_abilities.py`

No dedicated tests for `resolve_family_abilities()`. The test `test_combined_abilities` merely checks that `result.class_counts is not None`, which doesn't verify family ability resolution.

---

### MIN-002: Regex Patterns May Miss Effect Variations
**Location**: `C:\Users\larai\CartesSociete\src\game\abilities.py`
**Lines**: 74-82

```python
_ATK_PATTERN = re.compile(r"\+(\d+)\s*(?:ATQ|dgt|atq)", re.IGNORECASE)
```

This won't match:
- "+1 au dgt des sorts des mages" (nature_ancien_de_la_nature bonus_text)
- "Les +3 ATQ si diplo air" (nature_diplo_terre bonus_text)

The regex assumes a direct "+N ATQ" format, not conditional or contextual bonuses.

---

### MIN-003: Invocateur Demon Summoning Not Implemented
**Location**: Nowhere

Invocateur class scaling references demon summoning ("invoque un diablotin", "demon mineur", "une succube", "un demon majeur"), but:
1. No code exists to summon demons
2. The demon_deck exists but is never drawn from for invocation

---

### MIN-004: Monture Card Draw Not Implemented
**Location**: Nowhere

Monture class threshold 3: "piocher une carte cout 5 dans la pile (au hasard)"

Like Forgeron, this draw effect is defined but never executed.

---

### MIN-005: Dragon PO Cost Effects Not Implemented
**Location**: Nowhere

Dragon class uses conditional abilities with PO costs ("1 PO" -> effect), suggesting an active ability system where players spend PO to activate effects. No such system exists.

---

## Dead Code Found

| File | Line(s) | Code | Status |
|------|---------|------|--------|
| abilities.py | 358-369 | `get_player_attack_with_abilities()` | ~~UNUSED~~ **RESOLVED: Removed** |
| abilities.py | 372-383 | `get_player_health_with_abilities()` | ~~UNUSED~~ **RESOLVED: Removed** |
| models.py | 75-81 | `ConditionalAbility` class | ~~PARSED BUT NEVER RESOLVED~~ **RESOLVED: Used by resolve_conditional_abilities()** |
| models.py | 92 | `FamilyAbilities.passive` | ~~PARSED BUT NEVER USED~~ **RESOLVED: Used by resolve_passive_abilities()** |
| models.py | 112 | `ClassAbilities.passive` | ~~PARSED BUT NEVER USED~~ **RESOLVED: Used by resolve_passive_abilities()** |

---

## Recommendations

1. ~~**IMMEDIATE**: Implement `resolve_conditional_abilities()` function~~ **✅ RESOLVED: PR #18**
2. ~~**IMMEDIATE**: Implement passive ability effects~~ **✅ RESOLVED: PR #18**
3. ~~**HIGH**: Create an effects system for draw-based abilities (Forgeron weapons, Monture draws)~~ **✅ RESOLVED: PR #18**
4. ~~**HIGH**: Implement Econome PO generation mechanic~~ **✅ RESOLVED: PR #18**
5. ~~**HIGH**: Add S-Team to board count exclusion logic~~ **✅ RESOLVED: PR #18**
6. ~~**MEDIUM**: Expand bonus_text parsing to cover more effect patterns~~ **✅ RESOLVED: PR #19**
7. ~~**MEDIUM**: Remove dead helper functions or integrate them properly~~ **✅ RESOLVED: Already removed**
8. **LOW**: Add comprehensive family ability tests
9. **LOW**: Document which abilities are intentionally manual vs. automated

---

## Auditor's Notes

I've spent considerable time untangling this "abilities system." What we have here is a classic case of building the data model before building the execution layer. The cards have elaborate ability definitions, the repository dutifully parses them, the renderer beautifully displays them... and then the game engine ignores most of them.

The per_turn_self_damage implementation for Mutanus shows what SHOULD have been done for all effects: parse during load, store in structured field, apply during game loop. Instead, we have regex patterns that detect some effects, structured fields for others, and complete gaps for many.

Per regulatory requirement 7.3.2: "All defined game mechanics MUST have corresponding implementation or be documented as future work." This codebase fails that requirement comprehensively.

As I've noted seventeen times before: parsing data is not the same as using data. I see we've decided to ignore best practices again.

I'll be watching.

---

*Report generated by Wealon, Regulatory Compliance Team*
*Classification: INTERNAL - DEVELOPMENT*
