# Gap Analysis - CartesSociete January 2026

**Version**: 1.0
**Date**: 2026-01-19
**Author**: Yoni (Master Orchestrator)
**Method**: BMAD Gap Analysis Framework

---

## Purpose

This document identifies gaps between the current state of CartesSociete and desired future state, categorizing them by domain and priority.

---

## Part 1: Technical Gaps

### 1.1 Code Architecture Gaps

| Gap ID | Current State | Desired State | Impact | Priority |
|--------|--------------|---------------|--------|----------|
| ARCH-01 | abilities.py is 2,149 lines | Modular, <500 lines per file | Maintainability | MEDIUM |
| ARCH-02 | Regex-based French parsing | Structured pattern registry | Reliability | HIGH |
| ARCH-03 | Single-file player implementations | Consistent strategy framework | Extensibility | LOW |
| ARCH-04 | Hardcoded observation encoding | Configurable feature engineering | Flexibility | LOW |

**Gap Details**:

**ARCH-01: Monolithic abilities.py**
- Lines of code: 2,149
- Functions: 30+
- Concerns: Parsing, resolution, effects, enums, dataclasses
- Risk: Single point of failure, hard to test in isolation
- Remediation: Split into abilities/parsing.py, abilities/resolution.py, abilities/effects.py

**ARCH-02: Regex French Parsing**
- Current: 20+ regex patterns scattered throughout
- Problem: Unknown patterns fail silently
- Risk: New cards may not work correctly
- Remediation: Pattern registry with unknown detection and alerting

### 1.2 Test Coverage Gaps

| Gap ID | Current State | Desired State | Impact | Priority |
|--------|--------------|---------------|--------|----------|
| TEST-01 | 367 tests total | 500+ tests | Confidence | MEDIUM |
| TEST-02 | Family abilities undertested | Comprehensive family tests | Correctness | HIGH |
| TEST-03 | No load/stress tests | Performance baselines | Scalability | LOW |
| TEST-04 | Some edge cases missing | Full edge case coverage | Reliability | MEDIUM |

**Gap Details**:

**TEST-02: Family Abilities**
- From audit MIN-001: No dedicated tests for resolve_family_abilities()
- Risk: Family-specific bugs may go undetected
- Remediation: Create test_family_abilities.py with all 10 families

### 1.3 RL System Gaps

| Gap ID | Current State | Desired State | Impact | Priority |
|--------|--------------|---------------|--------|----------|
| RL-01 | Basic observation encoding | Rich feature engineering | Performance | HIGH |
| RL-02 | No self-play | Self-play curriculum | Strength | MEDIUM |
| RL-03 | Single seed training | Multi-seed validation | Robustness | MEDIUM |
| RL-04 | No interpretability | Action explanations | Debug | LOW |

**Gap Details**:

**RL-01: Observation Encoding**
- Current: Basic card features (cost, attack, health, level, family, class)
- Missing: Synergy indicators, evolution potential, market opportunities
- Impact: Agent may miss strategic patterns
- Remediation: Add computed features based on domain knowledge

### 1.4 Data Quality Gaps

| Gap ID | Current State | Desired State | Impact | Priority |
|--------|--------------|---------------|--------|----------|
| DATA-01 | No card data validation | Schema validation | Integrity | MEDIUM |
| DATA-02 | Manual JSON editing | Validation tooling | Productivity | LOW |
| DATA-03 | Some cards may have inconsistent data | All cards validated | Correctness | MEDIUM |

---

## Part 2: Documentation Gaps

### 2.1 Technical Documentation

| Gap ID | Current State | Desired State | Impact | Priority |
|--------|--------------|---------------|--------|----------|
| DOC-01 | rl-research-plan.md dated 2024 | Current status reflected | Clarity | HIGH |
| DOC-02 | No API reference | Complete API docs | Usability | MEDIUM |
| DOC-03 | Informal code comments | Formal docstrings | Maintainability | LOW |

**Gap Details**:

**DOC-01: Outdated RL Research Plan**
- Document says "Created: 2024-12-31" but references future work
- Phase 1 checklist items marked as incomplete
- Reality: Much infrastructure already exists
- Remediation: Update document to reflect actual progress

### 2.2 Process Documentation

| Gap ID | Current State | Desired State | Impact | Priority |
|--------|--------------|---------------|--------|----------|
| PROC-01 | Lapin player undocumented | Strategy explained | Knowledge | MEDIUM |
| PROC-02 | No balance methodology doc | Clear process | Repeatability | HIGH |
| PROC-03 | Training procedures informal | Formal runbooks | Operations | LOW |

---

## Part 3: Functional Gaps

### 3.1 Game Engine Gaps

| Gap ID | Current State | Desired State | Impact | Priority |
|--------|--------------|---------------|--------|----------|
| GAME-01 | 2-player focus | 3-5 player support | Flexibility | LOW |
| GAME-02 | All abilities implemented | Verified against rules | Correctness | MEDIUM |
| GAME-03 | No replay system | Game replay capability | Debug | LOW |

### 3.2 Analysis Gaps

| Gap ID | Current State | Desired State | Impact | Priority |
|--------|--------------|---------------|--------|----------|
| ANLS-01 | Basic card stats | Comprehensive metrics | Insight | HIGH |
| ANLS-02 | No visualization | Dashboard/charts | Communication | MEDIUM |
| ANLS-03 | Manual interpretation | Guided analysis | Productivity | MEDIUM |
| ANLS-04 | No historical tracking | Trend analysis | Learning | LOW |

**Gap Details**:

**ANLS-01: Card Statistics**
- Current: pick_rate, win_correlation (basic)
- Needed:
  - Evolution impact (win rate change after evolving)
  - Synergy coefficient (performance with other cards)
  - Position impact (early vs late game value)
  - Counter metrics (performance against specific cards)

### 3.3 Player Strategy Gaps

| Gap ID | Current State | Desired State | Impact | Priority |
|--------|--------------|---------------|--------|----------|
| STRAT-01 | 5 implemented strategies | 8+ diverse strategies | Meta analysis | MEDIUM |
| STRAT-02 | Strategies hardcoded | Configurable parameters | Experimentation | LOW |
| STRAT-03 | No strategy documentation | All strategies documented | Knowledge | MEDIUM |

---

## Part 4: Governance Gaps

### 4.1 Current Governance Health

**Governance Framework Documented and Frozen** - Operational compliance to be verified through ongoing audits.

| Aspect | Status |
|--------|--------|
| AGENTS.md | Current, FROZEN |
| Baseline v1.0 | Documented |
| Human checkpoints | Defined |
| Agent boundaries | Clear |
| Change control | Active |

### 4.2 Future Governance Considerations

| Consideration | When Relevant |
|---------------|---------------|
| Multi-contributor support | If team grows |
| External exposure security | If deployed externally |
| Compliance requirements | If regulations apply |

---

## Part 5: Gap Prioritization

### Priority 1: Critical (Must Address)

| Gap | Impact | Effort | Timeline |
|-----|--------|--------|----------|
| DOC-01 | HIGH | LOW | Sprint 1.1 |
| TEST-02 | HIGH | MEDIUM | Sprint 1.2 |
| ARCH-02 | HIGH | MEDIUM | Sprint 1.3 |

### Priority 2: High (Should Address)

| Gap | Impact | Effort | Timeline |
|-----|--------|--------|----------|
| RL-01 | HIGH | HIGH | Q1 |
| ANLS-01 | HIGH | MEDIUM | Q2 |
| PROC-02 | MEDIUM | LOW | Q2 |

### Priority 3: Medium (Could Address)

| Gap | Impact | Effort | Timeline |
|-----|--------|--------|----------|
| ARCH-01 | MEDIUM | HIGH | Q4 |
| TEST-01 | MEDIUM | MEDIUM | Ongoing |
| DATA-01 | MEDIUM | LOW | Q2 |

### Priority 4: Low (Nice to Have)

| Gap | Impact | Effort | Timeline |
|-----|--------|--------|----------|
| GAME-01 | LOW | HIGH | 2027+ |
| RL-04 | LOW | MEDIUM | 2027+ |
| STRAT-02 | LOW | MEDIUM | Q3 |

---

## Part 6: Gap Closure Plan

### Immediate Actions (This Week)

1. **DOC-01**: Update rl-research-plan.md
2. **Commit untracked files**: Close version control gap
3. **Add family ability tests**: Start TEST-02 closure

### Q1 Actions

1. **RL-01**: Enhance observation encoding during RL training
2. **ARCH-02**: Add pattern registry before adding new cards
3. **TEST-02**: Complete family ability test suite

### Q2 Actions

1. **ANLS-01**: Expand card statistics during balance analysis
2. **PROC-02**: Document balance methodology alongside analysis
3. **DATA-01**: Add card validation before data expansion

### Q3-Q4 Actions

1. **ARCH-01**: Refactor abilities.py during code maturity phase
2. **STRAT-03**: Document strategies as they're implemented
3. **Ongoing testing**: Increase coverage incrementally

---

## Part 7: Gap Tracking

### Gap Status Definitions

| Status | Meaning |
|--------|---------|
| OPEN | Gap identified, not started |
| IN_PROGRESS | Actively being addressed |
| RESOLVED | Gap closed |
| DEFERRED | Intentionally postponed |
| ACCEPTED | Gap accepted as technical debt |

### Current Gap Summary

| Priority | Open | In Progress | Resolved | Deferred | Accepted |
|----------|------|-------------|----------|----------|----------|
| Critical | 3 | 0 | 0 | 0 | 0 |
| High | 3 | 0 | 0 | 0 | 0 |
| Medium | 7 | 0 | 0 | 0 | 0 |
| Low | 6 | 0 | 0 | 0 | 0 |
| **Total** | **19** | **0** | **0** | **0** | **0** |

---

## Part 8: Review Schedule

| Review | Frequency | Owned By |
|--------|-----------|----------|
| Gap status update | Bi-weekly | Yoni |
| Gap re-prioritization | Monthly | Human + Yoni |
| New gap identification | Continuous | All agents |
| Gap closure verification | Per sprint | Wealon |

---

*This document will be updated as gaps are identified and closed.*

*Generated by BMAD Gap Analysis Framework*
*Governed by Baseline v1.0*
