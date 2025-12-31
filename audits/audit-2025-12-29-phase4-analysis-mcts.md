# Regulatory Audit Report

**Auditor**: Wealon, Regulatory Team
**Date**: 2025-12-29
**Scope**: PR #12 - feat/phase4-analysis-mcts (Balance Analysis, MCTS Player, Matchup Analysis)
**Verdict**: MAJOR ISSUES FOUND

---

## Executive Summary

*Sighs heavily*

I see we've decided to implement an MCTS algorithm and balance analysis framework. How... ambitious. While the code demonstrates a reasonable understanding of Monte Carlo Tree Search and statistical analysis, I have found - as I always do - numerous issues that require immediate attention. Per regulatory requirements, this PR cannot be approved in its current state.

The developers have clearly put effort into this implementation, but effort does not excuse cutting corners on security validation, exception handling, and test coverage. As I've noted in seventeen previous audits, "it works on my machine" is not a security posture.

---

## Critical Issues [SECURITY]

### CRIT-001: Silent Exception Swallowing Creates Security Blind Spots

**File**: `src/players/mcts_player.py`
**Lines**: 308-311, 323-326

```python
# Line 308-311
try:
    execute_action(state, player_state, action)
except Exception:
    # Ignore invalid actions during simulation
    pass

# Line 323-326
try:
    resolve_combat(state)
except Exception:
    # Ignore combat errors in simulation
    pass
```

**Impact**: Catching bare `Exception` and silently ignoring it is a security anti-pattern. This could mask:
- Memory corruption issues
- State inconsistency bugs
- Injection attacks if game state is user-influenced
- Resource exhaustion conditions

**Recommendation**: Catch specific exceptions (e.g., `InvalidActionError`, `CombatError`). Log unexpected exceptions. At minimum, use a debug-level log statement.

---

### CRIT-002: Potential Resource Exhaustion via Deep Copy in Hot Path

**File**: `src/players/mcts_player.py`
**Lines**: 194-195, 279-280

```python
# Line 194 (called in hot loop)
sim_state = self._clone_state(state)

# Line 279
return copy.deepcopy(state)
```

**Impact**: `copy.deepcopy()` is called once per simulation iteration (up to 10,000 times per decision). Deep copying complex game states with circular references or large data structures could cause:
- Memory exhaustion (DoS vector)
- CPU starvation on complex states
- Garbage collection pressure

**Recommendation**:
1. Implement a custom `__deepcopy__` method with optimized cloning
2. Consider using immutable state with structural sharing
3. Add memory bounds/monitoring for simulation
4. Profile memory usage under maximum simulation counts

---

### CRIT-003: Insufficient Input Validation Bounds

**File**: `src/players/mcts_player.py`
**Lines**: 47-62

```python
MAX_SIMULATIONS: int = field(default=10000, repr=False, init=False)
MAX_ROLLOUT_DEPTH: int = field(default=100, repr=False, init=False)
```

**Impact**: While bounds exist (commendable), 10,000 simulations x 100 rollout depth = potential for 1,000,000 game state evaluations per single MCTS decision. Combined with deep copy overhead, this is a DoS vector.

**Recommendation**:
1. Add combined complexity bounds (e.g., `simulations * depth < 100,000`)
2. Add timeout mechanism for MCTS search
3. Document worst-case complexity in docstring
4. Consider adaptive simulation budget based on available time

---

## Major Issues [CODE QUALITY]

### MAJ-001: Missing Timeout/Cancellation Mechanism for MCTS

**File**: `src/players/mcts_player.py`
**Lines**: 185-215 (`_run_mcts` method)

```python
# Run simulations
for _ in range(self.config.num_simulations):
    # ... simulation code with no timeout check
```

**Impact**: No way to interrupt a long-running MCTS search. In a production environment, this could cause:
- UI freezes in interactive games
- Timeouts in competitive matches
- Resource starvation in multi-agent simulations

**Recommendation**: Add optional timeout parameter and check elapsed time in the simulation loop.

---

### MAJ-002: Hardcoded Magic Numbers

**File**: `src/analysis/matchup.py`
**Lines**: 59-60

```python
# Z-score for confidence level (using 1.96 for 95%)
z = 1.96 if confidence == 0.95 else 2.576  # 99%
```

**Impact**: Violates CLAUDE.md: "NEVER hardcode game values (use configs)". Only supports 95% and 99% confidence levels. Any other value silently uses 99%.

**Recommendation**:
1. Use scipy.stats.norm.ppf for proper z-score calculation
2. Or add a lookup table for common confidence levels
3. Raise ValueError for unsupported confidence levels

**File**: `src/analysis/matchup.py`
**Line**: 106

```python
# Critical value for df=1, alpha=0.05 is 3.84
is_significant = chi_sq > 3.84
```

**Impact**: Hardcoded chi-square critical value only works for alpha=0.05, df=1.

---

### MAJ-003: Potential Division by Zero in Statistical Functions

**File**: `src/analysis/matchup.py`
**Lines**: 96-106

```python
# Expected values under null hypothesis (equal win rates)
decided_games = wins_1 + wins_2
if decided_games == 0:
    return (0.0, False)

expected = decided_games / 2

# Chi-square statistic
chi_sq = ((wins_1 - expected) ** 2 + (wins_2 - expected) ** 2) / expected
```

**Impact**: If `decided_games = 0`, we return early. But if `expected = 0` through some other code path, we'd have division by zero.

**Recommendation**: Add explicit guard: `if expected == 0: return (0.0, False)`

---

### MAJ-004: Type Checking Import Pattern Creates Runtime Risk

**File**: `src/players/mcts_player.py`
**Lines**: 10-13

```python
if TYPE_CHECKING:
    from src.game.state import GameState, PlayerState
```

Then later at runtime (line 248):
```python
from src.game.executor import get_legal_actions_for_player
```

**Impact**: Type hints are not available at runtime for isinstance checks. The inline import in `_simulate` is called 10,000 times per decision - creating import overhead.

**Recommendation**: Move runtime imports to module level. Only use TYPE_CHECKING for type annotations.

---

### MAJ-005: Inconsistent Error Handling in Balance Analysis

**File**: `src/analysis/balance.py`
**Line**: 148

```python
if len(player_factories) < 2:
    raise ValueError("Need at least 2 player factories for analysis")
```

**Impact**: Good validation here, but no validation for:
- Empty player_factories list (line 148 handles len < 2)
- None values in player_factories
- Factories that return invalid Player objects

**Recommendation**: Add comprehensive input validation.

---

## Minor Issues [STYLE/BEST PRACTICES]

### MIN-001: Unused Import in Test File

**File**: `tests/test_analysis.py`
**Line**: 13

```python
from src.analysis import (
    ...
    chi_square_test,  # Imported but not in __all__ of analysis/__init__.py
    ...
)
```

**Impact**: `chi_square_test` is imported directly but not exported in `__init__.py`. Test works due to direct module import, but this is inconsistent.

**Recommendation**: Either add to `__all__` or import from submodule.

---

### MIN-002: Docstring Missing Raises Section

**File**: `src/players/mcts_player.py`
**Lines**: 139-156 (`__init__` method)

```python
def __init__(
    self,
    player_id: int,
    name: str | None = None,
    config: MCTSConfig | None = None,
    seed: int | None = None,
) -> None:
    """Initialize MCTS player.

    Args:
        player_id: The player's ID.
        name: Optional display name.
        config: MCTS configuration.
        seed: Random seed for reproducibility.
    """
```

**Impact**: Per CLAUDE.md docstring requirements, missing `Raises` section. MCTSConfig validation can raise ValueError.

**Recommendation**: Add `Raises: ValueError: If config validation fails.`

---

### MIN-003: Property Methods Without Docstrings

**File**: `src/analysis/balance.py`
**Lines**: 82-88

```python
@property
def win_rate_1(self) -> float:
    """Win rate for type 1."""  # One-liner acceptable but minimal

@property
def draw_rate(self) -> float:
    """Draw rate."""  # Same minimal pattern
```

**Impact**: Technically compliant but could be more descriptive about edge cases (e.g., "Returns 0.0 if no games played").

---

### MIN-004: Magic Number in Evaluation Function

**File**: `src/players/mcts_player.py`
**Line**: 271

```python
return our_strength / total_strength
```

Where earlier (line 267):
```python
return 0.5  # Magic number for neutral position
```

**Impact**: 0.5 represents a neutral evaluation but is undocumented.

**Recommendation**: Use a named constant: `NEUTRAL_EVALUATION = 0.5`

---

### MIN-005: Test Assertions Could Be More Specific

**File**: `tests/test_mcts.py`
**Lines**: 89-90

```python
best = parent.best_child(1.414)
# Child2 has higher exploitation (0.6 vs 0.5) but fewer visits
# UCB1 considers both - best depends on exact values
assert best in [child1, child2]
```

**Impact**: This assertion doesn't actually verify correct UCB1 behavior - it just checks that *some* child is returned.

**Recommendation**: Calculate expected UCB1 values and assert the correct child is selected.

---

## Dead Code Found

### DEAD-001: Unused `chi_square_test` Function Export

**File**: `src/analysis/__init__.py`

The `chi_square_test` function exists in `matchup.py` but is NOT exported in `__init__.py`. Either it's:
1. Dead code that should be removed
2. Missing from exports (and tests import it directly anyway)

---

### DEAD-002: Unreachable Code Path in MCTS

**File**: `src/players/mcts_player.py`
**Line**: 222

```python
if not node.untried_actions:
    return node
```

**Impact**: This guard is at the start of `_expand`, but `_expand` is only called when `not node.is_fully_expanded()`, which means `untried_actions` is non-empty. This code path is never executed.

---

## Test Coverage Gaps

### TEST-001: Missing Edge Case Tests for MCTS

**Missing tests for**:
- MCTS with exactly 1 legal action (should return immediately)
- MCTS with game ending during simulation
- MCTS with circular/repeating game states
- MCTS behavior when state cloning fails

---

### TEST-002: No Stress Tests for Resource Exhaustion

**Missing**:
- Test with maximum simulation count (10,000)
- Test with maximum rollout depth (100)
- Memory profiling under load
- Timeout behavior testing

---

### TEST-003: Statistical Function Edge Cases

**File**: `tests/test_analysis.py`

**Missing tests for**:
- `wilson_score_interval` with confidence levels other than 0.95
- `cohens_h` with p=0 or p=1 (boundary conditions)
- `chi_square_test` with very large numbers (overflow potential)

---

## Recommendations

Per regulatory requirements, the following changes are REQUIRED before approval:

1. **[CRITICAL]** Replace bare `except Exception` with specific exception types and add logging
2. **[CRITICAL]** Add complexity bounds for MCTS (simulations x depth limit)
3. **[CRITICAL]** Add timeout mechanism for MCTS search
4. **[MAJOR]** Replace hardcoded statistical constants with proper calculations or lookup tables
5. **[MAJOR]** Move runtime imports to module level for performance
6. **[MAJOR]** Add input validation for player factories
7. **[MINOR]** Export `chi_square_test` in `__init__.py` or remove from tests
8. **[MINOR]** Add more specific test assertions for UCB1 behavior
9. **[MINOR]** Remove unreachable code in `_expand` method
10. **[MINOR]** Add stress tests for resource exhaustion scenarios

---

## Auditor's Notes

I have spent considerable time reviewing this code, and I must say - while it pains me to admit it - the overall structure is reasonably sound. The developers have shown understanding of MCTS theory and statistical analysis. The type hints are present (as REQUIRED by CLAUDE.md), docstrings exist on public APIs (mostly), and there's actual test coverage.

However.

The silent exception swallowing is inexcusable. The lack of timeout mechanisms in a computationally intensive algorithm is concerning. The hardcoded magic numbers violate explicitly stated project guidelines. These are not minor oversights - they represent either carelessness or a fundamental misunderstanding of production-ready code.

I note that this is the fourth time I have flagged silent exception handling in simulation code. I begin to wonder if my audit reports are being used as kindling rather than guidance.

The tests exist but do not test the edge cases that matter. Testing the happy path is trivial. Testing resource exhaustion, timeout behavior, and boundary conditions is where professionals distinguish themselves from hobbyists.

I will be watching this PR closely. I expect to see revisions addressing at minimum the CRITICAL and MAJOR issues before any consideration of approval.

---

*I'll be watching.*

---

**Wealon**
*Regulatory Compliance Division*
*"Trust, but verify. Then verify again."*
