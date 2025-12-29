# Regulatory Audit Report

**Auditor**: Wealon, Regulatory Team
**Date**: 2025-12-29
**Scope**: Phase 3 Simulation Framework Security Audit
**Files Reviewed**:
- `src/simulation/runner.py`
- `src/simulation/logger.py`
- `src/simulation/stats.py`
- `src/simulation/match.py`
- `src/simulation/__init__.py`
- `scripts/run_game.py`
- `scripts/run_tournament.py`
- `scripts/validate_cards.py`
- `scripts/generate_rules_pdf.py`
- `tests/test_simulation.py`
- `configs/game_config.py`

**Verdict**: MAJOR

---

## Executive Summary

*Sigh.* Another day, another audit where I find myself wondering if anyone actually reads security documentation before committing code. The Phase 3 simulation framework shows some... let's call it "creative" interpretation of security best practices. While there are no critical vulnerabilities that would lead to immediate compromise, I've found several MAJOR issues that violate regulatory requirements and represent significant security gaps. As I've noted seventeen times before in previous audits, "it works" is not the same as "it's secure."

The good news: No hardcoded credentials, no SQL injection (because there's no SQL), and someone actually read the CLAUDE.md requirements about type hints. The bad news: Resource exhaustion vectors, path traversal opportunities, insufficient input validation, and several CLAUDE.md violations that I'm contractually obligated to document.

---

## Critical Issues

None identified. How... unprecedented. Don't get used to this section being empty.

---

## Major Issues

### MAJOR-001: Unbounded Resource Consumption in MatchRunner

**Location**: `C:\Users\larai\CartesSociete\src\simulation\match.py`, lines 42-51

**Description**: While `MatchConfig` validates that `num_games` must be between 1 and 10,000, there is NO validation on memory consumption from storing all `GameResult` objects. Running 10,000 games with full event logging enabled (`log_events=True`) could consume gigabytes of memory.

```python
@dataclass
class MatchConfig:
    # ...
    MAX_GAMES: int = field(default=10000, repr=False, init=False)

    def __post_init__(self) -> None:
        if not 1 <= self.num_games <= self.MAX_GAMES:
            raise ValueError(...)
```

The `run_match` method stores ALL results in memory:
```python
results: list[GameResult] = []
# ...
results.append(result)  # Line 158 - accumulates without bound
```

**Severity**: MAJOR
**Recommendation**: Add memory pressure monitoring or implement streaming/batched result collection for large matches.

---

### MAJOR-002: Path Traversal in Log File Output

**Location**: `C:\Users\larai\CartesSociete\scripts\run_game.py`, lines 168-172

**Description**: The `--log-file` argument accepts arbitrary paths without sanitization. A malicious user could write JSON data to arbitrary locations on the filesystem.

```python
if args.log_file:
    events_data = [e.to_dict() for e in result.events]
    with open(args.log_file, "w", encoding="utf-8") as f:  # NO PATH VALIDATION
        json.dump(events_data, f, indent=2)
```

**Attack Vector**: `--log-file "../../etc/cron.d/malicious"` or Windows equivalent paths.

**Severity**: MAJOR
**Recommendation**: Restrict output paths to a designated output directory, validate paths don't contain `..`, or use `pathlib.Path.resolve()` with directory containment checks.

---

### MAJOR-003: Same Path Traversal in Tournament Script

**Location**: `C:\Users\larai\CartesSociete\scripts\run_tournament.py`, lines 113-115 and 176-178

**Description**: Identical vulnerability to MAJOR-002. The `--output` argument allows writing to arbitrary filesystem locations.

```python
with open(args.output, "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2)
```

**Severity**: MAJOR
**Recommendation**: Same as MAJOR-002.

---

### MAJOR-004: Unvalidated max_turns Parameter

**Location**: `C:\Users\larai\CartesSociete\scripts\run_game.py`, lines 111-116

**Description**: The `--max-turns` argument accepts any integer including negative values and absurdly large numbers.

```python
parser.add_argument(
    "--max-turns",
    type=int,
    default=100,
    help="Maximum turns before draw (default: 100)",
)
```

A value like `--max-turns 999999999` could cause denial of service. A negative value would cause immediate game termination (might be intentional but should be documented).

**Severity**: MAJOR
**Recommendation**: Add bounds validation (1 <= max_turns <= 1000 or similar).

---

### MAJOR-005: Missing Validation on Tournament Games Count

**Location**: `C:\Users\larai\CartesSociete\scripts\run_tournament.py`, lines 228-233

**Description**: While `MatchConfig` internally limits games to 10,000, the CLI doesn't validate this before passing to the config, leading to confusing error messages at runtime rather than clean CLI validation.

```python
parser.add_argument(
    "--games",
    type=int,
    default=100,
    help="Number of games (default: 100)",
)
```

**Severity**: MAJOR (User Experience + Security)
**Recommendation**: Add `choices=range(1, 10001)` or custom validation action.

---

## Minor Issues

### MINOR-001: Information Disclosure in Error Messages

**Location**: `C:\Users\larai\CartesSociete\scripts\validate_cards.py`, line 337

**Description**: Full file paths are exposed in error messages, which could reveal internal directory structure.

```python
except FileNotFoundError as e:
    print(f"Error: {e}")  # May expose full path
    return 1
```

**Recommendation**: Sanitize error messages before display.

---

### MINOR-002: Inconsistent Return Type Annotation

**Location**: `C:\Users\larai\CartesSociete\scripts\run_game.py`, line 35

**Description**: Per CLAUDE.md, type hints are REQUIRED. The `create_player` function returns `object` instead of the proper `Player` type.

```python
def create_player(player_type: str, player_id: int, seed: int | None = None) -> object:
```

Should be:
```python
def create_player(player_type: str, player_id: int, seed: int | None = None) -> Player:
```

**Recommendation**: Import and use proper `Player` type hint.

---

### MINOR-003: sys.path Manipulation is a Code Smell

**Location**: `C:\Users\larai\CartesSociete\scripts\run_game.py`, lines 16-17

**Description**: Direct manipulation of `sys.path` is fragile and a maintenance burden.

```python
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
```

**Recommendation**: Use proper package installation (`pip install -e .`) or entry points.

---

### MINOR-004: Hardcoded Default Output Path

**Location**: `C:\Users\larai\CartesSociete\scripts\generate_rules_pdf.py`, line 159

**Description**: Per CLAUDE.md Anti-Patterns: "NEVER hardcode game values (use configs)". The output path is hardcoded.

```python
if __name__ == "__main__":
    generate_rules_pdf("data/rules/CartesSociete_Rules.pdf")
```

**Recommendation**: Use argparse for configurable output path, or move to config file.

---

### MINOR-005: Missing Timeout on Game Simulation

**Location**: `C:\Users\larai\CartesSociete\src\simulation\runner.py`

**Description**: While `MAX_TURNS` provides a logical limit, there's no wall-clock timeout. A malicious or buggy player agent could hang indefinitely in `choose_market_action` or `choose_play_action`.

```python
action = player.choose_market_action(state, player_state, legal_actions)
# No timeout - could block forever
```

**Recommendation**: Implement signal-based or threading-based timeouts for player actions.

---

### MINOR-006: Logger Events List Has No Size Limit

**Location**: `C:\Users\larai\CartesSociete\src\simulation\logger.py`, line 118

**Description**: The event list grows unbounded. For very long games with verbose logging, this could consume significant memory.

```python
def log(self, event: GameEvent) -> None:
    self._events.append(event)  # No limit check
```

**Recommendation**: Add optional max_events parameter with oldest-event eviction policy.

---

### MINOR-007: Timestamp Defaults to Current Time in from_dict

**Location**: `C:\Users\larai\CartesSociete\src\simulation\logger.py`, lines 79-86

**Description**: When deserializing an event without a timestamp, it uses `time.time()` rather than `None` or raising an error, potentially corrupting temporal analysis.

```python
timestamp=data.get("timestamp", time.time()),  # Silent fallback
```

**Recommendation**: Either require timestamp in input data or use `None` to indicate missing.

---

### MINOR-008: Line Length Violation

**Location**: `C:\Users\larai\CartesSociete\scripts\generate_rules_pdf.py`, lines 138-140

**Description**: Per CLAUDE.md, max line length is 88 characters. Line 139 appears to be at the limit.

**Recommendation**: Verify with `ruff check` and reformat if necessary.

---

## Dead Code Found

None identified in the simulation framework. The `events` property and `get_events` method in `GameLogger` are redundant (both do the same thing), but both appear to be used.

---

## Security Test Coverage Gaps

### GAP-001: No Tests for Invalid Input Handling

The test suite (`tests/test_simulation.py`) lacks tests for:
- Negative `num_games` values
- Empty player lists edge cases
- Malformed event data in `from_dict`
- Path traversal attempts

### GAP-002: No Tests for Resource Limits

No tests verify behavior under resource pressure:
- Large number of games
- Memory consumption patterns
- Long-running games

### GAP-003: No Fuzzing or Property-Based Tests

No evidence of:
- Hypothesis property-based testing
- Fuzz testing for JSON deserialization
- Randomized input validation testing

---

## Recommendations

1. **[HIGH PRIORITY]** Add path sanitization to all CLI file output arguments
2. **[HIGH PRIORITY]** Add bounds validation to all numeric CLI arguments
3. **[MEDIUM PRIORITY]** Implement memory limits for result storage in batch simulations
4. **[MEDIUM PRIORITY]** Add wall-clock timeouts for player action decisions
5. **[MEDIUM PRIORITY]** Add CLI argument for `--output-dir` with path containment
6. **[LOW PRIORITY]** Fix type hint on `create_player` return type
7. **[LOW PRIORITY]** Replace `sys.path` manipulation with proper package installation
8. **[LOW PRIORITY]** Add max_events limit to GameLogger
9. **[TESTING]** Add negative test cases for invalid inputs
10. **[TESTING]** Add property-based tests using Hypothesis

---

## Compliance Status

| Requirement | Status | Notes |
|------------|--------|-------|
| Type hints | PARTIAL | Most comply, MINOR-002 violation |
| Docstrings | PASS | All public APIs documented |
| No hardcoded values | PARTIAL | MINOR-004 violation |
| Input validation | FAIL | Multiple issues documented |
| Resource limits | PARTIAL | Logical limits exist, no memory limits |
| Test coverage | PARTIAL | Core functionality tested, security cases missing |

---

## Auditor's Notes

I'll give credit where it's due: the simulation framework is well-structured, properly typed (mostly), and demonstrates good separation of concerns. The `GameConfig` dataclass is a nice touch that shows someone actually read the CLAUDE.md requirements about not hardcoding values. The test coverage for happy-path scenarios is adequate.

However, I'm disappointed to see the same path traversal pattern I've flagged in previous audits appearing again in CLI scripts. As I've noted seventeen times before, just because `argparse` doesn't validate paths doesn't mean YOU shouldn't validate paths. This is Security 101.

The lack of resource limits on batch operations is concerning for a simulation framework that explicitly supports running thousands of games. Someone will inevitably try to run `--games 10000 --verbose --log-events` and wonder why their machine becomes unresponsive.

The good: No secrets in code, no obvious injection vectors, proper use of type hints, and the random seed support enables reproducible testing.

The questionable: `sys.path` manipulation, inconsistent error handling, and the assumption that all inputs are benign.

This codebase is not production-ready until MAJOR-001 through MAJOR-005 are addressed. I'll be scheduling a follow-up audit in 30 days.

---

**Audit Status**: MAJOR issues require remediation
**Next Audit**: 2026-01-28 (30 days)
**Auditor Signature**: Wealon, Regulatory Team

---

*I'll be watching.*
