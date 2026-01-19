# CartesSociete: Project Context Bible

**Version**: 1.0
**Last Updated**: 2026-01-19
**Authors**: BMAD+AGENTIC Agent Ecosystem
**Status**: Living Document

---

## 1. Domain Essence

### 1.1 What This Project IS

CartesSociete is a **digital implementation of a physical card game** with three concurrent concerns:

1. **Game Engine** - A deterministic state machine implementing the complete ruleset
2. **AI Players** - Strategy-driven agents (from random to RL-trained) that compete
3. **Balance Analysis** - Statistical tools to identify overpowered/underpowered cards

The project is NOT:
- A playable UI/game client (no human-facing interface exists)
- A competitive esports platform
- A card data management system (card data is static JSON)

### 1.2 Domain Mental Model

The mental model is a **turn-based asymmetric card game** where:

```
TURN FLOW:
┌─────────────────────────────────────────────────────────────┐
│  MARKET PHASE                                               │
│  ├── Players receive PO (gold) based on turn number         │
│  ├── Market reveals cards from current cost tier deck       │
│  └── Players buy cards (cost ≤ available PO)                │
├─────────────────────────────────────────────────────────────┤
│  PLAY PHASE                                                 │
│  ├── Players play cards from hand to board (max 5 slots)    │
│  ├── Players can evolve (3x same card → Level 2)            │
│  ├── Players can equip weapons to board cards               │
│  ├── Players can sacrifice cards for effects                │
│  └── Players can replace board cards                        │
├─────────────────────────────────────────────────────────────┤
│  COMBAT PHASE                                               │
│  ├── Calculate total ATK per player (base + abilities)      │
│  ├── Calculate total DEF per player (HP of board cards)     │
│  ├── Damage = max(0, enemy_ATK - player_DEF) + imblocable   │
│  ├── Add spell damage (bypasses everything)                 │
│  └── Apply damage to player health                          │
├─────────────────────────────────────────────────────────────┤
│  END PHASE                                                  │
│  ├── Apply per-turn effects (healing, self-damage)          │
│  ├── Deck mixing on even turns (lower tier → higher tier)   │
│  └── Check for elimination / game over                      │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Core Entities & Their Relationships

```
CARD TAXONOMY:
┌────────────────────────────────────────────────────────────┐
│ Card                                                       │
│   ├── id (unique identifier)                               │
│   ├── name (display name, evolution key)                   │
│   ├── card_type: CREATURE | WEAPON | DEMON                 │
│   ├── cost: 1-5 (determines deck placement)                │
│   ├── level: 1 | 2 (Level 2 = evolved)                     │
│   ├── family: LAPIN | CYBORG | ATLANTIDE | NINJA | ...     │
│   ├── card_class: ARCHER | BERSEKER | COMBATTANT | ...     │
│   ├── attack: base ATK value                               │
│   ├── health: base PV/HP value                             │
│   ├── family_abilities: scaling bonuses at thresholds      │
│   ├── class_abilities: scaling bonuses at thresholds       │
│   └── bonus_text: special effect string (parsed at runtime)│
└────────────────────────────────────────────────────────────┘

FAMILY (9 creature families + 2 special):
┌────────────────────────────────────────────────────────────┐
│ LAPIN     - Wide board strategy (+N board slots)           │
│ CYBORG    - Tech synergy with S-Team, efficient stats      │
│ ATLANTIDE - Diplo cross-synergies, water theme             │
│ NINJA     - High damage, solo bonuses, stealth             │
│ NEIGE     - Ice magic, defensive, control                  │
│ NATURE    - Healing, growth, sustainability                │
│ RATON     - Economic bonuses, raccoon family synergy       │
│ HALL_OF_WIN - Legendary cards, Hall threshold bonuses      │
│ ARME      - Weapons (no family abilities)                  │
│ DEMON     - Summoned by Invocateurs, unique restrictions   │
└────────────────────────────────────────────────────────────┘

CLASS (17 classes with distinct mechanics):
┌────────────────────────────────────────────────────────────┐
│ ARCHER      - Conditional ATK bonus vs Defenseurs          │
│ BERSEKER    - High ATK, self-damage tradeoff               │
│ COMBATTANT  - Generic ATK scaling per class count          │
│ DEFENSEUR   - HP scaling, protector synergies              │
│ DRAGON      - PO-to-damage conversion (spend gold for ATK) │
│ MAGE        - Spell damage (bypasses defense entirely)     │
│ INVOCATEUR  - Demon summoning at thresholds 1/2/4/6        │
│ MONTURE     - Card draw from cost-5 deck at threshold 3    │
│ FORGERON    - Weapon draw at thresholds 1/2/3              │
│ PROTECTEUR  - Defensive HP bonuses                         │
│ ECONOME     - Extra PO generation per turn                 │
│ ENVOUTEUR   - ATK bonus to all monsters                    │
│ DIPLO       - Cross-family synergies (Terre/Air/Mer)       │
│ STEAM       - S-Team (doesn't count as monster)            │
│ BOSS        - Unique boss mechanics                        │
│ TANK        - High HP, damage reduction                    │
│ OTHER       - Miscellaneous/uncategorized                  │
└────────────────────────────────────────────────────────────┘
```

### 1.4 The Damage Formula

This is the CRITICAL combat calculation that determines all game outcomes:

```python
def calculate_total_damage(attacker, defender, game_state):
    # 1. BASE DAMAGE
    base_atk = sum(card.attack for card in attacker.board)

    # 2. WEAPON BONUS
    weapon_atk = sum(
        weapon.attack
        for card_id, weapon in attacker.equipped_weapons.items()
    )

    # 3. CLASS ABILITY BONUSES (resolved from scaling thresholds)
    class_bonus = resolve_class_abilities(attacker)

    # 4. FAMILY ABILITY BONUSES (resolved from scaling thresholds)
    family_bonus = resolve_family_abilities(attacker)

    # 5. BONUS_TEXT EFFECTS (parsed from card text)
    bonus_text = resolve_bonus_text_effects(attacker, defender)

    # 6. TOTAL ATTACK
    total_atk = (
        base_atk + weapon_atk +
        class_bonus.attack + family_bonus.attack +
        bonus_text.attack_bonus - bonus_text.attack_penalty
    )

    # 7. DEFENSE CALCULATION
    defender_hp = sum(card.health for card in defender.board)

    # 8. BLOCKABLE DAMAGE (can be reduced by defense)
    blockable_damage = max(0, total_atk - defender_hp)

    # 9. IMBLOCABLE DAMAGE (bypasses defense)
    imblocable = (
        class_bonus.imblocable +
        bonus_text.flat_imblocable +
        bonus_text.per_turn_imblocable
    )

    # 10. SPELL DAMAGE (completely separate damage source)
    spell_damage = bonus_text.spell_damage

    # 11. FINAL DAMAGE TO PLAYER HEALTH
    total_damage = blockable_damage + imblocable + spell_damage

    return total_damage
```

**Why this matters for agents:**
- Balance analysis must understand this formula to identify overpowered combos
- RL agents must learn which actions maximize damage output
- Heuristic players use simplified approximations of this formula

---

## 2. Technical Architecture

### 2.1 Codebase Structure

```
CartesSociete/
├── src/
│   ├── cards/
│   │   └── models.py          # Card dataclasses, Family, CardClass enums
│   │   └── repository.py      # Card loading from JSON
│   ├── game/
│   │   ├── state.py           # GameState, PlayerState, GamePhase
│   │   ├── engine.py          # GameEngine orchestrator
│   │   ├── combat.py          # resolve_combat(), damage calculation
│   │   ├── abilities.py       # 800+ lines of ability resolution
│   │   ├── market.py          # Deck management, card revealing
│   │   ├── actions.py         # buy_card, play_card, evolve, etc.
│   │   └── executor.py        # Action execution bridge
│   ├── players/
│   │   ├── base.py            # Player abstract base class
│   │   ├── action.py          # Action dataclass, ActionType enum
│   │   ├── random_player.py   # RandomPlayer implementation
│   │   ├── greedy.py          # GreedyPlayer implementation
│   │   ├── heuristic.py       # HeuristicPlayer implementation
│   │   ├── mcts.py            # MCTSPlayer (Monte Carlo Tree Search)
│   │   └── evaluation.py      # Card evaluation heuristics
│   ├── simulation/
│   │   ├── runner.py          # GameRunner for full simulations
│   │   ├── logger.py          # Event logging for analysis
│   │   └── stats.py           # PlayerStats collection
│   ├── analysis/
│   │   └── card_tracker.py    # CardTracker for balance analysis
│   └── rl/
│       ├── environment.py     # CartesSocieteEnv (Gymnasium)
│       └── training.py        # PPOTrainer, MaskablePPO
├── data/cards/                 # JSON card definitions per family
├── configs/                    # Game configuration
├── scripts/
│   ├── train_ppo.py           # PPO training CLI
│   └── run_tournament.py      # Tournament simulation
└── tests/                      # Test suite
```

### 2.2 State Representation

```python
@dataclass
class GameState:
    players: list[PlayerState]      # 2-5 players
    turn: int                       # Current turn number
    phase: GamePhase                # MARKET | PLAY | COMBAT | END
    market_cards: list[Card]        # Currently available cards
    cost_1_deck: list[Card]         # Cost tier decks
    cost_2_deck: list[Card]
    cost_3_deck: list[Card]
    cost_4_deck: list[Card]
    cost_5_deck: list[Card]
    weapon_deck: list[WeaponCard]   # Weapons (drawn by Forgeron)
    demon_deck: list[DemonCard]     # Demons (summoned by Invocateur)
    discard_pile: list[Card]        # Discarded cards
    config: GameConfig              # Game rules configuration

@dataclass
class PlayerState:
    player_id: int
    name: str
    health: int                     # Player PV (starts at 30)
    hand: list[Card]                # Cards in hand
    board: list[Card]               # Cards on board (max 5)
    po: int                         # Current gold
    equipped_weapons: dict[str, WeaponCard]  # card_id → weapon
    spells: list[Card]              # Active spell effects
    sacrifices: list[Card]          # Sacrificed this turn
    eliminated: bool                # True if health <= 0
```

### 2.3 RL Environment Design

```python
class CartesSocieteEnv(gym.Env):
    """Gymnasium environment for PPO training."""

    # Observation space: ~300+ dimensional vector
    # - Player stats (health, PO)
    # - Hand cards (one-hot encoded)
    # - Board cards (stats, families, classes)
    # - Opponent board (observable)
    # - Market cards (observable)
    # - Turn/phase information

    # Action space: Discrete(max_actions)
    # - With action masking for legal moves only

    # Reward shaping:
    REWARD_WIN = 10.0
    REWARD_LOSE = -10.0
    REWARD_EVOLUTION = 0.3
    REWARD_DAMAGE_DEALT = 0.05  # per damage
    REWARD_CARD_BOUGHT = 0.1
    REWARD_CARD_PLAYED = 0.05
    REWARD_HEALTH_DIFF = 0.02   # per health differential
    TIME_PENALTY = -0.01        # per turn
```

---

## 3. Core Assumptions

### 3.1 Explicit Assumptions (Documented)

| Assumption | Location | Risk if Wrong |
|------------|----------|---------------|
| 2-5 players | configs/default.py | Game balance breaks |
| 30 starting health | state.py:55 | Win conditions break |
| 5 board slots max | state.py:70 | Board overflow bugs |
| 3 cards to evolve | actions.py:200 | Evolution logic fails |
| Cost 1-5 only | market.py | Deck sorting breaks |
| Level 1 and 2 only | models.py | Evolution chains break |
| Turn-based (not real-time) | engine.py | Entire architecture |

### 3.2 Hidden Assumptions (Implicit in Code)

| Assumption | Evidence | Risk Level |
|------------|----------|------------|
| Abilities stack additively | abilities.py:700+ | HIGH - multipliers could break this |
| Demons can't gain normal bonuses | abilities.py:701 | MEDIUM - inconsistent enforcement |
| S-Team doesn't count as monster | abilities.py:27 | MEDIUM - edge cases |
| Spell damage bypasses ALL defense | combat.py:89 | HIGH - balance assumption |
| Weapons persist across turns | state.py:140 | LOW - but unclear on evolution |
| Card IDs are globally unique | models.py:45 | MEDIUM - deep copies create duplicates |
| JSON card data is trusted | repository.py | LOW - but no validation |
| Family abilities shared across family | lapin.json | HIGH - all Lapins have same scaling |

### 3.3 Domain Assumptions (Game Design)

| Assumption | Impact |
|------------|--------|
| All players have equal information (except opponent hands) | Fair play requirement |
| Combat is simultaneous (not attacker-defender) | Critical balance property |
| Market cards are random but known after reveal | Strategy element |
| Deck mixing introduces variance | Reduces determinism |
| Higher cost = stronger cards | Implicit balance contract |

---

## 4. Known Unknowns & Risk Zones

### 4.1 Technical Risk Zones

```
RISK MAP:
┌────────────────────────────────────────────────────────────┐
│ abilities.py (800+ lines)                                  │
│ ├── 50+ regex patterns for bonus_text parsing              │
│ ├── Many edge cases in French text parsing                 │
│ ├── New cards may have unparseable bonus_text              │
│ └── RISK: New cards could silently fail to have abilities  │
├────────────────────────────────────────────────────────────┤
│ Combat Formula Complexity                                  │
│ ├── 10+ damage sources combined                            │
│ ├── Order of operations matters                            │
│ ├── Multiplicative vs additive bonuses unclear             │
│ └── RISK: Edge case damage calculations wrong              │
├────────────────────────────────────────────────────────────┤
│ Card Evolution                                             │
│ ├── Level 2 cards defined separately in JSON               │
│ ├── Name matching for evolution (fragile)                  │
│ ├── What happens to equipped weapons on evolution?         │
│ └── RISK: Evolution edge cases cause state corruption      │
├────────────────────────────────────────────────────────────┤
│ Action Space for RL                                        │
│ ├── Dynamic action count (depends on hand/board size)      │
│ ├── Action masking critical for legal moves                │
│ ├── Weapon equip + sacrifice actions relatively new        │
│ └── RISK: RL agent learns invalid action patterns          │
└────────────────────────────────────────────────────────────┘
```

### 4.2 Balance Risk Zones

```
BALANCE CONCERNS:
┌────────────────────────────────────────────────────────────┐
│ Lapin Family                                               │
│ ├── +N board slots is unique and powerful                  │
│ ├── Wide boards mean more abilities trigger                │
│ ├── Lapincruste (+2 slots) could be dominant               │
│ └── STATUS: Requires simulation data to validate           │
├────────────────────────────────────────────────────────────┤
│ Imblocable Damage Stacking                                 │
│ ├── Multiple sources can stack to instant-kill             │
│ ├── No upper bound on imblocable                           │
│ └── STATUS: Potential for degenerate combos                │
├────────────────────────────────────────────────────────────┤
│ Spell Damage (Mage class)                                  │
│ ├── Completely bypasses defense                            │
│ ├── Mage threshold 3 = double spell cast                   │
│ ├── Stacking mages could be oppressive                     │
│ └── STATUS: Needs balance simulation                       │
├────────────────────────────────────────────────────────────┤
│ Dragon PO-to-ATK Conversion                                │
│ ├── Spend gold for instant damage                          │
│ ├── Threshold-based (2/4/6 PO for 2x/3x/4x ATK)            │
│ ├── Interaction with Econome gold generation               │
│ └── STATUS: Economic balance critical                      │
└────────────────────────────────────────────────────────────┘
```

### 4.3 Open Questions (Require Investigation)

1. **Card Pool Size**: How many unique cards exist? Is the pool sufficient for diverse games?
2. **Family Balance**: Are all 9 families viable, or do some dominate?
3. **Class Synergies**: Which class combinations are strongest?
4. **Evolution ROI**: Is evolving always better than buying new cards?
5. **Weapon Balance**: Are weapons impactful enough to pursue?
6. **Demon Mechanics**: Do Invocateur's demons justify the class investment?
7. **Late Game Scaling**: Do high-cost cards justify their cost?

---

## 5. Quality Bars & Failure Definitions

### 5.1 Code Quality Requirements

| Aspect | Requirement | Tooling |
|--------|-------------|---------|
| Type Safety | 100% type hints on public APIs | pyrefly |
| Formatting | Black-compatible, sorted imports | ruff format, isort |
| Linting | Zero ruff errors | ruff check |
| Testing | All game mechanics have unit tests | pytest |
| Docstrings | Required on all public functions | convention |

### 5.2 Game Logic Correctness

| Test Category | Requirement |
|---------------|-------------|
| Combat calculation | Damage matches hand calculation |
| Evolution mechanics | 3 cards → 1 Level 2 card |
| Ability resolution | Scaling triggers at exact thresholds |
| Action legality | Illegal actions always rejected |
| State consistency | No orphaned cards, health never negative |

### 5.3 AI Player Requirements

| Player Type | Expected Behavior |
|-------------|-------------------|
| RandomPlayer | Valid random actions (never illegal) |
| GreedyPlayer | Beats RandomPlayer >60% |
| HeuristicPlayer | Beats GreedyPlayer >55% |
| PPO Agent | Beats HeuristicPlayer >50% after training |

### 5.4 Balance Analysis Requirements

| Metric | Healthy Range | Action if Outside |
|--------|---------------|-------------------|
| Card pick rate | 10-80% | Investigate if outside |
| Card win correlation | 40-60% | Flag for balance review |
| Family win rate | 45-55% | Indicates family imbalance |
| Class win rate | 45-55% | Indicates class imbalance |
| Evolution rate | 10-40% | Indicates evolution viability |

### 5.5 What Constitutes Failure

```
FAILURE CONDITIONS:
┌────────────────────────────────────────────────────────────┐
│ CRITICAL FAILURES (Stop everything):                       │
│ ├── Game state corruption (negative health, orphan cards)  │
│ ├── Infinite loop in game loop                             │
│ ├── RL agent crashes during training                       │
│ └── CI/CD pipeline broken                                  │
├────────────────────────────────────────────────────────────┤
│ MAJOR FAILURES (Require immediate fix):                    │
│ ├── Ability not triggering when it should                  │
│ ├── Combat damage calculation wrong                        │
│ ├── Legal action rejected or illegal action allowed        │
│ └── Test failures in core game logic                       │
├────────────────────────────────────────────────────────────┤
│ MINOR FAILURES (Track and fix):                            │
│ ├── Edge case bonus_text not parsed                        │
│ ├── Suboptimal AI player behavior                          │
│ ├── Balance outlier detected                               │
│ └── Missing test coverage                                  │
└────────────────────────────────────────────────────────────┘
```

---

## 6. Constraints

### 6.1 Technical Constraints

| Constraint | Reason | Impact |
|------------|--------|--------|
| Python 3.10+ | Type hint syntax | Can't use legacy Python |
| uv for dependencies | Project standard | No pip install |
| Windows primary | Developer machine | SubprocVecEnv issues |
| No CUDA required | Accessibility | CPU training only |
| JSON card data | Physical card source | No database |

### 6.2 Domain Constraints

| Constraint | Reason | Impact |
|------------|--------|--------|
| French card text | Physical cards are French | All ability parsing in French |
| Fixed card pool | Based on physical game | No procedural card generation |
| 2-player focus | Primary game mode | Multiplayer is secondary |
| Turn limit (100) | Prevent infinite games | Force decisions |

### 6.3 Process Constraints

| Constraint | Reason | Impact |
|------------|--------|--------|
| CI must pass | Quality gate | No merge without green |
| Conventional commits | Git history | Commit message format |
| Branch workflow | Code review | No direct main commits |
| Type hints | Code quality | All new code typed |

---

## 7. Evolution Considerations

### 7.1 Near-Term Evolution (Planned)

1. **More AI Players**: MCTS improvements, DQN, AlphaZero-style
2. **Balance Tooling**: Automated balance reports, change impact simulation
3. **Card Expansion**: Support for new card families/classes
4. **Tournament Mode**: Multi-game statistical analysis

### 7.2 Potential Future Directions

1. **Human UI**: Web or CLI interface for human play
2. **Network Play**: Online multiplayer
3. **Card Editor**: Tools to create/modify cards
4. **Meta Analysis**: Deck building optimization

### 7.3 Architecture Extensibility

| Extension Point | How to Extend |
|-----------------|---------------|
| New player types | Inherit from `Player` base class |
| New card families | Add enum, JSON, ability patterns |
| New classes | Add enum, scaling patterns |
| New game modes | Fork `GameRunner`, modify phases |
| New analysis | Add modules to `analysis/` |

---

## 8. Agent-Specific Context

### 8.1 For ML/Balance Agents (Alexios)

- Combat formula is the key optimization target
- Reward shaping directly affects learned behavior
- Action masking is critical for valid RL
- Balance metrics guide game design decisions

### 8.2 For Code Quality Agents (Clovis, Wealon)

- abilities.py is the highest-risk file (800+ lines, regex parsing)
- French text parsing has many edge cases
- Test coverage should focus on game logic correctness
- Type hints enforce API contracts

### 8.3 For Research Agents (Remy, Iacopo)

- Family/class synergies are unexplored territory
- Win rate correlations indicate strategic value
- Evolution mechanics affect deck building
- Late game economics need study

### 8.4 For Planning Agents (Yoni, Gabriel)

- Game engine is feature-complete
- Focus is on AI improvement and balance
- No human UI means no UX considerations
- Simulation throughput matters for analysis

---

## 9. Document Maintenance

### 9.1 Update Triggers

This document MUST be updated when:
- New card families or classes are added
- Combat formula changes
- New AI player types are created
- Balance thresholds are adjusted
- Core architecture changes

### 9.2 Review Schedule

- After each major feature
- Monthly for accuracy check
- When new team members join
- Before balance analysis runs

---

*This document is the source of truth for all agents working on CartesSociete. When in doubt, consult this document first.*

*Generated by BMAD+AGENTIC Phase 1: Project Reality Lock*
