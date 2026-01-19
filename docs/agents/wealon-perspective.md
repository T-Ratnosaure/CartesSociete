# Auditor Perspective: Wealon's View of the Agent Ecosystem

**Perspective**: Auditor / Risk Assessor
**Agent**: wealon-regulatory-auditor (Currently Inactive)
**Bias**: "What could go wrong?"
**Last Updated**: 2026-01-19

---

## Executive Summary

As an auditor reviewing this ecosystem from the outside, I see **structural risks that are being papered over with documentation**. The ecosystem has fundamental gaps that are acknowledged but not resolved. The "defer to human" pattern appears in every difficult case, which defeats the purpose of an autonomous agent system. This is a well-documented house built on sand.

---

## Part 1: Critical Findings

### Finding 1: CRITICAL - No Domain Authority

**Observation**: No agent in this ecosystem actually understands CartesSociete game rules.

**Evidence**:
- friction-map.md explicitly calls this "CRITICAL (10/10)"
- project-context.md serves as documentation, not reasoning
- Every game rule question routes to human

**Risk Assessment**:
The entire project is a GAME ENGINE with AI PLAYERS for a CARD GAME. Yet no agent understands the game. This is like having a medical diagnosis system where no agent understands medicine.

**What Could Go Wrong**:
- RL agent learns to exploit game bugs, not play well
- Balance analysis identifies statistical outliers that are intentional design
- Code changes break game rules, no agent notices
- New features violate game design principles

**My Recommendation**:
This is not a "document and escalate" problem. Either:
1. Create a game-mechanic-expert agent (rejected as "too complex")
2. Embed game rules into agent instructions (not done)
3. Accept that this is a human-supervised system (current)

Option 3 is honest but means this isn't an autonomous agent ecosystem - it's a human-supervised tool collection.

---

### Finding 2: HIGH - Quality Theater Risk

**Observation**: The ecosystem has multiple overlapping review mechanisms, but the overlap may create false confidence rather than actual quality.

**Evidence**:
- Clovis reviews process
- Quality-Control reviews substance
- Both must pass
- But neither understands game rules (see Finding 1)

**Risk Assessment**:
A change to combat.py could:
- Pass Clovis (correct git workflow, has tests, typed)
- Pass Quality-Control (tests run, implementation looks real)
- Still be WRONG (game logic error)

Neither agent can catch: "This damage calculation doesn't match the physical card game rules."

**What Could Go Wrong**:
- Code passes all reviews but is semantically incorrect
- Tests pass but test the wrong behavior
- "Reviewed by 2 agents" creates false confidence
- Bugs discovered much later, expensive to fix

**My Recommendation**:
Acknowledge that agent review is INSUFFICIENT for game logic correctness. Either:
1. Add game rule tests that agents can verify
2. Require human review for game logic changes
3. Accept that game logic errors will slip through

Current documentation doesn't clearly state this limitation.

---

### Finding 3: MEDIUM - Handoff Document Decay

**Observation**: Handoff contracts are defined but enforcement is "major changes only."

**Evidence**:
- simulations.md approves handoff contracts only for major changes
- "Bug fixes, refactoring, test additions" are exempt
- These exempt categories can still have significant context

**Risk Assessment**:
A "bug fix" to abilities.py could actually be a design decision. Without a handoff document:
- Why was this specific fix chosen?
- What alternatives were rejected?
- What edge cases were considered?

**What Could Go Wrong**:
- "Small" changes accumulate without documentation
- Future developers don't understand why code exists
- Reverting changes becomes risky (might break unknown things)

**My Recommendation**:
Lower the threshold for handoff contracts, especially for:
- abilities.py (the highest-risk file)
- combat.py (damage formula)
- environment.py (RL observation/action space)

These are load-bearing files where "small" changes have big impacts.

---

### Finding 4: MEDIUM - Silent Failure in Ability Parsing

**Observation**: abilities.py uses regex to parse French bonus_text. Unknown patterns fail silently.

**Evidence**:
- 50+ regex patterns in abilities.py
- No "unrecognized pattern" logging
- New cards could have unparseable abilities

**Risk Assessment**:
A new card with bonus_text "Inflige 5 DGT quand l'ennemi joue une carte" might not match any pattern. Result: ability silently ignored. Game plays wrong.

**What Could Go Wrong**:
- New cards don't work as intended
- Balance analysis based on incorrect card behavior
- Bugs appear "random" (only when specific card is played)
- No agent would catch this (see Finding 1)

**My Recommendation**:
1. Add logging for unparseable bonus_text
2. Fail loudly, not silently
3. Add integration tests that verify all cards' abilities trigger
4. Make data-sophie responsible for card data validation

---

### Finding 5: LOW - Financial Agent Temptation

**Observation**: Financial agents are "explicitly rejected" but the door is left open for "explicit user approval."

**Evidence**:
- AGENTS.md: "Invoking a rejected agent requires explicit user approval"
- simulations.md rejects financial agents for domain mismatch

**Risk Assessment**:
The exception creates a path to misuse. A user might say "let's use Nicolas-risk-manager for game balance" without understanding why it's rejected.

**What Could Go Wrong**:
- User invokes financial agent "just to try"
- Agent applies wrong mental models
- Results look authoritative but are misleading
- Decisions made on bad analysis

**My Recommendation**:
Remove the exception path. If financial agents are wrong for this domain, they're wrong. Explicit user approval doesn't fix domain mismatch.

---

## Part 2: Process Audit

### Process 1: Code Review Flow

**Current**: Quality-Control → Clovis → PR → CI → Merge

**Audit Findings**:
| Step | Strength | Weakness |
|------|----------|----------|
| Quality-Control | Catches workarounds | Doesn't understand game rules |
| Clovis | Ensures process | Doesn't evaluate correctness |
| CI | Automated checks | Only tests what's tested |
| Merge | Clean history | No final game logic check |

**Gap**: No step verifies game logic correctness for game-changing code.

**Recommendation**: Add human review checkpoint for files matching:
- `**/combat*.py`
- `**/abilities*.py`
- `**/state*.py`

### Process 2: ML Development Flow

**Current**: Alexios (design) → Dulcy (implement) → Pierre-Jean (tune)

**Audit Findings**:
| Step | Strength | Weakness |
|------|----------|----------|
| Alexios | Architecture expertise | Financial bias, no game knowledge |
| Dulcy | Implementation skill | Doesn't validate design |
| Pierre-Jean | Tuning expertise | Doesn't question architecture |

**Gap**: No one validates that the RL agent is learning to play the game correctly (vs exploiting bugs).

**Recommendation**: Add evaluation step that checks:
- Does agent win by legal play?
- Does agent exploit edge cases?
- Does agent use diverse strategies?

### Process 3: Balance Analysis Flow

**Current**: (Ad-hoc, no defined flow)

**Audit Findings**:
This is not a process - it's a gap with workarounds.

**Recommendation**: Either formalize a process or acknowledge balance analysis as out-of-scope for agents.

---

## Part 3: Documentation Audit

### Document: project-context.md

**Strengths**:
- Comprehensive domain model
- Clear damage formula
- Explicit assumptions

**Weaknesses**:
- No machine-readable rules
- Can't be "queried" by agents
- May drift from actual code

**Recommendation**: Add automated tests that verify project-context.md matches code behavior.

### Document: AGENTS.md

**Strengths**:
- Clear agent categories
- Usage rules defined
- Governance in place

**Weaknesses**:
- "Conditional" agents vaguely defined
- Activation conditions subjective
- No agent effectiveness metrics

**Recommendation**: Define quantitative triggers for conditional agents.

### Document: friction-map.md

**Strengths**:
- Honest about gaps
- Severity scored
- Mitigation attempts

**Weaknesses**:
- CRITICAL gaps deferred
- "Human escalation" overused
- No resolution timeline

**Recommendation**: Create resolution plan for CRITICAL gaps, even if plan is "accept and document."

---

## Part 4: Risk Register

| ID | Risk | Likelihood | Impact | Current Mitigation | Adequacy |
|----|------|------------|--------|-------------------|----------|
| R1 | Game logic errors undetected | HIGH | HIGH | Documentation + human review | INADEQUATE |
| R2 | RL agent learns wrong behavior | MEDIUM | HIGH | Win rate metrics | PARTIAL |
| R3 | Balance analysis misleading | MEDIUM | MEDIUM | Human interpretation | PARTIAL |
| R4 | Ability parsing fails silently | MEDIUM | MEDIUM | None | INADEQUATE |
| R5 | Handoff context lost | LOW | MEDIUM | Optional contracts | PARTIAL |
| R6 | Agent ecosystem drift | LOW | LOW | Monthly review | ADEQUATE |

### Risk R1: Game Logic Errors
**Current State**: No agent can catch game logic errors. Tests catch implementation bugs, not design bugs.
**Required Action**: Accept this limitation explicitly OR add game rule verification.

### Risk R2: RL Agent Learns Wrong
**Current State**: Win rate is the metric, but winning by exploiting bugs counts as winning.
**Required Action**: Add qualitative evaluation of agent behavior, not just win rate.

### Risk R4: Silent Parsing Failure
**Current State**: Unknown bonus_text patterns are silently ignored.
**Required Action**: Add logging and alerting for unparseable patterns.

---

## Part 5: Comparison to Builder Perspective

| Topic | Builder (Yoni) Says | I (Wealon) Say |
|-------|---------------------|----------------|
| Game mechanics gap | "Human escalation works" | "Defeats ecosystem purpose" |
| Quality-Control | "Sometimes over-blocks" | "Can't catch real problems" |
| ML agent overlap | "Escalation protocol handles it" | "Wastes time diagnosing" |
| Balance analysis | "Need clearer workflow" | "Need domain expertise first" |
| Documentation | "Helps me route" | "Can't substitute for reasoning" |

**Fundamental Disagreement**:
Yoni optimizes for "getting tasks routed." I optimize for "getting tasks done correctly." These are different goals. Yoni can route a balance analysis request, but routing to agents that don't understand balance doesn't solve the problem.

---

## Part 6: Audit Verdict

### Overall Assessment: CONDITIONAL PASS

This ecosystem is **acceptable for development tasks** but **inadequate for its stated goals**.

**Acceptable For**:
- Code implementation with human oversight
- Git/CI/CD process enforcement
- ML training implementation (not design validation)

**Inadequate For**:
- Autonomous game design decisions
- Balance analysis without human interpretation
- Game logic correctness verification

### Required Actions for Full Pass

1. **Acknowledge Scope Limitation**: State explicitly that game design/balance requires human judgment
2. **Add Silent Failure Detection**: Log unparseable ability patterns
3. **Strengthen Game Logic Review**: Human checkpoint for game-changing code
4. **Define Balance Analysis Scope**: What can agents do vs what requires human

### Recommended Actions (Not Required)

1. Create game-mechanic-expert agent (deferred due to complexity)
2. Add game rule integration tests
3. Quantify agent effectiveness

---

## Conclusion

This ecosystem is well-documented but not well-defended. The documentation acknowledges risks without resolving them. The phrase "escalate to human" appears too often for a system designed for autonomous operation.

If the goal is "agents help humans work faster," this ecosystem succeeds. If the goal is "agents can work autonomously," this ecosystem fails for game design and balance tasks.

The builder perspective (Yoni) sees routing problems. I see reasoning problems. Routing to agents that can't reason about the domain doesn't help.

---

*This perspective prioritizes "catching problems" over "getting things done."*

*Generated by BMAD+AGENTIC Phase 5: Multi-Perspective Audit (Auditor View)*
