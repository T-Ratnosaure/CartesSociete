"""Statistics-based player using tournament card presence win rates.

This player uses empirical win rate data from the Layer-1 tournament
to evaluate cards. Cards with higher presence win rates are prioritized
for both buying and playing.

Data source: tournament_cards_42 (22,600 games, protocol 1.1.0)
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.game.state import GameState, PlayerState

from .action import Action, ActionType
from .base import Player, PlayerInfo

# Card presence win rates from tournament_cards_42
# Format: card_id -> win_rate (0.0 to 1.0)
# Only cards with 100+ appearances included for statistical validity
CARD_WIN_RATES: dict[str, float] = {
    # Top performers (>70% win rate)
    "cyborg_lolo_le_gorille_2": 0.836,
    "atlantide_rathon_2": 0.825,
    "raton_eraton_2": 0.821,
    "nature_ancien_de_la_nature_2": 0.811,
    "lapin_gardien_des_carottes_2": 0.810,
    "atlantide_maitre_des_flots_2": 0.806,
    "atlantide_reine_des_flots_2": 0.804,
    "neige_bonhomme_de_neige_2": 0.803,
    "nature_druide_ancien_2": 0.798,
    "raton_raton_baveur_2": 0.794,
    "hall_of_win_chevalier_demoniaque_2": 0.786,
    "lapin_lapindrax_2": 0.782,
    "neige_yeti_2": 0.780,
    "atlantide_poulpe_geant_2": 0.774,
    "cyborg_invocatrice_steam_2": 0.770,
    "lapin_lapindompte_2": 0.769,
    "nature_treant_ancien_2": 0.766,
    "raton_archimage_raton_2": 0.762,
    "neige_pere_noel_2": 0.757,
    "hall_of_win_wyrm_de_glace_2": 0.754,
    "ninja_maitre_rat_2": 0.749,
    "ninja_dryade_lotus_2": 0.745,
    # Strong performers (60-70% win rate)
    "cyborg_lolo_le_gorille_1": 0.669,
    "lapin_lapindrax_1": 0.640,
    "lapin_gardien_des_carottes_1": 0.631,
    "nature_diplo_terre_1": 0.590,
    "atlantide_diplo_mer_1": 0.579,
    "ninja_diplo_air_1": 0.573,
    "raton_eraton_1": 0.571,
    "neige_marchand_de_glace_1": 0.568,
    "atlantide_joe_le_fish_1": 0.563,
    "hall_of_win_demon_du_hasard_1": 0.555,
    "lapin_lapinvocateur_1": 0.530,
    "neige_pere_noel_1": 0.526,
    "nature_ancien_de_la_nature_1": 0.524,
    "atlantide_reine_des_flots_1": 0.520,
    "neige_mur_de_glace_1": 0.504,
    "hall_of_win_wyrm_de_glace_1": 0.499,
    "ninja_maitre_rat_1": 0.486,
    "lapin_lapindomptable_1": 0.482,
    "hall_of_win_chevalier_demoniaque_1": 0.482,
    "nature_treant_ancien_1": 0.471,
    # Weak performers (<50% win rate)
    "ninja_dryade_lotus_1": 0.417,
    "cyborg_invocatrice_steam_1": 0.408,
    "raton_archimage_raton_1": 0.387,
    "raton_raton_baveur_1": 0.380,
    "neige_bonhomme_de_neige_1": 0.375,
    "atlantide_poulpe_geant_1": 0.370,
    "neige_yeti_1": 0.365,
    "cyborg_tech_goblin_1": 0.355,
    "hall_of_win_demon_du_hasard_2": 0.345,
    "nature_druide_ancien_1": 0.340,
    "atlantide_rathon_1": 0.335,
    "atlantide_maitre_des_flots_1": 0.330,
    "ninja_tigre_lotus_1": 0.293,
    "lapin_lapincruste_2": 0.285,
    "ninja_invocatrice_ninja_1": 0.240,
}

# Family average win rates (fallback when card not in CARD_WIN_RATES)
FAMILY_WIN_RATES: dict[str, float] = {
    "atlantide": 0.610,
    "nature": 0.545,
    "lapin": 0.533,
    "raton": 0.528,
    "hall_of_win": 0.518,
    "hall": 0.518,  # Alias
    "neige": 0.483,
    "cyborg": 0.460,
    "ninja": 0.461,
    "arme": 0.500,  # Neutral for weapons
    "demon": 0.500,  # Neutral for demons
}

# Level bonus (Level 2 cards have significantly higher win rates)
LEVEL_2_BONUS = 0.10  # +10% for Level 2 cards when estimating


def get_card_win_rate(card_id: str, family: str, level: int) -> float:
    """Get the win rate for a card, using fallbacks if not found.

    Args:
        card_id: The card's unique identifier.
        family: The card's family (lowercase).
        level: The card's level (1 or 2).

    Returns:
        Estimated win rate between 0.0 and 1.0.
    """
    # Direct lookup
    if card_id in CARD_WIN_RATES:
        return CARD_WIN_RATES[card_id]

    # Fallback: family average + level bonus
    family_lower = family.lower().replace(" ", "_")
    base_rate = FAMILY_WIN_RATES.get(family_lower, 0.50)

    if level == 2:
        return min(1.0, base_rate + LEVEL_2_BONUS)
    return base_rate


class StatsPlayer(Player):
    """Player that uses empirical card presence win rates.

    This player prioritizes cards based on their correlation with winning
    from the Layer-1 tournament data (22,600 games).

    Strategy:
    - MARKET: Buy cards with highest presence win rates
    - PLAY: Always evolve when possible, then play highest win rate cards

    Note: This is observational correlation, not causal. Cards may appear
    in winning decks because winners have more cards, not because the
    cards caused the win.
    """

    @property
    def info(self) -> PlayerInfo:
        """Return metadata about this player agent."""
        return PlayerInfo(
            name=self._name or f"stats_{self.player_id}",
            agent_type="stats",
            version="1.0.0",
        )

    def _get_card_score(self, card) -> float:
        """Get the win rate score for a card.

        Args:
            card: The card to evaluate.

        Returns:
            Win rate score between 0.0 and 1.0.
        """
        family_str = card.family.value.lower().replace(" ", "_")
        return get_card_win_rate(card.id, family_str, card.level)

    def choose_market_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Buy the card with highest presence win rate.

        Args:
            state: Current game state.
            player_state: This player's state.
            legal_actions: Available actions.

        Returns:
            The buy action for the highest win rate card, or end_phase.
        """
        buy_actions = [
            a
            for a in legal_actions
            if a.action_type == ActionType.BUY_CARD and a.card is not None
        ]

        if not buy_actions:
            return Action.end_phase()

        # Score by presence win rate
        scored = [(a, self._get_card_score(a.card)) for a in buy_actions]
        scored.sort(key=lambda x: x[1], reverse=True)

        # Buy highest win rate card
        return scored[0][0]

    def choose_play_action(
        self,
        state: "GameState",
        player_state: "PlayerState",
        legal_actions: list[Action],
    ) -> Action:
        """Play cards prioritizing evolution and high win rate.

        Evolution is always prioritized (Level 2 cards have ~10% higher
        win rates). Then plays the highest win rate card from hand.

        Args:
            state: Current game state.
            player_state: This player's state.
            legal_actions: Available actions.

        Returns:
            The chosen play action, or end_phase.
        """
        # First priority: always evolve (Level 2 significantly better)
        evolve_actions = [
            a for a in legal_actions if a.action_type == ActionType.EVOLVE
        ]
        if evolve_actions:
            return evolve_actions[0]

        # Second priority: play cards from hand by win rate
        play_actions = [
            a
            for a in legal_actions
            if a.action_type == ActionType.PLAY_CARD and a.card is not None
        ]

        if play_actions:
            scored = [(a, self._get_card_score(a.card)) for a in play_actions]
            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[0][0]

        # Third priority: replace cards if beneficial
        replace_actions = [
            a
            for a in legal_actions
            if a.action_type == ActionType.REPLACE_CARD
            and a.card is not None
            and a.target_card is not None
        ]

        if replace_actions:
            best_action = None
            best_improvement = 0.0

            for action in replace_actions:
                new_score = self._get_card_score(action.card)
                old_score = self._get_card_score(action.target_card)
                improvement = new_score - old_score

                if improvement > best_improvement:
                    best_improvement = improvement
                    best_action = action

            if best_action is not None and best_improvement > 0:
                return best_action

        return Action.end_phase()
