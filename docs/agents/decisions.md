# Agent Ecosystem Decisions Log - CartesSociete

**Version**: 1.0
**Last Updated**: 2026-01-19
**Phase**: BMAD+AGENTIC Phase 6 - Decisions & Memory

---

## Purpose

This document records all design decisions, rejected alternatives, open questions, and technical debt related to the agent ecosystem. It serves as the institutional memory of why the system is built this way.

---

## Part 1: Major Design Decisions

### Decision D001: Yoni-First Architecture

**Date**: 2026-01-19
**Decision**: All user requests route through yoni-orchestrator first, with documented exceptions.

**Context**:
The agent ecosystem has many specialized agents. Without a routing layer, users must know which agent handles what.

**Options Considered**:

| Option | Pros | Cons |
|--------|------|------|
| **A: Direct agent invocation** | Fast, no overhead | Users must know agents, miss coordination |
| **B: Always-Yoni** | Consistent, coordinated | Overhead for simple queries |
| **C: Yoni-first with exceptions** | Balance of A and B | Requires exception documentation |

**Decision**: Option C

**Rationale**:
- Orchestration is valuable for complex tasks
- Simple queries (file lookup) don't need orchestration
- Documented exceptions give best of both worlds

**Consequences**:
- Users must learn exception rules
- Explore can be called directly for simple lookups
- Complex tasks get proper coordination

**Technical Debt**: None

---

### Decision D002: No Game-Mechanic-Expert Agent

**Date**: 2026-01-19
**Decision**: Defer creating a game-mechanic-expert agent. Use documentation + human escalation instead.

**Context**:
No existing agent understands CartesSociete game rules. This is a CRITICAL gap per friction-map.md.

**Options Considered**:

| Option | Pros | Cons |
|--------|------|------|
| **A: Create game-mechanic-expert** | Closes gap, autonomous | Complex, maintenance burden, persona risk |
| **B: Documentation + human** | Simple, accurate | Human bottleneck, not autonomous |
| **C: Embed rules in agent instructions** | No new agent | Instructions become huge, still no reasoning |

**Decision**: Option B

**Rationale**:
- Project is small enough that human escalation is acceptable
- Creating a new agent persona has high complexity cost
- Embedded instructions don't give reasoning capability
- Defer until human escalation becomes bottleneck

**Consequences**:
- Game rule questions require human input
- Agents provide supporting data, humans make game decisions
- System is not fully autonomous for game design

**Technical Debt**:
- **TD001**: Game mechanics gap - revisit if project scales
- **TD002**: Balance analysis partially automated - human interpretation required

---

### Decision D003: Sequential Review (QC → Clovis)

**Date**: 2026-01-19
**Decision**: Quality-Control reviews first (substance), then Clovis reviews (process).

**Context**:
Both agents review code, creating overlap. Need clear order.

**Options Considered**:

| Option | Pros | Cons |
|--------|------|------|
| **A: Clovis first** | Process gates early | May format code that gets rejected |
| **B: QC first** | Substance validated before process | QC may review unformatted code |
| **C: Parallel** | Fast | May conflict, duplicate work |

**Decision**: Option B

**Rationale**:
- No point committing code that's substantively wrong
- QC catches "fake implementations" that would waste Clovis's time
- Sequential is clearer than parallel

**Consequences**:
- QC reviews may see unformatted code
- Two review steps (acceptable overhead)

**Technical Debt**: None

---

### Decision D004: ML Agent Escalation Protocol

**Date**: 2026-01-19
**Decision**: For ML problems, escalate Dulcy → Pierre-Jean → Alexios.

**Context**:
Three ML agents (Dulcy, Pierre-Jean, Alexios) overlap. Need routing clarity.

**Options Considered**:

| Option | Pros | Cons |
|--------|------|------|
| **A: Always start with Alexios** | Expert opinion first | Overkill for simple bugs |
| **B: Always start with Dulcy** | Implementation issues most common | Wastes time if architecture wrong |
| **C: Diagnose first, then route** | Best match | Diagnosis is also a routing problem |
| **D: Dulcy → Pierre-Jean → Alexios** | Incremental escalation | May iterate through all three |

**Decision**: Option D

**Rationale**:
- Most ML issues are implementation bugs (Dulcy)
- If code is correct, hyperparameters are next suspect (Pierre-Jean)
- Architecture problems are rarest (Alexios)
- Escalation matches probability of root cause

**Consequences**:
- May take 3 steps to reach architecture issues
- Each agent can escalate to next
- Accept inefficiency as cost of clear protocol

**Technical Debt**:
- **TD003**: No pre-diagnosis step - could add lightweight triage later

---

### Decision D005: Conditional Wealon Activation

**Date**: 2026-01-19
**Status**: ⚠️ SUPERSEDED by D009

**Original Decision**: Wealon (auditor) is inactive by default, activated only for specific triggers.

**Context**:
Wealon provides deep audits but adds review overhead.

**Options Considered**:

| Option | Pros | Cons |
|--------|------|------|
| **A: Always active** | Comprehensive audits | Slows everything |
| **B: Never active** | Fast iteration | Miss security/quality issues |
| **C: Triggered activation** | Balance | Requires trigger definition |

**Original Decision**: Option C

**Original Activation Triggers**:
- Pre-release checkpoint
- External code exposure
- Authentication/security changes
- Monthly technical debt inventory

**Original Rationale**:
- Research project doesn't need constant auditing
- Major milestones benefit from deep review
- Monthly cadence catches drift

**SUPERSESSION NOTE (2026-01-19)**:
This decision was superseded by D009 which makes Wealon MANDATORY for every task as an exit gate. The original "triggered activation" approach was upgraded to "always active" to ensure quality control on all work.

**Technical Debt**: None (superseded)

---

### Decision D006: Handoff Contracts for Major Changes Only

**Date**: 2026-01-19
**Decision**: Formal handoff documents required only for major changes.

**Context**:
Handoff contracts preserve context but add overhead.

**Major Change Definition**:
- New model architecture
- New game mechanic
- Changes to combat formula
- Changes to ability parsing

**Exempt**:
- Bug fixes
- Refactoring
- Test additions
- Documentation

**Rationale**:
- Full enforcement is too heavy
- Major changes have highest context loss risk
- Small changes context fits in commit message

**Consequences**:
- Small changes may lose context
- Load-bearing files get documentation

**Technical Debt**:
- **TD004**: Small changes to abilities.py may need more documentation than exemption allows

---

### Decision D007: Financial Agents Explicitly Rejected

**Date**: 2026-01-19
**Decision**: Financial domain agents (14 agents) are never used for CartesSociete.

**Context**:
Many available agents are designed for financial markets.

**Rejected Agents**:
research-remy-stocks, iacopo-macro-futures-analyst, nicolas-risk-manager, victor-pnl-manager, pnl-validator, trading-execution-engine, backtester-agent, cost-optimizer-lucas, french-tax-optimizer, helena-execution-manager, portfolio-manager-jean-yves, legal-team-lead, legal-compliance-reviewer, antoine-nlp-expert

**Rationale**:
- Card games ≠ financial markets
- Mental models don't transfer
- "Portfolio optimization" ≠ "deck building"
- Wrong domain leads to wrong conclusions

**Consequences**:
- Cannot use 14 available agents
- Must build game-specific workflows
- No temptation to misapply financial concepts

**Technical Debt**: None (this is a feature)

---

### Decision D008: Baseline v1.0 Governance Freeze

**Date**: 2026-01-19
**Decision**: Freeze all design documents as Baseline v1.0 with formal change control.

**Context**:
After completing BMAD+AGENTIC design phases, Wealon audit, system truth resolution, enforcement pass, and human operating contract, the system is complete and must be stabilized.

**Frozen Artifacts**:
- AGENTS.md (v2.0)
- project-context.md
- expanded-inventory.md
- friction-map.md
- simulations.md
- decisions.md (this document)
- yoni-perspective.md
- wealon-perspective.md
- baseline-v1.0.md (governance master)

**Rationale**:
- Design work is complete
- Continued modification creates drift
- Operational stability requires frozen baseline
- Changes must be governed, not exploratory

**Consequences**:
- No design changes without v2.0 process
- All modifications must be classified (legal vs breaking)
- Human checkpoints are permanent
- Scope boundaries are non-negotiable

**Technical Debt**: None (this is governance closure)

---

### Decision D009: Mandatory Wealon Exit Gate

**Date**: 2026-01-19
**Decision**: Wealon is MANDATORY for every task as an exit gate auditor.

**Context**:
After completing BMAD+AGENTIC design, the need for consistent quality control became apparent. The original D005 (conditional activation) was insufficient.

**Supersedes**: D005 (Conditional Wealon Activation)

**New Rule**:
- Wealon MUST be called at the end of every task
- No task is complete until Wealon has reviewed it
- Wealon audits: code changes, planning artifacts, compliance, completeness

**Rationale**:
- Consistent quality enforcement
- Catches shortcuts and workarounds
- Ensures compliance with project standards
- Exit gate prevents incomplete work from being marked done

**Consequences**:
- Every task takes longer (audit step added)
- Higher quality output
- Issues caught before commit, not after

**Technical Debt**: None

---

### Decision D010: Analytical Mandate (Three-Layer Distinction)

**Date**: 2026-01-19
**Decision**: Establish a non-negotiable three-layer distinction for all agent output.

**Context**:
CartesSociete exists to analyze the game mathematically, statistically, and strategically. The distinction between what agents CAN do and what requires human judgment was implicit. This decision makes it explicit and binding.

**The Three Layers**:

| Layer | Scope | Authority |
|-------|-------|-----------|
| **Layer 1: Descriptive & Strategic Analysis** | Simulations, win rates, correlations, equilibria, outliers, comparisons | **AGENT-ALLOWED** |
| **Layer 2: Normative Interpretation** | "Balanced", "unbalanced", "good", "bad", "healthy", "unhealthy" | **HUMAN-ONLY** |
| **Layer 3: Prescriptive Decisions** | "Should change", "buff", "nerf", design recommendations | **HUMAN-ONLY** |

**Decision**: This mandate is NON-NEGOTIABLE and defines the system's identity.

**Rationale**:
- Agents excel at computation, statistics, and game theory
- Agents cannot reason about design intent or player experience
- Clear boundaries prevent scope creep into game design
- Human designers need data, not opinions

**Consequences**:
- All agent output must use descriptive language
- Forbidden phrases: "overpowered", "unhealthy", "better design", "should be nerfed"
- Required phrasing: "dominates in X% of matchups", "statistically significant correlation"
- When interpretation is needed, agents must state "This requires human judgment"

**Success Criterion**:
1. Output reveals game structure without claiming design authority
2. Humans can use agent data to make decisions
3. Agents never substitute analysis for judgment

**Technical Debt**: None (this is governance closure)

---

## Part 2: Open Questions

### OQ001: Should Balance Analysis Be In-Scope for Agents?

**Status**: ✅ RESOLVED by D010 (Analytical Mandate)

**Question**: Can agents autonomously perform balance analysis, or is this inherently a human task?

**Resolution**: The three-layer distinction clarifies this completely:
- **Layer 1 (Agent-Allowed)**: Run simulations, compute statistics, identify outliers, calculate correlations
- **Layer 2 (Human-Only)**: Interpret what "balanced" means, judge whether something is "good" or "bad"
- **Layer 3 (Human-Only)**: Propose changes, recommend buffs/nerfs

**Final Answer**: Agents perform Layer 1 analysis. Layers 2 and 3 are human-only. This is not a limitation but the system's identity.

---

### OQ002: How to Validate RL Agent Behavior Qualitatively?

**Question**: Win rate measures success, but how do we know the agent plays "correctly" vs exploiting bugs?

**Current Answer**: Unknown. We have:
- Win rate metrics
- Game logs (for manual inspection)

We don't have:
- Automated "play style" evaluation
- Bug exploitation detection
- Strategy diversity metrics

**Implications**: High-win-rate agent might be gaming the system.

**Revisit When**: Training produces agents that "feel wrong" despite winning.

---

### OQ003: Should abilities.py Fail Loudly?

**Question**: When bonus_text doesn't match any pattern, should the system fail loudly or log and continue?

**Current Answer**: Implicit silent failure (not designed either way).

**Arguments for Loud Failure**:
- Catches data errors immediately
- Prevents incorrect game behavior

**Arguments for Silent + Log**:
- Allows partial functionality
- Doesn't crash for optional features

**Implications**: Current behavior is undefined - it's neither loud nor logged.

**Required Action**: Define explicit behavior (Decision D008 pending).

---

### OQ004: What Makes a "Major Change"?

**Question**: Handoff contracts are required for "major changes" but definition is fuzzy.

**Current Definition**:
- New model architecture
- New game mechanic
- Changes to combat formula
- Changes to ability parsing

**Edge Cases**:
- Bug fix that changes combat edge case behavior?
- Refactor that touches abilities.py structure?
- New card that uses existing mechanics?

**Implications**: Some edge cases may slip through.

**Revisit When**: Context loss causes rework.

---

## Part 3: Technical Debt Register

| ID | Description | Severity | Origin | Mitigation | Resolution Plan |
|----|-------------|----------|--------|------------|-----------------|
| TD001 | Game mechanics gap | HIGH | D002 | Documentation + human | Revisit if human escalation bottlenecks |
| TD002 | Balance analysis partially automated | MEDIUM | D002 | Human interpretation | Define workflow, accept limitation |
| TD003 | No ML diagnosis step | LOW | D004 | Escalation protocol | Add lightweight triage if escalations excessive |
| TD004 | Small changes to abilities.py | LOW | D006 | Commit messages | Lower handoff threshold for this file |
| TD005 | Silent ability parsing failure | HIGH | OQ003 | None | Implement logging (D008 pending) |
| TD006 | No RL behavior validation | MEDIUM | OQ002 | Manual inspection | Add qualitative metrics |

---

## Part 4: Rejected Alternatives Archive

### Rejected: Create Game-Mechanic-Expert Agent (D002)

**Why Proposed**: Closes critical game mechanics gap.

**Why Rejected**:
- Creating agent persona is complex
- Must keep agent updated with rule changes
- Risk of agent "drift" from game intent
- Human escalation acceptable for project size

**Conditions to Reconsider**:
- Human escalation becomes bottleneck (>5 game rule questions/week)
- Project scales to need autonomous balance analysis
- New team members unfamiliar with game

---

### Rejected: Always-On Wealon Audits (D005)

**Why Proposed**: Comprehensive code audits catch more issues.

**Why Rejected**:
- Review overhead for research project
- Slows iteration
- Diminishing returns after Quality-Control

**Conditions to Reconsider**:
- Project becomes production software
- Code becomes externally visible
- Security becomes a requirement

---

### Rejected: Financial Agents for Game Economics (D007)

**Why Proposed**: Financial agents have economic analysis expertise.

**Why Rejected**:
- Mental models don't transfer
- "Risk" in finance ≠ "risk" in games
- Would require constant domain translation
- Simulations.md demonstrated this thoroughly

**Conditions to Reconsider**: Never. This is a fundamental domain mismatch.

---

### Rejected: Parallel Quality-Control + Clovis Review (D003)

**Why Proposed**: Faster reviews.

**Why Rejected**:
- May produce conflicting results
- Wasted effort if one rejects
- Sequential is clearer

**Conditions to Reconsider**:
- Review time becomes bottleneck
- Agents learn to coordinate parallel review

---

### Rejected: Remove Quality-Control (Simulation 6)

**Why Proposed**: Reduces overlap with Clovis.

**Why Rejected**:
- QC catches different issues than Clovis
- Clovis = process, QC = substance
- Removing either creates gap

**Conditions to Reconsider**: Never. Both are needed.

---

## Part 5: Memory for Future Sessions

### Context That Must Be Preserved

1. **ANALYTICAL MANDATE** - Three-layer distinction is NON-NEGOTIABLE (see D010)
   - Layer 1 (Descriptive): Agents DO statistics, simulations, game theory
   - Layer 2 (Normative): Agents DO NOT judge "balanced", "good", "bad"
   - Layer 3 (Prescriptive): Agents DO NOT recommend changes
2. **SYSTEM IS FROZEN** - Baseline v1.0 is authoritative, see baseline-v1.0.md
3. **Yoni is the entry point** - but Explore can be called directly for simple lookups
4. **No agent understands game rules** - game design questions need human input
5. **ML escalation order is Dulcy → Pierre-Jean → Alexios**
6. **Financial agents are never used** - domain mismatch is fundamental
7. **Wealon is MANDATORY** - exit gate for every task (see D009)
8. **abilities.py is high-risk** - extra care for changes
9. **Human checkpoints are MANDATORY** - for combat.py, abilities.py, state.py
10. **Design phase is CLOSED** - all changes are governed, not exploratory

### Patterns That Work

1. "Fix bug in X" → Explore → implement → QC → Clovis → merge
2. "Improve RL performance" → Dulcy → Pierre-Jean → Alexios
3. "Run balance simulation" → Dulcy → Alexios → human
4. "Add new feature" → Plan → implement → QC → Clovis → merge

### Patterns That Fail

1. "Is card X balanced?" → No agent can answer
2. "Design new game mechanic" → No agent owns this
3. "Should we change the combat formula?" → Human decision required

---

## Part 6: Document Maintenance

### FROZEN STATUS

This document is part of Baseline v1.0 and is now **FROZEN**.

Updates are only allowed for:
- Recording new decisions that comply with baseline-v1.0.md
- Resolving open questions without changing scope
- Documenting new technical debt within existing boundaries

Updates are NOT allowed for:
- Scope expansion
- Assumption reversal
- Authority changes
- Human checkpoint removal

### Update Triggers (Within Baseline v1.0)

This document MAY be updated when:
- New decision complies with frozen scope (add to Part 1)
- Open question is resolved without scope change (update Part 2)
- Technical debt is resolved (update Part 3)
- Alternative is rejected within existing framework (add to Part 4)

### Review Schedule

- Monthly Wealon audit (triggered)
- Pre-release checkpoint
- When new team members onboard (read-only orientation)

---

*This document is the institutional memory of the agent ecosystem.*
*Status: FROZEN under Baseline v1.0*
*Governance: baseline-v1.0.md*

*Generated by BMAD+AGENTIC Phase 6: Decisions & Memory*
