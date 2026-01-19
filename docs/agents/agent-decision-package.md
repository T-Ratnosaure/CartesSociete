# Agent Decision Package - CartesSociete

**Document Version**: 1.0
**Created**: 2026-01-19
**Phase**: BMAD Governance - Phase 7 (FINAL)
**Status**: AWAITING HUMAN APPROVAL

---

## Executive Summary

This package presents the recommended agent ecosystem for CartesSociete, a card game design and simulation project. The ecosystem has been designed following BMAD methodology to be:

- **Minimal**: 13 active agents (4 primary, 5 conditional, 4 system)
- **Sufficient**: Covers game engine, RL/ML, quality, and CI/CD needs
- **Governed**: Clear rules for usage, addition, and removal
- **Evolvable**: Quarterly review process defined

---

## Recommended Agent Ecosystem

### Primary Agents (4)

| Agent | Purpose | Why Primary |
|-------|---------|-------------|
| **yoni-orchestrator** | Master coordinator | Entry point for all requests |
| **it-core-clovis** | Git/code quality | Essential for any development |
| **quality-control-enforcer** | Implementation validation | Catches shortcuts in game logic |
| **lamine-deployment-expert** | CI/CD & testing | Project has GitHub Actions CI |

### Conditional Agents (5)

| Agent | Purpose | Condition |
|-------|---------|-----------|
| **alexios-ml-predictor** | RL architecture, balance | RL/ML work only (adapt guidance) |
| **dulcy-ml-engineer** | Training pipelines | RL implementation only |
| **pierre-jean-ml-advisor** | Training optimization | Performance tuning only |
| **ml-production-engineer** | Research cleanup | Research-to-production only |
| **data-engineer-sophie** | Data pipelines | If complexity increases |

### System Agents (4)

| Agent | Purpose | Usage |
|-------|---------|-------|
| **Explore** | Codebase search | Daily exploration |
| **Plan** | Implementation strategy | Complex features |
| **general-purpose** | Multi-step research | When specialists don't fit |
| **claude-code-guide** | Tooling help | Meta questions |

### Explicitly Rejected (14)

All financial domain agents: research-remy-stocks, iacopo, nicolas, victor, pnl-validator, trading-engine, cost-optimizer, french-tax, helena, portfolio-jean-yves, legal-team-lead, legal-compliance, antoine-nlp-expert

**Reason**: CartesSociete is a game design project, not financial software.

---

## Key Architectural Decisions

### Decision 1: Yoni-First Pattern
All user requests route through yoni-orchestrator, which coordinates specialized agents.

### Decision 2: Three-Track Structure
- **Development Track**: clovis, quality-control, lamine
- **ML/RL Track**: alexios, dulcy, pierre-jean, ml-production
- **Exploration Track**: Explore, Plan, general-purpose

### Decision 3: Financial Domain Rejection
14 agents explicitly rejected as wrong domain. This is non-negotiable unless project scope fundamentally changes.

### Decision 4: Security Agents Inactive
cybersecurity-expert-maxime and wealon-regulatory-auditor available but inactive (not production software). Can activate if project goes external.

---

## Open Questions

### Question 1: Alexios Adaptation
Alexios is designed for financial ML. For game RL work:
- **Option A**: Use as-is, manually adapt recommendations (RECOMMENDED)
- **Option B**: Create game-specific ML agent guidance
- **Option C**: Don't use ML agents, rely on manual RL work

### Question 2: Balance Analysis Agent
No specialized game balance agent exists:
- **Option A**: Use alexios for statistical analysis, user provides game design context (RECOMMENDED)
- **Option B**: Don't use agents for balance, manual analysis only
- **Option C**: Create custom game-balance agent specification

### Question 3: Agent Tracking
Should we log agent invocations for optimization?
- **Option A**: No tracking initially, add if needed (RECOMMENDED)
- **Option B**: Implement basic tracking from start
- **Option C**: Full metrics system

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Alexios gives financial patterns | Medium | Low | User adapts recommendations |
| Agent overhead for simple tasks | Low | Low | Direct exploration allowed |
| RL training without validation | Medium | Medium | Manual monitoring, standard practices |
| Ecosystem becomes stale | Low | Medium | Quarterly reviews |

---

## Implementation

If approved, the following will be active:

```
docs/agents/
├── AGENTS.md                    # Main governance (active)
├── project-context-summary.md   # Project analysis
├── available-agents-inventory.md # Full agent list
├── agent-relevance-matrix.md    # Classification rationale
├── agent-architecture.md        # Interaction design
├── agent-evolution-plan.md      # Future planning
└── agent-decision-package.md    # This document
```

The CLAUDE.md will reference `docs/agents/AGENTS.md` for agent usage rules.

---

## Approval Checklist

Please review and check each item:

```
REQUIRED APPROVALS:

- [ ] Approve Primary Agents (yoni, clovis, quality-control, lamine)

- [ ] Approve Conditional Agents (alexios, dulcy, pierre-jean, ml-production, data-sophie)

- [ ] Approve System Agents (Explore, Plan, general-purpose, claude-code-guide)

- [ ] Approve Rejections (14 financial domain agents)

- [ ] Approve Yoni-First routing pattern

- [ ] Approve quarterly review process


OPTIONAL MODIFICATIONS:

- [ ] Modify Primary agent list: ____________________

- [ ] Modify Conditional agent list: ____________________

- [ ] Activate Inactive agent: ____________________

- [ ] Reconsider Rejected agent: ____________________


OPEN QUESTIONS (choose one for each):

Question 1 - Alexios Adaptation:
- [ ] Option A: Use as-is with manual adaptation (Recommended)
- [ ] Option B: Create game-specific guidance
- [ ] Option C: Don't use ML agents

Question 2 - Balance Analysis:
- [ ] Option A: Alexios + user context (Recommended)
- [ ] Option B: Manual analysis only
- [ ] Option C: Create custom agent spec

Question 3 - Agent Tracking:
- [ ] Option A: No tracking initially (Recommended)
- [ ] Option B: Basic tracking from start
- [ ] Option C: Full metrics system


FINAL DECISION:

- [ ] APPROVE as recommended
- [ ] APPROVE with modifications noted above
- [ ] DEFER decision (specify what additional information needed)
- [ ] REJECT (specify concerns)


Signature: ____________________
Date: ____________________
```

---

## Next Steps After Approval

1. Mark AGENTS.md as APPROVED (update status)
2. Update CLAUDE.md to reference AGENTS.md
3. Add changelog entry to AGENTS.md
4. Begin using agent ecosystem per governance rules
5. Schedule first quarterly review

---

## Supporting Documents

| Document | Purpose | Location |
|----------|---------|----------|
| Project Context | Project analysis | `project-context-summary.md` |
| Agent Inventory | Full agent list | `available-agents-inventory.md` |
| Relevance Matrix | Classification | `agent-relevance-matrix.md` |
| Architecture | Interaction design | `agent-architecture.md` |
| Evolution Plan | Future planning | `agent-evolution-plan.md` |

---

*This package requires human approval before the agent ecosystem becomes active.*

**DO NOT PROCEED beyond this point without explicit human approval.**
