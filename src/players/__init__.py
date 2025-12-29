"""Player agents for CartesSociete.

This package provides various AI player implementations:
- RandomPlayer: Baseline random agent
- GreedyPlayer: Maximizes immediate card value
- HeuristicPlayer: Rule-based strategy with synergy/evolution awareness
- MCTSPlayer: Monte Carlo Tree Search (stub)

Example usage:
    from src.players import RandomPlayer, GreedyPlayer, HeuristicPlayer
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
from .base import Player, PlayerInfo
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
from .heuristic import HeuristicPlayer
from .mcts_player import MCTSConfig, MCTSNode, MCTSPlayer
from .random_player import RandomPlayer

__all__ = [
    # Base classes
    "Action",
    "ActionType",
    "Player",
    "PlayerInfo",
    # Player implementations
    "RandomPlayer",
    "GreedyPlayer",
    "HeuristicPlayer",
    "MCTSPlayer",
    "MCTSConfig",
    "MCTSNode",
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
