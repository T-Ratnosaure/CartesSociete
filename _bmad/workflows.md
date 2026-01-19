# BMAD Workflow Definitions - CartesSociete

**Version**: 1.0
**Last Updated**: 2026-01-19

---

## Workflow Overview

| Workflow | Trigger | Agents | Output |
|----------|---------|--------|--------|
| FULL_PLANNING | New feature, >2 files | yoni, clovis, qc | PRD, architecture, tasks |
| INTEGRATION | Cross-domain work | yoni, clovis | Integration spec |
| ML_DESIGN | RL/ML changes | yoni, alexios, dulcy | ML design, training config |
| BALANCE_REVIEW | Game balance work | yoni, alexios | Balance analysis |
| ADR | Infrastructure decisions | yoni, lamine | ADR document |
| SKIP | Simple changes | none | Direct execution |

---

## FULL_PLANNING_WORKFLOW

**Trigger**: New feature, >= 2 files impacted

### Stages

```
ANALYZE → SCOPE → ARCHITECT → DECOMPOSE
```

### Stage Details

#### 1. ANALYZE
- Understand the request
- Identify affected components
- List dependencies

#### 2. SCOPE
- Define boundaries
- Identify out-of-scope items
- Set acceptance criteria

#### 3. ARCHITECT
- Design component structure
- Define interfaces
- Plan data flow

#### 4. DECOMPOSE
- Break into tasks
- Assign to agents
- Define order/dependencies

### Artifacts

| Artifact | Template | Location |
|----------|----------|----------|
| PRD-lite | `_bmad/templates/prd-lite.md` | `docs/planning/prd-lite/` |
| Architecture | `_bmad/templates/architecture.md` | `docs/planning/architecture/` |
| Task Breakdown | `_bmad/templates/task-breakdown.yaml` | `docs/planning/task-breakdowns/` |

---

## INTEGRATION_WORKFLOW

**Trigger**: >= 2 domains touched

### Stages

```
ANALYZE → INTERFACE_MAPPING → CONTRACT_DEFINITION
```

### Stage Details

#### 1. ANALYZE
- Identify domains involved
- Map current boundaries
- Identify integration points

#### 2. INTERFACE_MAPPING
- Define data exchange formats
- Map function signatures
- Identify shared state

#### 3. CONTRACT_DEFINITION
- Define contracts between components
- Specify error handling
- Document assumptions

### Artifacts

| Artifact | Location |
|----------|----------|
| Integration Spec | `docs/planning/integration/` |

---

## ML_DESIGN_WORKFLOW

**Trigger**: RL/ML architecture or training changes

### Stages

```
PROBLEM_DEFINITION → ARCHITECTURE_REVIEW → TRAINING_PLAN
```

### Stage Details

#### 1. PROBLEM_DEFINITION
- Define learning objective
- Specify input/output spaces
- Identify constraints

#### 2. ARCHITECTURE_REVIEW
- Review model architecture
- Assess computational requirements
- Consider alternatives

#### 3. TRAINING_PLAN
- Define curriculum
- Set hyperparameters
- Plan evaluation

### Artifacts

| Artifact | Location |
|----------|----------|
| ML Design | `docs/planning/ml-design/` |
| Training Config | `configs/training/` |

### Agent Roles

- **alexios**: Architecture decisions, reward design
- **dulcy**: Pipeline implementation, training code
- **pierre-jean**: Hyperparameter advice, optimization

---

## BALANCE_REVIEW_WORKFLOW

**Trigger**: Card balance or game rule changes

### Stages

```
CURRENT_STATE → METRICS_ANALYSIS → CHANGE_PROPOSAL
```

### Stage Details

#### 1. CURRENT_STATE
- Document current card stats
- Note current win rates
- Identify reported issues

#### 2. METRICS_ANALYSIS
- Run simulations
- Compute balance metrics
- Compare to targets

#### 3. CHANGE_PROPOSAL
- Propose stat changes
- Predict impact
- Define validation tests

### Artifacts

| Artifact | Location |
|----------|----------|
| Balance Analysis | `docs/planning/balance/` |

---

## ADR_WORKFLOW

**Trigger**: Infrastructure or significant technical decisions

### Stages

```
CONTEXT → OPTIONS → DECISION → CONSEQUENCES
```

### Stage Details

#### 1. CONTEXT
- Describe the situation
- Explain why a decision is needed
- List stakeholders

#### 2. OPTIONS
- List all viable options
- Pros/cons for each
- Estimate effort

#### 3. DECISION
- State the chosen option
- Justify the choice
- Note rejections with reasons

#### 4. CONSEQUENCES
- Positive outcomes
- Negative outcomes
- Risks and mitigations

### Artifacts

| Artifact | Location |
|----------|----------|
| ADR | `docs/adr/NNNN-title.md` |

---

## SKIP_WORKFLOW

**Trigger**: Simple, low-risk changes

### Criteria
- Single file change
- No cross-domain impact
- No ML/RL changes
- Well-understood pattern

### Behavior
- Direct execution
- Standard git workflow
- Quality gates still apply

---

## Workflow Selection Matrix

| Request Type | Files | Domains | ML | Workflow |
|--------------|-------|---------|-----|----------|
| New feature | Any | 1 | No | FULL_PLANNING |
| New feature | Any | 1 | Yes | ML_DESIGN |
| Bug fix | 1 | 1 | No | SKIP |
| Bug fix | 2+ | 1 | No | FULL_PLANNING |
| Refactor | 2+ | 1 | No | FULL_PLANNING |
| Refactor | Any | 2+ | No | INTEGRATION |
| Balance change | Any | 1 | Yes | BALANCE_REVIEW |
| CI/CD change | Any | 1 | No | ADR |
| Config change | 1 | 1 | No | SKIP or ADR |

---

## Parallel Execution

Workflows can execute in parallel when independent:

```
User: "Add new card family and train RL agent on it"

Detected:
├── new_feature: true (new card family)
├── ml_impact: true (RL training)
└── file_impact: 5+

Parallel Workflows:
├── FULL_PLANNING (card family) → architecture.md
└── ML_DESIGN (RL training) → ml-design.md

Sequential After:
└── INTEGRATION (connect card family to RL) → integration-spec.md
```

---

*Reference this document when Yoni selects workflows.*
