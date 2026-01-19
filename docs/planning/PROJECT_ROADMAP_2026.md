# CartesSociete Project Roadmap 2026

**Version**: 1.0
**Created**: 2026-01-19
**Author**: Yoni (Master Orchestrator)
**Governance**: Aligned with Baseline v1.0

---

## Executive Vision

Transform CartesSociete from a functional card game simulation into a **comprehensive balance analysis platform** that helps game designers make data-driven decisions about card design.

### Strategic Goals

1. **Train competitive RL agent** that surpasses HeuristicPlayer
2. **Generate actionable balance insights** from simulation data
3. **Expand player strategy library** for meta-game analysis
4. **Maintain governance compliance** throughout development

---

## Quarter 1: Foundation Completion (Jan - Mar 2026)

### Q1 Theme: "Complete What We Started"

#### Sprint 1.1 (Jan 20 - Feb 2)
**Focus**: Housekeeping and Technical Debt

| Task | Owner | Priority | Est. Hours |
|------|-------|----------|------------|
| Commit untracked files (lapin_player.py, analysis scripts) | Clovis | HIGH | 1 |
| Update rl-research-plan.md with current status | Yoni | MEDIUM | 2 |
| Document Lapin player strategy | Human | MEDIUM | 3 |
| Add unknown pattern detection to abilities.py | Dulcy | HIGH | 4 |

**Definition of Done**:
- All files tracked in git
- No modified-but-uncommitted files
- RL research plan reflects current state
- Wealon exit audit completed (AG-02)

#### Sprint 1.2 (Feb 3 - Feb 16)
**Focus**: RL Training Phase 1

| Task | Owner | Priority | Est. Hours |
|------|-------|----------|------------|
| Complete RL curriculum Stage 1 (vs Random) | Alexios/Dulcy | HIGH | 8 |
| Implement training checkpointing | Dulcy | HIGH | 4 |
| Create evaluation framework | Dulcy | MEDIUM | 4 |
| Run 1000-game baseline metrics | Lamine | MEDIUM | 2 |

**Success Criteria**:
- PPO agent achieves >70% win rate vs RandomPlayer
- Training logs captured in TensorBoard
- Checkpoints saved every 10k steps
- Wealon exit audit completed (AG-02)

#### Sprint 1.3 (Feb 17 - Mar 2)
**Focus**: RL Training Phase 2

| Task | Owner | Priority | Est. Hours |
|------|-------|----------|------------|
| RL curriculum Stage 2 (vs Greedy) | Alexios/Dulcy | HIGH | 8 |
| Analyze failure modes | Pierre-Jean | MEDIUM | 4 |
| Tune hyperparameters if needed | Pierre-Jean | MEDIUM | 4 |
| Document training insights | Yoni | LOW | 2 |

**Success Criteria**:
- PPO agent achieves >60% win rate vs GreedyPlayer
- Identified any architecture issues
- Hyperparameter decisions documented
- Wealon exit audit completed (AG-02)

#### Sprint 1.4 (Mar 3 - Mar 16)
**Focus**: RL Training Phase 3

| Task | Owner | Priority | Est. Hours |
|------|-------|----------|------------|
| RL curriculum Stage 3 (vs Heuristic) | Alexios/Dulcy | HIGH | 12 |
| Implement opponent scheduling | Dulcy | MEDIUM | 4 |
| Evaluate convergence | Pierre-Jean | MEDIUM | 4 |

**Success Criteria**:
- PPO agent achieves >50% win rate vs HeuristicPlayer
- Training stable (no divergence)
- Performance documented
- Wealon exit audit completed (AG-02)

#### Sprint 1.5 (Mar 17 - Mar 31)
**Focus**: Q1 Review and Balance Analysis Prep

| Task | Owner | Priority | Est. Hours |
|------|-------|----------|------------|
| Q1 review and documentation | Yoni | HIGH | 4 |
| Prepare balance analysis infrastructure | Dulcy | MEDIUM | 6 |
| Run comprehensive game statistics | Lamine | MEDIUM | 4 |
| Human review of RL strategies | Human | HIGH | 4 |

**Q1 Exit Criteria**:
- RL agent competitive with HeuristicPlayer
- Training infrastructure stable
- Balance analysis infrastructure ready
- All work reviewed by Wealon

---

## Quarter 2: Balance Analysis Platform (Apr - Jun 2026)

### Q2 Theme: "Data-Driven Insights"

#### Phase 2.1: Large-Scale Simulation (Apr 1 - Apr 30)

| Deliverable | Description |
|-------------|-------------|
| 10,000-game dataset | Mixed opponent matchups |
| Per-card statistics | Pick rate, win correlation |
| Per-family metrics | Family win rates |
| Per-class metrics | Class effectiveness |

**Human Checkpoint Required**: Review raw statistics before interpretation

#### Phase 2.2: Insight Generation (May 1 - May 31)

| Analysis | Owned By | Output |
|----------|----------|--------|
| Outlier card detection | Alexios | List of statistically abnormal cards |
| Family balance report | Alexios | Family comparison with confidence intervals |
| Cost curve analysis | Alexios | Cost efficiency metrics |
| Evolution impact study | Alexios | Pre/post evolution performance |

**Human Checkpoint Required**: Interpret findings, approve recommendations

#### Phase 2.3: Reporting and Visualization (Jun 1 - Jun 30)

| Deliverable | Description |
|-------------|-------------|
| Balance dashboard | Interactive metrics display |
| Card tier list | Human-approved ranking |
| Data reports | Metrics and analysis for human-driven change decisions |
| Q2 summary report | Complete analysis document |

**Q2 Exit Criteria**:
- Balance analysis complete for all cards
- Human-reviewed recommendations generated
- Dashboard operational
- All work reviewed by Wealon

---

## Quarter 3: Strategy Expansion (Jul - Sep 2026)

### Q3 Theme: "Meta-Game Exploration"

#### Phase 3.1: New Player Strategies (Jul - Aug)

| Strategy | Description | Complexity |
|----------|-------------|------------|
| AggroPlayer | Fast damage, early game | MEDIUM |
| ControlPlayer | Denial, late game | HIGH |
| ComboPlayer | Synergy-focused | HIGH |
| MixedPlayer | Adaptive strategy | VERY HIGH |

**Human Approval Required**: Strategy definitions before implementation

#### Phase 3.2: Meta-Game Analysis (Sep)

| Analysis | Description |
|----------|-------------|
| Rock-Paper-Scissors mapping | Strategy counter relationships |
| Nash equilibrium search | Stable strategy mixtures |
| Strategy diversity metrics | Meta-game health indicators |

**Q3 Exit Criteria**:
- 3+ new competitive strategies
- Meta-game report generated
- Strategy documentation complete

---

## Quarter 4: Platform Maturity (Oct - Dec 2026)

### Q4 Theme: "Production Readiness"

#### Phase 4.1: Code Maturity (Oct)

| Task | Description |
|------|-------------|
| abilities.py refactor | Split into smaller modules |
| Comprehensive test expansion | 90%+ coverage |
| Performance optimization | Sub-second game simulation |

#### Phase 4.2: Documentation (Nov)

| Document | Purpose |
|----------|---------|
| API reference | Complete code documentation |
| User guide | How to use the platform |
| Balance methodology | How analysis works |

#### Phase 4.3: Year Review (Dec)

| Activity | Description |
|----------|-------------|
| 2026 retrospective | What worked, what didn't |
| 2027 planning | Next year roadmap |
| Knowledge transfer | Ensure continuity |

**Q4 Exit Criteria**:
- Production-quality codebase
- Complete documentation
- 2027 roadmap approved

---

## Governance Compliance

### Throughout All Quarters

| Requirement | How Addressed |
|-------------|---------------|
| Yoni-first workflow | All tasks routed through orchestrator |
| Wealon exit gate | Every sprint reviewed by auditor |
| Human checkpoints | Marked explicitly above |
| Baseline v1.0 | No scope expansion into game design |

### Breaking Change Watch List

These would require v2.0 governance process:
- Any agent claiming to understand game rules
- Automated balance change recommendations
- Removal of human checkpoints
- Integration of financial agents

---

## Success Metrics

### End of 2026 Goals

| Metric | Target |
|--------|--------|
| RL agent win rate vs Heuristic | > 55% |
| Card balance metrics collected | 100% of cards have metrics for human interpretation |
| Strategy diversity | 6+ competitive strategies |
| Test coverage | > 90% |
| Documentation completeness | All public APIs documented |

### Health Indicators

| Indicator | Healthy Range |
|-----------|---------------|
| Test pass rate | > 99% |
| Human escalation rate | < 5 game questions/week |
| Technical debt items | < 10 open items |
| Audit findings | 0 critical, < 3 major |

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| RL training fails to converge | MEDIUM | HIGH | Curriculum learning, expert consultation |
| Balance analysis inconclusive | LOW | MEDIUM | Larger sample sizes, human interpretation |
| Key contributor unavailable | LOW | HIGH | Documentation, knowledge transfer |
| Governance drift | LOW | MEDIUM | Wealon audits, baseline enforcement |

---

## Resource Requirements

### Compute
- Training: 8+ CPU cores, optional GPU
- Storage: ~5GB for checkpoints and logs
- Time: ~100 hours total training time over year

### Human Time
- Game design questions: ~2-4 hours/month
- Checkpoint reviews: ~4 hours/quarter
- Balance interpretation: ~8 hours/quarter

---

## Approval

This roadmap is proposed for 2026. Human approval required before execution.

**Status**: PROPOSED
**Requires**: Human acknowledgment

```
- [ ] I approve this roadmap
- [ ] I will provide human checkpoints as marked
- [ ] I understand governance compliance requirements
- [ ] I accept resource requirements

Signature: ____________________
Date: ____________________
```

---

*Document created by BMAD Planning Process*
*Governed by Baseline v1.0*
