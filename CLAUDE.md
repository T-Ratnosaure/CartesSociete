# CLAUDE.md - CartesSociete

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
**READ THIS FILE CAREFULLY. RESPECT ALL INSTRUCTIONS.**

---

## Project Overview

**CartesSociete** is a project for designing solutions for a cardboard/card game. The project focuses on:

- **Game mechanics design** - Card interactions, rules, balance
- **Strategy optimization** - Optimal plays, probability analysis
- **Simulation & testing** - Game state simulation, Monte Carlo analysis
- **Balance analysis** - Card power levels, win rates, fairness

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

### Code Quality
```bash
# Import sorting (AUTHORITATIVE - run first)
uv run isort .

# Code formatting
uv run ruff format .

# Linting
uv run ruff check .

# Type checking
uv run pyrefly check

# Run tests
uv run pytest
```

---

## Project Structure

```
CartesSociete/
├── src/                   # Main source code
│   ├── cards/            # Card definitions and types
│   ├── game/             # Game engine and rules
│   ├── players/          # Player strategies and AI
│   ├── simulation/       # Game simulation tools
│   └── analysis/         # Balance and statistics analysis
├── tests/                # Test suite
├── data/                 # Card data, game logs
├── notebooks/            # Analysis notebooks
├── configs/              # Game configuration files
└── scripts/              # CLI scripts
```

---

## Multi-Agent Architecture

### MANDATORY WORKFLOW

**These rules are NON-NEGOTIABLE. Failure to follow them is unacceptable.**

1. **ALWAYS CALL YONI FIRST**
   - **FOR EVERY USER REQUEST**, you MUST call `yoni-orchestrator` via the Task tool
   - Yoni coordinates all specialized agents and creates execution plans
   - **NEVER** try to handle complex tasks yourself - delegate to experts

2. **ALWAYS USE SPECIALIZED AGENTS**
   - Launch multiple agents in parallel when tasks are independent
   - Trust agent outputs - they are domain experts

### Primary Agents for This Project

| Agent | Specialty | When to Call |
|-------|-----------|--------------|
| **yoni-orchestrator** | Task coordination | **EVERY user request** - call FIRST |
| **alexios-ml-predictor** | ML/optimization | Balance analysis, win rate prediction |
| **it-core-clovis** | Code quality | Git workflow, PR review, code optimization |
| **quality-control-enforcer** | Quality assurance | Review implementations, catch shortcuts |
| **lamine-deployment-expert** | CI/CD & TDD | Pipelines, testing infrastructure |

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
2. **NEVER** create PRs without review agents

---

**Remember: ALWAYS call yoni-orchestrator FIRST for every user request!**
