import logging
from typing import Dict, List, Tuple, Optional, Any, Union, cast
import numpy as np  # type: ignore
from ..models import Team, Tournament, Round
from ..services.march_ml_mania_data import MarchMLManiaDataService
from ..services.bracketology_data import BracketologyDataService

logger = logging.getLogger(__name__)


class HistoricalAnalyzer:
    """Analyzes historical tournament data to make predictions."""

    def __init__(self):
        """Initialize the analyzer with data services."""
        self.march_ml_mania_service = MarchMLManiaDataService()
        self.bracketology_service = BracketologyDataService()

    def _calculate_team_score(
        self, team_id: int, seed: int, opponent_id: int, opponent_seed: int
    ) -> float:
        """Calculate a team's score based on historical performance."""
        # Get team's tournament history
        history = self.march_ml_mania_service.get_tournament_history(str(team_id))

        # Get head-to-head history
        matchup_history = self.march_ml_mania_service.get_matchup_history(
            str(team_id), str(opponent_id)
        )

        # Get seed matchup statistics
        seed_stats = self.march_ml_mania_service.get_seed_matchup_stats(
            seed, opponent_seed
        )

        # Calculate base score components
        tournament_success = history.get("win_pct", 0.0) * 0.25  # 25% weight

        # Seed advantage (higher seeds are better, so we invert)
        seed_factor = (17 - seed) / 16  # Normalize to 0-1 range
        seed_weight = 0.30  # 30% weight

        # Head-to-head success
        h2h_games = matchup_history.get("games", 0)
        if h2h_games > 0:
            h2h_factor = matchup_history.get("team1_wins", 0) / h2h_games
        else:
            h2h_factor = 0.5  # Neutral if no history
        h2h_weight = 0.15  # 15% weight

        # Seed matchup historical success
        if seed < opponent_seed:  # If we're the higher seed
            upset_resistance = (
                seed_stats.get("higher_seed_wins", 0) / seed_stats.get("total_games", 1)
                if seed_stats.get("total_games", 0) > 0
                else 0.7
            )
            seed_history_factor = upset_resistance
        else:  # If we're the lower seed
            upset_rate = (
                seed_stats.get("upset_percentage", 0.0) / 100
                if seed_stats.get("total_games", 0) > 0
                else 0.3
            )
            seed_history_factor = upset_rate
        seed_history_weight = 0.20  # 20% weight

        # Tournament experience bonus
        experience_bonus = (
            min(history.get("appearances", 0) / 10, 1) * 0.10
        )  # Up to 10% bonus

        # Combine all factors
        score = (
            tournament_success * 0.25
            + seed_factor * seed_weight
            + h2h_factor * h2h_weight
            + seed_history_factor * seed_history_weight
            + experience_bonus
        )

        return float(score)

    def predict_winner(
        self, team1: Team, team2: Team, seed1: int, seed2: int
    ) -> Tuple[Team, float]:
        """Predict the winner of a matchup and return confidence percentage.

        Args:
            team1: First team in matchup
            team2: Second team in matchup
            seed1: Tournament seed of first team
            seed2: Tournament seed of second team

        Returns:
            Tuple of (predicted_winner, confidence_percentage)
        """
        # Get historical data from both services
        march_ml_mania_score1 = self._calculate_march_ml_mania_score(team1, seed1)
        march_ml_mania_score2 = self._calculate_march_ml_mania_score(team2, seed2)

        # Get advanced matchup factors from Bracketology data
        matchup_factors = self.bracketology_service.get_matchup_factors(
            team1, team2, seed1, seed2
        )

        # Calculate final scores incorporating all factors
        final_score1 = float(
            self._calculate_final_score(
                historical_weight=0.6,
                statistical_weight=0.4,
                historical_score=march_ml_mania_score1,
                statistical_score=matchup_factors.get("team1_score", 0.5),
            )
        )
        final_score2 = float(
            self._calculate_final_score(
                historical_weight=0.6,
                statistical_weight=0.4,
                historical_score=march_ml_mania_score2,
                statistical_score=matchup_factors.get("team2_score", 0.5),
            )
        )

        # Determine winner and confidence
        total_score = final_score1 + final_score2
        if total_score == 0:
            # If no data available, slightly favor the better seed
            return (team1, 55.0) if seed1 < seed2 else (team2, 55.0)

        team1_probability = final_score1 / total_score
        confidence = abs(team1_probability - 0.5) * 2 * 100  # Convert to percentage

        return (team1, confidence) if team1_probability > 0.5 else (team2, confidence)

    def _calculate_march_ml_mania_score(self, team: Team, seed: int) -> float:
        """Calculate a team's base score using March ML Mania dataset."""
        tournament_stats = self.march_ml_mania_service.get_tournament_history(team.name)
        if not tournament_stats:  # Check if dict is empty
            return 0.0

        # Calculate score components from March ML Mania data
        win_pct = tournament_stats.get("win_pct", 0.0)
        avg_seed = tournament_stats.get("avg_seed", 0.0)
        seed_factor = (17 - seed) / 16  # Normalize seed strength

        # Weighted combination
        return float(
            win_pct * 0.4
            + ((17 - avg_seed) / 16) * 0.3  # Normalize seed to 0-1 range
            + seed_factor * 0.3
        )

    def _calculate_final_score(
        self,
        historical_weight: float,
        statistical_weight: float,
        historical_score: float,
        statistical_score: float,
    ) -> float:
        """Calculate final score combining historical and statistical data."""
        return float(
            (historical_score * historical_weight)
            + (statistical_score * statistical_weight)
        )

    def get_upset_probability(self, higher_seed: int, lower_seed: int) -> float:
        """Get probability of an upset for a seed matchup."""
        # Get historical upset data from Bracketology service
        base_prob = self.bracketology_service.get_upset_probability(
            higher_seed, lower_seed
        )

        # Adjust based on seed difference
        seed_diff = lower_seed - higher_seed
        seed_factor = seed_diff / 15  # Normalize to 0-1 range

        # Final probability is weighted combination
        return float(base_prob * 0.7 + seed_factor * 0.3)

    def get_team_tournament_stats(self, team: Team) -> Dict[str, float]:
        """Get comprehensive tournament statistics for a team."""
        # Get basic stats from March ML Mania data
        stats = self.march_ml_mania_service.get_tournament_history(team.name)
        if not stats:  # Check if dict is empty
            return {
                "appearances": 0.0,
                "wins": 0.0,
                "losses": 0.0,
            }
        return cast(Dict[str, float], stats)

    def get_matchup_analysis(
        self, team1: Team, team2: Team, seed1: int, seed2: int
    ) -> Dict[str, Any]:
        """Get detailed analysis of a matchup."""
        # Get head-to-head history
        h2h_stats = self.march_ml_mania_service.get_matchup_history(
            team1.name, team2.name
        )

        # Calculate win percentage and average margin
        total_games = h2h_stats.get("games", 0)
        team1_wins = h2h_stats.get("team1_wins", 0)
        win_pct = 0.5 if total_games == 0 else team1_wins / total_games
        avg_margin = h2h_stats.get("avg_margin", 0.0)

        # Get upset probability if applicable
        if seed1 < seed2:
            upset_prob = self.get_upset_probability(seed1, seed2)
        else:
            upset_prob = self.get_upset_probability(seed2, seed1)

        return {
            "historical_matchups": h2h_stats,
            "team_comparisons": {
                "head_to_head_win_pct": win_pct,
                "head_to_head_avg_margin": avg_margin,
                "upset_probability": upset_prob,
            },
        }
