# Available Agents Inventory

**Document Version**: 1.0
**Created**: 2026-01-19
**Phase**: BMAD Analysis - Phase 2

---

## Overview

This document enumerates ALL available agents in the environment, regardless of project relevance. Agent selection decisions are made in Phase 3.

---

## 1. Orchestrators & Managers

### yoni-orchestrator
- **Domain**: Task coordination
- **Role**: Master orchestrator for ALL user requests
- **Strengths**: Creates unified execution plans, coordinates multiple agents
- **Risks**: Overhead for simple tasks
- **Dependencies**: All other agents
- **Trigger**: EVERY user message

### jacques-head-manager
- **Domain**: Multi-team orchestration
- **Role**: High-level coordination across IT-Core, Legal, Research, Data teams
- **Strengths**: Strategic decision-making, work distribution
- **Risks**: Too heavyweight for single-domain tasks
- **Dependencies**: Team managers

### jean-david-it-core-manager
- **Domain**: IT Core team
- **Role**: Coordinates IT development tasks, manages specialized agents
- **Strengths**: Task routing, team oversight
- **Risks**: None identified
- **Dependencies**: IT-Core agents (Clovis, Lamine)

### gabriel-task-orchestrator
- **Domain**: Task prioritization
- **Role**: Global dependency management, workflow orchestration
- **Strengths**: Identifies blockers, resolves dependencies
- **Risks**: None identified
- **Dependencies**: All teams

### helena-execution-manager
- **Domain**: Trading execution
- **Role**: Trade execution coordination, backtesting oversight
- **Strengths**: Order management, execution quality
- **Risks**: Not applicable to non-trading projects
- **Dependencies**: Trading Engine, Backtester

### portfolio-manager-jean-yves
- **Domain**: Portfolio management
- **Role**: Research team lead, mathematical financial modeling
- **Strengths**: Research coordination, mathematical rigor
- **Risks**: Financial focus may not fit game projects
- **Dependencies**: Research team agents

---

## 2. ML & AI Agents

### alexios-ml-predictor
- **Domain**: Machine learning prediction
- **Role**: Design, build, optimize ML predictors
- **Strengths**: Feature engineering, model selection, time series, risk models
- **Risks**: Designed for financial data
- **Dependencies**: None

### dulcy-ml-engineer
- **Domain**: ML engineering
- **Role**: ML pipelines, model training, feature engineering
- **Strengths**: PyTorch training loops, model evaluation, data processing
- **Risks**: None identified
- **Dependencies**: None

### pierre-jean-ml-advisor
- **Domain**: ML guidance
- **Role**: Practical ML advice, fine-tuning, hyperparameter tuning
- **Strengths**: Bridges research and implementation
- **Risks**: None identified
- **Dependencies**: None

### ml-production-engineer
- **Domain**: ML productionization
- **Role**: Transform research/notebook code to production
- **Strengths**: Code refactoring, type hints, error handling
- **Risks**: None identified
- **Dependencies**: None

### antoine-nlp-expert
- **Domain**: Natural Language Processing
- **Role**: NLP solutions, transformer architectures, LLM fine-tuning
- **Strengths**: Sentiment analysis, embeddings, text processing
- **Risks**: Not applicable to structured game data
- **Dependencies**: None

---

## 3. Development & Quality

### it-core-clovis
- **Domain**: Code quality
- **Role**: Git workflow compliance, PR review, code optimization
- **Strengths**: Branch management, code review, efficiency analysis
- **Risks**: None identified
- **Dependencies**: None

### lamine-deployment-expert
- **Domain**: CI/CD and TDD
- **Role**: Deployment pipelines, GitHub Actions, test infrastructure
- **Strengths**: CI/CD debugging, deployment strategies
- **Risks**: None identified
- **Dependencies**: None

### quality-control-enforcer
- **Domain**: Quality assurance
- **Role**: Validate work quality, catch workarounds and shortcuts
- **Strengths**: Identifies incomplete implementations, simulated functionality
- **Risks**: None identified
- **Dependencies**: None

---

## 4. Security & Audit

### cybersecurity-expert-maxime
- **Domain**: Cybersecurity
- **Role**: Security assessments, vulnerability analysis, threat modeling
- **Strengths**: Secure coding, penetration testing guidance
- **Risks**: None identified
- **Dependencies**: None

### wealon-regulatory-auditor
- **Domain**: Code audit
- **Role**: Thorough audits, security vulnerabilities, dead code, tech debt
- **Strengths**: Uncompromising review, documentation
- **Risks**: May be heavy for non-production code
- **Dependencies**: None

---

## 5. Financial Domain (Low Relevance)

### research-remy-stocks
- **Domain**: Stock/equity research
- **Role**: Stock analysis, stochastic calculus, options pricing
- **Relevance to CartesSociete**: **None** - financial markets, not card games

### iacopo-macro-futures-analyst
- **Domain**: Macroeconomics
- **Role**: Futures markets, economic indicators, central bank policy
- **Relevance to CartesSociete**: **None**

### nicolas-risk-manager
- **Domain**: Risk management
- **Role**: VaR calculations, exposure monitoring, position limits
- **Relevance to CartesSociete**: **None** - financial risk

### victor-pnl-manager
- **Domain**: PnL validation
- **Role**: Profit/loss attribution, reconciliation
- **Relevance to CartesSociete**: **None**

### pnl-validator
- **Domain**: PnL automation
- **Role**: Automated PnL checks
- **Relevance to CartesSociete**: **None**

### trading-execution-engine
- **Domain**: Trade execution
- **Role**: Order generation, execution algorithms
- **Relevance to CartesSociete**: **None**

### backtester-agent
- **Domain**: Trading backtesting
- **Role**: Strategy simulation, transaction cost modeling
- **Relevance to CartesSociete**: **Partial** - could adapt for game strategy testing

### cost-optimizer-lucas
- **Domain**: Cost optimization
- **Role**: API costs, ML inference costs, transaction costs
- **Relevance to CartesSociete**: **Low** - minimal cost concerns

### french-tax-optimizer
- **Domain**: French taxation
- **Role**: Tax-efficient investment structures
- **Relevance to CartesSociete**: **None**

---

## 6. Data Engineering

### data-engineer-sophie
- **Domain**: Data pipelines
- **Role**: Data source selection, ETL, data quality
- **Strengths**: Pipeline design, data validation
- **Risks**: None identified
- **Dependencies**: None

### data-research-liaison
- **Domain**: Cross-team communication
- **Role**: Technical communication between Data and Research teams
- **Strengths**: Precise, factual reporting
- **Risks**: May be overhead for small teams
- **Dependencies**: None

---

## 7. Legal & Compliance

### legal-team-lead
- **Domain**: Legal coordination
- **Role**: Regulatory work, compliance, legal oversight
- **Relevance to CartesSociete**: **None** - no regulatory requirements

### legal-compliance-reviewer
- **Domain**: Financial compliance
- **Role**: Trading strategy compliance, securities laws
- **Relevance to CartesSociete**: **None**

---

## 8. System/Utility Agents

### Explore
- **Domain**: Codebase exploration
- **Role**: Quick file/code searches, codebase questions
- **Strengths**: Fast, thorough, multiple naming conventions
- **Risks**: None identified
- **Dependencies**: None

### Plan
- **Domain**: Implementation planning
- **Role**: Design implementation strategies, identify critical files
- **Strengths**: Architectural trade-offs, step-by-step plans
- **Risks**: None identified
- **Dependencies**: None

### general-purpose
- **Domain**: Multi-purpose
- **Role**: Research, code search, multi-step tasks
- **Strengths**: Flexible, handles complex queries
- **Risks**: May be less efficient than specialized agents
- **Dependencies**: None

### claude-code-guide
- **Domain**: Claude Code assistance
- **Role**: Answers questions about Claude Code features, hooks, settings
- **Relevance to CartesSociete**: **Meta** - for tooling questions only

---

## Governance Flags

### Undocumented Agents
- None identified. All agents have descriptions.

### Overlapping Agents
| Domain | Overlapping Agents | Resolution |
|--------|-------------------|------------|
| ML/AI | alexios, dulcy, pierre-jean | Different specializations: prediction vs engineering vs advice |
| Orchestration | yoni, jacques, gabriel | Different scopes: task vs team vs workflow |
| Code Quality | clovis, quality-control | Different focuses: git/PR vs implementation quality |

---

*This inventory informs the relevance analysis in Phase 3.*
