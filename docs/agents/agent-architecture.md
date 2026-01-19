# Agent Architecture - CartesSociete

**Document Version**: 1.0
**Created**: 2026-01-19
**Phase**: BMAD Solutioning - Phase 4

---

## Overview

This document defines how agents interact within the CartesSociete project, establishing clear orchestration flows, authority boundaries, and escalation paths.

---

## Interaction Architecture

```
                         USER REQUEST
                              |
                              v
                   +-------------------+
                   | yoni-orchestrator |  <-- Entry point for ALL requests
                   +-------------------+
                              |
            +-----------------+------------------+
            |                 |                  |
            v                 v                  v
    +-------------+   +-------------+    +-------------+
    | Development |   |   ML/RL     |    | Exploration |
    |   Track     |   |   Track     |    |   Track     |
    +-------------+   +-------------+    +-------------+
            |                 |                  |
            v                 v                  v
    +-----------+     +-----------+      +-----------+
    | clovis    |     | alexios   |      | Explore   |
    | quality   |     | dulcy     |      | Plan      |
    | lamine    |     | pierre-j  |      | general   |
    +-----------+     | ml-prod   |      +-----------+
                      +-----------+
```

---

## Orchestration Flow

### Primary Flow: Yoni-First

```
1. User Request arrives
2. yoni-orchestrator receives request
3. Yoni analyzes and creates execution plan
4. Yoni routes to appropriate track(s)
5. Track agents execute tasks
6. Results flow back through Yoni
7. Yoni synthesizes and responds
```

**Rule**: NEVER bypass Yoni for user requests.

---

## Track Definitions

### Development Track

**Purpose**: Code quality, git workflow, CI/CD, testing

**Agents**:
| Agent | Role | Trigger |
|-------|------|---------|
| it-core-clovis | Git workflow, PR review, code optimization | Pre-commit, PR creation |
| quality-control-enforcer | Implementation validation | Post-feature completion |
| lamine-deployment-expert | CI/CD, test infrastructure | Pipeline changes |

**Flow**:
```
Feature Implementation:
  [Code Written] --> quality-control-enforcer --> [Validation]
                                                      |
                                                      v
  [Commit Ready] --> it-core-clovis --> [PR Created]
                                              |
                                              v
  [CI/CD Issue] --> lamine-deployment-expert --> [Fixed]
```

### ML/RL Track

**Purpose**: Reinforcement learning, model training, balance analysis

**Agents**:
| Agent | Role | Trigger |
|-------|------|---------|
| alexios-ml-predictor | RL architecture, balance prediction | Design decisions |
| dulcy-ml-engineer | Training pipelines, gymnasium integration | Implementation |
| pierre-jean-ml-advisor | Hyperparameter tuning, training optimization | Performance issues |
| ml-production-engineer | Research-to-production cleanup | Code productionization |

**Flow**:
```
RL Development:
  [Design Question] --> alexios --> [Architecture Decision]
                                           |
                                           v
  [Implementation] --> dulcy --> [Pipeline Built]
                                      |
                                      v
  [Training Issues] --> pierre-jean --> [Optimized]
                                             |
                                             v
  [Production Ready] --> ml-production-engineer --> [Cleaned]
```

### Exploration Track

**Purpose**: Codebase understanding, planning, research

**Agents**:
| Agent | Role | Trigger |
|-------|------|---------|
| Explore | Fast codebase search, file patterns | "Where is...", "Find..." |
| Plan | Implementation strategy | Complex feature planning |
| general-purpose | Multi-step research | Complex queries |

**Flow**:
```
Research Task:
  [Question] --> Explore (quick) --> [Located]
       |
       +--> general-purpose (complex) --> [Researched]

Planning Task:
  [Feature Request] --> Plan --> [Strategy Defined]
```

---

## Authority Boundaries

### Decision Authority

| Decision Type | Authority | Escalation |
|---------------|-----------|------------|
| Agent routing | yoni-orchestrator | N/A |
| Git workflow | it-core-clovis | User approval for force actions |
| Code quality standards | quality-control-enforcer | User for overrides |
| ML architecture | alexios | User for major design choices |
| CI/CD configuration | lamine-deployment | User for breaking changes |
| Production readiness | quality-control-enforcer | User for deployment |

### Execution Authority

| Agent | Can Execute | Cannot Execute |
|-------|-------------|----------------|
| yoni-orchestrator | Task routing, plan creation | Direct code changes |
| it-core-clovis | Git commands, PR creation | Force push without approval |
| quality-control-enforcer | Code review, issue identification | Code fixes (flags only) |
| lamine-deployment | Pipeline configuration | Production deployments |
| alexios | ML design recommendations | Autonomous training runs |
| dulcy | Training code implementation | Long-running training |

---

## Conflict Resolution

### Agent Disagreement Protocol

1. **Identify conflict** - When two agents provide contradictory guidance
2. **Document positions** - Capture each agent's recommendation and rationale
3. **Escalate to user** - Present options with tradeoffs
4. **User decides** - Final authority rests with user

### Domain Boundary Conflicts

| Conflict | Resolution |
|----------|------------|
| Clovis vs Quality-Control on code | Clovis for git/format, QC for logic |
| Alexios vs Dulcy on ML | Alexios for design, Dulcy for implementation |
| Yoni routing disagreement | Yoni has final routing authority |

---

## Responsibility Matrix (RACI)

| Activity | Yoni | Clovis | QC | Lamine | Alexios | Dulcy |
|----------|------|--------|----|---------|---------| ------|
| Request Intake | **R** | - | - | - | - | - |
| Task Routing | **R** | - | - | - | - | - |
| Git Workflow | A | **R** | - | - | - | - |
| Code Review | A | **R** | C | - | - | - |
| Feature Validation | A | C | **R** | - | - | - |
| CI/CD Setup | A | I | C | **R** | - | - |
| RL Design | A | - | - | - | **R** | C |
| Training Pipeline | A | - | - | - | C | **R** |

**Legend**: R=Responsible, A=Accountable, C=Consulted, I=Informed

---

## Escalation Paths

### Technical Escalation
```
Issue Detected --> Owning Agent --> Yoni (if cross-cutting) --> User (if blocking)
```

### Quality Escalation
```
Code Issue --> quality-control-enforcer --> it-core-clovis (if git-related)
                                        --> User (if policy violation)
```

### ML Escalation
```
Training Issue --> dulcy --> pierre-jean (if tuning) --> alexios (if architecture)
                                                     --> User (if fundamental)
```

---

## Single Points of Failure

| SPOF | Risk | Mitigation |
|------|------|------------|
| yoni-orchestrator | All routing blocked | Can use agents directly in emergency |
| it-core-clovis | No PR review | User can review manually |
| alexios | No ML guidance | Pierre-Jean can provide basic guidance |

---

## Governance Notes

1. **No Financial Agents**: Explicitly rejected agents must never be invoked
2. **Yoni-First**: All user requests route through Yoni unless:
   - Emergency requiring direct agent access
   - Simple exploration tasks (use Explore directly)
3. **Track Isolation**: Agents should not cross track boundaries without Yoni coordination
4. **User Authority**: Users can override any agent decision
5. **Audit Trail**: Quality-control-enforcer provides final validation before PRs

---

*This architecture informs the governance policies in Phase 5.*
