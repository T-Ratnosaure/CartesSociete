# Agent Evolution Plan - CartesSociete

**Document Version**: 1.0
**Created**: 2026-01-19
**Phase**: BMAD Forward Design - Phase 6

---

## Overview

This document defines how the agent ecosystem will evolve over time, including observability requirements, audit triggers, and promotion/removal criteria.

---

## Current State

### Active Agent Count
| Category | Count |
|----------|-------|
| Primary | 4 |
| Conditional | 5 |
| System | 4 |
| **Total Active** | **13** |

### Utilization Baseline (To Be Tracked)
| Agent | Expected Usage Frequency |
|-------|-------------------------|
| yoni-orchestrator | Every request |
| it-core-clovis | Every PR/commit |
| quality-control-enforcer | After features |
| lamine-deployment-expert | Weekly |
| alexios-ml-predictor | During RL work |
| dulcy-ml-engineer | During RL work |
| Explore | Daily |

---

## Observability Gaps

### Gap 1: Agent Invocation Tracking
- **Current**: No tracking of which agents are invoked
- **Target**: Log all agent invocations with timestamps
- **Priority**: Medium (useful for optimization)

### Gap 2: Agent Effectiveness Metrics
- **Current**: No measurement of agent value-add
- **Target**: Track task completion rates, user overrides
- **Priority**: Low (qualitative feedback sufficient initially)

### Gap 3: Cross-Agent Coordination
- **Current**: Manual via Yoni
- **Target**: Understand bottlenecks in multi-agent flows
- **Priority**: Low (simple workflows currently)

---

## Performance Blind Spots

### Blind Spot 1: ML Agent Domain Adaptation
- **Issue**: Alexios is designed for financial ML, not game ML
- **Risk**: May suggest inappropriate patterns
- **Mitigation**: User must adapt recommendations
- **Future**: Consider game-specific ML agent if patterns emerge

### Blind Spot 2: RL Training Validation
- **Issue**: No agent specifically validates RL training quality
- **Risk**: Overfitting, reward hacking may go undetected
- **Mitigation**: Manual monitoring, standard RL practices
- **Future**: Consider RL validation specialist if needed

### Blind Spot 3: Game Balance Interpretation
- **Issue**: No domain expert for card game balance
- **Risk**: Statistical analysis without game design context
- **Mitigation**: User provides game design expertise
- **Future**: Could add game-balance specialist if project scales

---

## Future Domains

### Likely to Appear
| Domain | Probability | Trigger | Agent Implication |
|--------|-------------|---------|-------------------|
| Multi-player support (3-5 players) | High | After 2-player stable | None - existing agents sufficient |
| New card families | High | Game expansion | None - data engineering only |
| Web UI for visualization | Medium | If sharing results | cybersecurity-expert-maxime activation |
| API for external tools | Medium | If integrating | cybersecurity-expert-maxime activation |
| Continuous training | Low | If RL matures | ML agent workflow expansion |

### Unlikely
| Domain | Why Unlikely | Agent Implication |
|--------|--------------|-------------------|
| Financial integration | Not a trading project | N/A |
| Legal/compliance | No regulatory exposure | N/A |
| Production deployment | Research tool | N/A |

---

## Evolution Triggers

### Agent Audit Triggers

| Trigger | Action |
|---------|--------|
| Agent unused for 30+ days | Review for removal |
| Agent frequently bypassed | Review effectiveness |
| New project domain emerges | Review agent coverage |
| User complaints about agent | Investigate and adjust |
| Major feature addition | Review agent alignment |

### Agent Promotion Triggers

| Trigger | From | To | Action |
|---------|------|----|---------
| Regular use of conditional agent | Conditional | Consider Primary | Document pattern, update AGENTS.md |
| Inactive agent needed 3+ times | Inactive | Conditional | Activate with conditions |
| New capability matches need | N/A | Add new | Follow addition process |

### Agent Removal Triggers

| Trigger | Action |
|---------|--------|
| No invocations in 60 days | Move to Inactive |
| Consistently poor guidance | Document issues, consider removal |
| Domain no longer relevant | Move to Rejected |
| Better alternative available | Document transition |

---

## Quarterly Review Process

### Review Checklist

```markdown
## Agent Ecosystem Quarterly Review - Q[X] 20XX

### 1. Usage Analysis
- [ ] Review agent invocation logs (if available)
- [ ] Identify most/least used agents
- [ ] Note any agents never invoked

### 2. Effectiveness Check
- [ ] Gather user feedback on agent quality
- [ ] Document any overrides or corrections
- [ ] Note any recurring agent limitations

### 3. Coverage Assessment
- [ ] List new features added this quarter
- [ ] Check if existing agents covered needs
- [ ] Identify any coverage gaps

### 4. Domain Evolution
- [ ] Note any new project directions
- [ ] Assess if Inactive agents should be activated
- [ ] Check if Rejected agents need reconsideration

### 5. Actions
- [ ] Document promotions/demotions
- [ ] Update AGENTS.md if needed
- [ ] Update this evolution plan if needed
```

---

## Conservative Principles

### Principle 1: Minimal Viable Agent Set
- Start with fewer agents
- Add only when clear need demonstrated
- Prefer human expertise over specialized agents

### Principle 2: Domain Boundaries
- Financial agents remain rejected
- Security agents remain inactive until external exposure
- Legal agents remain rejected unless regulations apply

### Principle 3: Human Authority
- User can override any agent decision
- User approval required for ecosystem changes
- Document all changes in changelog

### Principle 4: Reversibility
- All agent additions can be reversed
- All agent removals can be undone
- Maintain audit trail

---

## Risk Mitigation

### Risk: Agent Sprawl
- **Mitigation**: Strict addition criteria, quarterly reviews
- **Indicator**: Active agent count > 15

### Risk: Agent Dependency
- **Mitigation**: Maintain manual fallbacks
- **Indicator**: Tasks blocked without specific agent

### Risk: Stale Ecosystem
- **Mitigation**: Quarterly reviews, trigger-based updates
- **Indicator**: No ecosystem changes in 6+ months despite project evolution

---

## Metrics to Track (Future)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Agent invocations/week | - | Count |
| User override rate | <10% | Overrides / invocations |
| Task completion with agents | >90% | Completed / attempted |
| Time to task completion | Decreasing | Average time |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-19 | Initial evolution plan |

---

*This plan should be reviewed quarterly and updated as the project evolves.*
