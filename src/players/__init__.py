"""Player agents for CartesSociete.

This package provides various AI player implementations:
- RandomPlayer: Baseline random agent
- GreedyPlayer: Maximizes immediate card value
- HeuristicPlayer: Rule-based strategy with synergy/evolution awareness
- MCTSPlayer: Monte Carlo Tree Search (stub)

Family-focused strategy agents:
- LapinPlayer: Lapin swarm strategy (board flooding)
- CyborgPlayer: Cyborg aggression (demon summoning)
- NaturePlayer: Nature imblocable damage strategy
- AtlantidePlayer: Atlantide healing sustain
- NinjaPlayer: Ninja economy/replay strategy
- NeigePlayer: Neige economy engine
- RatonPlayer: Raton linear scaling
- HallOfWinPlayer: Hall of Win variance/gambling

Cross-cutting archetype agents:
- AggroPlayer: Maximum damage per turn
- TempoPlayer: PO/action efficiency
- ControlPlayer: Defensive stability
- SpellMagePlayer: Spell damage scaling

Example usage:
    from src.players import RandomPlayer, GreedyPlayer, AggroPlayer, TempoPlayer
    from src.game.executor import get_legal_actions_for_player, execute_action

    # Create players
    player1 = RandomPlayer(player_id=0, seed=42)
    player2 = GreedyPlayer(player_id=1)

    # Get legal actions
    actions = get_legal_actions_for_player(state, player_state)

    # Choose and execute action
    action = player1.choose_market_action(state, player_state, actions)
    result = execute_action(state, player_state, action)
"""

from .action import Action, ActionType
from .aggro_player import AggroPlayer
from .atlantide_player import AtlantidePlayer
from .base import Player, PlayerInfo
from .control_player import ControlPlayer
from .cyborg_player import CyborgPlayer
from .evaluation import (
    DEFAULT_WEIGHTS,
    EvaluationWeights,
    calculate_base_value,
    calculate_class_synergy,
    calculate_cost_efficiency,
    calculate_evolution_potential,
    calculate_family_synergy,
    calculate_imblocable_bonus,
    evaluate_board_position,
    evaluate_card_for_play,
    evaluate_card_for_purchase,
    evaluate_threat_level,
)
from .greedy_player import GreedyPlayer
from .hallofwin_player import HallOfWinPlayer
from .heuristic import HeuristicPlayer
from .lapin_player import LapinPlayer
from .mcts_player import MCTSConfig, MCTSNode, MCTSPlayer
from .nature_player import NaturePlayer
from .neige_player import NeigePlayer
from .ninja_player import NinjaPlayer
from .random_player import RandomPlayer
from .raton_player import RatonPlayer
from .spellmage_player import SpellMagePlayer
from .tempo_player import TempoPlayer

__all__ = [
    # Base classes
    "Action",
    "ActionType",
    "Player",
    "PlayerInfo",
    # Generic player implementations
    "RandomPlayer",
    "GreedyPlayer",
    "HeuristicPlayer",
    "MCTSPlayer",
    "MCTSConfig",
    "MCTSNode",
    # Family-focused strategy players
    "LapinPlayer",
    "CyborgPlayer",
    "NaturePlayer",
    "AtlantidePlayer",
    "NinjaPlayer",
    "NeigePlayer",
    "RatonPlayer",
    "HallOfWinPlayer",
    # Cross-cutting archetype players
    "AggroPlayer",
    "TempoPlayer",
    "ControlPlayer",
    "SpellMagePlayer",
    # Evaluation functions and weights
    "EvaluationWeights",
    "DEFAULT_WEIGHTS",
    "calculate_base_value",
    "calculate_class_synergy",
    "calculate_cost_efficiency",
    "calculate_evolution_potential",
    "calculate_family_synergy",
    "calculate_imblocable_bonus",
    "evaluate_board_position",
    "evaluate_card_for_play",
    "evaluate_card_for_purchase",
    "evaluate_threat_level",
]
