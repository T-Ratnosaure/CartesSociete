# Regulatory Audit Report

**Auditor**: Wealon, Regulatory Team
**Date**: 2026-01-01
**Scope**: Lapin Family Board Limit Implementation (Post PR #20)
**Verdict**: PARTIALLY COMPLIANT

---

## Executive Summary

*sighs heavily*

After the "critical bug" where ALL Lapin cards were merrily hopping past board limits like they owned the place, I have been tasked with auditing the "fix." Per regulatory requirements, I have examined every line of the implementation, cross-referenced with the card definitions, and have found... well, let's say "room for improvement." As I've noted in previous audits, the development team continues to demonstrate a fascinating interpretation of "following specifications."

The core fix is **functional** but contains **documentation inconsistencies**, **missing edge case tests**, and what I can only describe as a **creative comment about cumulative thresholds** that directly contradicts the actual implementation.

---

## Critical Issues

### No Critical Issues Found

Surprisingly, no security vulnerabilities or game-breaking bugs were identified. I am... almost impressed. Almost.

---

## Major Issues

### MAJOR-001: Documentation Comment Contradicts Implementation

**File**: `C:\Users\larai\CartesSociete\src\game\abilities.py`
**Lines**: 1025-1030

The comment states:
```python
# Calculate family threshold bonus
# These are cumulative: at 5 Lapins, you get both +1 (from 3) and +2 (from 5) = +3
# But looking at the data, the thresholds seem to be highest-wins, not cumulative
# Let's check: threshold 3 = "+1 cartes", threshold 5 = "+2 cartes"
# The "+2" at threshold 5 is likely the total bonus, not additional
# So at 5 Lapins: +2 total, at 3-4 Lapins: +1 total
```

This is a **thinking-out-loud comment** that was left in production code. The implementation does use highest-wins (which is correct per card definitions), but the comment creates confusion by first suggesting cumulative, then changing its mind. Per CLAUDE.md requirements: *"Clear card text and rules, Consistent terminology."*

**Recommendation**: Remove the rambling inner monologue and replace with a clear docstring:
```python
# Family threshold bonus (highest-wins, not cumulative):
# - 3+ Lapins: +1 board slot
# - 5+ Lapins: +2 board slots (replaces +1, not additional)
```

### MAJOR-002: Threshold Semantics Could Cause Future Bugs

**File**: `C:\Users\larai\CartesSociete\data\cards\lapin.json`

The card definitions show:
```json
"family_abilities": {
  "scaling": [
    {"threshold": 3, "effect": "+1 cartes sur le plateau"},
    {"threshold": 5, "effect": "+2 cartes sur le plateau"},
    {"threshold": 8, "effect": "+2 ATQ pour tous les lapins"}
  ]
}
```

Threshold 8 gives "+2 ATQ" which is an **attack bonus**, not a board slot bonus. The `calculate_lapin_board_limit` function only processes thresholds 3 and 5 via hardcoded `if` statements:

```python
if lapin_count >= 5:
    result.family_threshold_bonus = 2
elif lapin_count >= 3:
    result.family_threshold_bonus = 1
```

This is **technically correct** but uses hardcoded values instead of parsing the ability effects. If a new card introduces a different threshold (e.g., threshold 4: "+1.5 cartes"), the code will silently ignore it.

**Recommendation**: Either:
1. Parse the `_BOARD_EXPANSION_PATTERN` from family abilities, OR
2. Add explicit documentation that only thresholds 3 and 5 are supported

---

## Minor Issues

### MINOR-001: Inconsistent Error Message Formatting

**File**: `C:\Users\larai\CartesSociete\src\game\actions.py`
**Lines**: 208-211

```python
raise BoardFullError(
    f"Lapin board is full ({lapin_count}/{limit_result.total_limit}). "
    f"Need Lapincruste or more Lapins to expand limit."
)
```

The error message says "more Lapins" but at threshold 5+ you already have the maximum threshold bonus. The message should indicate that Lapincruste is the only way to expand further if threshold 5 is already reached.

### MINOR-002: Missing Type Hint in Pattern Constant

**File**: `C:\Users\larai\CartesSociete\src\game\abilities.py`
**Lines**: 294-298

```python
# Patterns for Lapincruste board limit expansion
_LAPIN_BOARD_EXPANSION_PATTERN = re.compile(
    r"(?:peut\s+poser|poser)\s+(\d+)\s+lapins?\s+suppl[ée]mentaires?\s+en\s+jeu",
    re.IGNORECASE,
)
```

Per CLAUDE.md: *"Type Hints (REQUIRED)"*. The regex pattern should be typed:
```python
_LAPIN_BOARD_EXPANSION_PATTERN: re.Pattern[str] = re.compile(...)
```

### MINOR-003: Redundant Import in Error Path

**File**: `C:\Users\larai\CartesSociete\src\game\actions.py`
**Lines**: 204-206

```python
from .abilities import calculate_lapin_board_limit

limit_result = calculate_lapin_board_limit(player, max_board)
```

The `calculate_lapin_board_limit` is imported inside the error handling block. While this works, it's imported at the top level for `can_play_lapin_card` already at line 14. This import is redundant.

### MINOR-004: Test Class Missing Final Assertion Test

**File**: `C:\Users\larai\CartesSociete\tests\test_abilities.py`
**Line**: 1386

The `TestLapinBoardLimits` class ends abruptly at line 1386. There's no test for:
1. Multiple Lapincruste cards stacking (e.g., 2x Lapincruste Lv1 = +4)
2. Mixed Lapincruste levels (1x Lv1 + 1x Lv2 = +6)
3. Non-Lapin cards still using standard board limit enforcement

---

## Dead Code Found

### None Detected

However, the pattern `_BOARD_EXPANSION_PATTERN` at line 301-303 is **never used** in the Lapin board limit calculation:

```python
_BOARD_EXPANSION_PATTERN = re.compile(
    r"\+(\d+)\s+cartes?\s+sur\s+le\s+plateau", re.IGNORECASE
)
```

This pattern exists but the actual implementation uses hardcoded `if/elif` statements. This is either:
- Dead code that should be removed
- Intended for future use (should be documented)
- An incomplete refactor (concerning)

---

## Compliance Matrix

| Requirement | Status | Notes |
|-------------|--------|-------|
| Lapincruste Lv1 (+2 slots) | COMPLIANT | Regex parses "2 lapins supplementaires" correctly |
| Lapincruste Lv2 (+4 slots) | COMPLIANT | Regex parses "4 lapins supplementaires" correctly |
| Threshold 3 (+1 slot) | COMPLIANT | Hardcoded but correct |
| Threshold 5 (+2 slots, replaces) | COMPLIANT | Hardcoded but correct |
| Multiple Lapincruste stacking | COMPLIANT | Loop adds all bonuses |
| Lapincruste + threshold stacking | COMPLIANT | Both bonuses added |
| Demons bypass limits | COMPLIANT | Line 198-199 in actions.py |
| Non-Lapin standard limits | COMPLIANT | Lines 212-217 in actions.py |
| Blocking Lapin plays at limit | COMPLIANT | can_play_lapin_card() enforced |
| Legal actions excludes blocked | COMPLIANT | executor.py lines 126-128 |
| Error messages informative | PARTIAL | Minor inaccuracy noted |
| Test coverage | PARTIAL | Missing edge case tests |

---

## Recommendations

### Required Fixes (Before Next PR)

1. **MAJOR-001**: Clean up the rambling comment in `calculate_lapin_board_limit()`
2. **MINOR-002**: Add type hints to regex pattern constants per CLAUDE.md

### Recommended Improvements

3. Add tests for:
   - Multiple Lapincruste cards (2x Lv1)
   - Mixed Lapincruste levels (1x Lv1 + 1x Lv2)
   - Verifying non-Lapin cards still respect standard board limit

4. Either use `_BOARD_EXPANSION_PATTERN` to parse family abilities or remove it

5. Improve error message to accurately reflect expansion options

---

## Verification Steps Performed

1. Verified regex pattern `_LAPIN_BOARD_EXPANSION_PATTERN` matches:
   - "Le joueur peut poser 2 lapins supplementaires en jeu" (Lv1) - MATCH
   - "Le joueur peut poser 4 lapins supplementaires en jeu" (Lv2) - MATCH

2. Verified `lapin.json` card definitions:
   - Lapincruste Level 1: `bonus_text` = "Le joueur peut poser 2 lapins supplementaires en jeu" - CORRECT
   - Lapincruste Level 2: `bonus_text` = "Le joueur peut poser 4 lapins supplementaires en jeu" - CORRECT
   - Family thresholds 3, 5: "+1 cartes", "+2 cartes" - CORRECT

3. Verified enforcement in `actions.py`:
   - Demons bypass (line 198-199) - CORRECT
   - Lapins use `can_play_lapin_card()` (line 200-211) - CORRECT
   - Non-Lapins use `player.can_play_card()` (line 212-217) - CORRECT

4. Verified `executor.py` excludes blocked Lapin plays from legal actions (lines 126-128) - CORRECT

5. Verified test coverage in `TestLapinBoardLimits`:
   - 11 tests covering base case, thresholds, Lapincruste, stacking - ADEQUATE
   - Missing: multiple Lapincruste, mixed levels - GAPS IDENTIFIED

---

## Auditor's Notes

How... creative... to fix a "critical bug" where ALL Lapins bypassed limits, only to leave behind:
- A stream-of-consciousness comment explaining your thought process
- An unused regex pattern sitting there collecting virtual dust
- Test coverage that stops just short of the interesting edge cases

Per my previous 6 audits in December 2025, I have noted similar patterns of "almost but not quite complete" implementations. The development team continues to demonstrate that reading requirements documents is apparently optional.

That said, the core functionality IS correct. The bug IS fixed. Lapins now respect their proper limits, Lapincruste's special ability is no longer useless, and Demons still bypass limits as intended.

I will grudgingly acknowledge this is acceptable for a game that involves card-playing rabbits.

---

**I'll be watching.**

*- Wealon, Regulatory Team*

---

## Appendix A: Code Snippets Reviewed

### abilities.py - calculate_lapin_board_limit (Lines 998-1050)
```python
def calculate_lapin_board_limit(
    player: PlayerState,
    base_limit: int = 8,
) -> LapinBoardLimitResult:
    # ... implementation reviewed
```

### actions.py - play_card Lapin Handling (Lines 193-217)
```python
is_lapin = card.family == Family.LAPIN
is_demon = card.card_type == CardType.DEMON
# ... enforcement logic reviewed
```

### executor.py - get_legal_actions_for_player (Lines 121-131)
```python
for card in player.hand:
    # Demons bypass board limit
    if card.card_type == CardType.DEMON:
        actions.append(Action.play(card))
    # Lapins have special board limit rules
    elif card.family == Family.LAPIN:
        if can_play_lapin_card(player, max_board):
            actions.append(Action.play(card))
    # Normal cards use standard limit
    elif player.can_play_card(max_board):
        actions.append(Action.play(card))
```

---

*Report generated by Wealon, Regulatory Team. Any complaints about this audit should be submitted in triplicate to /dev/null.*
