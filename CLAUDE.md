# CLAUDE.md - CartesSociete

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
**READ THIS FILE WITH EXTREME CARE. RESPECT EVERY INSTRUCTION. BMAD+AGENTIC WORKFLOW IS MANDATORY.**

---

## Project Overview

**CartesSociete** is a project for designing solutions for a cardboard/card game. The project focuses on:

- **Game mechanics design** - Card interactions, rules, balance
- **Strategy optimization** - Optimal plays, probability analysis
- **Simulation & testing** - Game state simulation, Monte Carlo analysis
- **Balance analysis** - Card power levels, win rates, fairness
- **Reinforcement Learning** - AI players using PPO, curriculum learning

---

## MANDATORY WORKFLOW: BMAD + AGENTIC

> **BMAD is a behavior, not a structure.**
> Every user request goes through Yoni, who determines the appropriate workflow based on complexity triggers.

### 1. ALWAYS CALL YONI FIRST

**FOR EVERY USER REQUEST**, you MUST call `yoni-orchestrator` via the Task tool.

- Yoni coordinates all specialized agents and creates execution plans
- Yoni selects the appropriate BMAD workflow based on triggers
- **NEVER** try to handle complex tasks yourself - delegate to experts
- **This is the MOST IMPORTANT rule in this project**

### 2. ALWAYS CALL WEALON LAST

**AT THE END OF EVERY TASK**, you MUST call `wealon-regulatory-auditor` via the Task tool.

- Wealon audits and reviews all work before completion
- Wealon catches quality issues, shortcuts, and incomplete implementations
- Wealon verifies compliance with project standards
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

When dispatching a workflow, Yoni SHOULD log routing decisions for observability:

```
YONI ROUTING:
├── Request: "{brief summary}"
├── Triggers: [new_feature: YES, domain_crossing: NO, file_impact: 3]
├── Workflow: FULL_PLANNING
├── Agents: [alexios, clovis, qc, lamine]
└── Rationale: New feature with >= 2 files
```

---

## Agent Governance

**Full agent governance is defined in:** `docs/agents/AGENTS.md`

### Primary Agents (Always Available)

| Agent | Specialty | When to Call |
|-------|-----------|--------------|
| **yoni-orchestrator** | Task coordination | **EVERY user request** - call FIRST |
| **it-core-clovis** | Code quality | Git workflow, PR review, code optimization |
| **quality-control-enforcer** | Quality assurance | Review implementations, catch shortcuts |
| **lamine-deployment-expert** | CI/CD & TDD | Pipelines, testing infrastructure |

### Conditional Agents (For Specific Tasks)

| Agent | Specialty | When to Call |
|-------|-----------|--------------|
| **alexios-ml-predictor** | ML/optimization | RL design, balance prediction (adapt to game domain) |
| **dulcy-ml-engineer** | ML engineering | Training pipelines, gymnasium integration |
| **pierre-jean-ml-advisor** | ML guidance | Hyperparameter tuning, training optimization |
| **ml-production-engineer** | Productionization | Research-to-production cleanup |
| **data-engineer-sophie** | Data pipelines | Complex data flows (if needed) |

### Agent Role Distinctions

**Clovis vs QC:**
- **Clovis** = Structural quality (architecture, design patterns, git workflow compliance)
- **QC** = Implementation quality (correctness, completeness, edge cases, catching shortcuts)

**Alexios vs Dulcy vs Pierre-Jean:**
- **Alexios** = Architecture design, reward shaping, model selection
- **Dulcy** = Pipeline implementation, PyTorch code, training loops
- **Pierre-Jean** = Practical advice, hyperparameter tuning, troubleshooting

### Rejected Agents (DO NOT USE)

All financial domain agents are **explicitly rejected** for this project:
- research-remy-stocks, iacopo, nicolas, victor, pnl-validator
- trading-engine, cost-optimizer, french-tax, helena, portfolio-jean-yves
- legal-team-lead, legal-compliance, antoine-nlp-expert

**See** `docs/agents/AGENTS.md` **for full governance policies.**

---

## BMAD + AGENTIC Planning Framework

> **BMAD is a behavior, not a structure.**
> Planning Mode is an event-driven cognitive system that Yoni enters when complexity crosses thresholds.

### Activation

Planning Mode activates when:
1. User says **"use BMAD+AGENTIC workflow"**
2. Yoni detects complexity triggers (automatic)

**ALL complex requests MUST go through Planning Mode. There are no exceptions.**

### Workflow Dispatch Pattern

```
dispatch(event) → workflow.run(context)  ✅ CORRECT
if planning: do_everything()             ❌ WRONG (monolith)
```

Yoni dispatches to specific workflows, not one giant planning blob.

### Complexity Triggers

| Trigger | Condition | Workflow |
|---------|-----------|----------|
| `new_feature` | Any new capability | FULL_PLANNING |
| `domain_crossing` | >= 2 domains touched | INTEGRATION |
| `file_impact` | >= 2 files changed | FULL_PLANNING |
| `rl_architecture` | RL model/training changes | ML_DESIGN |
| `balance_analysis` | Card balance work | BALANCE_REVIEW |
| `infrastructure` | CI/CD or config changes | ADR |
| `simple_change` | Single file, low risk, no ML | SKIP (direct execute) |

### Workflow Definitions

**FULL_PLANNING_WORKFLOW**
```
ANALYZE → SCOPE → ARCHITECT → DECOMPOSE
Artifacts: prd-lite.md, architecture.md, task-breakdown.yaml
```

**ML_DESIGN_WORKFLOW**
```
PROBLEM_DEFINITION → ARCHITECTURE_REVIEW → TRAINING_PLAN
Artifacts: ml-design.md, training-config.yaml
```

**BALANCE_REVIEW_WORKFLOW**
```
CURRENT_STATE → METRICS_ANALYSIS → CHANGE_PROPOSAL
Artifacts: balance-analysis.md
```

**INTEGRATION_WORKFLOW**
```
ANALYZE → INTERFACE_MAPPING → CONTRACT_DEFINITION
Artifacts: integration-spec.md
```

**ADR_WORKFLOW**
```
CONTEXT → OPTIONS → DECISION → CONSEQUENCES
Artifacts: adr-{number}-{title}.md
```

### Agent Roles in Planning Mode

| Agent | Planning Mode Role |
|-------|-------------------|
| **yoni-orchestrator** | Trigger detection, workflow dispatch, coordination |
| **alexios-ml-predictor** | RL architecture review, complexity assessment |
| **dulcy-ml-engineer** | Training pipeline design, implementation planning |
| **it-core-clovis** | Code impact analysis, quality gates |
| **quality-control-enforcer** | Task breakdown validation, completeness check |
| **lamine-deployment-expert** | Infrastructure ADR workflow |

### Artifact Output Locations

| Artifact Type | Location |
|---------------|----------|
| PRD-lite | `docs/planning/prd-lite/{date}-{feature}.md` |
| Architecture | `docs/planning/architecture/{date}-{feature}.md` |
| ML Design | `docs/planning/ml-design/{date}-{feature}.md` |
| Balance Analysis | `docs/planning/balance/{date}-{analysis}.md` |
| Task Breakdown | `docs/planning/task-breakdowns/{date}-{feature}.yaml` |
| ADR | `docs/adr/{number}-{title}.md` |

### Planning Mode Behavior

1. **Autonomous** - No user approval ceremonies for workflow selection
2. **Fast** - Maximum 60 seconds for planning phase
3. **Artifact-rich** - Persist all decisions as .md files
4. **Modular** - Each workflow is a separate cognitive unit

### Key References

- **Agent Governance:** `docs/agents/AGENTS.md`
- **Workflow Config:** `_bmad/config.yaml`
- **Workflow Details:** `_bmad/workflows.md`
- **Templates:** `docs/planning/TEMPLATES.md`
- **ADR Index:** `docs/adr/`

---

## Development Commands

### Package Management
```bash
# Install dependencies
uv sync

# Add a new dependency
uv add <package-name>

# Add a dev dependency
uv add --dev <package-name>
```

**FORBIDDEN:** `uv pip install`, `@latest` syntax, pip directly

### Code Quality (RUN IN THIS ORDER)
```bash
# 1. Import sorting (AUTHORITATIVE - run first)
uv run isort .

# 2. Code formatting
uv run ruff format .

# 3. Linting
uv run ruff check .

# 4. Type checking
uv run pyrefly check

# 5. Run tests
uv run pytest
```

---

## Project Structure

```
CartesSociete/
├── _bmad/                # BMAD framework configuration
│   ├── config.yaml       # Triggers and workflow config
│   ├── workflows.md      # Workflow definitions
│   └── templates/        # Planning artifact templates
├── src/                  # Main source code
│   ├── cards/            # Card definitions and types
│   ├── game/             # Game engine and rules
│   ├── players/          # Player strategies and AI
│   ├── rl/               # Reinforcement learning
│   ├── simulation/       # Game simulation tools
│   └── analysis/         # Balance and statistics analysis
├── tests/                # Test suite
├── data/                 # Card data, game logs
├── notebooks/            # Analysis notebooks
├── configs/              # Game configuration files
├── scripts/              # CLI scripts
├── docs/
│   ├── agents/           # Agent governance (AGENTS.md)
│   ├── planning/         # BMAD planning artifacts
│   └── adr/              # Architecture Decision Records
└── audits/               # Security/quality audits
```

---

## Git Workflow

After completing any significant feature, fix, or change:

1. Create a new feature branch: `git checkout -b feat/description` or `fix/description`
2. Commit changes with conventional commit messages
3. Push the branch: `git push -u origin <branch-name>`
4. **Launch review agents** before creating PR:
   - `it-core-clovis` - Git workflow & code quality review
   - `quality-control-enforcer` - Quality assurance
5. Create PR through GitHub CLI
6. **NEVER** merge if CI fails

### GitHub CLI
GitHub CLI (`gh`) is installed at: `"/c/Program Files/GitHub CLI/gh.exe"`
```bash
"/c/Program Files/GitHub CLI/gh.exe" pr create --title "type(scope): description" --body "..."
"/c/Program Files/GitHub CLI/gh.exe" pr list
"/c/Program Files/GitHub CLI/gh.exe" pr checks <number>
"/c/Program Files/GitHub CLI/gh.exe" pr merge <number> --squash --delete-branch
```

### CI/CD Merge Workflow

**This is the MANDATORY workflow for all changes:**

```
1. CREATE BRANCH
   git checkout -b feat/description  (or fix/description)

2. MAKE CHANGES
   - Write code
   - Add tests if needed

3. RUN LOCAL CHECKS (before committing)
   uv run isort .
   uv run ruff format .
   uv run ruff check .
   uv run pytest

4. COMMIT & PUSH
   git add <files>
   git commit -m "type(scope): description"
   git push -u origin <branch-name>

5. CREATE PR
   gh pr create --title "type(scope): description" --body "..."

6. WATCH CI PIPELINE
   gh pr checks <number> --watch

7. IF CI FAILS:
   - Read the error logs: gh run view <run-id> --log-failed
   - Fix the issues locally
   - Commit and push again
   - Go back to step 6

8. IF CI PASSES:
   gh pr merge <number> --squash --delete-branch

9. SYNC LOCAL MASTER
   git checkout master
   git pull
```

**Key Rules:**
- **NEVER** merge if CI fails
- **ALWAYS** run local checks before pushing
- **ALWAYS** use `--squash` for clean history
- **ALWAYS** use `--delete-branch` to clean up

---

## Code Quality Standards

### Type Hints (REQUIRED)
```python
def calculate_damage(
    attacker: Card,
    defender: Card,
    modifiers: list[Modifier],
) -> int:
    """Calculate damage dealt by attacker to defender."""
    ...
```

### Docstrings (REQUIRED for public APIs)
```python
def play_card(card: Card, target: Target) -> GameState:
    """Play a card targeting a specific entity.

    Args:
        card: The card to play.
        target: The target of the card effect.

    Returns:
        Updated game state after the card is played.

    Raises:
        InvalidPlayError: If the card cannot be played on the target.
    """
    ...
```

### Testing (REQUIRED for new features)
- Unit tests for all game mechanics
- Integration tests for game flow
- Simulation tests for balance analysis

---

## Game Design Principles

### 1. Balance
- Track win rates across different strategies
- Use simulation to test new cards before finalizing
- Avoid dominant strategies

### 2. Clarity
- Clear card text and rules
- Consistent terminology
- Predictable interactions

### 3. Depth
- Multiple viable strategies
- Meaningful decisions each turn
- Skill-rewarding mechanics

---

## Anti-Patterns (NEVER DO)

### Design Anti-Patterns
1. **NEVER** add cards without balance testing
2. **NEVER** create auto-win conditions
3. **NEVER** ignore edge case interactions

### Code Anti-Patterns
1. **NEVER** commit without testing
2. **NEVER** hardcode game values (use configs)
3. **NEVER** skip type hints
4. **NEVER** merge without CI passing
5. **NEVER** work directly on main branch

### Agent Anti-Patterns
1. **NEVER** skip calling Yoni for user requests
2. **NEVER** skip calling Wealon at task completion
3. **NEVER** create PRs without review agents
4. **NEVER** use rejected financial domain agents
5. **NEVER** bypass BMAD workflows for complex tasks
6. **NEVER** mark a task complete without Wealon audit

---

## Example Planning Flow

```
User: "Add new Lapin card family synergy"

┌─────────────────────────────────────────────────────┐
│ ENTRY: YONI                                         │
├─────────────────────────────────────────────────────┤
│ Yoni detects:                                       │
│ ├── new_feature: true                               │
│ ├── domains: [cards, game, players]                 │
│ ├── estimated_files: 4+                             │
│ └── balance_impact: true                            │
│                                                     │
│ Triggers:                                           │
│ ├── FULL_PLANNING (new feature, >2 files)           │
│ └── BALANCE_REVIEW (affects game balance)           │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│ PLANNING + EXECUTION                                │
├─────────────────────────────────────────────────────┤
│ Executes:                                           │
│ ├── FULL_PLANNING → prd-lite.md, architecture.md    │
│ └── BALANCE_REVIEW → balance-analysis.md            │
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
- **ALWAYS call yoni-orchestrator FIRST** for every user request
- **ALWAYS call wealon-regulatory-auditor LAST** before completing any task
- **BMAD workflows ensure every complex task is properly planned and executed**
