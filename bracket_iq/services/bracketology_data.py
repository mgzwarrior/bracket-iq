"""Service for handling the Bracketology dataset with advanced features."""
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from bracket_iq.models import Team

class BracketologyDataService:
    """Service for loading and processing the Bracketology dataset."""
    
    def __init__(self, data_dir: str = "kaggle_datasets/march-madness-data"):
        """Initialize the service with the data directory."""
        self.data_dir = data_dir
        self._upset_stats = None
        self._seed_matchups = None
        self._team_stats = None
        self._conference_stats = None
        self._team_archetypes = None
    
    def _load_upset_stats(self) -> pd.DataFrame:
        """Load upset statistics data."""
        if self._upset_stats is None:
            path = os.path.join(self.data_dir, "upset_stats.csv")
            self._upset_stats = pd.read_csv(path)
        return self._upset_stats
    
    def _load_seed_matchups(self) -> pd.DataFrame:
        """Load seed matchup statistics."""
        if self._seed_matchups is None:
            path = os.path.join(self.data_dir, "seed_matchups.csv")
            self._seed_matchups = pd.read_csv(path)
        return self._seed_matchups
    
    def _load_team_stats(self) -> pd.DataFrame:
        """Load detailed team statistics."""
        if self._team_stats is None:
            path = os.path.join(self.data_dir, "team_stats.csv")
            self._team_stats = pd.read_csv(path)
        return self._team_stats
    
    def _load_conference_stats(self) -> pd.DataFrame:
        """Load conference performance statistics."""
        if self._conference_stats is None:
            path = os.path.join(self.data_dir, "conference_stats.csv")
            self._conference_stats = pd.read_csv(path)
        return self._conference_stats
    
    def _load_team_archetypes(self) -> pd.DataFrame:
        """Load team archetype classifications."""
        if self._team_archetypes is None:
            path = os.path.join(self.data_dir, "team_archetypes.csv")
            self._team_archetypes = pd.read_csv(path)
        return self._team_archetypes
    
    def get_upset_probability(self, higher_seed: int, lower_seed: int) -> float:
        """Get the historical probability of an upset between two seeds.
        
        Args:
            higher_seed: The numerically lower seed (better team)
            lower_seed: The numerically higher seed (underdog)
            
        Returns:
            float: Probability of an upset (0-1)
        """
        upset_stats = self._load_upset_stats()
        matchup = upset_stats[
            (upset_stats['higher_seed'] == higher_seed) & 
            (upset_stats['lower_seed'] == lower_seed)
        ]
        if matchup.empty:
            return 0.0
        return float(matchup['upset_probability'].iloc[0])
    
    def get_seed_matchup_stats(self, seed1: int, seed2: int) -> Dict[str, float]:
        """Get historical statistics for matchups between two seeds.
        
        Args:
            seed1: First team's seed
            seed2: Second team's seed
            
        Returns:
            Dict containing:
                - win_probability: Historical win probability for seed1
                - avg_point_diff: Average point differential
                - close_game_probability: Probability of game being decided by 5 or fewer points
        """
        matchups = self._load_seed_matchups()
        stats = matchups[
            ((matchups['seed1'] == seed1) & (matchups['seed2'] == seed2)) |
            ((matchups['seed1'] == seed2) & (matchups['seed2'] == seed1))
        ]
        
        if stats.empty:
            return {
                'win_probability': 0.5,
                'avg_point_diff': 0.0,
                'close_game_probability': 0.0
            }
        
        # Normalize stats based on seed1 perspective
        is_reversed = stats['seed1'].iloc[0] != seed1
        win_prob = float(stats['seed1_win_probability'].iloc[0])
        point_diff = float(stats['avg_point_differential'].iloc[0])
        
        return {
            'win_probability': 1 - win_prob if is_reversed else win_prob,
            'avg_point_diff': -point_diff if is_reversed else point_diff,
            'close_game_probability': float(stats['close_game_probability'].iloc[0])
        }
    
    def get_team_archetype(self, team: Team) -> Optional[str]:
        """Get the playing style archetype for a team.
        
        Args:
            team: Team object
            
        Returns:
            str: Team's archetype (e.g., 'Offensive Powerhouse', 'Defensive Specialist', etc.)
        """
        archetypes = self._load_team_archetypes()
        team_data = archetypes[archetypes['team_id'] == team.id]
        if team_data.empty:
            return None
        return str(team_data['archetype'].iloc[0])
    
    def get_team_advanced_stats(self, team: Team) -> Dict[str, float]:
        """Get advanced statistics for a team.
        
        Args:
            team: Team object
            
        Returns:
            Dict containing advanced metrics:
                - offensive_efficiency
                - defensive_efficiency
                - tempo
                - experience
                - bench_minutes
                - etc.
        """
        stats = self._load_team_stats()
        team_stats = stats[stats['team_id'] == team.id]
        
        if team_stats.empty:
            return {}
        
        return {
            'offensive_efficiency': float(team_stats['offensive_efficiency'].iloc[0]),
            'defensive_efficiency': float(team_stats['defensive_efficiency'].iloc[0]),
            'tempo': float(team_stats['tempo'].iloc[0]),
            'experience': float(team_stats['experience'].iloc[0]),
            'bench_minutes': float(team_stats['bench_minutes'].iloc[0]),
            'effective_fg_pct': float(team_stats['effective_fg_pct'].iloc[0]),
            'turnover_pct': float(team_stats['turnover_pct'].iloc[0]),
            'offensive_reb_pct': float(team_stats['offensive_reb_pct'].iloc[0]),
            'ft_rate': float(team_stats['ft_rate'].iloc[0])
        }
    
    def get_conference_strength(self, conference_id: str) -> Dict[str, float]:
        """Get conference strength metrics.
        
        Args:
            conference_id: Conference identifier
            
        Returns:
            Dict containing:
                - overall_rating
                - sos_rank
                - tournament_success_rate
                - etc.
        """
        conf_stats = self._load_conference_stats()
        conference = conf_stats[conf_stats['conference_id'] == conference_id]
        
        if conference.empty:
            return {}
        
        return {
            'overall_rating': float(conference['overall_rating'].iloc[0]),
            'sos_rank': float(conference['sos_rank'].iloc[0]),
            'tournament_success_rate': float(conference['tournament_success_rate'].iloc[0]),
            'avg_seed': float(conference['avg_seed'].iloc[0]),
            'sweet_16_appearances': float(conference['sweet_16_appearances'].iloc[0])
        }
    
    def get_matchup_factors(self, team1: Team, team2: Team, seed1: int, seed2: int) -> Dict[str, float]:
        """Get comprehensive matchup analysis factors.
        
        Args:
            team1: First team
            team2: Second team
            seed1: First team's seed
            seed2: Second team's seed
            
        Returns:
            Dict containing all relevant matchup factors:
                - seed_advantage
                - style_matchup
                - conference_advantage
                - experience_factor
                - etc.
        """
        # Get team stats
        team1_stats = self.get_team_advanced_stats(team1)
        team2_stats = self.get_team_advanced_stats(team2)
        
        # Get seed matchup stats
        seed_stats = self.get_seed_matchup_stats(seed1, seed2)
        
        # Get team archetypes
        team1_archetype = self.get_team_archetype(team1)
        team2_archetype = self.get_team_archetype(team2)
        
        # Calculate style matchup score (if archetypes available)
        style_matchup = 0.0
        if team1_archetype and team2_archetype:
            # This would be based on historical performance between archetypes
            # For now, using a placeholder neutral value
            style_matchup = 0.5
        
        # Calculate statistical advantages
        if team1_stats and team2_stats:
            offensive_advantage = team1_stats['offensive_efficiency'] - team2_stats['defensive_efficiency']
            defensive_advantage = team1_stats['defensive_efficiency'] - team2_stats['offensive_efficiency']
            tempo_factor = abs(team1_stats['tempo'] - team2_stats['tempo'])
            experience_advantage = team1_stats['experience'] - team2_stats['experience']
        else:
            offensive_advantage = defensive_advantage = tempo_factor = experience_advantage = 0.0
        
        return {
            'seed_advantage': seed_stats['win_probability'],
            'style_matchup': style_matchup,
            'offensive_advantage': offensive_advantage,
            'defensive_advantage': defensive_advantage,
            'tempo_factor': tempo_factor,
            'experience_advantage': experience_advantage,
            'expected_point_diff': seed_stats['avg_point_diff'],
            'close_game_likelihood': seed_stats['close_game_probability']
        } 