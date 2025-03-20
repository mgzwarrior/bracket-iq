import logging
from typing import Dict, List, Tuple, Optional
import numpy as np
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
        
    def _calculate_team_score(self, team_id: int, seed: int, opponent_id: int, opponent_seed: int) -> float:
        """Calculate a team's score based on historical performance."""
        # Get team's tournament history
        history = self.march_ml_mania_service.get_tournament_history(team_id, years_back=10)
        
        # Get head-to-head history
        matchup_history = self.march_ml_mania_service.get_matchup_history(team_id, opponent_id)
        
        # Get seed matchup statistics
        seed_stats = self.march_ml_mania_service.get_seed_matchup_stats(seed, opponent_seed)
        
        # Calculate base score components
        tournament_success = history["win_percentage"] * 0.25  # 25% weight
        
        # Seed advantage (higher seeds are better, so we invert)
        seed_factor = (17 - seed) / 16  # Normalize to 0-1 range
        seed_weight = 0.30  # 30% weight
        
        # Head-to-head success
        h2h_games = matchup_history["total_games"]
        if h2h_games > 0:
            h2h_factor = matchup_history["team1_wins"] / h2h_games
        else:
            h2h_factor = 0.5  # Neutral if no history
        h2h_weight = 0.15  # 15% weight
        
        # Seed matchup historical success
        if seed < opponent_seed:  # If we're the higher seed
            upset_resistance = seed_stats["higher_seed_wins"] / seed_stats["total_games"] if seed_stats["total_games"] > 0 else 0.7
            seed_history_factor = upset_resistance
        else:  # If we're the lower seed
            upset_rate = seed_stats["upset_percentage"] / 100 if seed_stats["total_games"] > 0 else 0.3
            seed_history_factor = upset_rate
        seed_history_weight = 0.20  # 20% weight
        
        # Tournament experience bonus
        experience_bonus = min(history["appearances"] / 10, 1) * 0.10  # Up to 10% bonus
        
        # Combine all factors
        score = (tournament_success * 0.25 +
                seed_factor * seed_weight +
                h2h_factor * h2h_weight +
                seed_history_factor * seed_history_weight +
                experience_bonus)
        
        return score
    
    def predict_winner(self, team1: Team, team2: Team, seed1: int, seed2: int) -> Tuple[Team, float]:
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
        matchup_factors = self.bracketology_service.get_matchup_factors(team1, team2, seed1, seed2)
        
        # Calculate final scores incorporating all factors
        final_score1 = self._calculate_final_score(
            march_ml_mania_score1,
            matchup_factors,
            is_team1=True
        )
        final_score2 = self._calculate_final_score(
            march_ml_mania_score2,
            matchup_factors,
            is_team1=False
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
        tournament_stats = self.march_ml_mania_service.get_tournament_history(team)
        if tournament_stats.empty:
            return 0.0
        
        # Calculate score components from March ML Mania data
        win_pct = tournament_stats['wins'].sum() / len(tournament_stats)
        avg_margin = (tournament_stats['points_scored'] - tournament_stats['points_allowed']).mean()
        seed_factor = (17 - seed) / 16  # Normalize seed strength
        
        # Weighted combination
        return (win_pct * 0.4 + 
                (avg_margin / 30) * 0.3 +  # Normalize margin to 0-1 range
                seed_factor * 0.3)

    def _calculate_final_score(self, march_ml_mania_score: float, matchup_factors: Dict[str, float], is_team1: bool) -> float:
        """Calculate final score incorporating all factors.
        
        Args:
            march_ml_mania_score: Base score from March ML Mania data
            matchup_factors: Advanced factors from Bracketology data
            is_team1: Whether this is for team1 (vs team2)
            
        Returns:
            float: Final weighted score
        """
        if not matchup_factors:
            return march_ml_mania_score
        
        # Get relevant factors
        seed_advantage = matchup_factors['seed_advantage'] if is_team1 else (1 - matchup_factors['seed_advantage'])
        offensive_adv = matchup_factors['offensive_advantage'] if is_team1 else -matchup_factors['offensive_advantage']
        defensive_adv = matchup_factors['defensive_advantage'] if is_team1 else -matchup_factors['defensive_advantage']
        experience_adv = matchup_factors['experience_advantage'] if is_team1 else -matchup_factors['experience_advantage']
        
        # Normalize advanced metrics to 0-1 range
        offensive_factor = 0.5 + (offensive_adv / 20)  # Assuming max efficiency diff of ±20
        defensive_factor = 0.5 + (defensive_adv / 20)
        experience_factor = 0.5 + (experience_adv / 4)  # Assuming max experience diff of ±4 years
        
        # Weight the factors
        weights = {
            'march_ml_mania_historical': 0.25,
            'seed_advantage': 0.20,
            'offensive': 0.20,
            'defensive': 0.20,
            'experience': 0.15
        }
        
        final_score = (
            march_ml_mania_score * weights['march_ml_mania_historical'] +
            seed_advantage * weights['seed_advantage'] +
            offensive_factor * weights['offensive'] +
            defensive_factor * weights['defensive'] +
            experience_factor * weights['experience']
        )
        
        return max(0.0, min(1.0, final_score))  # Ensure score is between 0 and 1

    def get_upset_probability(self, higher_seed: int, lower_seed: int) -> float:
        """Calculate probability of an upset between seeds.
        
        Args:
            higher_seed: The numerically lower seed (better team)
            lower_seed: The numerically higher seed (underdog)
            
        Returns:
            float: Probability of upset (0-1)
        """
        if not (1 <= higher_seed <= 16 and 1 <= lower_seed <= 16):
            raise ValueError("Seeds must be between 1 and 16")
        if higher_seed >= lower_seed:
            raise ValueError("higher_seed must be numerically lower than lower_seed")
        
        # Combine probabilities from both datasets
        bracketology_prob = self.bracketology_service.get_upset_probability(higher_seed, lower_seed)
        
        # Get historical matchup data from March ML Mania
        march_ml_mania_history = self.march_ml_mania_service.get_seed_matchup_history(higher_seed, lower_seed)
        if not march_ml_mania_history.empty:
            march_ml_mania_prob = len(march_ml_mania_history[march_ml_mania_history['upset']]) / len(march_ml_mania_history)
        else:
            march_ml_mania_prob = 0.0
        
        # Weight the probabilities (favoring Bracketology's more detailed analysis)
        return 0.7 * bracketology_prob + 0.3 * march_ml_mania_prob

    def get_team_tournament_stats(self, team: Team) -> Dict[str, float]:
        """Get comprehensive tournament statistics for a team.
        
        Args:
            team: Team to analyze
            
        Returns:
            Dict containing various tournament statistics
        """
        # Get basic stats from March ML Mania data
        march_ml_mania_stats = self.march_ml_mania_service.get_tournament_history(team)
        if march_ml_mania_stats.empty:
            return {}
        
        # Get advanced stats from Bracketology data
        advanced_stats = self.bracketology_service.get_team_advanced_stats(team)
        
        # Combine the statistics
        basic_stats = {
            'games_played': len(march_ml_mania_stats),
            'wins': march_ml_mania_stats['wins'].sum(),
            'losses': len(march_ml_mania_stats) - march_ml_mania_stats['wins'].sum(),
            'points_scored': march_ml_mania_stats['points_scored'].mean(),
            'points_allowed': march_ml_mania_stats['points_allowed'].mean(),
            'avg_seed': march_ml_mania_stats['seed'].mean()
        }
        
        # Calculate derived statistics
        basic_stats['win_percentage'] = basic_stats['wins'] / basic_stats['games_played']
        basic_stats['avg_scoring_margin'] = basic_stats['points_scored'] - basic_stats['points_allowed']
        
        # Merge with advanced stats if available
        if advanced_stats:
            basic_stats.update(advanced_stats)
        
        return basic_stats

    def get_matchup_analysis(self, team1: Team, team2: Team, seed1: int, seed2: int) -> Dict[str, float]:
        """Get detailed analysis of a matchup.
        
        Args:
            team1: First team
            team2: Second team
            seed1: First team's seed
            seed2: Second team's seed
            
        Returns:
            Dict containing detailed matchup analysis
        """
        # Get matchup factors from Bracketology data
        factors = self.bracketology_service.get_matchup_factors(team1, team2, seed1, seed2)
        
        # Get historical head-to-head from March ML Mania data
        h2h = self.march_ml_mania_service.get_head_to_head(team1, team2)
        
        # Calculate head-to-head stats if available
        if not h2h.empty:
            team1_wins = len(h2h[h2h['winner_id'] == team1.id])
            total_games = len(h2h)
            h2h_win_pct = team1_wins / total_games
            avg_margin = h2h[h2h['winner_id'] == team1.id]['point_diff'].mean()
        else:
            h2h_win_pct = 0.5
            avg_margin = 0.0
        
        # Combine all analysis factors
        analysis = {
            'head_to_head_win_pct': h2h_win_pct,
            'head_to_head_avg_margin': avg_margin,
            'upset_probability': self.get_upset_probability(min(seed1, seed2), max(seed1, seed2))
        }
        
        # Add Bracketology factors
        analysis.update(factors)
        
        return analysis 