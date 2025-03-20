"""Service for loading and processing March Machine Learning Mania data."""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class MarchMLManiaDataService:
    """Service for loading and processing March Machine Learning Mania data."""
    
    def __init__(self, data_dir: str = "march-machine-learning-mania-2025"):
        self.data_dir = Path(data_dir)
        self.teams_df = None
        self.tourney_results_df = None
        self.tourney_seeds_df = None
        self.regular_season_df = None
        self._load_data()
    
    def _load_data(self):
        """Load all necessary data files."""
        try:
            # Load teams data
            self.teams_df = pd.read_csv(
                self.data_dir / "MTeams.csv"
            )
            
            # Load tournament results
            self.tourney_results_df = pd.read_csv(
                self.data_dir / "MNCAATourneyDetailedResults.csv"
            )
            
            # Load tournament seeds
            self.tourney_seeds_df = pd.read_csv(
                self.data_dir / "MNCAATourneySeeds.csv"
            )
            
            # Load regular season results
            self.regular_season_df = pd.read_csv(
                self.data_dir / "MRegularSeasonDetailedResults.csv"
            )
            
        except Exception as e:
            logger.error(f"Error loading March ML Mania data: {e}")
            raise
    
    def get_team_name(self, team_id: int) -> str:
        """Get team name from ID."""
        team = self.teams_df[self.teams_df["TeamID"] == team_id]
        return team["TeamName"].iloc[0] if not team.empty else "Unknown"
    
    def get_tournament_history(self, team_id: int, start_year: int = None, end_year: int = None) -> Dict:
        """Get tournament history for a team."""
        # Filter by year range if provided
        results = self.tourney_results_df.copy()
        if start_year:
            results = results[results["Season"] >= start_year]
        if end_year:
            results = results[results["Season"] <= end_year]
        
        # Get games where team was winner or loser
        team_wins = results[results["WTeamID"] == team_id]
        team_losses = results[results["LTeamID"] == team_id]
        
        # Calculate statistics
        total_games = len(team_wins) + len(team_losses)
        wins = len(team_wins)
        win_pct = wins / total_games if total_games > 0 else 0
        
        # Calculate scoring stats
        points_scored = team_wins["WScore"].sum() + team_losses["LScore"].sum()
        points_allowed = team_wins["LScore"].sum() + team_losses["WScore"].sum()
        avg_margin = (points_scored - points_allowed) / total_games if total_games > 0 else 0
        
        # Get seeds for each appearance
        seeds = self.tourney_seeds_df[
            (self.tourney_seeds_df["TeamID"] == team_id)
        ]
        avg_seed = seeds["Seed"].mean() if not seeds.empty else None
        
        return {
            "games_played": total_games,
            "wins": wins,
            "losses": total_games - wins,
            "win_percentage": win_pct,
            "points_scored": points_scored,
            "points_allowed": points_allowed,
            "avg_scoring_margin": avg_margin,
            "appearances": len(seeds),
            "average_seed": avg_seed
        }
    
    def get_matchup_history(self, team1_id: int, team2_id: int, years_back: int = 10) -> Dict:
        """Get historical matchup data between two teams."""
        current_year = self.tourney_results_df["Season"].max()
        start_year = current_year - years_back
        
        # Get tournament matchups
        tourney_games = self.tourney_results_df[
            (
                ((self.tourney_results_df["WTeamID"] == team1_id) & 
                 (self.tourney_results_df["LTeamID"] == team2_id)) |
                ((self.tourney_results_df["WTeamID"] == team2_id) & 
                 (self.tourney_results_df["LTeamID"] == team1_id))
            ) &
            (self.tourney_results_df["Season"] >= start_year)
        ]
        
        # Get regular season matchups
        regular_games = self.regular_season_df[
            (
                ((self.regular_season_df["WTeamID"] == team1_id) & 
                 (self.regular_season_df["LTeamID"] == team2_id)) |
                ((self.regular_season_df["WTeamID"] == team2_id) & 
                 (self.regular_season_df["LTeamID"] == team1_id))
            ) &
            (self.regular_season_df["Season"] >= start_year)
        ]
        
        # Calculate head-to-head stats
        team1_tourney_wins = len(tourney_games[tourney_games["WTeamID"] == team1_id])
        team1_regular_wins = len(regular_games[regular_games["WTeamID"] == team1_id])
        
        total_games = len(tourney_games) + len(regular_games)
        team1_total_wins = team1_tourney_wins + team1_regular_wins
        
        return {
            "total_games": total_games,
            "tournament_games": len(tourney_games),
            "regular_season_games": len(regular_games),
            "team1_wins": team1_total_wins,
            "team2_wins": total_games - team1_total_wins,
            "team1_tournament_wins": team1_tourney_wins,
            "team2_tournament_wins": len(tourney_games) - team1_tourney_wins
        }
    
    def get_seed_matchup_stats(self, seed1: int, seed2: int, years_back: int = 10) -> Dict:
        """Analyze historical outcomes for specific seed matchups."""
        current_year = self.tourney_results_df["Season"].max()
        start_year = current_year - years_back
        
        # Get tournament games from recent years
        recent_games = self.tourney_results_df[
            self.tourney_results_df["Season"] >= start_year
        ]
        
        # Merge with seeds data
        games_with_seeds = pd.merge(
            recent_games,
            self.tourney_seeds_df[["Season", "TeamID", "Seed"]],
            left_on=["Season", "WTeamID"],
            right_on=["Season", "TeamID"],
            suffixes=("", "_winner")
        )
        games_with_seeds = pd.merge(
            games_with_seeds,
            self.tourney_seeds_df[["Season", "TeamID", "Seed"]],
            left_on=["Season", "LTeamID"],
            right_on=["Season", "TeamID"],
            suffixes=("_winner", "_loser")
        )
        
        # Filter for specific seed matchup
        matchups = games_with_seeds[
            ((games_with_seeds["Seed_winner"] == seed1) & 
             (games_with_seeds["Seed_loser"] == seed2)) |
            ((games_with_seeds["Seed_winner"] == seed2) & 
             (games_with_seeds["Seed_loser"] == seed1))
        ]
        
        total_games = len(matchups)
        if total_games == 0:
            return {
                "total_games": 0,
                "higher_seed_wins": 0,
                "upset_percentage": 0,
                "avg_point_diff": 0
            }
        
        # Calculate statistics
        higher_seed_wins = len(matchups[
            matchups["Seed_winner"] < matchups["Seed_loser"]
        ])
        
        return {
            "total_games": total_games,
            "higher_seed_wins": higher_seed_wins,
            "upset_percentage": (total_games - higher_seed_wins) / total_games * 100,
            "avg_point_diff": (matchups["WScore"] - matchups["LScore"]).mean()
        } 