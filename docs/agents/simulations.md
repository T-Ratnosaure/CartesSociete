# Impact Simulations - CartesSociete Agent Ecosystem

**Version**: 1.0
**Last Updated**: 2026-01-19
**Phase**: BMAD+AGENTIC Phase 4 - Second-Order Effects

---

## Purpose

This document simulates the impact of potential changes to the agent ecosystem. Each simulation traces first-order effects (immediate), second-order effects (ripples), and third-order effects (emergent consequences).

---

## Simulation 1: Remove Yoni-Orchestrator Requirement

### Change Description
Remove the "always call Yoni first" rule. Allow direct agent invocation.

### First-Order Effects
| Effect | Impact |
|--------|--------|
| Faster simple queries | Users call Explore directly |
| Less token overhead | No orchestration layer |
| Simpler mental model | "Just call the agent you need" |

### Second-Order Effects
| Effect | Impact |
|--------|--------|
| Wrong agent selection | Users don't know which agent fits |
| Missed coordination | Multi-agent tasks become fragmented |
| Duplicate work | Two agents do same thing |
| Context loss | Agents don't know what others did |

### Third-Order Effects
| Effect | Impact |
|--------|--------|
| User frustration | "Why did that fail?" |
| Agent blame | "Agent X is bad" when routing was bad |
| Ecosystem distrust | Users avoid agents entirely |

### Simulation Verdict
**DO NOT IMPLEMENT**: Second-order effects outweigh first-order gains. However, document exceptions (Explore direct use) to capture the valid first-order benefit.

### Mitigated Alternative
Keep Yoni-first rule but document explicit exceptions:
- Single-file lookup → Explore directly
- Quick codebase question → Explore directly
- Everything else → Yoni first

---

## Simulation 2: Add Game-Mechanic-Expert Agent

### Change Description
Create a new agent persona specialized in CartesSociete game rules.

### First-Order Effects
| Effect | Impact |
|--------|--------|
| Domain expertise available | Game rule questions answered |
| Gap closure | Fills the critical gap from friction-map |
| Better balance analysis | Agent understands what balance means |

### Second-Order Effects
| Effect | Impact |
|--------|--------|
| Agent proliferation | One more agent to manage |
| Integration complexity | Where does game-expert fit in routing? |
| Maintenance burden | Must keep agent updated with rule changes |
| Overlap with Alexios | Both could claim balance analysis |

### Third-Order Effects
| Effect | Impact |
|--------|--------|
| Domain fragmentation | Game-expert vs ML-agents for balance |
| Routing confusion | Yoni doesn't know when to use game-expert |
| Persona drift | Game-expert starts doing ML work |

### Simulation Verdict
**DEFER**: The benefit is real, but the complexity cost is high. Current mitigation (documentation + human escalation) is acceptable for project size. Revisit if game rules become more complex or if human escalation becomes bottleneck.

### Mitigated Alternative
Instead of new agent, create a "game rules consultation" workflow:
1. Any agent can query project-context.md
2. Complex rule questions escalate to human
3. Answered questions update documentation

---

## Simulation 3: Replace MaskablePPO with DQN

### Change Description
Change RL algorithm from PPO to DQN for the training pipeline.

### First-Order Effects
| Effect | Impact |
|--------|--------|
| Different training dynamics | DQN is off-policy, different behavior |
| Simpler action selection | No policy network needed |
| Experience replay | Better sample efficiency |

### Second-Order Effects
| Effect | Impact |
|--------|--------|
| Action masking complexity | DQN + masking is less standard |
| Hyperparameter reset | All tuning work lost |
| Dulcy retraining | Implementation knowledge obsolete |
| Pierre-Jean retraining | Tuning advice changes |

### Third-Order Effects
| Effect | Impact |
|--------|--------|
| Comparison baseline lost | Can't compare to previous runs |
| Research direction change | Different literature to follow |
| Potential dead end | DQN may not work better |

### Simulation Verdict
**DO NOT IMPLEMENT** without clear evidence PPO is failing. The second-order cost of invalidating existing work is high. If implemented, treat as "new experiment" not "replacement."

### Mitigated Alternative
Run DQN as parallel experiment:
- Keep PPO as baseline
- Implement DQN separately
- Compare results before switching
- Preserve option to abandon DQN

---

## Simulation 4: Activate Wealon Regulatory Auditor

### Change Description
Activate wealon-regulatory-auditor for regular code audits.

### First-Order Effects
| Effect | Impact |
|--------|--------|
| Deeper code review | Catches issues Clovis/QC miss |
| Security awareness | Proactive vulnerability detection |
| Technical debt tracking | Systematic debt documentation |

### Second-Order Effects
| Effect | Impact |
|--------|--------|
| Review bottleneck | Every change needs Wealon review |
| Overlap with Quality-Control | Both review for quality |
| Audit fatigue | Too many review steps |
| False positives | Research code flagged unnecessarily |

### Third-Order Effects
| Effect | Impact |
|--------|--------|
| Development slowdown | Iteration speed drops |
| Review avoidance | Skip reviews to save time |
| Compliance theater | Reviews happen but aren't useful |

### Simulation Verdict
**PARTIALLY IMPLEMENT**: Wealon provides value but shouldn't be always-on. Use for:
- Major releases
- Before publishing code
- After security-sensitive changes

### Mitigated Implementation
```
Wealon Activation Triggers:
- Pre-release checkpoint
- External code exposure
- Authentication/security changes
- Monthly debt inventory
```

---

## Simulation 5: Strict Enforcement of Handoff Contracts

### Change Description
Require formal handoff documents for every agent-to-agent transfer.

### First-Order Effects
| Effect | Impact |
|--------|--------|
| Context preserved | No information lost in handoffs |
| Clear accountability | Who said what when |
| Audit trail | Can trace decisions |

### Second-Order Effects
| Effect | Impact |
|--------|--------|
| Documentation overhead | Every handoff needs a document |
| Bureaucracy | Process becomes heavy |
| Creative friction | Exploration slowed by paperwork |

### Third-Order Effects
| Effect | Impact |
|--------|--------|
| Document decay | Templates filled mechanically |
| Form over substance | Documents exist but aren't read |
| Agent avoidance | Skip agents to avoid handoffs |

### Simulation Verdict
**PARTIALLY IMPLEMENT**: Full enforcement is overkill. Apply to:
- Architecture decisions (Alexios → Dulcy)
- Major features
- Non-trivial changes

### Mitigated Implementation
```
Handoff Contract Required:
- New model architecture
- New game mechanic
- Changes to combat formula
- Changes to ability parsing

Handoff Contract Optional:
- Bug fixes
- Refactoring
- Test additions
- Documentation
```

---

## Simulation 6: Remove Quality-Control-Enforcer

### Change Description
Eliminate Quality-Control agent, rely only on Clovis for review.

### First-Order Effects
| Effect | Impact |
|--------|--------|
| Faster reviews | One reviewer instead of two |
| Simpler workflow | Less agents involved |
| Reduced confusion | No Clovis vs QC overlap |

### Second-Order Effects
| Effect | Impact |
|--------|--------|
| Workarounds slip through | Clovis doesn't detect fake implementations |
| False confidence | "Clovis approved" means less |
| Quality degradation | Subtle issues accumulate |

### Third-Order Effects
| Effect | Impact |
|--------|--------|
| Technical debt explosion | Shortcuts become architecture |
| Trust erosion | Code reliability drops |
| Expensive fixes | Problems found late are costly |

### Simulation Verdict
**DO NOT IMPLEMENT**: Quality-Control catches things Clovis misses by design. The overlap is intentional (process + substance). Keep both.

### Mitigated Alternative
Clarify division of labor instead of removing:
- Clovis: Process (git, format, types)
- Quality-Control: Substance (real implementation, meaningful tests)
- Sequential, not redundant

---

## Simulation 7: Add Balance-Analyst Agent Persona

### Change Description
Create agent persona specifically for game balance analysis.

### First-Order Effects
| Effect | Impact |
|--------|--------|
| Balance gap closed | Dedicated balance expertise |
| Analysis automation | Agent can propose balance changes |
| Domain-specific metrics | Understands pick rate, win correlation |

### Second-Order Effects
| Effect | Impact |
|--------|--------|
| Alexios overlap | Both do statistical analysis |
| Domain knowledge source | Where does balance-analyst learn game rules? |
| Recommendation authority | Can agent propose card changes? |

### Third-Order Effects
| Effect | Impact |
|--------|--------|
| Balance by algorithm | Removes human judgment from balance |
| Meta-gaming | Players could reverse-engineer balance agent |
| Design philosophy loss | Agent doesn't understand "fun" |

### Simulation Verdict
**DEFER**: Similar to game-mechanic-expert, the complexity cost is high. For now:
1. Alexios provides statistical interpretation
2. Human applies game design judgment
3. Document balance decision rationale

### If Implemented Later
```
Balance-Analyst Scope:
- CAN: Calculate metrics, identify outliers
- CAN: Suggest statistical targets
- CANNOT: Propose specific card changes
- CANNOT: Override human balance decisions
```

---

## Simulation 8: Enforce TDD for All Changes

### Change Description
Require Lamine-style TDD for every code change.

### First-Order Effects
| Effect | Impact |
|--------|--------|
| Higher test coverage | Everything tested |
| Regression prevention | Changes can't break existing |
| Design pressure | TDD forces better design |

### Second-Order Effects
| Effect | Impact |
|--------|--------|
| Exploration friction | Hard to TDD experimental code |
| Test maintenance | More tests to maintain |
| False security | Passing tests ≠ correct code |

### Third-Order Effects
| Effect | Impact |
|--------|--------|
| Test-first dogma | Testing becomes ritual |
| Undertested research | ML experiments skip TDD |
| Two-tier codebase | Tested core, untested experiments |

### Simulation Verdict
**PARTIALLY IMPLEMENT**: TDD valuable for core game logic, not for all code.

### Mitigated Implementation
```
TDD Required:
- Combat calculation
- Ability resolution
- State transitions
- Action legality

TDD Optional:
- RL training experiments
- Analysis scripts
- Visualization code

TDD Exempt:
- Notebooks
- One-off scripts
```

---

## Simulation 9: Integrate Financial Agents for "Balance Economics"

### Change Description
Use financial agents (Nicolas-risk-manager, etc.) for game economy analysis.

### First-Order Effects
| Effect | Impact |
|--------|--------|
| Economic expertise | Sophisticated resource analysis |
| Risk frameworks | VaR-style balance metrics |
| Optimization tools | Portfolio theory for deck building |

### Second-Order Effects
| Effect | Impact |
|--------|--------|
| Domain mismatch | Financial concepts don't map cleanly |
| Translation overhead | Every query needs domain translation |
| Wrong mental models | "Market efficiency" ≠ game balance |

### Third-Order Effects
| Effect | Impact |
|--------|--------|
| Analysis confusion | Financial metrics mislead |
| Over-engineering | Simple game treated as complex market |
| Wasted expertise | Agents applied to wrong domain |

### Simulation Verdict
**DO NOT IMPLEMENT**: The domain mismatch is fundamental. Financial agents assume:
- Continuous prices
- Rational actors
- Historical data

Game balance involves:
- Discrete actions
- Player skill variance
- Design intent

### Better Alternative
If economic analysis needed, adapt concepts manually:
- "Risk" → variance in win rate
- "Return" → expected card value
- "Portfolio" → deck composition

Don't use financial agents; use financial concepts translated to game domain.

---

## Simulation 10: Monthly Agent Ecosystem Review

### Change Description
Schedule monthly review of agent effectiveness.

### First-Order Effects
| Effect | Impact |
|--------|--------|
| Systematic evaluation | Catch ecosystem drift |
| Friction detection | Find new friction points |
| Evolution opportunity | Adapt ecosystem to needs |

### Second-Order Effects
| Effect | Impact |
|--------|--------|
| Meeting overhead | Time spent reviewing |
| Documentation burden | Must track agent usage |
| Change hesitancy | Wait for review to make changes |

### Third-Order Effects
| Effect | Impact |
|--------|--------|
| Review theater | Reviews happen but don't improve |
| Ecosystem calcification | "We reviewed, so it's fine" |

### Simulation Verdict
**IMPLEMENT WITH LIGHT TOUCH**: Review is valuable but should be lightweight.

### Implementation
```
Monthly Agent Review (30 min):
1. Review friction-map.md for new entries
2. Check for recurring patterns in queries
3. Identify unused agents
4. Identify missing capabilities
5. Update documentation if needed

NOT Required:
- Formal report
- Multi-hour meeting
- Approval process
```

---

## Part 2: Simulation Summary

### Approved Changes
| Change | Condition |
|--------|-----------|
| Yoni exceptions for Explore | Document clearly |
| Wealon activation | Triggers only |
| Handoff contracts | Major changes only |
| TDD enforcement | Core logic only |
| Monthly review | Lightweight |

### Rejected Changes
| Change | Reason |
|--------|--------|
| Remove Yoni-first | Second-order chaos |
| Remove Quality-Control | Quality degradation |
| Financial agents | Domain mismatch |
| DQN replacement | Loses existing work |

### Deferred Changes
| Change | Revisit When |
|--------|--------------|
| Game-mechanic-expert | Human escalation becomes bottleneck |
| Balance-analyst | Analysis needs exceed human bandwidth |

---

## Part 3: Simulation Methodology

For future simulations, use this framework:

### Step 1: Define the Change
- What exactly changes?
- What stays the same?

### Step 2: First-Order Effects
- What happens immediately?
- Who is directly affected?

### Step 3: Second-Order Effects
- What do first-order effects cause?
- What workflows change?
- What dependencies break?

### Step 4: Third-Order Effects
- What emergent behaviors appear?
- What long-term trends develop?
- What cultural changes occur?

### Step 5: Verdict
- NET POSITIVE: Implement
- NET NEGATIVE: Reject
- CONDITIONAL: Implement with constraints
- DEFERRED: Revisit later

### Step 6: Mitigation
- If rejected, what captures the benefit without the cost?
- If conditional, what are the constraints?

---

*Each proposed change to the agent ecosystem should go through this simulation before implementation.*

*Generated by BMAD+AGENTIC Phase 4: Impact Simulations*
