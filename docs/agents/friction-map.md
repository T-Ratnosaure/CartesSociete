# Friction Map - CartesSociete Agent Ecosystem

**Version**: 1.0
**Last Updated**: 2026-01-19
**Phase**: BMAD+AGENTIC Phase 3 - Friction Analysis

---

## Purpose

This document identifies **friction points** in the agent ecosystem - places where agents overlap, conflict, create gaps, or have problematic handoffs. Friction is not always bad, but unacknowledged friction causes failures.

---

## Part 1: Overlap Analysis

Overlaps occur when multiple agents could reasonably handle the same task, creating ambiguity about which to use.

### 1.1 ML/AI Agent Overlap

**Overlapping Agents**: alexios-ml-predictor, dulcy-ml-engineer, pierre-jean-ml-advisor

**Overlap Zone**: "Help me improve my RL agent's performance"

| Scenario | Alexios Claims | Dulcy Claims | Pierre-Jean Claims |
|----------|---------------|--------------|-------------------|
| "Model not learning" | Architecture issue | Code bug | Hyperparameter |
| "Win rate plateaued" | Need better reward | Implementation error | Need curriculum |
| "Overfitting detected" | Change architecture | Fix data pipeline | Tune regularization |

**Friction Score**: HIGH (8/10)

**Why This Matters**:
In CartesSociete, RL training problems are common. When PPO agent isn't learning, which agent should diagnose? The answer depends on the root cause, but the root cause is unknown at query time.

**Resolution Protocol**:
```
1. Start with Dulcy (implementation issues are most common)
2. If code is correct, escalate to Pierre-Jean (hyperparameters)
3. If hyperparameters exhausted, escalate to Alexios (architecture)
```

**Remaining Risk**: Step 1-3 could waste time if root cause is actually architecture. Accept this as cost of avoiding over-engineering.

---

### 1.2 Code Quality Agent Overlap

**Overlapping Agents**: it-core-clovis, quality-control-enforcer

**Overlap Zone**: "Review this code before I merge"

| Aspect | Clovis Focuses On | Quality-Control Focuses On |
|--------|-------------------|---------------------------|
| Git workflow | Correct branch, message format | Not relevant |
| Code style | Formatting, type hints | Not relevant |
| Tests exist | Yes/no | Tests actually test something |
| Implementation | Syntactically correct | Semantically correct |
| Shortcuts | Doesn't detect | Primary detection target |

**Friction Score**: MEDIUM (5/10)

**Why This Matters**:
A PR could pass Clovis (correct format, has tests, proper commit) but fail Quality-Control (tests are mocks, implementation is fake). Conversely, quality code could fail Clovis on process grounds.

**Resolution Protocol**:
```
1. Quality-Control runs FIRST (is the code actually good?)
2. Clovis runs SECOND (is the process correct?)
3. Both must pass for merge
```

**Remaining Risk**: Quality-Control may flag valid design decisions as "workarounds." Document intentional decisions explicitly.

---

### 1.3 Orchestration Overlap

**Overlapping Agents**: yoni-orchestrator, general-purpose, Explore

**Overlap Zone**: "How does the combat system work?"

| Agent | Response Style |
|-------|---------------|
| Yoni | Routes to Explore, adds coordination overhead |
| general-purpose | Deep research, may be overkill |
| Explore | Quick search, good for targeted queries |

**Friction Score**: LOW (3/10)

**Why This Matters**:
Over-orchestration wastes tokens and time. Under-orchestration misses context.

**Resolution Protocol**:
```
- Specific file/function lookup → Explore directly
- Conceptual question requiring exploration → Explore
- Complex multi-step task → Yoni
- Complex research with unknowns → general-purpose
```

---

## Part 2: Gap Analysis

Gaps occur when no agent clearly owns a responsibility, leaving tasks orphaned.

### 2.1 Game Mechanics Domain Gap

**The Gap**: No agent deeply understands CartesSociete game rules.

**Evidence**:
- Alexios thinks in ML terms (inputs, outputs, losses)
- Dulcy thinks in implementation terms (tensors, batches)
- Clovis thinks in code quality terms (style, process)
- Quality-Control thinks in verification terms (real vs fake)

**None of them think in game terms**:
- Why does Archer bonus trigger against Defenseur?
- Is Lapin family's board expansion balanced?
- Does the combat formula match the physical card game?

**Gap Severity**: CRITICAL (10/10)

**Impact**:
- Balance analysis could use wrong metrics
- RL reward shaping could incentivize wrong behaviors
- Code review couldn't catch game logic errors
- New features could violate game design principles

**Mitigation**:
```
OPTION A: Domain Expert Role (Not Implemented)
- Create a game-mechanic-expert agent persona
- Problem: No such agent exists in the system

OPTION B: Documentation Compensation (Current)
- project-context.md serves as domain reference
- All agents must consult it for game rule questions
- Problem: Document is passive, can't reason

OPTION C: Human as Domain Expert
- Escalate all game rule questions to user
- Problem: Defeats purpose of agent ecosystem
```

**Current Approach**: Option B + C hybrid. Document + human escalation.

**Technical Debt**: This gap is the largest architectural weakness. Game rule questions will require human input until resolved.

---

### 2.2 Balance Analysis Gap

**The Gap**: No agent owns end-to-end balance analysis.

**What Exists**:
- `card_tracker.py` collects statistics
- Simulation can run games
- Analysis templates exist

**What's Missing**:
- No agent to interpret balance data
- No agent to propose balance changes
- No agent to validate balance changes

**Gap Severity**: HIGH (7/10)

**Why It Matters**:
CartesSociete has explicit goal of balance analysis, but no agent pathway to achieve it.

**Mitigation**:
```
OPTION A: Repurpose Alexios for Balance
- Alexios understands metrics and thresholds
- Translate "overpowered card" to "model with high feature importance"
- Problem: Requires explicit translation layer

OPTION B: Create Balance Analysis Workflow
- Combine: Dulcy (run simulations) → Alexios (interpret metrics) → Human (approve changes)
- Problem: No agent proposes actual card changes

OPTION C: Accept as Human Task
- Agents provide data, human makes decisions
- Problem: Reduces autonomy
```

**Current Approach**: Option A + C. Alexios interprets, human decides.

---

### 2.3 Card Data Management Gap

**The Gap**: No agent owns card JSON data quality.

**Evidence**:
- Card data lives in `data/cards/*.json`
- `repository.py` loads cards but doesn't validate
- `abilities.py` parses bonus_text but silently fails on unknown patterns

**What Could Go Wrong**:
- New card added with typo in bonus_text
- Card's family_abilities don't match family definition
- Level 2 card not linked to Level 1 card

**Gap Severity**: MEDIUM (5/10)

**Mitigation**:
```
- data-engineer-sophie could own data quality
- But: Card data rarely changes (physical cards are source)
- For now: Manual review when cards added
```

**Technical Debt**: No automated card data validation. If card pool expands significantly, this becomes a problem.

---

### 2.4 Production Deployment Gap

**The Gap**: No production deployment pathway exists.

**Evidence**:
- No deployment scripts
- No inference server
- No model serving infrastructure

**Gap Severity**: LOW (2/10)

**Why Low**:
This project is research/analysis, not production software. No deployment is needed.

**Mitigation**: Document this as explicit non-goal. If deployment becomes needed, activate cybersecurity-maxime and create deployment infrastructure.

---

## Part 3: Handoff Analysis

Handoffs occur when work transfers between agents. Lossy handoffs cause context to disappear.

### 3.1 Alexios → Dulcy Handoff

**The Handoff**: Architecture design → Implementation

**What Should Transfer**:
- Model architecture (layers, activations)
- Input/output specifications (shapes, types)
- Training procedure (optimizer, schedule)
- Evaluation criteria

**What Gets Lost**:
- Rationale for design choices
- Rejected alternatives
- Implicit assumptions about data

**Friction Score**: MEDIUM (6/10)

**Handoff Contract**:
```markdown
## Architecture Handoff: [Feature Name]

### Model Architecture
- Input shape: (N,)
- Output shape: (M,)
- Hidden layers: [256, 256]
- Activation: ReLU

### Training
- Algorithm: MaskablePPO
- Learning rate: 3e-4
- Batch size: 64

### Why This Design
- [Explicit rationale]
- Rejected: [Alternative] because [reason]

### Assumptions
- [Assumption 1]
- [Assumption 2]

### Success Criteria
- Win rate > X% against [opponent]
```

**Enforcement**: All architecture handoffs must include rationale and rejected alternatives.

---

### 3.2 Implementation → Review Handoff

**The Handoff**: Dulcy/Clovis → Quality-Control

**What Should Transfer**:
- What was built
- Why it was built this way
- What tests exist
- Known limitations

**What Gets Lost**:
- Intent behind design choices
- What "success" looks like
- Edge cases intentionally not handled

**Friction Score**: MEDIUM (5/10)

**Handoff Contract**:
```markdown
## Implementation Handoff: [Feature Name]

### What Was Built
- [Description]

### Design Decisions
- [Decision 1]: Because [reason]
- [Decision 2]: Because [reason]

### Tests
- Unit: [files]
- Integration: [files]
- Not tested: [gaps and why]

### Known Limitations
- [Limitation 1]: Intentional because [reason]

### Success Criteria
- [Criterion 1]
- [Criterion 2]
```

---

### 3.3 Research → Production Handoff

**The Handoff**: ML-Production-Engineer cleanup

**What Should Transfer**:
- Working research code (messy but correct)
- Implicit knowledge of what's important
- Test data and validation approach

**What Gets Lost**:
- "Magic constants" that make it work
- Order-dependent operations
- Subtle implementation details

**Friction Score**: HIGH (7/10)

**Handoff Contract**:
```markdown
## Research-to-Production Handoff

### Research Code Location
- Notebooks: [paths]
- Scripts: [paths]

### Known "Magic"
- [Value X is 0.3 because empirically works]
- [Order matters: do A before B]

### Critical Tests
- [Test 1]: Must pass or algorithm wrong
- [Test 2]: Regression test

### What CAN'T Change
- [Function X]: Mathematically derived
- [Constant Y]: From paper/experiment
```

---

## Part 4: Conflict Analysis

Conflicts occur when agents have incompatible goals or recommendations.

### 4.1 Speed vs Quality Conflict

**Conflicting Agents**: User expectations vs Quality-Control

**The Conflict**:
- User wants fast iteration
- Quality-Control wants thorough review
- Every feature gets scrutinized

**Manifestation**:
- "Just make it work" vs "But there's a workaround here"
- Quick fixes flagged as shortcuts
- Technical debt accumulates or progress slows

**Resolution Protocol**:
```
- Explicit "draft" vs "final" modes
- Draft: Skip Quality-Control, accept tech debt
- Final: Full Quality-Control review
- Document tech debt for later cleanup
```

---

### 4.2 Process vs Progress Conflict

**Conflicting Agents**: Clovis vs Development speed

**The Conflict**:
- Clovis enforces branch workflow
- Quick fixes feel heavy when routed through branches
- Direct commits to main tempting for "small" changes

**Resolution Protocol**:
```
- Define "trivial change" threshold
- Trivial: < 10 lines, no logic change → direct commit OK
- Non-trivial: branch workflow required
- Document exceptions
```

---

### 4.3 Simplicity vs Correctness Conflict

**Conflicting Agents**: Dulcy implementation vs Alexios design

**The Conflict**:
- Alexios may propose complex architecture
- Dulcy implements simpler version to get something working
- Simplification may lose important properties

**Manifestation**:
- "I simplified the architecture" vs "That was load-bearing complexity"
- Missing features discovered late
- Rework required

**Resolution Protocol**:
```
1. Dulcy must document any simplifications
2. Simplifications reviewed against success criteria
3. Explicit "MVP vs Full" specification from Alexios
```

---

## Part 5: Friction Severity Matrix

| Friction Point | Type | Severity | Impact on CartesSociete |
|---------------|------|----------|-------------------------|
| ML agent overlap | Overlap | HIGH | Common RL debugging confusion |
| Game mechanics gap | Gap | CRITICAL | No agent understands rules |
| Balance analysis gap | Gap | HIGH | Core project goal unaddressed |
| Alexios→Dulcy handoff | Handoff | MEDIUM | Architecture rationale lost |
| Speed vs Quality | Conflict | MEDIUM | Slows iteration |
| Code quality overlap | Overlap | MEDIUM | Redundant reviews |
| Card data gap | Gap | MEDIUM | No validation |
| Orchestration overlap | Overlap | LOW | Minor inefficiency |
| Deployment gap | Gap | LOW | Not needed |

---

## Part 6: Mitigation Priority

Based on severity and impact, address friction in this order:

### Priority 1: CRITICAL
1. **Game Mechanics Gap**: Document heavily, escalate to human, consider custom agent persona
2. **Balance Analysis Gap**: Create explicit workflow combining existing agents

### Priority 2: HIGH
3. **ML Agent Overlap**: Establish clear escalation protocol
4. **Alexios→Dulcy Handoff**: Enforce handoff contracts

### Priority 3: MEDIUM
5. **Code Quality Overlap**: Sequential review order
6. **Speed vs Quality Conflict**: Define draft/final modes
7. **Card Data Gap**: Add validation when pool expands

### Priority 4: LOW
8. **Orchestration Overlap**: Document direct-use patterns
9. **Deployment Gap**: Accept as non-goal

---

## Part 7: Open Friction (Unresolved)

These friction points are acknowledged but not resolved:

### 7.1 No Game Expert Agent
**Status**: Compensated with documentation and human escalation
**Risk**: Human becomes bottleneck for game rule questions
**Resolution Path**: Consider creating game-mechanic persona in agent descriptions

### 7.2 Balance Decision Authority
**Status**: Human makes all balance decisions
**Risk**: Agents provide data but can't recommend
**Resolution Path**: Could train Alexios on balance decision patterns

### 7.3 French Language Processing
**Status**: abilities.py parses French text with regex
**Risk**: New card text may not parse, failing silently
**Resolution Path**: Add unknown pattern detection and alerts

---

## Part 8: Friction Monitoring

How to detect new friction:

### 8.1 Signals of Overlap Friction
- Multiple agents called for same task
- Agent disputes (one says X, another says Y)
- Redundant work performed

### 8.2 Signals of Gap Friction
- Questions with no clear agent owner
- Human repeatedly answers same domain questions
- Tasks dropped or incomplete

### 8.3 Signals of Handoff Friction
- Rework due to missing context
- "I didn't know that" after handoff
- Different agents have different understanding of same work

### 8.4 Signals of Conflict Friction
- Process slows unexpectedly
- Quality complaints after delivery
- Repeated debates about same issues

---

*This document must be updated when new friction is discovered or resolved.*

*Generated by BMAD+AGENTIC Phase 3: Friction Mapping*
