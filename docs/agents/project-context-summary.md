# CartesSociete - Project Context Summary

**Document Version**: 1.0
**Created**: 2026-01-19
**Phase**: BMAD Analysis - Phase 1

---

## Project Type

**Domain**: Game Design & Simulation
**Subtype**: Card Game Engine + AI Strategy Research

CartesSociete is a comprehensive card game design and simulation platform for a tactical card game. It encompasses:

1. **Game Engine** - Full game loop with combat, market, abilities, and state management
2. **AI Research** - Multiple player strategies including RL-based agents
3. **Balance Analysis** - Card statistics tracking and balance metrics
4. **Simulation Tools** - Tournament runners and statistical analysis

---

## Core Domains

### 1. Game Engine Domain
- Card models (Creature, Weapon, Demon types)
- Combat system with damage resolution
- Market system (buying cards, deck management)
- Ability system (family abilities, class abilities, passives)
- State management (player health, board, hand, PO/currency)

### 2. AI/Player Domain
- Abstract `Player` base class for all agents
- RandomPlayer (baseline)
- GreedyPlayer (value-based)
- HeuristicPlayer (rule-based with evolution tracking)
- MCTSPlayer (Monte Carlo Tree Search)
- LapinPlayer (custom strategy in development)
- **Future**: PPO/RL Agent via stable-baselines3

### 3. Reinforcement Learning Domain
- Gymnasium environment wrapper (`CartesSocieteEnv`)
- PPO training with curriculum learning
- Reward shaping for game-specific objectives
- Self-play and opponent scheduling

### 4. Analysis Domain
- Card balance metrics (pick rate, win correlation)
- Matchup analysis between strategies
- Card tracker for per-game statistics
- Balance reports and recommendations

### 5. Simulation Domain
- Match runner for batch simulations
- Tournament orchestration
- Statistics collection and aggregation
- Logging and replay

---

## Non-Goals

1. **NOT a production game** - This is a design/research tool, not a playable product
2. **NOT a web application** - No frontend, API, or deployment concerns
3. **NOT financial software** - No trading, transactions, or monetary components
4. **NOT NLP-focused** - Card text is structured data, not free-form language

---

## Risk Profile

| Risk Area | Level | Notes |
|-----------|-------|-------|
| Security | **Low** | No external APIs, no user data, local execution only |
| Compliance | **None** | No regulatory requirements |
| Data Privacy | **None** | No personal data handled |
| Financial | **None** | No financial transactions |
| ML Overfitting | **Medium** | RL agents may overfit to specific opponents |
| Code Quality | **Medium** | Research code may have shortcuts |

---

## Expected Evolution

### Short-term (Current Focus)
- Complete RL research plan implementation
- Fix GreedyPlayer evolution awareness
- Train PPO agent through curriculum
- Generate card balance reports

### Medium-term
- Expand player strategy library
- Add new card families/abilities
- Implement advanced balance metrics
- Support 3-5 player games (currently 2-player focused)

### Long-term (Potential)
- Multi-agent self-play training
- Automated balance suggestions
- Card generation/design assistance
- Game rule experimentation

---

## Technical Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.12 |
| RL Framework | stable-baselines3, gymnasium |
| Visualization | tensorboard |
| Testing | pytest, pytest-cov |
| Code Quality | ruff, isort, pre-commit |
| CI/CD | GitHub Actions |

---

## Key Files

| Component | Path |
|-----------|------|
| Game Engine | `src/game/engine.py` |
| Card Models | `src/cards/models.py` |
| Player Base | `src/players/base.py` |
| RL Environment | `src/rl/environment.py` |
| Balance Analysis | `src/analysis/balance.py` |
| Match Runner | `src/simulation/runner.py` |

---

## Stakeholder Context

- **Primary User**: Game designer iterating on card game balance
- **Secondary Users**: AI researchers testing game-playing strategies
- **Not Applicable**: End users, customers, external integrations

---

*This document informs agent selection decisions. Agents should be chosen based on these project characteristics.*
