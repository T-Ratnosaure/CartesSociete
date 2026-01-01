"""Game engine for CartesSociete.

This package provides the core game logic including state management,
actions, combat resolution, and the game loop.
"""

from .abilities import (
    AbilityEffect,
    AbilityResolutionResult,
    AbilityTarget,
    PerTurnEffectResult,
    apply_per_turn_effects,
    get_ability_summary,
    resolve_all_abilities,
    resolve_class_abilities,
    resolve_family_abilities,
    resolve_per_turn_effects,
)
from .actions import (
    ActionError,
    ActionResult,
    ActionType,
    BoardFullError,
    EvolutionError,
    InsufficientPOError,
    InvalidCardError,
    InvalidPhaseError,
    buy_card,
    end_turn,
    evolve_cards,
    play_card,
    replace_card,
)
from .combat import (
    CombatResult,
    DamageBreakdown,
    calculate_damage,
    calculate_imblocable_damage,
    get_combat_summary,
    resolve_combat,
)
from .engine import GameEngine, TurnResult
from .executor import (
    InvalidActionError,
    execute_action,
    get_legal_actions_for_player,
)
from .market import (
    get_market_summary,
    mix_decks,
    refresh_market,
    reveal_market_cards,
    setup_decks,
    should_mix_decks,
)
from .state import (
    GamePhase,
    GameState,
    InvalidGameStateError,
    InvalidPlayerError,
    PlayerState,
    create_initial_game_state,
)

__all__ = [
    # State
    "GamePhase",
    "GameState",
    "InvalidGameStateError",
    "InvalidPlayerError",
    "PlayerState",
    "create_initial_game_state",
    # Abilities
    "AbilityEffect",
    "AbilityResolutionResult",
    "AbilityTarget",
    "PerTurnEffectResult",
    "apply_per_turn_effects",
    "get_ability_summary",
    "resolve_all_abilities",
    "resolve_class_abilities",
    "resolve_family_abilities",
    "resolve_per_turn_effects",
    # Actions
    "ActionError",
    "ActionResult",
    "ActionType",
    "BoardFullError",
    "EvolutionError",
    "InsufficientPOError",
    "InvalidCardError",
    "InvalidPhaseError",
    "buy_card",
    "end_turn",
    "evolve_cards",
    "play_card",
    "replace_card",
    # Combat
    "CombatResult",
    "DamageBreakdown",
    "calculate_damage",
    "calculate_imblocable_damage",
    "get_combat_summary",
    "resolve_combat",
    # Market
    "get_market_summary",
    "mix_decks",
    "refresh_market",
    "reveal_market_cards",
    "setup_decks",
    "should_mix_decks",
    # Engine
    "GameEngine",
    "TurnResult",
    # Executor
    "InvalidActionError",
    "execute_action",
    "get_legal_actions_for_player",
]
