# BMAD Planning Templates

**Version**: 1.0
**Last Updated**: 2026-01-19

---

## Overview

This document describes the planning artifact templates used by the BMAD+AGENTIC framework in CartesSociete.

---

## Template Locations

| Template | Source | Output Directory |
|----------|--------|------------------|
| PRD-lite | `_bmad/templates/prd-lite.md` | `docs/planning/prd-lite/` |
| Architecture | `_bmad/templates/architecture.md` | `docs/planning/architecture/` |
| ML Design | `_bmad/templates/ml-design.md` | `docs/planning/ml-design/` |
| Balance Analysis | `_bmad/templates/balance-analysis.md` | `docs/planning/balance/` |
| Task Breakdown | `_bmad/templates/task-breakdown.yaml` | `docs/planning/task-breakdowns/` |
| Integration Spec | `_bmad/templates/integration-spec.md` | `docs/planning/integration/` |

---

## Naming Convention

All planning artifacts follow this naming pattern:

```
{YYYY-MM-DD}-{feature-slug}.{ext}
```

Examples:
- `2026-01-19-new-card-family.md`
- `2026-01-19-ppo-training.yaml`
- `2026-01-19-balance-cyborg-family.md`

---

## Directory Structure

```
docs/planning/
├── TEMPLATES.md          # This file
├── prd-lite/            # Product requirement documents
├── architecture/        # Technical architecture docs
├── ml-design/           # ML/RL design documents
├── balance/             # Card balance analysis
├── task-breakdowns/     # Task decomposition YAMLs
└── integration/         # Cross-domain integration specs

docs/adr/
├── 0001-{title}.md      # Architecture Decision Records
├── 0002-{title}.md
└── ...
```

---

## When to Create Each Artifact

| Workflow | Artifacts Created |
|----------|-------------------|
| FULL_PLANNING | PRD-lite, Architecture, Task Breakdown |
| INTEGRATION | Integration Spec |
| ML_DESIGN | ML Design, (optional) Task Breakdown |
| BALANCE_REVIEW | Balance Analysis |
| ADR | ADR document |
| SKIP | None |

---

## Template Quick Reference

### PRD-lite
Use for defining WHAT needs to be built.
- Problem statement
- Goals and non-goals
- User stories
- Success metrics

### Architecture
Use for defining HOW it will be built.
- Component diagram
- Data flow
- Files impacted
- Testing strategy

### ML Design
Use for RL/ML specific designs.
- Input/output spaces
- Network architecture
- Training curriculum
- Reward shaping

### Balance Analysis
Use for game balance investigations.
- Current statistics
- Simulation results
- Change proposals
- Validation plan

### Task Breakdown
Use for decomposing work into agent tasks.
- Task list with dependencies
- Agent assignments
- Acceptance criteria
- Execution order

### ADR
Use for recording significant technical decisions.
- Context
- Options considered
- Decision and rationale
- Consequences

---

*Reference: `_bmad/workflows.md` for workflow details*
