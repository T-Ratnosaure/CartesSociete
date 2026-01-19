# Agent Ecosystem Decisions Log - CartesSociete

**Version**: 1.3
**Last Updated**: 2026-01-19
**Phase**: BMAD+AGENTIC Phase 6 - Decisions & Memory (D011-D016 + S-01, S-04, RL-02 implemented)

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

### Decision D011: Ability Parsing Strict Mode

**Date**: 2026-01-19
**Decision**: Unmatched ability patterns must raise errors when strict mode is enabled.

**Context**:
Technical review finding S-02 identified silent regex failure in `abilities.py`. When bonus_text does not match any pattern, the system silently returns 0 without indication.

**Options Considered**:

| Option | Pros | Cons |
|--------|------|------|
| **A: Maintain silent behavior** | No changes, stable | Missing patterns invisible |
| **B: Add logging only** | Visibility gained | Silent failures still occur |
| **C: Add strict mode** | Failure is explicit | Requires mode flag |
| **D: Track match metrics** | Statistical visibility | No per-card feedback |

**Decision**: Option C — Strict mode

**Rationale**:
- Unknown card text is invalid, not ignorable
- Missing patterns indicate incomplete implementation or data errors
- Strict mode converts ambiguity into explicit failure
- Mode flag allows gradual rollout

**Consequences**:
- Strict mode enabled → unmatched patterns raise errors
- All card text must be parseable or explicitly ignored
- Missing patterns are no longer silently tolerated

**Technical Debt**: Resolves TD005

**Source**: Technical review finding S-02

---

### Decision D012: Lapin Board Expansion Asymmetry Accepted

**Date**: 2026-01-19
**Decision**: Lapin family's unique board expansion mechanics are accepted as intentional design.

**Context**:
Technical review finding G-02 identified that Lapin is the only family with board expansion mechanics (Lapincruste +2/+4 slots, family thresholds +1/+2 slots).

**Options Considered**:

| Option | Pros | Cons |
|--------|------|------|
| **A: Accept as intended asymmetry** | Preserves design identity | Asymmetric strategy space |
| **B: Add expansion to other families** | Symmetry | Dilutes Lapin identity |

**Decision**: Option A — Accept as intended asymmetry

**Rationale**:
- Lapin asymmetry is a design identity, not a balance accident
- Board expansion defines Lapin's strategic niche
- Symmetry is not a requirement for good design

**Consequences**:
- Lapin remains the only family with board expansion
- This is documented design intent, not technical debt
- Future balance discussions must respect this identity

**Technical Debt**: None (design acceptance)

**Source**: Technical review finding G-02

---

### Decision D013: S-Team Board Limit Bypass Accepted

**Date**: 2026-01-19
**Decision**: S-Team cards intentionally do not count toward board limit.

**Context**:
Technical review finding G-05 identified that S-Team passive ("Ne compte pas comme un monstre du plateau") bypasses the board limit.

**Options Considered**:

| Option | Pros | Cons |
|--------|------|------|
| **A: Accept as intended asymmetry** | Preserves class identity | Free board presence |
| **B: Remove or modify passive** | Symmetry | Removes S-Team uniqueness |

**Decision**: Option A — Accept as intended asymmetry

**Rationale**:
- Free board presence is a class identity, not a loophole
- S-Team's passive is their defining characteristic
- Removing it would require fundamental class redesign

**Consequences**:
- S-Team maintains unique board bypass
- This is documented design intent, not technical debt
- Strategic implications are accepted

**Technical Debt**: None (design acceptance)

**Source**: Technical review finding G-05

---

### Decision D014: Configurable RL Reward Shaping

**Date**: 2026-01-19
**Decision**: Reward shaping constants become configuration parameters.

**Context**:
Technical review finding RL-01 identified asymmetric reward shaping (+0.1 damage dealt, -0.05 damage taken) that may influence learned agent strategies toward aggression.

**Options Considered**:

| Option | Pros | Cons |
|--------|------|------|
| **A: Keep current rewards** | Stable | Playstyle hard-coded |
| **B: Equalize damage rewards** | Neutrality | May reduce learning signal |
| **C: Remove shaping entirely** | Pure win/lose signal | Sparse rewards |
| **D: Make rewards configurable** | Experimentation enabled | Configuration complexity |

**Decision**: Option D — Make rewards configurable

**Rationale**:
- Playstyle is not hard-coded; it is a tunable axis
- Research project benefits from experimentation
- Default values can remain, but flexibility is explicitly supported
- No single reward structure is known to be "correct"

**Consequences**:
- Reward constants move to TrainingConfig
- Experiments can compare different reward structures
- Trained agents are explicitly shaped by their config

**Technical Debt**: None

**Source**: Technical review finding RL-01

---

### Decision D015: No Hidden-Information Leakage in RL

**Date**: 2026-01-19
**Decision**: RL agents must not observe hidden information (opponent hand, deck order, etc.).

**Context**:
Technical review finding RL-03 identified potential for observation space to leak hidden game state to agents.

**Options Considered**:

| Option | Pros | Cons |
|--------|------|------|
| **A: Verify encoding is correct** | Certainty gained | Requires audit |
| **B: Implement partial observability** | Training validity | May reduce performance |

**Decision**: No leakage allowed — full partial observability required

**Rationale**:
- Training validity > short-term performance
- Agents that rely on hidden info do not transfer to real play
- This is a correctness requirement, not a preference

**Consequences**:
- Observation encoding MUST be audited
- Any trained agents that relied on leaked info become INVALID
- RL training is FROZEN until audit is complete
- `_encode_observation()` must only expose:
  - Agent's own hand
  - Public board state (both players' boards)
  - Visible opponent info (health, PO, card counts)
  - Turn and phase information

**Invalidation Notice**:
All previously trained agents are NON-AUTHORITATIVE until observation audit confirms no leakage. Win rate baselines established before this decision may not reflect valid gameplay.

**Audit Completion (2026-01-19)**:
Observation encoding audit completed. **NO LEAKAGE DETECTED.**

Observation includes:
- Player stats: health, PO, board count, hand size, turn ✅
- Player's own hand ✅ (valid - player sees own hand)
- Player's board ✅ (public)
- Opponent's board ✅ (public)
- Market cards ✅ (public)

NOT included (correctly hidden):
- Opponent's hand ✅
- Opponent's deck ✅
- Player's deck ✅
- Deck order/composition ✅

**STATUS: AUDIT PASSED - RL training unblocked**

**Technical Debt**: None (requirement)

**Source**: Technical review finding RL-03

---

### Decision D016: Create agent-architecture.md

**Date**: 2026-01-19
**Decision**: Create the missing `docs/agents/agent-architecture.md` file per workflow specification.

**Context**:
Technical review finding D-02 identified that the global CLAUDE.md workflow specifies `docs/agents/agent-architecture.md` as a Phase 4 output, but this file does not exist.

**Options Considered**:

| Option | Pros | Cons |
|--------|------|------|
| **A: Create the file** | Workflow compliance | Documentation work |
| **B: Update global workflow** | No new file needed | Workflow deviation |
| **C: Document deviation** | Explicit exception | Workflow incomplete |

**Decision**: Option A — Create the file

**Rationale**:
- Workflow spec is authoritative; implementation conforms
- Architecture information exists but is scattered
- Consolidation improves navigability

**Consequences**:
- File will be created consolidating:
  - Agent routing architecture
  - Responsibility boundaries
  - Escalation paths
  - Governance notes
- Content extracted from AGENTS.md, friction-map.md, expanded-inventory.md

**Technical Debt**: None

**Source**: Technical review finding D-02

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

**Status**: ✅ RESOLVED by D011 (Ability Parsing Strict Mode)

**Question**: When bonus_text doesn't match any pattern, should the system fail loudly or log and continue?

**Resolution**: D011 establishes strict mode — unmatched patterns raise errors when strict mode is enabled.

**Final Answer**: Unknown card text is invalid, not ignorable. Strict mode converts ambiguity into explicit failure. Missing patterns are no longer silently tolerated.

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

### OQ005: Hardcoded Approximations in Ability Effects

**Status**: ✅ RESOLVED

**Context**: Technical review found two hardcoded approximations in abilities.py:

1. **R-01 (Deck Reveal ATK)**: ✅ RESOLVED - Implemented actual deck peek in PR #27
   - Original: `avg_atk = 3` approximation
   - Solution: Added `game_state` parameter to `resolve_bonus_text_effects()`, uses actual `peek_current_deck()` to get top card ATK

2. **R-02 (Women Family Bonus)**: ✅ RESOLVED - Added gender attribute in PR #28
   - Original: `women_count = fam_count // 2 + 1` approximation
   - Solution: Added `Gender` enum to card models, repository parses gender from JSON, abilities.py counts actual female cards

**Resolution**: Human chose Option B for both - implement exact computation.

**Note**: R-02 requires gender data to be populated in card JSON files for full functionality. Cards without gender data default to UNKNOWN.

---

### OQ006: Dragon PO Spending Auto-Maximize

**Status**: ✅ RESOLVED - Human chose Option B (PR #29)

**Context**: Technical review finding R-03 notes that Dragon conditional abilities auto-maximize PO spending rather than allowing explicit player choice.

**Resolution**: Implemented explicit PO spending:
- `resolve_conditional_abilities(player, po_to_spend)` requires explicit PO
- `calculate_damage(attacker, defender, dragon_po_spend)` - new parameter
- `resolve_combat(state, dragon_po_choices)` - dict mapping player_id to PO spend
- If no PO specified, Dragon abilities do NOT activate

---

### OQ007: Class Scaling - Highest Wins vs Cumulative

**Status**: ✅ RESOLVED - Human chose Highest-Wins (PR #29)

**Context**: Technical review findings R-04 and R-05 note inconsistency in scaling behavior:
- **Class abilities**: Only highest threshold applies (R-04)
- **Dragon conditionals**: Previously cumulative effects (R-03)
- **Lapin thresholds**: Code comment showed interpretive uncertainty (R-05)

**Resolution**: Unified to highest-wins for all scaling:
- Dragon conditional abilities now use highest-wins instead of cumulative
- Only the ability at the specified PO tier activates
- Lower tier abilities do NOT stack
- Example: Spending 2 PO activates only 2 PO effect, not 1+2 PO effects

---

### OQ008: Ninja Check TODO

**Status**: ✅ RESOLVED - Human chose Option A (PR #29)

**Context**: Technical review finding R-06 identified a TODO for ninja selection check.

**Resolution**: Implemented ninja selection tracking:
- Added `ninja_selected: bool` field to `PlayerState` (default False)
- Weapon ATK bonus from "si ninja choisi" now requires `ninja_selected=True`
- Bonus no longer applies unconditionally
- Must be set during draft phase when player selects a Ninja card

---

## Part 3: Technical Debt Register

### Technical Debt Review (2026-01-19)

**Reclassification Summary:**
- TD001 and TD002 are reclassified as **intentional system limitations**, not debt.
- TD004 and TD010 are **operational constraints** handled by process or platform choice.
- TD003 and TD006 remain **optional improvements** to be revisited only if escalation volume or interpretability needs justify the cost.
- **No technical debt item blocks current execution.**

### Resolved Items

| ID | Description | Status | Resolution |
|----|-------------|--------|------------|
| TD005 | Silent ability parsing failure | ✅ RESOLVED | Strict mode implemented per D011 |
| TD007 | Deck reveal ATK approximation | ✅ RESOLVED | Fixed via actual deck peek in PR #27 |
| TD008 | Women family bonus approximation | ✅ RESOLVED | Fixed via gender attribute in PR #28 |
| TD009 | Ninja check not implemented | ✅ RESOLVED | Fixed via ninja_selected field in PR #29 |
| TD011 | Dual RNG sources | ✅ RESOLVED | Fixed via Shuffler protocol in PR #26 |
| TD012 | MCTS no default timeout | ✅ RESOLVED | Fixed via 5s default in PR #26 |
| TD013 | Self-play callback stub | ✅ RESOLVED | Fixed via ModelOpponentPlayer in PR #26 |

### Permanent System Limitations (Not Debt)

| ID | Description | Classification | Rationale |
|----|-------------|----------------|-----------|
| TD001 | Game mechanics gap | 🔒 SYSTEM LIMITATION | Intentional by Analytical Mandate - Layer 2/3 authority separation |
| TD002 | Balance analysis interpretation | 🔒 DESIGNED WORKFLOW | Agents provide metrics (Layer 1), humans interpret (Layer 2) |

### Operational Constraints (Not Debt)

| ID | Description | Classification | Handling |
|----|-------------|----------------|----------|
| TD004 | abilities.py change sensitivity | 📋 PROCESS NOTE | Use detailed commit messages; human discipline |
| TD010 | Windows parallelism limitation | 💻 PLATFORM CONSTRAINT | Accept or use Linux for RL training |

### Optional Improvements (True Debt - Deferred)

| ID | Description | Priority | Revisit Trigger |
|----|-------------|----------|-----------------|
| TD003 | No ML diagnosis step | LOW | N ML escalations/week with trivial root cause |
| TD006 | No RL behavior validation | LOW | When agent behavior becomes a design input |

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
11. **ABILITY PARSING STRICT MODE** - Unmatched patterns must fail explicitly (see D011)
12. **LAPIN ASYMMETRY ACCEPTED** - Board expansion is intentional design identity (see D012)
13. **S-TEAM ASYMMETRY ACCEPTED** - Board limit bypass is intentional class identity (see D013)
14. **REWARD SHAPING IS CONFIGURABLE** - Playstyle is tunable, not hard-coded (see D014)
15. **NO HIDDEN-INFO LEAKAGE IN RL** - Partial observability required; AUDIT PASSED 2026-01-19 (see D015)
16. **RL TRAINING UNBLOCKED** - Observation audit confirmed no leakage; training can resume (see D015)
17. **RNG UNIFIED** - market.py now accepts optional Shuffler for reproducibility (S-01, PR #26)
18. **MCTS DEFAULT TIMEOUT** - 5 second timeout prevents DoS (S-04, PR #26)
19. **SELF-PLAY WORKS** - ModelOpponentPlayer + SelfPlayCallback properly copy model weights (RL-02, PR #26)
20. **OQ005 RESOLVED** - Both R-01 (deck reveal) and R-02 (women bonus) now use exact computation (PR #27, #28)
21. **OQ006-OQ008 RESOLVED** - All game mechanics decisions implemented (PR #29):
    - OQ006: Dragon abilities require explicit PO spending
    - OQ007: All scaling uses highest-wins (not cumulative)
    - OQ008: Ninja weapon bonus requires ninja_selected flag

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
