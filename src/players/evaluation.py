"""Card evaluation utilities for AI players.

This module provides heuristic functions for evaluating cards and board positions.
These are used by greedy and heuristic players to make decisions.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.cards.models import Card
    from src.game.state import GameState, PlayerState


def calculate_base_value(card: "Card") -> float:
    """Calculate raw stat value of a card.

    Args:
        card: The card to evaluate.

    Returns:
        Base value (ATK + HP).
    """
    return float(card.attack + card.health)


def calculate_family_synergy(
    card: "Card",
    player_state: "PlayerState",
) -> float:
    """Calculate family synergy bonus.

    Family synergies scale with the number of cards of the same family
    on the board. This gives bonus value for cards that match existing
    board composition.

    Args:
        card: The card being evaluated.
        player_state: Current player state.

    Returns:
        Synergy bonus based on family members on board.
    """
    family_count = sum(1 for c in player_state.board if c.family == card.family)
    # Scaling bonuses typically activate at 2, 3, 4, 5, 6, 8
    # Give bonus for approaching thresholds
    if family_count >= 1:
        return family_count * 0.5
    return 0.0


def calculate_class_synergy(
    card: "Card",
    player_state: "PlayerState",
) -> float:
    """Calculate class synergy bonus.

    Class abilities also scale with matching cards on board.

    Args:
        card: The card being evaluated.
        player_state: Current player state.

    Returns:
        Synergy bonus based on class members on board.
    """
    class_count = sum(1 for c in player_state.board if c.card_class == card.card_class)
    if class_count >= 1:
        return class_count * 0.3
    return 0.0


def calculate_evolution_potential(
    card: "Card",
    player_state: "PlayerState",
) -> float:
    """Calculate evolution potential bonus.

    Higher value if we're close to evolving this card (have copies).

    Args:
        card: The card being evaluated.
        player_state: Current player state.

    Returns:
        Evolution potential bonus.
    """
    # Count copies of this card in hand and board (Level 1 only)
    name_count = sum(
        1
        for c in player_state.hand + player_state.board
        if c.name == card.name and c.level == 1
    )

    # 0 copies: no bonus
    # 1 copy: small bonus (we have 1, need 2 more)
    # 2 copies: large bonus (we're 1 away from evolution!)
    if name_count >= 2:
        return 3.0  # Very close to evolution
    elif name_count == 1:
        return 1.0  # Building towards it
    return 0.0


def calculate_imblocable_bonus(card: "Card") -> float:
    """Calculate bonus for imblocable damage.

    Imblocable damage is extremely valuable as it bypasses defense.

    Args:
        card: The card being evaluated.

    Returns:
        Imblocable damage bonus.
    """
    return card.class_abilities.imblocable_damage * 2.5


def calculate_cost_efficiency(card: "Card") -> float:
    """Calculate cost efficiency (value per PO).

    Args:
        card: The card being evaluated.

    Returns:
        Cost efficiency ratio.
    """
    base = card.attack + card.health
    cost = card.cost or 1  # Treat X-cost as 1 for comparison
    return base / max(cost, 1)


def evaluate_card_for_purchase(
    card: "Card",
    player_state: "PlayerState",
    state: "GameState",
) -> float:
    """Comprehensive card evaluation for purchase decisions.

    Combines multiple factors to determine the value of buying a card.

    Args:
        card: The card to evaluate.
        player_state: Current player state.
        state: Current game state.

    Returns:
        Total evaluation score (higher is better).
    """
    score = calculate_base_value(card)
    score += calculate_family_synergy(card, player_state)
    score += calculate_class_synergy(card, player_state)
    score += calculate_evolution_potential(card, player_state)
    score += calculate_imblocable_bonus(card)
    score += calculate_cost_efficiency(card)

    # Late game bonus for high-stat cards
    if state.turn >= 7:
        score += card.attack * 0.3  # Prioritize damage late game

    return score


def evaluate_card_for_play(
    card: "Card",
    player_state: "PlayerState",
    state: "GameState",
) -> float:
    """Evaluate a card for playing from hand to board.

    Args:
        card: The card to evaluate.
        player_state: Current player state.
        state: Current game state.

    Returns:
        Play priority score (higher = play first).
    """
    score = calculate_base_value(card)
    score += calculate_family_synergy(card, player_state)
    score += calculate_class_synergy(card, player_state)
    score += calculate_imblocable_bonus(card)

    return score


def evaluate_board_position(player_state: "PlayerState") -> float:
    """Evaluate the strength of a player's board position.

    Args:
        player_state: The player state to evaluate.

    Returns:
        Board strength score.
    """
    total_atk = player_state.get_total_attack()
    total_hp = player_state.get_total_health()

    # Calculate imblocable damage
    imblocable = sum(c.class_abilities.imblocable_damage for c in player_state.board)

    return float(total_atk + total_hp + imblocable * 2)


def evaluate_threat_level(
    player_state: "PlayerState",
    opponents: list["PlayerState"],
) -> float:
    """Evaluate threat level from opponents.

    Args:
        player_state: This player's state.
        opponents: List of opponent states.

    Returns:
        Threat score (higher = more danger).
    """
    if not opponents:
        return 0.0

    own_defense = player_state.get_total_health()
    max_threat = 0.0

    for opp in opponents:
        opp_attack = opp.get_total_attack()
        opp_imblocable = sum(c.class_abilities.imblocable_damage for c in opp.board)
        # Damage = max(0, attack - defense) + imblocable
        potential_damage = max(0, opp_attack - own_defense) + opp_imblocable
        max_threat = max(max_threat, potential_damage)

    return max_threat
