# Reinforcement Learning Research Plan for CartesSociete

## Executive Summary

This document outlines a comprehensive research plan to use reinforcement learning (RL) to:
1. Discover optimal play strategies for the CartesSociete card game
2. Identify overpowered and underpowered cards
3. Detect balance issues in game rules
4. Propose concrete changes for improved game balance

## Current State Analysis

### Baseline Performance (150 games)
| Player Type | Win Rate | Notes |
|-------------|----------|-------|
| HeuristicPlayer | 100% | Dominant - tracks evolutions, saves PO |
| RandomPlayer | 49% | Baseline random play |
| GreedyPlayer | 0% | **Broken** - ignores evolution, loses to random |

### Critical Finding: GreedyPlayer Bug

The GreedyPlayer (`src/players/greedy_player.py`) has 0% win rate because it:
1. Always buys highest immediate-value card without considering evolution
2. Never saves PO for future turns
3. Ignores synergy bonuses that compound over time

Meanwhile, HeuristicPlayer (`src/players/heuristic.py`) dominates because it:
- Tracks evolution candidates (lines 79-95)
- Applies +10.0 bonus for completing evolutions (line 143)
- Saves PO when close to evolution (lines 97-117)
- Always evolves when possible (lines 222-227)

**Immediate Action Required**: Fix GreedyPlayer to provide valid baseline comparisons.

---

## Phase 1: Infrastructure Setup

### 1.1 Fix GreedyPlayer
Add minimal evolution awareness:
```python
def _evaluate_for_market_greedy(self, card, player_state, state):
    base_score = evaluate_card_for_purchase(card, player_state, state)

    # Add evolution bonus (simplified)
    name_count = sum(1 for c in player_state.hand + player_state.board
                     if c.name == card.name and c.level == 1)
    if name_count >= 2:
        base_score += 8.0  # Near evolution
    elif name_count == 1:
        base_score += 2.0  # Building towards evolution

    return base_score
```

### 1.2 Create Card Analytics Tracker

```python
# src/analytics/card_tracker.py

@dataclass
class CardGameStats:
    """Statistics for a card within a single game."""
    card_id: str
    was_available: bool = False      # Appeared in market
    was_purchased: bool = False      # Was bought
    was_played: bool = False         # Was played to board
    was_evolved: bool = False        # Was part of evolution
    on_winning_board: bool = False   # Present when game ended
    damage_dealt: int = 0            # Damage contribution

@dataclass
class CardAggregateStats:
    """Aggregate statistics across all games."""
    card_id: str
    times_available: int = 0
    times_purchased: int = 0
    times_played: int = 0
    times_evolved: int = 0
    times_on_winning_board: int = 0
    total_games: int = 0

    @property
    def pick_rate(self) -> float:
        return self.times_purchased / max(1, self.times_available)

    @property
    def win_correlation(self) -> float:
        return self.times_on_winning_board / max(1, self.times_played)
```

### 1.3 Gym Environment Wrapper

```python
# src/rl/environment.py

class CartesSocieteEnv(gym.Env):
    """OpenAI Gym environment for CartesSociete."""

    def __init__(self, opponent_factory=None):
        super().__init__()
        self.opponent_factory = opponent_factory or (lambda pid: RandomPlayer(pid))

        # Action space: discrete with variable valid actions
        self.action_space = gym.spaces.Discrete(50)  # Max possible actions

        # Observation space: flattened state
        self.observation_space = gym.spaces.Box(
            low=0, high=1, shape=(512,), dtype=np.float32
        )

    def reset(self):
        self.game_state = create_initial_game_state(num_players=2)
        self.opponent = self.opponent_factory(1)
        return self._encode_state()

    def step(self, action_idx):
        # Execute action
        legal_actions = get_legal_actions_for_player(
            self.game_state,
            self.game_state.players[0]
        )

        if action_idx >= len(legal_actions):
            action = Action.end_phase()
        else:
            action = legal_actions[action_idx]

        prev_state = copy.deepcopy(self.game_state)
        execute_action(self.game_state, self.game_state.players[0], action)

        # Calculate reward
        reward = self._compute_reward(prev_state, action)

        # Check done
        done = self.game_state.is_game_over()

        return self._encode_state(), reward, done, {}
```

---

## Phase 2: RL Agent Implementation

### 2.1 PPO Agent Architecture

```python
# src/rl/networks.py

class PolicyNetwork(nn.Module):
    """Actor network for action selection."""

    def __init__(self, state_dim=512, hidden_dim=256, max_actions=50):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, max_actions),
        )

    def forward(self, state, action_mask):
        logits = self.network(state)
        # Mask invalid actions
        logits = logits.masked_fill(~action_mask, float('-inf'))
        return F.softmax(logits, dim=-1)


class ValueNetwork(nn.Module):
    """Critic network for state value estimation."""

    def __init__(self, state_dim=512, hidden_dim=256):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, state):
        return self.network(state)
```

### 2.2 Training Configuration

```python
# src/rl/config.py

@dataclass
class PPOConfig:
    """Hyperparameters for PPO training."""
    # Core PPO
    learning_rate: float = 3e-4
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_epsilon: float = 0.2

    # Training
    num_epochs: int = 10
    batch_size: int = 64
    num_envs: int = 8
    steps_per_update: int = 2048

    # Network
    hidden_dim: int = 256

    # Coefficients
    value_coef: float = 0.5
    entropy_coef: float = 0.01

    # Curriculum
    opponent_schedule: list = field(default_factory=lambda: [
        (0, RandomPlayer),       # Start vs random
        (50000, HeuristicPlayer),  # Then vs heuristic
        (100000, "self"),        # Then self-play
    ])
```

### 2.3 Reward Shaping

```python
def compute_shaped_reward(
    prev_state: GameState,
    action: Action,
    new_state: GameState,
    player_id: int,
) -> float:
    """Compute reward with careful shaping."""
    reward = 0.0

    # Terminal rewards (sparse but important)
    if new_state.is_game_over():
        winner = new_state.get_winner()
        if winner and winner.player_id == player_id:
            return 1.0  # Win
        return -1.0  # Loss

    player = new_state.players[player_id]
    opponent = new_state.players[1 - player_id]

    # Evolution bonus (key strategic element)
    if action.action_type == ActionType.EVOLVE:
        reward += 0.15

    # Health differential improvement
    prev_player = prev_state.players[player_id]
    prev_opponent = prev_state.players[1 - player_id]
    prev_diff = prev_player.health - prev_opponent.health
    new_diff = player.health - opponent.health
    reward += 0.01 * (new_diff - prev_diff)

    # Board strength (attack + health)
    reward += 0.002 * (
        player.get_total_attack() + player.get_total_health()
    )

    # Imblocable damage bonus
    imblocable = sum(c.class_abilities.imblocable_damage for c in player.board)
    reward += 0.01 * imblocable

    # Small time penalty to encourage faster wins
    reward -= 0.001

    return reward
```

---

## Phase 3: Analysis Framework

### 3.1 Card Balance Metrics

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| Pick Rate | purchases / availability | >80%: Too strong, <20%: Too weak |
| Win Correlation | wins_with_card / games_with_card | >60%: Overpowered, <40%: Underpowered |
| Evolution Impact | win_rate_evolved - win_rate_base | >20%: Evolution too strong |
| Cost Efficiency | (ATK+HP)/cost * win_correlation | Identifies undercosted cards |
| Synergy Score | win_rate_combo - win_rate_solo | Identifies broken combos |

### 3.2 Rule Balance Analysis

Track these metrics to identify rule issues:

1. **First-Player Advantage**
   - Win rate by player position
   - Target: 45-55% for each position

2. **Game Length Distribution**
   - Average turns to completion
   - Variance in game length
   - Target: 10-15 turns average

3. **Snowball Factor**
   - Correlation between Turn 5 lead and final outcome
   - Target: <70% correlation

4. **Evolution Frequency**
   - Games with 0, 1, 2, 3+ evolutions
   - Target: Evolutions in 60-80% of games

5. **Family Diversity**
   - Win rate by primary family
   - Target: All families within 45-55%

### 3.3 Specific Questions to Answer

1. **Is imblocable damage balanced?**
   - Compare win rates with/without imblocable cards
   - Measure imblocable contribution to total damage

2. **Are S-Team cards (X-cost) viable?**
   - Pick rate and win correlation
   - Compare to fixed-cost alternatives

3. **Is the cost curve balanced?**
   - Win rate by average card cost in deck
   - Early aggression vs. late game scaling

4. **Are all families equally viable?**
   - Win rate by family focus
   - Identify dominant/weak families

5. **Are all classes equally useful?**
   - Pick rate and win correlation by class
   - Identify must-have vs. never-pick classes

---

## Phase 4: Implementation Timeline

### Week 1: Infrastructure
- [ ] Fix GreedyPlayer with evolution awareness
- [ ] Implement CardTracker for analytics
- [ ] Create Gym environment wrapper
- [ ] Run 1000-game baseline with new GreedyPlayer

### Week 2: RL Skeleton
- [ ] Implement PPO agent skeleton
- [ ] Implement policy and value networks
- [ ] Create training loop with logging
- [ ] Train initial agent vs RandomPlayer

### Week 3: Training at Scale
- [ ] Set up multi-environment training (8 parallel)
- [ ] Train agent through curriculum (Random -> Heuristic -> Self)
- [ ] Implement checkpointing and evaluation
- [ ] Track training curves

### Week 4: Analysis
- [ ] Run 10,000 games with trained RL agent
- [ ] Collect comprehensive card statistics
- [ ] Generate balance report
- [ ] Identify outlier cards

### Week 5: Deep Dive
- [ ] Analyze specific balance issues identified
- [ ] Test proposed rule changes in simulation
- [ ] Compare RL strategies to human intuition
- [ ] Document emergent strategies

### Week 6: Recommendations
- [ ] Compile final balance report
- [ ] Propose concrete card changes (stats, costs)
- [ ] Propose rule modifications
- [ ] Create presentation of findings

---

## Expected Deliverables

1. **RLPlayer** - Trained PPO agent that outperforms HeuristicPlayer
2. **Card Balance Report** - Per-card statistics and recommendations
3. **Rule Analysis Report** - First-player advantage, snowball factor, etc.
4. **Change Proposals** - Specific numeric changes with expected impact
5. **Codebase** - Reusable RL and analytics infrastructure

---

## Technical Requirements

### Dependencies to Add
```toml
[project.optional-dependencies]
rl = [
    "torch>=2.0.0",
    "gymnasium>=0.29.0",
    "stable-baselines3>=2.0.0",
    "tensorboard>=2.14.0",
    "numpy>=1.24.0",
]
```

### Compute Requirements
- Training: 8+ CPU cores, GPU optional (PPO is CPU-efficient)
- Storage: ~1GB for checkpoints and logs
- Time: ~24 hours for full training curriculum

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| RL fails to learn | Use curriculum learning, start with simple opponents |
| Reward hacking | Careful reward shaping, validate learned behaviors |
| Computational cost | Use efficient PPO, parallelize environments |
| Game complexity | Start with 2-player games only |
| Stochastic variance | Run many games (10,000+) for statistical significance |

---

## Appendix: Key Code Locations

| Component | File Path |
|-----------|-----------|
| Card definitions | `src/cards/models.py` |
| Card repository | `src/cards/repository.py` |
| Game state | `src/game/state.py` |
| Combat system | `src/game/combat.py` |
| Action execution | `src/game/executor.py` |
| Player base class | `src/players/base.py` |
| Evaluation heuristics | `src/players/evaluation.py` |
| Greedy player | `src/players/greedy_player.py` |
| Heuristic player | `src/players/heuristic.py` |
| MCTS player | `src/players/mcts_player.py` |
| Balance analyzer | `src/analysis/balance.py` |
| Match runner | `src/simulation/runner.py` |

---

## Next Steps

1. Review this plan with the team
2. Prioritize GreedyPlayer fix as blocking issue
3. Begin Week 1 implementation
4. Set up weekly progress reviews

**Document Version**: 1.0
**Created**: 2024-12-31
**Author**: Yoni (Master Orchestrator) with Alexios (ML) consultation
