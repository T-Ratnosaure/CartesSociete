# AGENTS.md - CartesSociete Agent Governance

**Document Version**: 2.0 (BMAD+AGENTIC Deep Design)
**Last Updated**: 2026-01-19
**Status**: FROZEN (Baseline v1.0)
**Governance**: [baseline-v1.0.md](baseline-v1.0.md)

---

## GOVERNANCE NOTICE

This document is part of **Baseline v1.0** and is now frozen.

- All changes must comply with [baseline-v1.0.md](baseline-v1.0.md)
- Breaking changes require v2.0 governance process
- Design phase is CLOSED - system is operational

---

## Quick Reference

| Category | Agents | Count |
|----------|--------|-------|
| **Primary** | yoni, clovis, quality-control, lamine | 4 |
| **Conditional** | alexios, dulcy, pierre-jean, ml-production, data-sophie | 5 |
| **System** | Explore, Plan, general-purpose, claude-code-guide | 4 |
| **Available but Inactive** | cybersecurity-maxime, wealon | 2 |
| **Explicitly Rejected** | Financial domain agents (14) | 14 |

---

## CRITICAL: Read Before Using Agents

### Known Limitations (From Auditor Perspective)

1. **No agent understands game rules** - Game design questions require human input
2. **Balance analysis is partial** - Agents provide metrics, humans interpret
3. **Quality review has blind spots** - Neither QC nor Clovis catches game logic errors
4. **abilities.py is highest-risk** - 800+ lines of regex parsing French text

See: [Wealon Perspective](wealon-perspective.md) for full audit

---

## 1. Primary Agents

### yoni-orchestrator
- **Role**: Master task orchestrator
- **Trigger**: EVERY user request (with exceptions below)
- **Exceptions**: Explore can be called directly for simple file lookups
- **See**: [Yoni Perspective](yoni-perspective.md) for routing analysis

### it-core-clovis
- **Role**: Code quality guardian (process)
- **Trigger**: Pre-commit, PR creation, code review
- **Blind Spots**: Does NOT understand game logic
- **See**: [Expanded Inventory](expanded-inventory.md) for cognitive profile

### quality-control-enforcer
- **Role**: Implementation validator (substance)
- **Trigger**: After feature completion, before PR merge
- **Blind Spots**: Does NOT understand game rules
- **Order**: Runs BEFORE Clovis (substance before process)

### lamine-deployment-expert
- **Role**: CI/CD and TDD specialist
- **Trigger**: Pipeline changes, test infrastructure, CI failures
- **TDD Required For**: Combat, abilities, state, action legality

---

## 2. Conditional Agents

### ML Agent Escalation Protocol

**When facing ML/RL issues, escalate in this order:**

```
Step 1: dulcy-ml-engineer
        ├── If implementation bug → Fix and done
        └── If code correct → Step 2

Step 2: pierre-jean-ml-advisor
        ├── If hyperparameter issue → Tune and done
        └── If hyperparameters exhausted → Step 3

Step 3: alexios-ml-predictor
        └── Redesign architecture
```

### alexios-ml-predictor
- **Condition**: Architecture design, model selection, reward shaping
- **Constraint**: Translate financial concepts to game domain
- **Blind Spot**: Doesn't understand game rules (only metrics)

### dulcy-ml-engineer
- **Condition**: Implementation, training loops, PyTorch code
- **Constraint**: None
- **Entry Point**: First stop for ML issues

### pierre-jean-ml-advisor
- **Condition**: Hyperparameter tuning, curriculum learning
- **Constraint**: None
- **Entry Point**: After Dulcy confirms code is correct

### ml-production-engineer
- **Condition**: Research-to-production transitions
- **Constraint**: None
- **Usage**: Cleanup after experimental code works

### data-engineer-sophie
- **Condition**: Complex data pipeline work
- **Current Need**: LOW (card data is static JSON)
- **Activate If**: Card data validation becomes critical

---

## 3. System Agents

### Explore
- **Usage**: Direct call OK for simple file/code lookups
- **When to use Yoni instead**: Complex multi-step queries

### Plan
- **Usage**: Complex feature planning, architectural decisions
- **When to use**: Multi-file changes, unclear requirements

### general-purpose
- **Usage**: When specialized agents don't fit
- **Preference**: Use specialized agents first

### claude-code-guide
- **Usage**: Questions about Claude Code tooling
- **Not for**: Project-specific questions

---

## 4. Available but Inactive

### cybersecurity-expert-maxime
- **Status**: INACTIVE
- **Activate When**: Project becomes externally exposed
- **Rationale**: No production deployment, no security surface

### wealon-regulatory-auditor
- **Status**: INACTIVE (triggered activation only)
- **Activation Triggers**:
  - Pre-release checkpoint
  - External code exposure
  - Authentication/security changes
  - Monthly technical debt inventory
- **Rationale**: Overkill for daily research work

---

## 5. Explicitly Rejected Agents

**DO NOT USE** - Wrong domain for card game project:

| Agent | Domain | Rejection Reason |
|-------|--------|-----------------|
| research-remy-stocks | Stock analysis | Financial markets ≠ card games |
| iacopo-macro-futures-analyst | Macroeconomics | Economic indicators irrelevant |
| nicolas-risk-manager | Financial risk | VaR ≠ game balance |
| victor-pnl-manager | PnL attribution | No profit/loss concept |
| pnl-validator | PnL automation | Not applicable |
| trading-execution-engine | Trade execution | No trading |
| backtester-agent | Trading backtesting | Could adapt, but not needed |
| cost-optimizer-lucas | Cost optimization | Minimal cost concerns |
| french-tax-optimizer | Taxation | Not applicable |
| helena-execution-manager | Trade execution | Not applicable |
| portfolio-manager-jean-yves | Portfolio management | Deck ≠ portfolio |
| legal-team-lead | Legal coordination | No legal requirements |
| legal-compliance-reviewer | Financial compliance | Not applicable |
| antoine-nlp-expert | NLP | Structured data, not text |

**Governance Rule**: Invoking rejected agents is NEVER permitted. Domain mismatch is fundamental.

---

## 6. Usage Rules

### Rule 1: Yoni-First (With Exceptions)
```
For user requests:
  1. Simple file lookup → Explore directly
  2. Everything else → Yoni first
```

### Rule 2: Development Workflow
```
After writing code:
  1. Quality-Control validates substance
  2. Clovis reviews process
  3. Lamine handles CI issues
```

### Rule 3: ML Workflow
```
For RL issues:
  1. Dulcy (implementation)
  2. Pierre-Jean (hyperparameters)
  3. Alexios (architecture)
```

### Rule 4: Handoff Contracts Required For
```
- New model architecture
- New game mechanic
- Changes to combat formula
- Changes to ability parsing

Not Required For:
- Bug fixes
- Refactoring
- Test additions
```

See: [Decisions Log](decisions.md) for full decision rationale

---

## 7. Known Friction Points

From [Friction Map](friction-map.md):

| Friction | Severity | Current Mitigation |
|----------|----------|-------------------|
| Game mechanics gap | CRITICAL | Documentation + human |
| Balance analysis gap | HIGH | Partial automation + human |
| ML agent overlap | HIGH | Escalation protocol |
| Alexios→Dulcy handoff | MEDIUM | Handoff contracts |
| Code quality overlap | MEDIUM | Sequential review order |

---

## 8. Compliance Requirements

| Requirement | Policy |
|-------------|--------|
| Financial agents | NEVER use |
| Game design questions | Escalate to human |
| Balance decisions | Human approval required |
| Wealon audits | Triggered activation only |
| Human approval | Required for agent changes |

---

## 9. Changelog

| Date | Change | Approved By |
|------|--------|-------------|
| 2026-01-19 | v1.0 - Initial shallow design | larai |
| 2026-01-19 | v2.0 - BMAD+AGENTIC deep design | larai |
| 2026-01-19 | v2.0 FROZEN - Baseline v1.0 governance | larai |

---

## 10. Supporting Documents (Deep Design)

### Governance
| Document | Purpose |
|----------|---------|
| [Baseline v1.0](baseline-v1.0.md) | **AUTHORITATIVE** - Change control, frozen assumptions |

### Core Documents
| Document | Purpose |
|----------|---------|
| [Project Context](../project-context.md) | Domain bible - game rules, architecture, assumptions |
| [Expanded Inventory](expanded-inventory.md) | Agent cognitive profiles with blind spots |
| [Friction Map](friction-map.md) | Overlaps, gaps, handoffs, conflicts |
| [Simulations](simulations.md) | Impact analysis of proposed changes |
| [Decisions](decisions.md) | Rationale, rejected alternatives, tech debt |

### Perspective Audits
| Document | Purpose |
|----------|---------|
| [Yoni Perspective](yoni-perspective.md) | Builder view - routing and workflows |
| [Wealon Perspective](wealon-perspective.md) | Auditor view - risks and gaps |

---

*This document governs all agent usage in CartesSociete.*
*Status: FROZEN under Baseline v1.0*
*Design phase: CLOSED*

*Generated by BMAD+AGENTIC Framework*
