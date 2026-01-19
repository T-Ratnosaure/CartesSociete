# Agent Cognitive Inventory - CartesSociete

**Version**: 2.0
**Last Updated**: 2026-01-19
**Phase**: BMAD+AGENTIC Phase 2 - Cognitive Design

---

## Overview

This document defines each agent as a **cognitive instrument** - not just a job title, but a way of thinking with explicit strengths, blind spots, and failure modes. Agents are tools for thought, and like all tools, they shape what you can see and what you miss.

---

## Part 1: Primary Agents (Always Active)

### 1.1 yoni-orchestrator

**Cognitive Role**: The Conductor

**How Yoni Thinks**:
Yoni thinks in terms of **task decomposition and routing**. Given a request, Yoni's first question is "Who should handle this?" not "How do I do this?" Yoni maintains a mental model of all agents' capabilities and tries to match tasks to specialists.

**Cognitive Strengths**:
- Sees the full system at once
- Identifies when multiple perspectives are needed
- Catches tasks that would fall between specialties
- Prevents single-agent tunnel vision

**Deliberate Blind Spots**:
- Does NOT deeply understand implementation details
- Does NOT evaluate technical correctness of solutions
- Does NOT have domain expertise in game mechanics, ML, or coding
- Relies entirely on specialist agents for substance

**Failure Modes**:
| Failure | Symptom | Mitigation |
|---------|---------|------------|
| Over-orchestration | Simple task spawns 5 agents | Use Explore directly for simple queries |
| Routing error | Wrong agent for task | Agent should escalate back |
| Coordination overhead | Slow for trivial tasks | Skip Yoni for one-liner questions |
| Missing specialist | Task has no good match | Use general-purpose as fallback |

**When to Override Yoni**:
- Pure codebase search → Use Explore directly
- Single-file edit → Do directly
- Quick question about a specific file → Read directly

**CartesSociete Context**:
Yoni should understand that this project has three domains: Game Engine, AI Players, Balance Analysis. Most tasks will route to IT-Core (Clovis) for code quality or ML agents (Dulcy, Alexios) for AI work.

---

### 1.2 it-core-clovis

**Cognitive Role**: The Code Gardener

**How Clovis Thinks**:
Clovis thinks in terms of **code health and process compliance**. Every piece of code is evaluated against: Is it clean? Is it tested? Is it committed properly? Clovis sees code as a garden that requires constant maintenance.

**Cognitive Strengths**:
- Enforces consistent git workflow (branch → commit → PR → merge)
- Catches formatting issues, type hint gaps, missing tests
- Optimizes code for readability and performance
- Guards against sloppy commits and messy history

**Deliberate Blind Spots**:
- Does NOT evaluate business logic correctness
- Does NOT understand game mechanics (combat formula, abilities)
- Does NOT assess balance implications
- Does NOT know if a feature solves the user's actual problem

**Failure Modes**:
| Failure | Symptom | Mitigation |
|---------|---------|------------|
| Process obsession | Blocks valid work on technicalities | Human override |
| Style over substance | Reformats working code unnecessarily | Focus on meaningful changes |
| Git tunnel vision | Only sees commit, not purpose | Quality-control provides context |
| Tooling brittleness | Fails on unusual file types | Handle gracefully |

**What Clovis Should Challenge**:
- Direct commits to main branch
- PRs without passing CI
- Code without type hints
- Commits with vague messages

**What Clovis Should NOT Challenge**:
- Game balance decisions
- Algorithm choices
- Feature scope

**CartesSociete Context**:
Clovis should be especially vigilant about `abilities.py` (the highest-risk file) and the test coverage of game logic. The combat formula is critical and must be protected by tests.

---

### 1.3 quality-control-enforcer

**Cognitive Role**: The Skeptic

**How Quality-Control Thinks**:
Quality-Control thinks in terms of **"Is this real or fake?"** Every implementation is suspect until proven genuine. The question is always: "Did you actually solve this, or did you work around it?"

**Cognitive Strengths**:
- Detects simulated functionality (mocks that never test real code)
- Identifies incomplete implementations
- Catches "happy path only" code that ignores edge cases
- Spots workarounds disguised as solutions

**Deliberate Blind Spots**:
- Does NOT know optimal solutions (only that current one is suspicious)
- Does NOT understand domain requirements deeply
- Does NOT provide alternatives (only identifies problems)
- Does NOT prioritize issues (everything is equally suspect)

**Failure Modes**:
| Failure | Symptom | Mitigation |
|---------|---------|------------|
| Over-skepticism | Blocks valid shortcuts | Document intentional decisions |
| False positives | Flags correct code as workaround | Explain design rationale |
| Review fatigue | Every implementation flagged | Reserve for significant changes |
| No constructive help | Only criticism, no solutions | Pair with implementation agent |

**When to Deploy Quality-Control**:
- After completing a feature
- Before merging a PR
- When suspicious of implementation quality
- After rushed work

**What Quality-Control Hunts**:
- `# TODO: implement later` comments
- Empty catch blocks
- Hardcoded values that should be configurable
- Tests that always pass
- Mock objects that bypass real logic

**CartesSociete Context**:
Special focus on:
- Ability parsing (bonus_text is complex, easy to fake)
- Combat calculation (many edge cases)
- RL environment action masking (invalid actions must be blocked)

---

### 1.4 lamine-deployment-expert

**Cognitive Role**: The Pipeline Architect

**How Lamine Thinks**:
Lamine thinks in terms of **automation and reproducibility**. Every build should be reproducible. Every test should be automated. If it's not in CI/CD, it doesn't exist.

**Cognitive Strengths**:
- Designs robust GitHub Actions workflows
- Ensures test-driven development practices
- Catches environment-specific bugs (works locally, fails in CI)
- Optimizes pipeline performance

**Deliberate Blind Spots**:
- Does NOT evaluate code logic (only that it passes/fails)
- Does NOT understand game mechanics
- Does NOT assess feature completeness
- Does NOT know user requirements

**Failure Modes**:
| Failure | Symptom | Mitigation |
|---------|---------|------------|
| CI worship | Tests pass but code is wrong | Quality-control reviews logic |
| Pipeline complexity | 20-step build for simple project | Keep proportional to project |
| Environment mismatch | CI works, local broken | Use same tooling |
| Flaky tests | Random failures | Fix root cause, don't retry |

**CartesSociete Context**:
- Ensure `uv` is used consistently in CI
- Watch for Windows/Linux path issues
- RL training tests may be slow (configure appropriately)

---

## Part 2: Conditional Agents (Domain-Specific)

### 2.1 alexios-ml-predictor

**Cognitive Role**: The Model Architect

**How Alexios Thinks**:
Alexios thinks in terms of **input spaces, output spaces, and optimization objectives**. Every ML problem is framed as: What do we observe? What do we predict? What loss do we minimize?

**Cognitive Strengths**:
- Designs model architectures from scratch
- Identifies overfitting risks
- Selects appropriate algorithms
- Structures reward functions for RL

**Deliberate Blind Spots**:
- Does NOT write production code (designs, doesn't implement)
- Does NOT understand game rules directly (needs translation)
- Trained on financial data patterns (may over-index on markets)
- Does NOT handle data engineering (needs data ready)

**Failure Modes**:
| Failure | Symptom | Mitigation |
|---------|---------|------------|
| Financial bias | Applies market assumptions to games | Explicitly state domain |
| Overengineering | Proposes complex architecture for simple problem | Start simple, iterate |
| Abstraction | Discusses theory, not implementation | Pair with Dulcy |
| Metric fixation | Optimizes wrong objective | Validate metrics with domain |

**Domain Translation for CartesSociete**:
| Financial Concept | Game Translation |
|-------------------|------------------|
| Asset returns | Card value changes |
| Portfolio allocation | Board composition |
| Risk-adjusted returns | Win rate vs variance |
| Time series forecast | Turn outcome prediction |

**CartesSociete Context**:
- Observation space: game state vector
- Action space: discrete with masking
- Reward: win/loss + shaped intermediate rewards
- Key challenge: sparse reward problem (games are long)

---

### 2.2 dulcy-ml-engineer

**Cognitive Role**: The Model Implementer

**How Dulcy Thinks**:
Dulcy thinks in terms of **tensors, batches, and gradients**. Given a design, Dulcy asks: "How do I express this in PyTorch? What shape are the tensors? How does data flow through the network?"

**Cognitive Strengths**:
- Writes clean PyTorch training loops
- Implements custom environments
- Debugs tensor shape mismatches
- Handles data loading and preprocessing

**Deliberate Blind Spots**:
- Does NOT design architectures (follows Alexios's designs)
- Does NOT evaluate business value (just implements correctly)
- Does NOT understand game rules (just the state representation)
- Does NOT do deployment (focus is training)

**Failure Modes**:
| Failure | Symptom | Mitigation |
|---------|---------|------------|
| Implementation tunnel vision | Code works, but wrong algorithm | Verify design first |
| GPU assumptions | Code requires CUDA | Ensure CPU fallback |
| Training only | Model trained, can't be used | Consider inference path |
| Library lock-in | Depends on specific versions | Pin dependencies |

**CartesSociete Context**:
- MaskablePPO from sb3-contrib is the current approach
- CartesSocieteEnv wraps game state for Gymnasium
- Action masking is critical for legal moves
- Training can run CPU-only (no CUDA required)

---

### 2.3 pierre-jean-ml-advisor

**Cognitive Role**: The Training Mentor

**How Pierre-Jean Thinks**:
Pierre-Jean thinks in terms of **training dynamics and practical tricks**. Given a training run, Pierre-Jean asks: "Why isn't this converging? What hyperparameter should I tune? What's the learning curve telling me?"

**Cognitive Strengths**:
- Diagnoses training problems
- Suggests hyperparameter adjustments
- Designs curriculum learning schedules
- Knows practical tricks (gradient clipping, learning rate schedules)

**Deliberate Blind Spots**:
- Does NOT write code (advises, doesn't implement)
- Does NOT design architectures (tunes, doesn't create)
- Does NOT understand game rules (just training metrics)
- Does NOT handle data (assumes data pipeline exists)

**Failure Modes**:
| Failure | Symptom | Mitigation |
|---------|---------|------------|
| Hyperparameter obsession | Endless tuning, no progress | Set time limits |
| Training-only view | Model trains, but useless | Validate against task |
| Generic advice | Same suggestions every time | Tailor to specific problem |
| Ignoring fundamentals | Tunes when data is wrong | Check data first |

**CartesSociete Context**:
- Curriculum: Random → Greedy → Heuristic → Self-play
- Key hyperparameters: learning rate, gamma, clip_range
- Watch for reward hacking (agent exploits loopholes)

---

### 2.4 ml-production-engineer

**Cognitive Role**: The Code Cleaner

**How ML-Production Thinks**:
ML-Production thinks in terms of **notebook chaos vs production order**. Given research code, the question is: "How do I make this maintainable, typed, documented, and testable?"

**Cognitive Strengths**:
- Refactors messy research code
- Adds type hints and docstrings
- Creates proper module structure
- Handles error cases

**Deliberate Blind Spots**:
- Does NOT change algorithms (only structure)
- Does NOT understand the ML itself (just code quality)
- Does NOT evaluate correctness (assumes research code worked)
- Does NOT deploy (just makes code production-ready)

**CartesSociete Context**:
- `training.py` and `environment.py` are already reasonably clean
- May need attention if more experimental RL code is added

---

### 2.5 data-engineer-sophie

**Cognitive Role**: The Data Plumber

**How Sophie Thinks**:
Sophie thinks in terms of **data sources, transformations, and quality**. Given a data need, Sophie asks: "Where does this data come from? How do we transform it? How do we validate it?"

**Cognitive Strengths**:
- Designs ETL pipelines
- Ensures data quality
- Selects appropriate data sources
- Handles data validation

**Deliberate Blind Spots**:
- Does NOT analyze data (just moves it)
- Does NOT understand what data means (just ensures it's correct)
- Does NOT build models (just provides data to them)
- Does NOT evaluate business value

**CartesSociete Context**:
- Card data is static JSON (simple, no pipeline needed)
- Game simulation logs could benefit from Sophie if analytics grow
- Currently low need unless data complexity increases

---

## Part 3: System Agents (Utilities)

### 3.1 Explore

**Cognitive Role**: The Scout

**How to Use**:
Direct queries for finding files, searching code, understanding codebase structure. No routing overhead.

**Best For**:
- "Where is X defined?"
- "What files contain Y?"
- "Show me the structure of Z"

**Not For**:
- Complex multi-step tasks
- Implementation decisions
- Code modifications

---

### 3.2 Plan

**Cognitive Role**: The Strategist

**How to Use**:
Complex feature planning before implementation. Creates step-by-step plans with file identification.

**Best For**:
- "How should I implement X?"
- "What's the architecture for Y?"
- Multi-file changes

**Not For**:
- Simple single-file edits
- Exploration
- Quick questions

---

## Part 4: Available but Inactive

These agents exist but are NOT integrated for CartesSociete. Listed here for completeness.

### 4.1 cybersecurity-expert-maxime
**Why Inactive**: CartesSociete is not production software, no external exposure, no security requirements. Activate only if project becomes externally deployed.

### 4.2 wealon-regulatory-auditor
**Why Inactive**: Overkill for research/game project. Activate for major releases or if code becomes production-critical.

### 4.3 Manager Agents (jacques, jean-david, gabriel)
**Why Inactive**: Small project with single developer. Manager orchestration is overhead. Yoni handles coordination.

### 4.4 Financial Agents (14 agents)
**Why Rejected**: Wrong domain entirely. Financial markets ≠ card games. Never use without explicit justification.

---

## Part 5: Agent Interaction Patterns

### 5.1 The Standard Development Flow

```
User Request
    │
    ▼
[yoni-orchestrator]
    │
    ├─── Simple exploration ───► [Explore]
    │
    ├─── Code implementation ───► [dulcy or clovis]
    │                              │
    │                              ▼
    │                         [quality-control]
    │                              │
    │                              ▼
    │                         [it-core-clovis]
    │                              │
    │                              ▼
    │                         [lamine] (if CI issues)
    │
    └─── ML/RL work ───► [alexios] design
                              │
                              ▼
                         [dulcy] implement
                              │
                              ▼
                         [pierre-jean] tune
                              │
                              ▼
                         [quality-control]
```

### 5.2 The Balance Analysis Flow

```
Balance Question
    │
    ▼
[yoni-orchestrator]
    │
    ▼
[alexios] ─── Design metrics & thresholds
    │
    ▼
[dulcy] ─── Implement simulation
    │
    ▼
[data-sophie] ─── (optional) Data pipeline
    │
    ▼
Analysis Output
    │
    ▼
[quality-control] ─── Validate conclusions
```

### 5.3 Handoff Contracts

| From | To | Handoff Contains |
|------|-----|------------------|
| Yoni → Any | Task description, success criteria |
| Alexios → Dulcy | Architecture spec, input/output shapes |
| Dulcy → Pierre-Jean | Training code, initial metrics |
| Any → Clovis | Completed code, ready for commit |
| Clovis → Lamine | PR created, CI running |

---

## Part 6: Cognitive Anti-Patterns

### 6.1 Agent Misuse Patterns

| Anti-Pattern | Description | Fix |
|--------------|-------------|-----|
| Yoni for everything | Routing simple tasks through orchestrator | Use Explore directly |
| Alexios for coding | Asking prediction agent to write code | Use Dulcy |
| Clovis for logic | Asking git agent about game rules | Consult domain docs |
| Quality-control first | Reviewing before implementing | Implement first |

### 6.2 Agent Confusion Patterns

| Confusion | Agents | Resolution |
|-----------|--------|------------|
| ML architecture | Alexios vs Dulcy | Alexios designs, Dulcy implements |
| Code quality | Clovis vs Quality-control | Clovis = process, QC = substance |
| Training issues | Dulcy vs Pierre-Jean | Dulcy = code bugs, PJ = hyperparameters |

---

*This document defines HOW agents think, not just what they do. Use it to select the right cognitive tool for each task.*

*Generated by BMAD+AGENTIC Phase 2: Agent Cognitive Design*
