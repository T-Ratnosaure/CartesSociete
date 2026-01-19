# Agent Relevance Matrix - CartesSociete

**Document Version**: 1.0
**Created**: 2026-01-19
**Phase**: BMAD Planning - Phase 3

---

## Classification Legend

| Category | Description |
|----------|-------------|
| **Primary** | Core agents, always available for this project |
| **Conditional** | Allowed under specific constraints |
| **System** | Tooling/meta agents for exploration and planning |
| **Available but Inactive** | Could be useful but not currently integrated |
| **Explicitly Rejected** | Wrong domain, do not use |

---

## Agent Relevance Table

| Agent | Domain | Relevance | Rationale | Risks | Conditions |
|-------|--------|-----------|-----------|-------|------------|
| **yoni-orchestrator** | Coordination | **Primary** | Master orchestrator for all requests | None | Call first for every request |
| **it-core-clovis** | Code Quality | **Primary** | Git workflow, PR review, code optimization - essential for any Python project | None | Before commits and PRs |
| **quality-control-enforcer** | QA | **Primary** | Catches shortcuts in game logic, validates implementations | None | After feature completion |
| **lamine-deployment-expert** | CI/CD | **Primary** | Project has GitHub Actions CI; TDD important for game rules | None | Pipeline changes, test infrastructure |
| **alexios-ml-predictor** | ML/Prediction | **Conditional** | RL agent training, balance prediction; needs adaptation from financial to game domain | May suggest financial patterns | When working on RL training, balance analysis |
| **dulcy-ml-engineer** | ML Engineering | **Conditional** | PPO implementation, training pipelines, gymnasium integration | None | RL infrastructure work |
| **pierre-jean-ml-advisor** | ML Guidance | **Conditional** | PPO hyperparameter tuning, curriculum learning advice | None | Training optimization questions |
| **ml-production-engineer** | ML Productionization | **Conditional** | Transform RL research notebooks into production-ready player agents | None | Research-to-production transitions |
| **data-engineer-sophie** | Data Engineering | **Conditional** | Card data pipelines, statistics aggregation if complexity grows | May be overkill | Complex data pipeline work |
| **Explore** | Codebase | **System** | Fast codebase exploration, file searches | None | Codebase questions |
| **Plan** | Planning | **System** | Implementation strategy design | None | Complex feature planning |
| **general-purpose** | Multi-purpose | **System** | Complex multi-step research | None | When specialized agents don't fit |
| **claude-code-guide** | Meta/Tooling | **System** | Claude Code usage questions | None | Tooling questions only |
| **cybersecurity-expert-maxime** | Security | **Available but Inactive** | Not production software; no external APIs | Overhead | Only if exposing externally |
| **wealon-regulatory-auditor** | Audit | **Available but Inactive** | Research code, less critical than production | Heavy process | Major releases only |
| **jean-david-it-core-manager** | IT Management | **Available but Inactive** | Small project, direct agent use preferred | Overhead | Only if team coordination needed |
| **jacques-head-manager** | Multi-team | **Available but Inactive** | No multi-team structure | N/A | Not applicable |
| **gabriel-task-orchestrator** | Task Orchestration | **Available but Inactive** | Yoni handles coordination; simpler workflows | Overlap | Only for complex dependencies |
| **data-research-liaison** | Communication | **Available but Inactive** | No separate teams | N/A | Not applicable |
| **backtester-agent** | Backtesting | **Available but Inactive** | Could adapt for strategy comparison, but simulation already exists | Requires adaptation | Consider for advanced strategy testing |
| **antoine-nlp-expert** | NLP | **Explicitly Rejected** | Card text is structured JSON, not free-form language | Would misapply NLP | **Do not use** |
| **research-remy-stocks** | Stocks | **Explicitly Rejected** | Financial markets, not card games | Wrong domain | **Do not use** |
| **iacopo-macro-futures-analyst** | Macro/Futures | **Explicitly Rejected** | Economics, not game design | Wrong domain | **Do not use** |
| **nicolas-risk-manager** | Financial Risk | **Explicitly Rejected** | VaR, position limits - not applicable | Wrong domain | **Do not use** |
| **victor-pnl-manager** | PnL | **Explicitly Rejected** | Profit/loss attribution - not applicable | Wrong domain | **Do not use** |
| **pnl-validator** | PnL | **Explicitly Rejected** | PnL automation - not applicable | Wrong domain | **Do not use** |
| **trading-execution-engine** | Trading | **Explicitly Rejected** | Order execution - not applicable | Wrong domain | **Do not use** |
| **cost-optimizer-lucas** | Cost | **Explicitly Rejected** | Financial cost focus | Wrong domain | **Do not use** |
| **french-tax-optimizer** | Tax | **Explicitly Rejected** | Taxation - not applicable | Wrong domain | **Do not use** |
| **helena-execution-manager** | Trading Execution | **Explicitly Rejected** | Trade execution - not applicable | Wrong domain | **Do not use** |
| **portfolio-manager-jean-yves** | Portfolio | **Explicitly Rejected** | Portfolio management - not applicable | Wrong domain | **Do not use** |
| **legal-team-lead** | Legal | **Explicitly Rejected** | No legal/regulatory requirements | Wrong domain | **Do not use** |
| **legal-compliance-reviewer** | Compliance | **Explicitly Rejected** | Financial compliance - not applicable | Wrong domain | **Do not use** |

---

## Agent Overlap Analysis

### ML/AI Agent Overlap

| Use Case | Preferred Agent | Rationale |
|----------|-----------------|-----------|
| RL Architecture Design | **alexios-ml-predictor** | Deep ML expertise for PPO design |
| Training Pipeline Implementation | **dulcy-ml-engineer** | PyTorch/training loop specialist |
| Hyperparameter Tuning | **pierre-jean-ml-advisor** | Practical tuning advice |
| Research-to-Production | **ml-production-engineer** | Code quality for production |

**Resolution**: Use based on task type. Alexios for design decisions, Dulcy for implementation, Pierre-Jean for optimization, ML-Production-Engineer for cleanup.

### Quality Agent Overlap

| Use Case | Preferred Agent | Rationale |
|----------|-----------------|-----------|
| Git Workflow | **it-core-clovis** | Branch management specialist |
| PR Review | **it-core-clovis** | Code review expert |
| Implementation Validation | **quality-control-enforcer** | Catches shortcuts and workarounds |

**Resolution**: Clovis for git/PR, Quality-Control for implementation review.

---

## Domain Mapping

| CartesSociete Domain | Primary Agent(s) | Conditional Agent(s) |
|---------------------|------------------|----------------------|
| Game Engine Development | it-core-clovis, quality-control | - |
| RL/AI Training | alexios, dulcy | pierre-jean |
| Balance Analysis | alexios | data-engineer-sophie |
| Simulation/Statistics | - | data-engineer-sophie |
| CI/CD Pipeline | lamine-deployment | - |
| Codebase Exploration | Explore | general-purpose |

---

## Recommendations Summary

### MUST USE
1. **yoni-orchestrator** - Every request
2. **it-core-clovis** - Git workflow, PRs
3. **quality-control-enforcer** - Feature validation

### SHOULD USE
4. **lamine-deployment-expert** - CI/CD changes
5. **alexios-ml-predictor** - RL work (adapt guidance)
6. **dulcy-ml-engineer** - Training pipelines

### MAY USE
7. **pierre-jean-ml-advisor** - Hyperparameter questions
8. **ml-production-engineer** - Research cleanup
9. **data-engineer-sophie** - Complex data flows
10. **Explore/Plan/general-purpose** - As needed

### DO NOT USE
All financial domain agents (14 agents explicitly rejected)

---

*This matrix informs the architecture design in Phase 4.*
