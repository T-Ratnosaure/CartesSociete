# CartesSociete Agent Ecosystem - Baseline v1.0

**Status**: FROZEN
**Freeze Date**: 2026-01-19
**Authority**: larai (Human Operator)
**Governance Level**: BINDING

---

## Step 1: Baseline Declaration

### Frozen Documents

The following documents constitute Baseline v1.0. Their content as of 2026-01-19 is the authoritative specification.

| Document | Path | Hash Checkpoint | Purpose |
|----------|------|-----------------|---------|
| AGENTS.md | `docs/agents/AGENTS.md` | v2.0 | Governance master |
| Project Context | `docs/project-context.md` | v1.0 | Domain bible |
| Expanded Inventory | `docs/agents/expanded-inventory.md` | v1.0 | Cognitive profiles |
| Friction Map | `docs/agents/friction-map.md` | v1.0 | Friction analysis |
| Simulations | `docs/agents/simulations.md` | v1.0 | Impact analysis |
| Decisions | `docs/agents/decisions.md` | v1.0 | Decision log |
| Yoni Perspective | `docs/agents/yoni-perspective.md` | v1.0 | Builder view |
| Wealon Perspective | `docs/agents/wealon-perspective.md` | v1.0 | Auditor view |
| Baseline Declaration | `docs/agents/baseline-v1.0.md` | v1.0 | This document |

### Frozen Assumptions

These assumptions are locked and cannot be changed without a new binding decision.

| ID | Assumption | Locked Value |
|----|------------|--------------|
| A1 | Agents understand game rules | **FALSE** |
| A2 | System can autonomously balance cards | **FALSE** |
| A3 | Human escalation is optional | **FALSE** - Mandatory |
| A4 | Financial agents are viable for game domain | **FALSE** - Rejected |
| A5 | Quality-Control can catch game logic errors | **FALSE** |
| A6 | System scope includes game design | **FALSE** - Excluded |
| A7 | Balance analysis is agent-automatable | **FALSE** |

### Non-Negotiable Scope Boundaries

These boundaries define what the system IS and IS NOT. They cannot be relaxed.

```
SYSTEM IS:
├── Software development support
├── Code quality enforcement
├── ML implementation support
├── CI/CD management
└── Documentation maintenance

SYSTEM IS NOT:
├── Game design authority
├── Balance decision maker
├── Game rule interpreter
├── Card design assistant
└── Autonomous game analyst
```

### Mandatory Agent Gates

These gates are permanent. They cannot be removed or bypassed.

| Gate | Trigger | Agent | Action |
|------|---------|-------|--------|
| AG-01 | Start of every task | yoni-orchestrator | Entry coordination |
| AG-02 | End of every task | wealon-regulatory-auditor | Exit audit |

### Mandatory Human Checkpoints

These checkpoints are permanent. They cannot be removed or delegated.

| Checkpoint | Trigger | Human Action Required |
|------------|---------|----------------------|
| HC-01 | Any change to `combat.py` | Review and approve |
| HC-02 | Any change to `abilities.py` | Review and approve |
| HC-03 | Any change to `state.py` | Review and approve |
| HC-04 | Game rule question from any agent | Answer or reject |
| HC-05 | Balance interpretation request | Provide human judgment |

---

## Step 2: Breaking Change Definitions

A **breaking change** is any change that violates Baseline v1.0 assumptions or boundaries. Breaking changes require:

1. New binding decision (documented in decisions.md)
2. New Wealon audit (full audit, not incremental)
3. Renegotiation of Human Operating Contract
4. Version increment to v2.0

### Category A: Scope Expansion (BREAKING)

Any attempt to expand system scope into game design territory.

| Change | Why Breaking |
|--------|--------------|
| Add game-mechanic-expert agent | Violates A1, expands scope |
| Add balance-analyst agent | Violates A2, A7, expands scope |
| Enable autonomous balance recommendations | Violates A2, A7 |
| Allow agents to propose card changes | Violates "SYSTEM IS NOT" |
| Remove human checkpoint for game files | Violates HC-01 through HC-05 |

### Category B: Assumption Reversal (BREAKING)

Any change that reverses a frozen assumption.

| Change | Why Breaking |
|--------|--------------|
| Claim an agent understands game rules | Reverses A1 |
| Integrate financial agents for balance | Reverses A4 |
| Make human escalation optional | Reverses A3 |
| Remove mandatory human checkpoints | Violates Non-Negotiable Boundaries |

### Category C: Authority Violation (BREAKING)

Any change that grants agents authority beyond their competence.

| Change | Why Breaking |
|--------|--------------|
| Alexios makes balance decisions | Authority exceeds competence |
| Any agent interprets game intent | Not within any agent's scope |
| Automated merge of game-rule files | Bypasses human checkpoint |

---

## Step 3: Allowed Change Paths

### Legal Evolution (Within v1.0)

Changes that can be made without breaking the baseline:

| Change Type | Conditions | Process |
|-------------|------------|---------|
| Bug fix in agent workflow | Does not change scope | Normal PR |
| Documentation clarification | Does not change meaning | Normal PR |
| New conditional agent activation | Already listed as "inactive" | Update AGENTS.md |
| Hyperparameter tuning for ML | No architecture change | Dulcy → Pierre-Jean |
| New tests for existing behavior | Tests match documented behavior | Lamine review |
| Tooling updates (CI/CD) | No scope change | Lamine review |
| Performance optimization | Same behavior, faster | Clovis review |

### Legal Agent Changes (Within v1.0)

| Agent Change | Allowed? | Conditions |
|--------------|----------|------------|
| Activate Wealon | YES | At trigger points only |
| Activate Maxime | YES | When external exposure occurs |
| Add new ML agent | NO | Would require v2.0 |
| Remove primary agent | NO | Would require v2.0 |
| Change agent instructions | MAYBE | If scope unchanged |

### Illegal Changes (Require v2.0)

These changes are NOT legal under v1.0 governance:

```
ILLEGAL WITHOUT v2.0:
├── Any new agent persona
├── Any scope expansion into game design
├── Any removal of human checkpoints
├── Any claim that agents understand game rules
├── Any financial agent integration
├── Any balance automation beyond data collection
├── Any reduction in human authority
└── Any removal of mandatory documentation
```

---

## Step 4: Review Triggers

### Automatic Re-Audit Triggers

Wealon must be activated (full audit) when:

| Trigger | Audit Scope |
|---------|-------------|
| Pre-release of any version | Full system |
| External code exposure | Security + governance |
| Authentication/security changes | Security focus |
| Monthly checkpoint | Technical debt + drift |
| Breaking change proposal | Full system + impact |

### Scope Reconsideration Triggers

The baseline assumptions must be reconsidered when:

| Trigger | Required Action |
|---------|-----------------|
| Human escalation exceeds 5 game-rule questions/week | Evaluate game-mechanic-expert |
| Game rules become too complex for documentation | Evaluate embedded rules |
| Project transitions to production | Full governance review |
| New team members join | Onboarding + scope review |

### System Freeze Triggers

All changes must halt pending governance review when:

| Trigger | Required Action |
|---------|-----------------|
| Baseline document contradiction discovered | Freeze until resolved |
| Human Operating Contract violated | Freeze until remediated |
| Agent acts outside documented scope | Freeze until investigated |
| Breaking change merged without approval | Revert + freeze |

---

## Step 5: Closure Statement

### Declaration

As of 2026-01-19, the CartesSociete Agent Ecosystem design phase is **CLOSED**.

The system defined in Baseline v1.0 is the authoritative specification for all agent operations in this project. All further changes are governed by this document, not by exploratory design.

### What This Means

1. **No new design work** without a v2.0 proposal
2. **No scope creep** into game design territory
3. **No assumption reversal** without explicit governance process
4. **No human checkpoint removal** under any circumstances
5. **All changes must be classifiable** as legal within v1.0 or flagged as breaking

### System Truth (Locked)

> Agents in this ecosystem are software development support tools.
> They cannot reason about game design, balance, or player experience.
> All game-domain questions require human judgment.
> This is not a limitation to be fixed. It is the system's identity.

### Human Authority (Affirmed)

The human operator (larai) retains:
- Final authority over all game design decisions
- Veto power over any agent recommendation
- Ability to invoke breaking change process
- Responsibility for all checkpoints

### Governance Chain

```
Baseline v1.0 (this document)
    ↓
AGENTS.md (governance master)
    ↓
Supporting Documents (context, friction, decisions)
    ↓
Agent Operations (bounded by above)
    ↓
Human Checkpoints (mandatory gates)
```

### Effective Immediately

This document is effective upon creation. All agent operations must comply with Baseline v1.0 starting now.

---

## Appendix: Version History

| Version | Date | Change | Authority |
|---------|------|--------|-----------|
| v1.0 | 2026-01-19 | Initial baseline freeze | larai |

---

## Appendix: Human Acknowledgment

By continuing to use this agent ecosystem, the human operator acknowledges:

- [ ] I understand agents cannot reason about game design
- [ ] I accept responsibility for all game-rule file changes
- [ ] I will answer escalated game questions or explicitly defer them
- [ ] I will not blame agents for game design failures
- [ ] I will follow the breaking change process for scope expansion

**Signature**: ____________________
**Date**: ____________________

---

*This document closes the BMAD+AGENTIC design phase for CartesSociete.*
*The system is now operational under governed change control.*
*Design work is complete. Execution begins.*

*Baseline v1.0 - Frozen 2026-01-19*
