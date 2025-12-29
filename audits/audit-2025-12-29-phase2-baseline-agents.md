# Regulatory Audit Report

**Auditor**: Wealon, Regulatory Team
**Date**: 2025-12-29
**Scope**: Phase 2 Baseline Agents Implementation (`src/players/`, `src/game/executor.py`)
**Verdict**: **MAJOR** - Multiple issues requiring attention before production deployment

---

## Executive Summary

*Sighs heavily*

I have completed my review of the Phase 2 baseline agents implementation. While I must reluctantly admit that the code follows some reasonable patterns - using type hints, docstrings, and immutable dataclasses - I have, as always, found numerous issues that apparently everyone else missed. Again.

The architecture is reasonably sound with proper separation of concerns between action representation, execution, and player strategies. However, I've identified security concerns, potential denial-of-service vectors, missing input validation, incomplete implementations shipped as "production", and the usual cavalcade of code quality issues that seem to plague this codebase.

Per regulatory requirements, all issues must be addressed before this code can be considered production-ready.

---

## Critical Issues

### CRIT-001: Unvalidated Action Input - Potential State Manipulation

**Location**: `C:\Users\larai\CartesSociete\src\game\executor.py`, lines 84-149

The `get_legal_actions_for_player()` function generates actions based on the current game state, but `execute_action()` does NOT verify that the action passed to it was actually generated from the current state. A malicious player implementation could construct arbitrary Action objects with cards that:

1. Don't exist in the market/hand/board
2. Have been modified (different stats than server-side version)
3. Reference cards from another player's state

While `actions.py` does some validation (checking card in market/hand), it relies on object identity checks (`card not in player.hand`). If a malicious agent clones a card object with modified stats, the identity check passes but the game state becomes corrupted.

```python
# executor.py line 55 - passes card directly to buy_card without hash/id verification
return buy_card(state, player, action.card)
```

**Severity**: CRITICAL
**Risk**: Game state manipulation, cheating in competitive play
**Recommendation**: Implement card ID-based validation, not object reference validation

---

### CRIT-002: Unbounded Computation in MCTS (DoS Vector)

**Location**: `C:\Users\larai\CartesSociete\src\players\mcts_player.py`, lines 34-37

The `MCTSConfig` allows arbitrary `num_simulations` with no upper bound:

```python
@dataclass
class MCTSConfig:
    num_simulations: int = 100
    # ... no max limit enforced
```

A malicious or misconfigured player could set `num_simulations` to an absurdly high value (e.g., `10**9`), causing denial of service when MCTS is fully implemented.

**Severity**: CRITICAL (when MCTS is implemented)
**Risk**: Denial of service, game server hang
**Recommendation**: Add maximum bounds validation in `__post_init__`

---

## Major Issues

### MAJ-001: Random Number Generator Not Cryptographically Secure

**Location**: `C:\Users\larai\CartesSociete\src\players\random_player.py`, line 41
**Location**: `C:\Users\larai\CartesSociete\src\players\mcts_player.py`, line 135

Both files use `random.Random()` for decision-making:

```python
self._rng = random.Random(seed)
```

While this is fine for testing and simulation, if these players are used in any scenario with prizes or competitive stakes, the PRNG is predictable given the seed. An attacker who can observe game outcomes could potentially reverse-engineer the seed and predict future random choices.

**Severity**: MAJOR
**Risk**: Predictable gameplay in competitive scenarios
**Recommendation**: Use `secrets` module for any non-reproducible randomness in production

---

### MAJ-002: Empty Legal Actions List Causes Crash

**Location**: `C:\Users\larai\CartesSociete\src\players\random_player.py`, line 68

```python
def choose_market_action(...) -> Action:
    return self._rng.choice(legal_actions)  # IndexError if empty!
```

If `legal_actions` is an empty list, `random.choice()` raises `IndexError`. While the executor *should* always include `END_PHASE`, there's no defensive programming here.

Same issue exists in:
- `random_player.py`, line 86
- `mcts_player.py`, line 227

**Severity**: MAJOR
**Risk**: Uncaught exception crashes game
**Recommendation**: Validate `legal_actions` is non-empty, raise explicit error or return safe default

---

### MAJ-003: Mutable Default in MCTSNode

**Location**: `C:\Users\larai\CartesSociete\src\players\mcts_player.py`, line 58

```python
children: list["MCTSNode"] = field(default_factory=list)
```

This is correctly using `default_factory`, but line 57 has:

```python
parent: "MCTSNode | None" = None
```

Wait, that's fine. Let me re-read... Actually, this is correctly implemented. *Grudgingly crosses off list*

However, the `MCTSNode` dataclass exposes mutable state (`children`, `visits`, `total_value`) that can be modified by any code with a reference. In adversarial scenarios, a malicious player could manipulate the tree.

**Severity**: MAJOR
**Risk**: Tree state corruption in adversarial scenarios
**Recommendation**: Consider making MCTSNode immutable or protecting modification

---

### MAJ-004: State Hash Function is Trivially Weak

**Location**: `C:\Users\larai\CartesSociete\src\players\mcts_player.py`, lines 229-245

```python
def _hash_state(self, state: "GameState") -> str:
    return f"state_{state.turn}_{state.phase.value}"
```

This hash function only considers turn number and phase, ignoring:
- Player boards and hands
- Market cards
- PO amounts
- Health totals

Two completely different game states could hash to the same value, causing the MCTS tree to incorrectly reuse analysis. This is a **fundamental correctness bug** for when MCTS is implemented.

**Severity**: MAJOR
**Risk**: Incorrect AI behavior, wrong move selection
**Recommendation**: Implement proper state hashing including all game-relevant data

---

### MAJ-005: Stub Implementation Shipped as "Version 0.1.0"

**Location**: `C:\Users\larai\CartesSociete\src\players\mcts_player.py`

The entire MCTSPlayer is a stub that falls back to random play. The version is `0.1.0-stub`, but this is exported in `__init__.py` alongside production-ready players. Users of the API have no type-level indication that this is a non-functional placeholder.

**Severity**: MAJOR
**Risk**: Users accidentally deploy non-functional AI
**Recommendation**: Either complete implementation or add clear runtime warnings/deprecation

---

## Minor Issues

### MIN-001: Inconsistent Import Location for `math`

**Location**: `C:\Users\larai\CartesSociete\src\players\mcts_player.py`, lines 80-82

```python
@property
def ucb1(self) -> float:
    # ...
    import math  # Lazy import inside method!
```

Per CLAUDE.md style requirements and common Python convention, imports should be at module level. This lazy import pattern is inconsistent with the rest of the codebase.

**Severity**: MINOR
**Risk**: Code style inconsistency, minor performance overhead
**Recommendation**: Move `import math` to top of file

---

### MIN-002: Magic Numbers in Evaluation Functions

**Location**: `C:\Users\larai\CartesSociete\src\players\evaluation.py`

Multiple hardcoded magic numbers without explanation:

- Line 47: `0.5` - family synergy multiplier
- Line 68: `0.3` - class synergy multiplier
- Line 98: `3.0` - evolution potential bonus (2 copies)
- Line 100: `1.0` - evolution potential bonus (1 copy)
- Line 115: `2.5` - imblocable damage multiplier
- Line 158: `0.3` - late game attack bonus

Per CLAUDE.md: "NEVER hardcode game values (use configs)"

**Severity**: MINOR (but direct CLAUDE.md violation!)
**Risk**: Difficult to tune balance, scattered constants
**Recommendation**: Extract to configuration dataclass

---

### MIN-003: Underscore-prefixed "Private" Attributes Accessed Externally

**Location**: `C:\Users\larai\CartesSociete\tests\test_players.py`, line 344

```python
player._evolution_targets.add("test")
```

Tests directly manipulate `_evolution_targets`, which is conventionally private. Either make it public or provide a test-friendly interface.

**Severity**: MINOR
**Risk**: Tests coupled to implementation details
**Recommendation**: Add proper test hooks or make attribute public

---

### MIN-004: Duplicate ActionType Enum

**Location**:
- `C:\Users\larai\CartesSociete\src\players\action.py` (ActionType)
- `C:\Users\larai\CartesSociete\src\game\actions.py` (ActionType)

Two separate `ActionType` enums exist with similar but not identical values:

**players/action.py**:
```python
class ActionType(Enum):
    BUY_CARD = "buy_card"
    PLAY_CARD = "play_card"
    REPLACE_CARD = "replace_card"
    EVOLVE = "evolve"
    END_PHASE = "end_phase"
```

**game/actions.py**:
```python
class ActionType(Enum):
    BUY_CARD = "buy_card"
    PLAY_CARD = "play_card"
    REPLACE_CARD = "replace_card"
    EVOLVE = "evolve"
    END_TURN = "end_turn"  # <-- Different!
```

This DRY violation will inevitably cause confusion. One uses `END_PHASE`, the other `END_TURN`.

**Severity**: MINOR
**Risk**: Confusion, potential bugs when wrong enum is used
**Recommendation**: Single source of truth for action types

---

### MIN-005: Counter Type Hint Could Be More Specific

**Location**: `C:\Users\larai\CartesSociete\src\players\heuristic.py`, line 91

```python
name_counts: Counter[str] = Counter()
```

This is actually fine. *Sighs* I'm really reaching here but that's my job.

However, line 131 in `executor.py` has:

```python
cards_by_name: dict[str, list] = {}  # list of what?
```

The `list` type is not parameterized. Should be `dict[str, list[Card]]`.

**Severity**: MINOR
**Risk**: Type checking incomplete
**Recommendation**: Use `dict[str, list[Card]]`

---

### MIN-006: Missing `__all__` Documentation in `__init__.py`

**Location**: `C:\Users\larai\CartesSociete\src\players\__init__.py`

The `__all__` list exports `MCTSNode` which is an internal implementation detail that users should not typically interact with directly.

**Severity**: MINOR
**Risk**: API surface larger than intended
**Recommendation**: Consider removing internal classes from `__all__`

---

## Dead Code Found

### DEAD-001: Unused `state` Parameter

**Location**: `C:\Users\larai\CartesSociete\src\players\evaluation.py`, line 136

```python
def evaluate_card_for_purchase(
    card: "Card",
    player_state: "PlayerState",
    state: "GameState",  # Only used for turn check
) -> float:
```

The `state` parameter is only used to check `state.turn >= 7`. Consider whether this complexity is warranted.

---

### DEAD-002: Unused Logging Statements

**Location**: `C:\Users\larai\CartesSociete\src\players\mcts_player.py`, line 216

```python
logger.debug(f"MCTS would run {self.config.num_simulations} simulations here")
```

Debug log in stub code that will need to be rewritten anyway.

---

## Recommendations

Per regulatory requirements, the following must be addressed before approval:

1. **[CRITICAL]** Implement card ID-based validation in `execute_action()` to prevent state manipulation
2. **[CRITICAL]** Add maximum bounds to MCTSConfig parameters
3. **[MAJOR]** Add empty list validation in all player `choose_*` methods
4. **[MAJOR]** Fix state hash function to include all relevant game state
5. **[MAJOR]** Mark MCTSPlayer as `@deprecated` or clearly document its stub status
6. **[MINOR]** Move `import math` to module level in mcts_player.py
7. **[MINOR]** Extract magic numbers to configuration (per CLAUDE.md requirements)
8. **[MINOR]** Consolidate duplicate ActionType enums
9. **[MINOR]** Add parameterized type hint for `cards_by_name` dict

---

## Testing Coverage Assessment

Current test coverage observations:

**Adequately Tested:**
- Action dataclass creation and representation
- Basic evaluation functions
- Player info properties
- Basic action selection (greedy, heuristic evolution priority)

**Missing Tests:**
- Empty `legal_actions` edge case (crash scenario)
- Malformed Action execution
- Evolution potential edge cases
- Threat level evaluation
- Replace action selection in HeuristicPlayer
- Integration with actual game flow
- Error handling paths in executor

**Severity**: MINOR (but concerning for production readiness)

---

## Auditor's Notes

I note that this is the first time I've audited this particular module, so I cannot make my usual passive-aggressive references to "as I noted seventeen times before." Rest assured, I will remember these issues for future audits.

The code quality is... acceptable... for a first pass. The use of frozen dataclasses for Action, proper type hints throughout, and docstrings on public APIs shows *someone* read the CLAUDE.md file. However, the magic numbers directly violate the stated coding standards, and shipping a stub implementation alongside production players is the kind of decision that keeps me employed.

The duplicate `ActionType` enum situation is particularly galling. I can already envision the bug reports when someone imports from the wrong module.

I will be conducting a follow-up audit once these issues are addressed.

**I'll be watching.**

---

*Report generated by Wealon, Regulatory Team*
*"Finding issues so you don't ship them"*
