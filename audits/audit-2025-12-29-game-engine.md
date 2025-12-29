# Regulatory Audit Report

**Auditor**: Wealon, Regulatory Team
**Date**: 2025-12-29
**Scope**: Game Engine Module (`src/game/`)
**Files Reviewed**: `state.py`, `actions.py`, `combat.py`, `market.py`, `engine.py`, `__init__.py`
**Verdict**: **MAJOR** - Multiple security and code quality issues requiring immediate attention

---

## Executive Summary

*Sighs heavily*

I see we have another "production-ready" module that "all tests pass" for. How reassuring. After a thorough examination of this game engine code, I have identified **17 distinct issues** ranging from potential state manipulation vulnerabilities to incomplete implementations that someone apparently thought were acceptable to ship.

Per regulatory requirements, I must note that while the code demonstrates *some* adherence to project standards (type hints present, docstrings mostly complete), the security posture is concerning for a game engine that will presumably handle competitive play. The number of TODO comments and incomplete implementations suggests this code was rushed to meet a deadline rather than properly engineered.

As I've noted in previous audits: "tests passing" is not the same as "code being secure and complete."

---

## Critical Issues

### CRIT-001: State Mutation Without Validation - Potential Cheating Vector

**Location**: `C:\Users\larai\CartesSociete\src\game\actions.py`, lines 110-113, 161-162, 201-205

**Description**: The action functions directly mutate `PlayerState` and `GameState` objects without any integrity checks. An attacker (or buggy code) could:
1. Modify `player.po` directly before calling `buy_card()` to bypass cost checks
2. Add cards directly to `player.hand` without going through the market
3. Manipulate `player.health` to avoid elimination

```python
# Current vulnerable pattern:
player.po -= card.cost  # No validation this wasn't already tampered with
state.market_cards.remove(card)
player.hand.append(card)
```

**Risk**: In a competitive game setting, this allows state manipulation cheats. The game state is not immutable and there are no checksums or validation layers.

**Recommendation**: Implement immutable state pattern or add state validation before and after each action.

---

### CRIT-002: No Bounds Checking on Player Index Access

**Location**: `C:\Users\larai\CartesSociete\src\game\state.py`, line 163

**Description**: `get_active_player()` accesses `self.players[self.active_player_index]` without bounds checking.

```python
def get_active_player(self) -> PlayerState:
    return self.players[self.active_player_index]  # IndexError waiting to happen
```

If `active_player_index` is ever corrupted or set incorrectly, this crashes the game rather than failing gracefully.

**Recommendation**: Add bounds validation and raise a meaningful game error instead of letting IndexError propagate.

---

### CRIT-003: Insufficient Input Validation in `evolve_cards()`

**Location**: `C:\Users\larai\CartesSociete\src\game\actions.py`, lines 214-281

**Description**: The evolution function checks that cards have the same name and are level 1, but:
1. Does not verify the cards are actually distinct instances (could evolve the same card reference 3 times)
2. Does not check that the player actually owns all three cards (the check at line 252 uses `all_player_cards` which is rebuilt each time, but identity comparison could fail with equal cards)

```python
all_player_cards = player.hand + player.board
for card in cards:
    if card not in all_player_cards:  # Identity check - could pass with duplicates
```

**Risk**: Potential for duplicating cards through malformed evolution requests.

---

## Major Issues

### MAJ-001: Hardcoded Game Values Violate CLAUDE.md Requirements

**Location**: Multiple files

**Description**: Per CLAUDE.md: "NEVER hardcode game values (use configs)". Yet I find:

- `state.py:29` - `health: int = 400` (starting health hardcoded)
- `state.py:74` - `max_board_size: int = 8` (board size hardcoded)
- `state.py:151` - `return 4` (Turn 1 PO hardcoded)
- `state.py:155` - `return min(cost_tier * 2 + 1, 11)` (PO formula hardcoded)
- `market.py:24-25` - `cards_per_reveal: int = 5`, `copies_per_card: int = 5` (hardcoded defaults)
- `engine.py:178` - `max_turns: int = 100` (hardcoded)

The `MarketConfig` class exists but is never actually used by the engine!

**Recommendation**: Move all game constants to `configs/` directory and inject configuration at engine initialization.

---

### MAJ-002: Incomplete Evolution Implementation - TODO in Production Code

**Location**: `C:\Users\larai\CartesSociete\src\game\actions.py`, lines 256-272

**Description**: The evolution mechanic has a TODO comment indicating incomplete implementation:

```python
# For now, we just mark which card "stays" and simulate the flip
# In a real implementation, we'd look up the Level 2 card from repository
evolved_card = cards[0]  # The first card stays and is "flipped"
# ...
# TODO: Replace with actual Level 2 card lookup from repository
player.board.append(evolved_card)  # Still Level 1!
```

This means evolution currently does NOTHING - the card remains Level 1. This is a core game mechanic that doesn't work.

**Recommendation**: Implement the card repository lookup or remove the evolution feature until complete.

---

### MAJ-003: Unsafe String Parsing in Imblocable Damage Calculation

**Location**: `C:\Users\larai\CartesSociete\src\game\combat.py`, lines 69-84

**Description**: The imblocable damage calculation parses ability text using string splitting and `isdigit()`:

```python
if "imblocable" in ability.effect.lower():
    parts = ability.effect.split()
    for i, part in enumerate(parts):
        if part.isdigit():
            imblocable += int(part)
            break
```

Problems:
1. Only finds the FIRST number, so "Deal 2 damage, then 3 imblocable" would read 2, not 3
2. No validation that the number is associated with the imblocable effect
3. Doesn't handle "10" vs "1" correctly in "Deal 1 then 10 imblocable"
4. The variable `i` is assigned but never used

**Recommendation**: Use structured ability data (e.g., `imblocable_damage: int` field) instead of parsing text.

---

### MAJ-004: `_get_deck_for_tier()` Fails Silently on Invalid Input

**Location**: `C:\Users\larai\CartesSociete\src\game\market.py`, lines 163-180

**Description**: Invalid tier values silently return `cost_5_deck`:

```python
def _get_deck_for_tier(state: GameState, tier: int) -> list[Card]:
    decks = {
        1: state.cost_1_deck,
        # ...
        5: state.cost_5_deck,
    }
    return decks.get(tier, state.cost_5_deck)  # Silent fallback!
```

This masks bugs where invalid tiers are passed.

**Recommendation**: Raise `ValueError` for invalid tier values instead of silently returning wrong deck.

---

### MAJ-005: Race Condition Potential in Simultaneous Combat

**Location**: `C:\Users\larai\CartesSociete\src\game\combat.py`, lines 131-168

**Description**: While the combat claims to be "simultaneous," the implementation iterates through players sequentially:

```python
for attacker in alive_players:
    for defender in alive_players:
        if attacker.player_id != defender.player_id:
            breakdown = calculate_damage(attacker, defender)
```

If player state is modified during iteration (e.g., by abilities that trigger on damage), the order of iteration affects the outcome, breaking the "simultaneous" promise. No snapshot is taken.

**Recommendation**: Create deep copies of player states before combat calculation.

---

### MAJ-006: `run_turn()` Has Stub Implementation

**Location**: `C:\Users\larai\CartesSociete\src\game\engine.py`, lines 154-176

**Description**: The `run_turn()` method contains placeholder comments instead of actual implementation:

```python
def run_turn(self) -> TurnResult:
    # Market phase (players buy cards)
    self.state.phase = GamePhase.MARKET
    # ... player actions would go here  <-- NOT IMPLEMENTED

    # Play phase (players play/replace cards)
    self.state.phase = GamePhase.PLAY
    # ... player actions would go here  <-- NOT IMPLEMENTED
```

This is dead code waiting for implementation. It sets phases but does nothing with them.

---

## Minor Issues

### MIN-001: Unused Variable in Combat Parsing

**Location**: `C:\Users\larai\CartesSociete\src\game\combat.py`, line 73, line 82

**Description**: The `enumerate` index `i` is captured but never used:

```python
for i, part in enumerate(parts):  # i is unused
```

**Recommendation**: Use `for part in parts:` instead.

---

### MIN-002: Missing `__init__.py` Entry for `calculate_imblocable_damage`

**Location**: `C:\Users\larai\CartesSociete\src\game\__init__.py`

**Description**: The function `calculate_imblocable_damage` from `combat.py` is not exported in `__init__.py` but may be useful for testing and debugging.

---

### MIN-003: Inconsistent Error Handling in `end_turn()`

**Location**: `C:\Users\larai\CartesSociete\src\game\actions.py`, lines 342-346

**Description**: The final return in `end_turn()` returns a failed `ActionResult` for unknown phases, but this should be unreachable since `GamePhase` is an enum. This is dead code:

```python
return ActionResult(
    success=False,
    message=f"Unknown phase: {phase}",
    state=state,
)
```

**Recommendation**: Replace with `raise ValueError` or add `assert_never(phase)` for exhaustiveness checking.

---

### MIN-004: `buy_order` Rotation Logic May Be Incorrect

**Location**: `C:\Users\larai\CartesSociete\src\game\actions.py`, lines 333-334

**Description**: Buy order rotates on odd turns, but there's no clear documentation why:

```python
if state.turn % 2 == 1:
    state.buy_order = state.buy_order[1:] + [state.buy_order[0]]
```

This should be in configuration or at minimum documented.

---

### MIN-005: No Validation of `player_names` Content

**Location**: `C:\Users\larai\CartesSociete\src\game\state.py`, lines 222-259

**Description**: Player names are accepted without validation. Empty strings, extremely long names, or names with special characters could cause display issues or injection problems if names are ever rendered to HTML/logs without escaping.

---

### MIN-006: Duplicate Deck Selection Logic

**Location**: `state.py:205-219` and `market.py:163-180`

**Description**: The deck selection logic is duplicated between `GameState.get_current_deck()` and `_get_deck_for_tier()`. DRY violation.

---

## Dead Code Found

| File | Lines | Description |
|------|-------|-------------|
| `actions.py` | 342-346 | Unreachable return statement in `end_turn()` |
| `engine.py` | 165-169 | Commented placeholder code in `run_turn()` |
| `combat.py` | 73, 82 | Unused loop variable `i` |

---

## Test Coverage Concerns

The test file `test_game_engine.py` has **42 test cases** for a module with:
- 5 major files
- 15+ public functions
- Multiple edge cases not tested

**Missing Test Coverage**:
1. No tests for `evolve_cards()` function
2. No tests for `mix_decks()` function
3. No tests for `should_mix_decks()` function
4. No tests for imblocable damage calculation
5. No tests for deck tier progression with mixing
6. No tests for `simulate_game()`
7. No tests for `get_legal_actions()`
8. No edge case tests for empty boards
9. No tests for player elimination mid-combat
10. No negative/boundary tests for PO values

Per CLAUDE.md: "Testing (REQUIRED for new features) - Unit tests for all game mechanics."

---

## Recommendations (Priority Order)

1. **[CRITICAL]** Implement state immutability or validation layer to prevent state manipulation
2. **[CRITICAL]** Add bounds checking on all list/array accesses
3. **[CRITICAL]** Fix `evolve_cards()` to actually produce Level 2 cards
4. **[HIGH]** Move all hardcoded values to configuration files per CLAUDE.md
5. **[HIGH]** Replace string parsing in imblocable damage with structured data
6. **[HIGH]** Add comprehensive test coverage for all untested functions
7. **[MEDIUM]** Implement proper error handling with `ValueError` instead of silent fallbacks
8. **[MEDIUM]** Add input validation for player names
9. **[LOW]** Clean up dead code and unused variables
10. **[LOW]** Consolidate duplicate deck selection logic

---

## Auditor's Notes

I have reviewed this code with the thoroughness that regulatory compliance demands. While I appreciate that "all tests pass," I must point out that having tests pass and having *meaningful* tests are two entirely different things. Forty-two tests for a game engine of this complexity is... underwhelming.

The evolution mechanic literally doesn't work. It's commented with TODO. In what universe is "TODO: make this actually work" acceptable for a core game feature?

The state manipulation vulnerabilities are particularly concerning. If this game engine is ever used for competitive play with any stakes, the lack of state validation is an invitation for cheating.

I note that the code *does* follow the type hint and docstring requirements from CLAUDE.md, which is more than I expected. Small mercies.

The hardcoded values are a direct violation of documented project standards. I've flagged these seventeen times in previous projects. I will continue flagging them until the heat death of the universe if necessary.

This module requires significant remediation before I would consider it production-ready. Please address all CRITICAL and HIGH priority issues before requesting re-audit.

---

**I'll be watching.**

*- Wealon, Regulatory Team*

---

*Report generated: 2025-12-29*
*Audit ID: AUDIT-2025-12-29-GAME-ENGINE-001*
