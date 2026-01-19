# BMAD + AGENTIC Methodology Setup Guide

**Purpose**: Complete guide to replicate the BMAD+AGENTIC agent governance methodology on any new project.
**Source**: CartesSociete implementation (2026-01-19)
**Version**: 1.0

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [Directory Structure](#3-directory-structure)
4. [Phase 1: Project Context Intake](#4-phase-1-project-context-intake)
5. [Phase 2: Agent Inventory](#5-phase-2-agent-inventory)
6. [Phase 3: Agent Relevance & Selection](#6-phase-3-agent-relevance--selection)
7. [Phase 4: Expanded Agent Profiles](#7-phase-4-expanded-agent-profiles)
8. [Phase 5: Friction Mapping](#8-phase-5-friction-mapping)
9. [Phase 6: Impact Simulations](#9-phase-6-impact-simulations)
10. [Phase 7: Multi-Perspective Audits](#10-phase-7-multi-perspective-audits)
11. [Phase 8: Decisions & Memory](#11-phase-8-decisions--memory)
12. [Phase 9: BMAD Framework Configuration](#12-phase-9-bmad-framework-configuration)
13. [Phase 10: CLAUDE.md Integration](#13-phase-10-claudemd-integration)
14. [Phase 11: Baseline Freeze](#14-phase-11-baseline-freeze)
15. [Phase 12: Wealon Audit & Commit](#15-phase-12-wealon-audit--commit)
16. [File Templates](#16-file-templates)
17. [Checklist](#17-checklist)

---

## 1. Overview

### What is BMAD+AGENTIC?

BMAD+AGENTIC is a methodology for designing, governing, and operating an agent ecosystem within a software project. It ensures:

- **Structured agent selection** - Only relevant agents are integrated
- **Clear governance** - Rules for agent usage, activation, and rejection
- **Quality gates** - Mandatory entry (Yoni) and exit (Wealon) gates
- **Documented decisions** - Full audit trail of why the system is built this way
- **Frozen baselines** - Change control for governance documents

### Core Principles

1. **Yoni-First**: Every user request goes through the orchestrator
2. **Wealon-Last**: Every task ends with an audit
3. **BMAD Workflows**: Complex tasks trigger planning workflows
4. **Human Checkpoints**: Some decisions require human approval
5. **Governance > Cleverness**: Document everything, assume nothing

### Time Investment

- **Shallow implementation**: ~30 minutes (skeleton only, not recommended)
- **Proper implementation**: ~4-8 hours (full methodology)

---

## 2. Prerequisites

### Required Knowledge

- Understanding of the project domain
- Familiarity with available agents in your environment
- Authority to make governance decisions

### Required Tools

- Claude Code with agent access
- Git repository
- Text editor for markdown

### Before Starting

1. Have a clear understanding of your project's goals
2. Know what domains your project touches
3. Identify any regulatory or compliance requirements
4. Understand your team size and workflow

---

## 3. Directory Structure

Create this structure in your project:

```
project-root/
├── _bmad/                          # BMAD framework configuration
│   ├── config.yaml                 # Triggers, workflows, routing
│   ├── workflows.md                # Detailed workflow definitions
│   └── templates/                  # Planning artifact templates
│       ├── prd-lite.md
│       ├── architecture.md
│       ├── task-breakdown.yaml
│       └── [domain-specific].md
├── docs/
│   ├── agents/                     # Agent governance
│   │   ├── AGENTS.md               # Master governance document
│   │   ├── available-agents-inventory.md
│   │   ├── agent-relevance-matrix.md
│   │   ├── expanded-inventory.md   # Cognitive profiles
│   │   ├── friction-map.md
│   │   ├── simulations.md
│   │   ├── decisions.md
│   │   ├── yoni-perspective.md
│   │   ├── wealon-perspective.md
│   │   └── baseline-v1.0.md
│   ├── planning/                   # BMAD planning artifacts
│   │   ├── TEMPLATES.md
│   │   ├── prd-lite/
│   │   ├── architecture/
│   │   ├── task-breakdowns/
│   │   └── [domain-specific]/
│   ├── adr/                        # Architecture Decision Records
│   └── project-context.md          # Domain bible
├── audits/                         # Wealon audit reports
└── CLAUDE.md                       # Project instructions
```

### Create Directories

```bash
mkdir -p _bmad/templates
mkdir -p docs/agents
mkdir -p docs/planning/{prd-lite,architecture,task-breakdowns}
mkdir -p docs/adr
mkdir -p audits
```

---

## 4. Phase 1: Project Context Intake

### Purpose

Create the "domain bible" - a comprehensive document that captures everything about your project that agents need to know.

### Output File

`docs/project-context.md`

### Required Sections

```markdown
# Project Context - [Project Name]

## 1. Project Overview
- What is this project?
- What problem does it solve?
- Who are the users?

## 2. Domain Model
- Key concepts and terminology
- Entity relationships
- Business rules

## 3. Technical Architecture
- Tech stack
- Key components
- Data flow

## 4. Assumptions
- What we assume to be true
- What we explicitly don't support

## 5. Constraints
- Technical constraints
- Business constraints
- Regulatory constraints

## 6. Risk Areas
- High-risk code/files
- Complex logic areas
- Frequently changing areas

## 7. Non-Goals
- What this project explicitly doesn't do
- Out of scope items
```

### How to Create

1. Read your existing codebase thoroughly
2. Identify all major components
3. Document domain-specific terminology
4. List all assumptions (implicit and explicit)
5. Identify high-risk files (e.g., complex parsers, critical calculations)

### Example Content

See: `CartesSociete/docs/project-context.md` for a complete example covering:
- Game mechanics (families, classes, phases)
- Combat formula with full mathematical specification
- RL environment architecture
- Card data structure
- Risk areas (abilities.py as highest-risk)

---

## 5. Phase 2: Agent Inventory

### Purpose

Enumerate ALL available agents regardless of whether they'll be used. This creates a complete picture before filtering.

### Output File

`docs/agents/available-agents-inventory.md`

### Required Sections

```markdown
# Available Agents Inventory

## All Available Agents

| Agent | Domain | Intended Role | Strengths | Risks | Dependencies |
|-------|--------|---------------|-----------|-------|--------------|
| yoni-orchestrator | Orchestration | Task coordination | ... | ... | ... |
| alexios-ml-predictor | ML/Optimization | Model design | ... | ... | ... |
| ... | ... | ... | ... | ... | ... |

## Agent Categories

### Orchestration Agents
- yoni-orchestrator
- [others]

### Development Agents
- it-core-clovis
- quality-control-enforcer
- lamine-deployment-expert

### ML/Data Agents
- alexios-ml-predictor
- dulcy-ml-engineer
- pierre-jean-ml-advisor
- data-engineer-sophie

### Security/Compliance Agents
- cybersecurity-expert-maxime
- wealon-regulatory-auditor

### Domain-Specific Agents
- [list all domain agents]

## Undocumented Agents (Governance Risk)
- [flag any agents without clear documentation]
```

### How to Create

1. List every agent available in your environment
2. Categorize by domain/function
3. Document what each agent does
4. Note any risks or dependencies
5. Flag undocumented agents as governance risks

---

## 6. Phase 3: Agent Relevance & Selection

### Purpose

Decide which agents matter for YOUR project. This is where you filter the inventory.

### Output File

`docs/agents/agent-relevance-matrix.md`

### Required Sections

```markdown
# Agent Relevance Matrix

## Classification Criteria

- **Primary**: Core agents, always available, no conditions
- **Conditional**: Allowed under specific constraints
- **System**: Meta/tooling agents (Explore, Plan, etc.)
- **Available but Inactive**: Exists but not needed yet
- **Explicitly Rejected**: Wrong domain, never use

## Relevance Matrix

| Agent | Domain | Relevance | Rationale | Risks | Conditions |
|-------|--------|-----------|-----------|-------|------------|
| yoni-orchestrator | Orchestration | PRIMARY | Entry point for all requests | None | Always use |
| alexios-ml-predictor | ML | CONDITIONAL | Useful for [X] | Financial bias | Translate to project domain |
| research-remy-stocks | Finance | REJECTED | Wrong domain | Domain mismatch | Never use |
| ... | ... | ... | ... | ... | ... |

## Selection Summary

### Primary Agents (X total)
1. yoni-orchestrator - [reason]
2. it-core-clovis - [reason]
3. ...

### Conditional Agents (X total)
1. alexios-ml-predictor - Condition: [when to use]
2. ...

### System Agents (X total)
1. Explore - [usage]
2. Plan - [usage]
3. ...

### Available but Inactive (X total)
1. cybersecurity-expert-maxime - Activate when: [trigger]
2. ...

### Explicitly Rejected (X total)
1. research-remy-stocks - Reason: [why rejected]
2. ...
```

### How to Create

1. For each agent in inventory, ask: "Does this project need this?"
2. Classify into the 5 categories
3. Document rationale for each decision
4. Be explicit about rejection reasons
5. Define conditions for conditional agents

### Key Decision Criteria

- **Domain match**: Does the agent's domain match your project?
- **Current need**: Do you need this capability now?
- **Future need**: Might you need it later?
- **Risk**: What could go wrong if you use this agent incorrectly?
- **Alternatives**: Is there a better-suited agent?

---

## 7. Phase 4: Expanded Agent Profiles

### Purpose

Define each integrated agent as a "cognitive instrument" with blind spots, failure modes, and interaction patterns. This is deeper than the inventory.

### Output File

`docs/agents/expanded-inventory.md`

### Required Sections

```markdown
# Expanded Agent Inventory - Cognitive Profiles

## Part 1: Primary Agents

### 1.1 yoni-orchestrator

**Cognitive Profile**:
- Mental model: Task router, not task executor
- Strengths: Coordination, parallel dispatch, workflow selection
- Blind spots: [what it can't see]
- Failure modes: [how it fails]

**Scope Boundary**:
> "Yoni routes tasks. Yoni does not execute domain logic."

**Interaction Patterns**:
- Receives: User requests
- Dispatches to: Specialized agents
- Returns: Aggregated results

**When to Override**: [conditions where human should bypass]

### 1.2 [next primary agent]
...

## Part 2: Conditional Agents

### 2.1 [conditional agent]

**Cognitive Profile**: ...
**Activation Conditions**: [when to use]
**Constraints**: [limitations]
**Domain Translation Required**: [if applicable]

## Part 3: System Agents

### 3.1 Explore
**Usage**: Direct call OK for [X]
**When to use Yoni instead**: [Y]

## Part 4: Available but Inactive

### 4.1 [inactive agent]
**Status**: INACTIVE / MANDATORY EXIT GATE / etc.
**Activate When**: [trigger]
**Rationale**: [why inactive]

## Part 5: Agent Interaction Patterns

### 5.1 The Standard Development Flow
[diagram or description]

### 5.2 The ML Escalation Flow
[diagram or description]

### 5.3 The Balance Analysis Flow
[diagram or description]
```

### How to Create

1. For each integrated agent, define:
   - What it's good at (strengths)
   - What it can't see (blind spots)
   - How it fails (failure modes)
   - Where its authority ends (scope boundary)
2. Define interaction patterns between agents
3. Create flow diagrams for common workflows

### Critical: Define Blind Spots

Every agent has blind spots. Document them explicitly:

```markdown
**Blind Spots**:
- Cannot understand [domain concept]
- Does not validate [X]
- Assumes [Y] is always true
- Cannot detect [Z] errors
```

---

## 8. Phase 5: Friction Mapping

### Purpose

Identify where agents overlap, where gaps exist, and how handoffs should work. This is critical for avoiding conflicts and filling gaps.

### Output File

`docs/agents/friction-map.md`

### Required Sections

```markdown
# Friction Map - Agent Ecosystem Analysis

## Part 1: Overlaps

Where do agents' responsibilities intersect?

| Overlap | Agents | Friction Type | Resolution |
|---------|--------|---------------|------------|
| Code quality | Clovis + QC | Dual review | Sequential: QC first, then Clovis |
| ML architecture | Alexios + Dulcy | Design vs implementation | Escalation protocol |
| ... | ... | ... | ... |

### Overlap Details

#### Overlap 1: [Name]
- **Agents involved**: [list]
- **What overlaps**: [description]
- **Why it's friction**: [explanation]
- **Resolution**: [how to handle]

## Part 2: Gaps

What capabilities are missing?

| Gap | Description | Severity | Current Mitigation |
|-----|-------------|----------|-------------------|
| Game mechanics | No agent understands game rules | CRITICAL | Documentation + human |
| Balance analysis | No agent can interpret balance | HIGH | Partial automation + human |
| ... | ... | ... | ... |

### Gap Details

#### Gap 1: [Name]
- **What's missing**: [description]
- **Why it matters**: [impact]
- **Severity**: CRITICAL / HIGH / MEDIUM / LOW
- **Current mitigation**: [workaround]
- **Future resolution**: [plan, if any]

## Part 3: Handoffs

How do agents transfer work to each other?

| Handoff | From | To | Trigger | Contract |
|---------|------|-----|---------|----------|
| Architecture → Implementation | Alexios | Dulcy | Design approved | ML design doc |
| Implementation → Review | Any | QC | Code complete | PR ready |
| ... | ... | ... | ... | ... |

### Handoff Contract Template

```yaml
handoff:
  from: [source agent]
  to: [target agent]
  trigger: [what initiates handoff]
  required_artifacts:
    - [artifact 1]
    - [artifact 2]
  acceptance_criteria:
    - [criterion 1]
    - [criterion 2]
```

## Part 4: Conflicts

Where might agents disagree?

| Conflict | Agents | Scenario | Resolution |
|----------|--------|----------|------------|
| Review disagreement | Clovis vs QC | Both reject for different reasons | Hierarchy: QC > Clovis for substance |
| ... | ... | ... | ... |

## Part 5: Friction Severity Summary

| Category | Count | Critical | High | Medium | Low |
|----------|-------|----------|------|--------|-----|
| Overlaps | X | 0 | X | X | X |
| Gaps | X | X | X | X | X |
| Handoffs | X | 0 | X | X | X |
| Conflicts | X | 0 | X | X | X |
```

### How to Create

1. List every place where two agents might work on the same thing (overlaps)
2. List every capability your project needs that no agent provides (gaps)
3. Define how work flows between agents (handoffs)
4. Identify where agents might disagree (conflicts)
5. Score severity and define resolutions

---

## 9. Phase 6: Impact Simulations

### Purpose

Before making any major decision, simulate its effects. This prevents unintended consequences.

### Output File

`docs/agents/simulations.md`

### Required Sections

```markdown
# Impact Simulations

## Simulation Methodology

For each proposed change:
1. Define the change
2. Identify first-order effects (immediate)
3. Identify second-order effects (ripples)
4. Identify third-order effects (emergent)
5. Make verdict: IMPLEMENT / REJECT / DEFER / CONDITIONAL

## Simulation 1: [Change Name]

### Change Description
[What exactly changes?]

### First-Order Effects
| Effect | Impact |
|--------|--------|
| [immediate effect 1] | [description] |
| ... | ... |

### Second-Order Effects
| Effect | Impact |
|--------|--------|
| [ripple effect 1] | [description] |
| ... | ... |

### Third-Order Effects
| Effect | Impact |
|--------|--------|
| [emergent effect 1] | [description] |
| ... | ... |

### Simulation Verdict
**[IMPLEMENT / REJECT / DEFER / CONDITIONAL]**: [rationale]

### Mitigated Alternative
[If rejected or conditional, what's the alternative?]

## Simulation Summary

### Approved Changes
| Change | Condition |
|--------|-----------|
| [change 1] | [any conditions] |

### Rejected Changes
| Change | Reason |
|--------|--------|
| [change 1] | [why rejected] |

### Deferred Changes
| Change | Revisit When |
|--------|--------------|
| [change 1] | [trigger for reconsideration] |
```

### Key Simulations to Run

1. **Remove Yoni-first rule** - What happens without orchestration?
2. **Add new domain expert agent** - Worth the complexity?
3. **Change algorithm/technology** - What existing work is invalidated?
4. **Activate dormant agent** - What overhead does it add?
5. **Enforce strict handoffs** - Too much bureaucracy?
6. **Remove an agent** - What gap does it create?

### How to Create

1. List every significant decision you're considering
2. For each, trace effects through 3 levels
3. Be honest about negative consequences
4. Document mitigated alternatives for rejected changes

---

## 10. Phase 7: Multi-Perspective Audits

### Purpose

View the system from different perspectives to catch blind spots. At minimum, create a "builder" view and an "auditor" view.

### Output Files

- `docs/agents/yoni-perspective.md` (Builder view)
- `docs/agents/wealon-perspective.md` (Auditor view)

### Builder Perspective Structure

```markdown
# Builder Perspective: [Agent Name]'s View

**Perspective**: Builder / Orchestrator
**Bias**: "How do we get things done?"

## Executive Summary
[Overall assessment from builder viewpoint]

## Part 1: Ecosystem Assessment

### What's Working
1. [Working thing 1] - [why it works]
2. ...

### What's Friction
1. [Friction point 1] - [why it's friction]
2. ...

## Part 2: Workflow Analysis

### Workflow 1: "[Common task]"
**Current Flow**: [diagram or steps]
**Assessment**: [SMOOTH / WORKABLE / POOR] ([score]/10)
[Analysis]

## Part 3: Agent Effectiveness Ratings

| Agent | Usefulness | Comment |
|-------|------------|---------|
| [agent 1] | X/10 | [comment] |
| ... | ... | ... |

## Part 4: Recommendations
1. [Recommendation 1]
2. ...

## Part 5: Risk Assessment (Builder Lens)

### Risks I Accept
| Risk | Why I Accept It |
|------|-----------------|
| ... | ... |

### Risks I'm Concerned About
| Risk | Why I'm Concerned |
|------|-------------------|
| ... | ... |
```

### Auditor Perspective Structure

```markdown
# Auditor Perspective: [Agent Name]'s View

**Perspective**: Auditor / Risk Assessor
**Bias**: "What could go wrong?"

## Executive Summary
[Overall assessment from auditor viewpoint - typically more critical]

## Part 1: Critical Findings

### Finding 1: [CRITICAL/HIGH/MEDIUM/LOW] - [Title]
**Observation**: [What you observed]
**Evidence**: [Where you saw it]
**Risk Assessment**: [Why it's a risk]
**What Could Go Wrong**: [Scenarios]
**Recommendation**: [How to fix]

## Part 2: Process Audit

### Process 1: [Process Name]
**Current**: [How it works]
**Audit Findings**:
| Step | Strength | Weakness |
|------|----------|----------|
| ... | ... | ... |
**Gap**: [What's missing]
**Recommendation**: [How to improve]

## Part 3: Documentation Audit

### Document: [Document Name]
**Strengths**: [What's good]
**Weaknesses**: [What's missing/wrong]
**Recommendation**: [How to improve]

## Part 4: Risk Register

| ID | Risk | Likelihood | Impact | Mitigation | Adequacy |
|----|------|------------|--------|------------|----------|
| R1 | [risk] | HIGH/MED/LOW | HIGH/MED/LOW | [current mitigation] | ADEQUATE/PARTIAL/INADEQUATE |

## Part 5: Comparison to Builder Perspective

| Topic | Builder Says | I Say |
|-------|--------------|-------|
| [topic] | [builder view] | [auditor view] |

## Part 6: Audit Verdict

**Overall Assessment**: [PASS / CONDITIONAL PASS / FAIL]

**Acceptable For**: [what the system can do]
**Inadequate For**: [what the system cannot do]

**Required Actions for Full Pass**:
1. [Action 1]
2. ...
```

### How to Create

1. Write the builder perspective first (optimistic, focused on getting work done)
2. Write the auditor perspective second (skeptical, focused on what could go wrong)
3. Compare the two and identify disagreements
4. Document how to resolve disagreements

---

## 11. Phase 8: Decisions & Memory

### Purpose

Record all design decisions with rationale. This is the institutional memory that explains WHY the system is built this way.

### Output File

`docs/agents/decisions.md`

### Required Sections

```markdown
# Agent Ecosystem Decisions Log

## Part 1: Major Design Decisions

### Decision D001: [Decision Title]

**Date**: [YYYY-MM-DD]
**Status**: [ACTIVE / SUPERSEDED by DXXX]
**Decision**: [One sentence summary]

**Context**:
[Why was this decision needed?]

**Options Considered**:

| Option | Pros | Cons |
|--------|------|------|
| **A: [Option A]** | [pros] | [cons] |
| **B: [Option B]** | [pros] | [cons] |
| **C: [Option C]** | [pros] | [cons] |

**Decision**: Option [X]

**Rationale**:
- [Reason 1]
- [Reason 2]

**Consequences**:
- [Consequence 1]
- [Consequence 2]

**Technical Debt**: [None / Description of debt created]

---

### Decision D002: ...

## Part 2: Open Questions

### OQ001: [Question]
**Question**: [Full question]
**Current Answer**: [Best current answer]
**Implications**: [What this means]
**Revisit When**: [Trigger for reconsideration]

## Part 3: Technical Debt Register

| ID | Description | Severity | Origin | Mitigation | Resolution Plan |
|----|-------------|----------|--------|------------|-----------------|
| TD001 | [description] | HIGH/MED/LOW | D00X | [current mitigation] | [plan] |

## Part 4: Rejected Alternatives Archive

### Rejected: [Alternative Name] (D00X)
**Why Proposed**: [reason]
**Why Rejected**: [reason]
**Conditions to Reconsider**: [triggers, or "Never"]

## Part 5: Memory for Future Sessions

### Context That Must Be Preserved
1. [Critical context 1]
2. [Critical context 2]
...

### Patterns That Work
1. "[Task type]" → [workflow]
2. ...

### Patterns That Fail
1. "[Question type]" → No agent can answer
2. ...

## Part 6: Document Maintenance

### Update Triggers
This document MUST be updated when:
- New major decision made
- New question arises
- Technical debt created or resolved
- Alternative rejected

### Review Schedule
- [When to review]
```

### Key Decisions to Document

1. **Entry point architecture** (Yoni-first or not?)
2. **Exit gate policy** (Wealon mandatory or triggered?)
3. **Domain expert agents** (Create new or use existing?)
4. **Review workflow** (Sequential or parallel?)
5. **Handoff contracts** (Strict or flexible?)
6. **Rejected agents** (Why each was rejected)

---

## 12. Phase 9: BMAD Framework Configuration

### Purpose

Configure the actual BMAD workflow system that will drive day-to-day operations.

### Output Files

- `_bmad/config.yaml` - Main configuration
- `_bmad/workflows.md` - Workflow definitions
- `_bmad/templates/*.md` - Planning templates

### config.yaml Structure

```yaml
# BMAD + AGENTIC Framework Configuration
# [Project Name]
# Version: 1.0

project:
  name: [Project Name]
  type: [project type]
  domains:
    - [domain 1]
    - [domain 2]

# Complexity triggers that activate Planning Mode
triggers:
  new_feature:
    condition: "Any new capability"
    workflow: FULL_PLANNING
    threshold: 1

  domain_crossing:
    condition: ">= 2 domains touched"
    workflow: INTEGRATION
    threshold: 2

  file_impact:
    condition: ">= 2 files changed"
    workflow: FULL_PLANNING
    threshold: 2

  # Add domain-specific triggers
  [domain]_change:
    condition: "[description]"
    workflow: [WORKFLOW_NAME]
    threshold: 1

  infrastructure:
    condition: "CI/CD or config changes"
    workflow: ADR
    threshold: 1

  simple_change:
    condition: "Single file, low risk"
    workflow: SKIP
    threshold: 0

# Workflow definitions
workflows:
  FULL_PLANNING:
    stages:
      - ANALYZE
      - SCOPE
      - ARCHITECT
      - DECOMPOSE
    artifacts:
      - prd-lite.md
      - architecture.md
      - task-breakdown.yaml
    agents:
      - yoni-orchestrator
      - [relevant agents]

  INTEGRATION:
    stages:
      - ANALYZE
      - INTERFACE_MAPPING
      - CONTRACT_DEFINITION
    artifacts:
      - integration-spec.md
    agents:
      - yoni-orchestrator
      - it-core-clovis

  # Add domain-specific workflows
  [DOMAIN]_WORKFLOW:
    stages:
      - [stage 1]
      - [stage 2]
    artifacts:
      - [artifact].md
    agents:
      - [agent list]

  ADR:
    stages:
      - CONTEXT
      - OPTIONS
      - DECISION
      - CONSEQUENCES
    artifacts:
      - adr-{number}-{title}.md
    agents:
      - yoni-orchestrator
      - lamine-deployment-expert

  SKIP:
    stages: []
    artifacts: []
    agents: []

# Agent routing
routing:
  entry_point: yoni-orchestrator

  tracks:
    development:
      agents:
        - it-core-clovis
        - quality-control-enforcer
        - lamine-deployment-expert
      triggers:
        - code_change
        - pr_creation

    # Add domain-specific tracks
    [domain]:
      agents:
        - [agent list]
      triggers:
        - [trigger list]

# Artifact locations
artifacts:
  prd_lite: "docs/planning/prd-lite/{date}-{feature}.md"
  architecture: "docs/planning/architecture/{date}-{feature}.md"
  task_breakdown: "docs/planning/task-breakdowns/{date}-{feature}.yaml"
  adr: "docs/adr/{number}-{title}.md"
  # Add domain-specific locations
  [domain]: "docs/planning/[domain]/{date}-{name}.md"

# Planning mode behavior
planning_mode:
  autonomous: true
  max_duration_seconds: 60
  artifact_persistence: true
  modular_workflows: true

# Quality gates
quality_gates:
  pre_commit:
    - [tool 1]
    - [tool 2]

  pre_merge:
    - ci_pass
    - quality_control_review
    - clovis_review

  # MANDATORY: Exit gate for every task
  task_completion:
    - wealon_audit  # REQUIRED

# Agent gates (entry and exit)
agent_gates:
  entry:
    agent: yoni-orchestrator
    trigger: start_of_task
    required: true

  exit:
    agent: wealon-regulatory-auditor
    trigger: end_of_task
    required: true
    blocks_completion: true
```

### workflows.md Structure

```markdown
# BMAD Workflow Definitions

## Workflow Overview

| Workflow | Trigger | Agents | Output |
|----------|---------|--------|--------|
| FULL_PLANNING | New feature, >2 files | [agents] | PRD, architecture, tasks |
| ... | ... | ... | ... |

## [WORKFLOW_NAME]

**Trigger**: [when this workflow activates]

### Stages

```
[STAGE 1] → [STAGE 2] → [STAGE 3]
```

### Stage Details

#### 1. [STAGE 1]
- [Action 1]
- [Action 2]

### Artifacts

| Artifact | Template | Location |
|----------|----------|----------|
| [artifact] | `_bmad/templates/[template].md` | `docs/planning/[folder]/` |

### Agent Roles

- **[agent 1]**: [role in this workflow]
- **[agent 2]**: [role in this workflow]

## Workflow Selection Matrix

| Request Type | Files | Domains | [Factor] | Workflow |
|--------------|-------|---------|----------|----------|
| New feature | Any | 1 | No | FULL_PLANNING |
| Bug fix | 1 | 1 | No | SKIP |
| ... | ... | ... | ... | ... |
```

### Template Files

Create templates in `_bmad/templates/`:

**prd-lite.md**:
```markdown
# PRD-Lite: [Feature Name]

**Date**: [YYYY-MM-DD]
**Author**: [who]
**Status**: DRAFT / APPROVED

## Problem Statement
[What problem are we solving?]

## Proposed Solution
[High-level solution]

## Scope
### In Scope
- [item 1]

### Out of Scope
- [item 1]

## Acceptance Criteria
- [ ] [criterion 1]
- [ ] [criterion 2]

## Risks
| Risk | Mitigation |
|------|------------|
| [risk] | [mitigation] |
```

**architecture.md**:
```markdown
# Architecture: [Feature Name]

**Date**: [YYYY-MM-DD]

## Overview
[High-level architecture]

## Components
### [Component 1]
- Purpose: [what it does]
- Interfaces: [how it connects]

## Data Flow
[Description or diagram]

## Dependencies
- [dependency 1]

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| [decision] | [why] |
```

**task-breakdown.yaml**:
```yaml
feature: [Feature Name]
date: [YYYY-MM-DD]
total_tasks: [N]

tasks:
  - id: 1
    title: [Task title]
    agent: [assigned agent]
    depends_on: []
    artifacts:
      - [artifact]
    acceptance:
      - [criterion]

  - id: 2
    title: [Task title]
    agent: [assigned agent]
    depends_on: [1]
    ...
```

---

## 13. Phase 10: CLAUDE.md Integration

### Purpose

Update the project's CLAUDE.md to integrate BMAD+AGENTIC workflows.

### Required Sections in CLAUDE.md

```markdown
# CLAUDE.md - [Project Name]

## MANDATORY WORKFLOW: BMAD + AGENTIC

> **BMAD is a behavior, not a structure.**
> Every user request goes through Yoni, who determines the appropriate workflow.

### 1. ALWAYS CALL YONI FIRST

**FOR EVERY USER REQUEST**, you MUST call `yoni-orchestrator` via the Task tool.

- Yoni coordinates all specialized agents
- Yoni selects the appropriate BMAD workflow
- **NEVER** try to handle complex tasks yourself
- **This is the MOST IMPORTANT rule**

### 2. ALWAYS CALL WEALON LAST

**AT THE END OF EVERY TASK**, you MUST call `wealon-regulatory-auditor`.

- Wealon audits all work before completion
- Wealon catches shortcuts and workarounds
- **No task is complete until Wealon has reviewed it**

### Mandatory Workflow Pattern

```
USER REQUEST
     ↓
┌────────────────────────────────────┐
│  1. YONI (Entry)                   │
│     - Detect triggers              │
│     - Select BMAD workflow         │
│     - Coordinate agents            │
└────────────────────────────────────┘
     ↓
┌────────────────────────────────────┐
│  2. PLANNING + EXECUTION           │
│     - BMAD workflow artifacts      │
│     - Agent delegation             │
│     - Implementation               │
└────────────────────────────────────┘
     ↓
┌────────────────────────────────────┐
│  3. WEALON (Exit)                  │
│     - Audit all changes            │
│     - Review for shortcuts         │
│     - Verify completeness          │
│     - Flag issues                  │
└────────────────────────────────────┘
     ↓
TASK COMPLETE (only after Wealon approval)
```

### 3. Yoni Decision Transparency

When dispatching, Yoni SHOULD log:

```
YONI ROUTING:
├── Request: "{brief summary}"
├── Triggers: [trigger1: YES, trigger2: NO, ...]
├── Workflow: [WORKFLOW_NAME]
├── Agents: [agent list]
└── Rationale: [why this workflow]
```

---

## Agent Governance

**Full governance:** `docs/agents/AGENTS.md`

### Primary Agents

| Agent | Specialty | When to Call |
|-------|-----------|--------------|
| yoni-orchestrator | Coordination | **EVERY request** - FIRST |
| wealon-regulatory-auditor | Audit | **EVERY task** - LAST |
| it-core-clovis | Code quality | Git, PR, review |
| quality-control-enforcer | QA | Implementation review |
| lamine-deployment-expert | CI/CD | Pipelines, testing |

### Conditional Agents

| Agent | Specialty | Condition |
|-------|-----------|-----------|
| [agent] | [specialty] | [when to use] |

### Rejected Agents

[List agents that should NEVER be used and why]

---

## BMAD + AGENTIC Planning Framework

### Activation

Planning Mode activates when:
1. User says **"use BMAD+AGENTIC workflow"**
2. Yoni detects complexity triggers (automatic)

### Complexity Triggers

| Trigger | Condition | Workflow |
|---------|-----------|----------|
| `new_feature` | Any new capability | FULL_PLANNING |
| `file_impact` | >= 2 files changed | FULL_PLANNING |
| `domain_crossing` | >= 2 domains | INTEGRATION |
| [domain trigger] | [condition] | [workflow] |
| `simple_change` | Single file, low risk | SKIP |

### Workflow Definitions

**FULL_PLANNING_WORKFLOW**
```
ANALYZE → SCOPE → ARCHITECT → DECOMPOSE
Artifacts: prd-lite.md, architecture.md, task-breakdown.yaml
```

[Add other workflows]

### Agent Roles in Planning Mode

| Agent | Planning Mode Role |
|-------|-------------------|
| yoni-orchestrator | Trigger detection, workflow dispatch |
| [agent] | [role] |

### Artifact Output Locations

| Artifact Type | Location |
|---------------|----------|
| PRD-lite | `docs/planning/prd-lite/{date}-{feature}.md` |
| Architecture | `docs/planning/architecture/{date}-{feature}.md` |
| [artifact] | [location] |

### Key References

- **Agent Governance:** `docs/agents/AGENTS.md`
- **Workflow Config:** `_bmad/config.yaml`
- **Workflow Details:** `_bmad/workflows.md`
- **Templates:** `docs/planning/TEMPLATES.md`

---

## Anti-Patterns (NEVER DO)

### Agent Anti-Patterns
1. **NEVER** skip calling Yoni for user requests
2. **NEVER** skip calling Wealon at task completion
3. **NEVER** create PRs without review agents
4. **NEVER** use rejected agents
5. **NEVER** bypass BMAD workflows for complex tasks
6. **NEVER** mark a task complete without Wealon audit

---

## Example Planning Flow

```
User: "[Example request]"

┌─────────────────────────────────────────────────────┐
│ ENTRY: YONI                                         │
├─────────────────────────────────────────────────────┤
│ Yoni detects:                                       │
│ ├── new_feature: true                               │
│ ├── domains: [domain1, domain2]                     │
│ └── estimated_files: X+                             │
│                                                     │
│ Triggers:                                           │
│ ├── FULL_PLANNING (new feature)                     │
│ └── [other workflow] (reason)                       │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│ PLANNING + EXECUTION                                │
├─────────────────────────────────────────────────────┤
│ Executes:                                           │
│ ├── FULL_PLANNING → prd-lite.md, architecture.md    │
│ └── [workflow] → [artifacts]                        │
│                                                     │
│ Handoff:                                            │
│ └── Task breakdown → Agent delegation → Code        │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│ EXIT: WEALON                                        │
├─────────────────────────────────────────────────────┤
│ Wealon audits:                                      │
│ ├── All code changes                                │
│ ├── Planning artifacts                              │
│ ├── Compliance with standards                       │
│ └── Completeness check                              │
│                                                     │
│ Result:                                             │
│ ├── APPROVED → Task complete                        │
│ └── ISSUES → Fix and re-audit                       │
└─────────────────────────────────────────────────────┘
```

---

**Remember:**
- **ALWAYS call yoni-orchestrator FIRST**
- **ALWAYS call wealon-regulatory-auditor LAST**
- **BMAD workflows ensure proper planning and execution**
```

---

## 14. Phase 11: Baseline Freeze

### Purpose

Freeze all governance documents as a baseline version with formal change control.

### Output File

`docs/agents/baseline-v1.0.md`

### Required Sections

```markdown
# [Project] Agent Ecosystem - Baseline v1.0

**Status**: FROZEN
**Freeze Date**: [YYYY-MM-DD]
**Authority**: [who approved]

---

## Step 1: Baseline Declaration

### Frozen Documents

| Document | Path | Version | Purpose |
|----------|------|---------|---------|
| AGENTS.md | `docs/agents/AGENTS.md` | v2.0 | Governance master |
| [document] | [path] | [version] | [purpose] |

### Frozen Assumptions

| ID | Assumption | Locked Value |
|----|------------|--------------|
| A1 | [assumption] | TRUE/FALSE |
| A2 | [assumption] | TRUE/FALSE |

### Non-Negotiable Scope Boundaries

```
SYSTEM IS:
├── [capability 1]
├── [capability 2]
└── [capability 3]

SYSTEM IS NOT:
├── [non-capability 1]
├── [non-capability 2]
└── [non-capability 3]
```

### Mandatory Agent Gates

| Gate | Trigger | Agent | Action |
|------|---------|-------|--------|
| AG-01 | Start of every task | yoni-orchestrator | Entry coordination |
| AG-02 | End of every task | wealon-regulatory-auditor | Exit audit |

### Mandatory Human Checkpoints

| Checkpoint | Trigger | Human Action Required |
|------------|---------|----------------------|
| HC-01 | [trigger] | [action] |

---

## Step 2: Breaking Change Definitions

A **breaking change** requires:
1. New binding decision
2. New Wealon audit
3. Version increment to v2.0

### Category A: Scope Expansion (BREAKING)

| Change | Why Breaking |
|--------|--------------|
| [change] | [reason] |

### Category B: Assumption Reversal (BREAKING)

| Change | Why Breaking |
|--------|--------------|
| [change] | [reason] |

---

## Step 3: Allowed Change Paths

### Legal Evolution (Within v1.0)

| Change Type | Conditions | Process |
|-------------|------------|---------|
| Bug fix | Does not change scope | Normal PR |
| Documentation clarification | Does not change meaning | Normal PR |

### Illegal Changes (Require v2.0)

```
ILLEGAL WITHOUT v2.0:
├── [illegal change 1]
├── [illegal change 2]
└── [illegal change 3]
```

---

## Step 4: Review Triggers

### Automatic Re-Audit Triggers

| Trigger | Audit Scope |
|---------|-------------|
| Pre-release | Full system |
| [trigger] | [scope] |

### System Freeze Triggers

| Trigger | Required Action |
|---------|-----------------|
| Baseline contradiction | Freeze until resolved |
| [trigger] | [action] |

---

## Step 5: Closure Statement

As of [date], the design phase is **CLOSED**.

The system is now **operational** under governed change control.

### System Truth (Locked)

> [One paragraph defining what this system IS and IS NOT]

### Human Authority (Affirmed)

The human operator retains:
- Final authority over [X]
- Veto power over [Y]
- Responsibility for [Z]

---

## Appendix: Human Acknowledgment

By using this system, the human operator acknowledges:

- [ ] I understand the system's limitations
- [ ] I accept responsibility for [X]
- [ ] I will follow the change control process
```

---

## 15. Phase 12: Wealon Audit & Commit

### Purpose

Before any commit, Wealon must audit the work.

### Process

1. **Stage files for commit**
   ```bash
   git add [files]
   ```

2. **Call Wealon for audit**
   ```
   Call wealon-regulatory-auditor via Task tool:
   "Audit all staged changes for commit approval"
   ```

3. **Address Wealon's findings**
   - Fix all CRITICAL and MAJOR issues
   - Address MINOR issues or document why deferred

4. **Re-audit if fixes were needed**
   - Wealon must approve the fixes

5. **Commit only after APPROVED verdict**
   ```bash
   git commit -m "[message]

   Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
   ```

### Wealon Audit Scope

Wealon should check:
- Consistency across all documents
- Completeness of required sections
- Quality and professionalism
- Governance compliance
- Security/risk implications

### Audit Report Location

Save audit reports to: `audits/audit-[date]-[topic].md`

---

## 16. File Templates

### Quick-Start Template Pack

Copy these files to start a new project:

1. **docs/project-context.md** - Adapt to your domain
2. **docs/agents/AGENTS.md** - Update agent selections
3. **_bmad/config.yaml** - Update triggers and workflows
4. **CLAUDE.md** - Update project-specific sections

### Template Repository Structure

```
templates/
├── docs/
│   ├── project-context.template.md
│   └── agents/
│       ├── AGENTS.template.md
│       ├── expanded-inventory.template.md
│       ├── friction-map.template.md
│       ├── simulations.template.md
│       ├── decisions.template.md
│       ├── yoni-perspective.template.md
│       ├── wealon-perspective.template.md
│       └── baseline-v1.0.template.md
├── _bmad/
│   ├── config.template.yaml
│   ├── workflows.template.md
│   └── templates/
│       ├── prd-lite.md
│       ├── architecture.md
│       └── task-breakdown.yaml
└── CLAUDE.template.md
```

---

## 17. Checklist

### Phase Completion Checklist

- [ ] **Phase 1**: `docs/project-context.md` created
- [ ] **Phase 2**: `docs/agents/available-agents-inventory.md` created
- [ ] **Phase 3**: `docs/agents/agent-relevance-matrix.md` created
- [ ] **Phase 4**: `docs/agents/expanded-inventory.md` created
- [ ] **Phase 5**: `docs/agents/friction-map.md` created
- [ ] **Phase 6**: `docs/agents/simulations.md` created
- [ ] **Phase 7**: `docs/agents/yoni-perspective.md` created
- [ ] **Phase 7**: `docs/agents/wealon-perspective.md` created
- [ ] **Phase 8**: `docs/agents/decisions.md` created
- [ ] **Phase 9**: `_bmad/config.yaml` created
- [ ] **Phase 9**: `_bmad/workflows.md` created
- [ ] **Phase 9**: `_bmad/templates/*.md` created
- [ ] **Phase 9**: `docs/planning/` structure created
- [ ] **Phase 10**: `CLAUDE.md` updated with BMAD sections
- [ ] **Phase 11**: `docs/agents/baseline-v1.0.md` created
- [ ] **Phase 11**: `docs/agents/AGENTS.md` marked as FROZEN
- [ ] **Phase 12**: Wealon audit completed
- [ ] **Phase 12**: All issues resolved
- [ ] **Phase 12**: Commit approved

### Quality Checklist

- [ ] All documents are cross-referenced
- [ ] All agents have defined blind spots
- [ ] All gaps have documented mitigations
- [ ] All decisions have rationale
- [ ] Yoni-first rule is documented
- [ ] Wealon-last rule is documented
- [ ] Agent gates are defined in config.yaml
- [ ] Human checkpoints are defined
- [ ] Breaking changes are defined
- [ ] Baseline is frozen

### Consistency Checklist

- [ ] Agent status matches across all documents
- [ ] Workflow definitions match config.yaml and workflows.md
- [ ] Trigger conditions are consistent
- [ ] Artifact locations are consistent
- [ ] No contradictions between documents

---

## Appendix: Known Limitations

### Document Structure

1. **Section vs Phase Numbering**: Sections 1-3 are overview/setup, sections 4-15 are the 12 implementation phases. This may cause confusion.

2. **Domain-Specific Workflows**: The guide includes templates for FULL_PLANNING, INTEGRATION, and ADR workflows. Domain-specific workflows (ML_DESIGN, BALANCE_REVIEW, etc.) are optional extensions - add them based on your project's needs.

3. **Template Repository**: The "Template Repository Structure" in section 16 is a suggested organization for a reusable template pack, not a requirement for each project.

### Path Variations

The global `~/.claude/CLAUDE.md` workflow specifies `docs/agents/project-context-summary.md` while this guide uses `docs/project-context.md`. Both are valid - choose based on your project structure. CartesSociete uses `docs/project-context.md`.

### Reference Implementation

This guide is based on CartesSociete (2026-01-19). Some files may have been consolidated:
- `agent-architecture.md` content may overlap with `expanded-inventory.md`
- Some templates may be project-specific

---

## Appendix: Common Pitfalls

### Pitfall 1: Shallow Implementation

**Symptom**: Skeleton documents with placeholder content
**Fix**: Each document must have real, project-specific content

### Pitfall 2: Missing Blind Spots

**Symptom**: Agents described only by strengths
**Fix**: Every agent MUST have documented blind spots

### Pitfall 3: Undefined Handoffs

**Symptom**: Agents work independently without coordination
**Fix**: Define explicit handoff contracts

### Pitfall 4: No Exit Gate

**Symptom**: Tasks marked complete without review
**Fix**: Wealon audit is MANDATORY for every task

### Pitfall 5: Scope Creep

**Symptom**: Agents used outside their domain
**Fix**: Define and enforce scope boundaries

### Pitfall 6: Document Drift

**Symptom**: Documents contradict each other
**Fix**: Regular consistency checks, Wealon audits

---

*This guide captures everything needed to replicate BMAD+AGENTIC on any project.*
*Source: CartesSociete implementation, 2026-01-19*
