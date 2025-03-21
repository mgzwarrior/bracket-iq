"""Service for loading and processing March Machine Learning Mania data."""

import pandas as pd  # type: ignore
import numpy as np  # type: ignore
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import logging

logger = logging.getLogger(__name__)


class MarchMLManiaDataService:
    """Service for loading and processing March Machine Learning Mania data."""

    def __init__(self, data_dir: str = "march-machine-learning-mania-2025"):
        self.data_dir = Path(data_dir)
        self.teams_df: Optional[pd.DataFrame] = None
        self.tourney_results_df: Optional[pd.DataFrame] = None
        self.tourney_seeds_df: Optional[pd.DataFrame] = None
        self.regular_season_df: Optional[pd.DataFrame] = None
        self._load_data()

    def _load_data(self) -> None:
        """Load all necessary data files."""
        try:
            # Load teams data
            self.teams_df = pd.read_csv(self.data_dir / "MTeams.csv")

            # Load tournament results
            self.tourney_results_df = pd.read_csv(
                self.data_dir / "MNCAATourneyDetailedResults.csv"
            )

            # Load tournament seeds
            self.tourney_seeds_df = pd.read_csv(self.data_dir / "MNCAATourneySeeds.csv")

            # Load regular season results
            self.regular_season_df = pd.read_csv(
                self.data_dir / "MRegularSeasonDetailedResults.csv"
            )

        except Exception as e:
            logger.error("Error loading March ML Mania data: %s", str(e))
            raise

    def get_team_name(self, team_id: int) -> str:
        """Get team name from ID."""
        if self.teams_df is None:
            return "Unknown"
        team = self.teams_df[self.teams_df["TeamID"] == team_id]
        return str(team["TeamName"].iloc[0]) if not team.empty else "Unknown"

    def get_tournament_history(
        self,
        team: Union[str, int],
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get a team's tournament history."""
        if self.tourney_results_df is None or self.tourney_seeds_df is None:
            return {}

        # Convert team name to ID if necessary
        team_id = team if isinstance(team, int) else self._get_team_id(team)
        if team_id is None:
            return {}

        # Filter by year range if specified
        results = self.tourney_results_df
        if start_year is not None:
            results = results[results["Season"] >= start_year]
        if end_year is not None:
            results = results[results["Season"] <= end_year]

        # Get games where team was involved
        team_games = results[
            (results["WTeamID"] == team_id) | (results["LTeamID"] == team_id)
        ]

        # Calculate statistics
        total_games = len(team_games)
        if total_games == 0:
            return {}

        wins = len(team_games[team_games["WTeamID"] == team_id])
        losses = total_games - wins

        # Get team's seeds over the years
        if self.tourney_seeds_df is not None:
            team_seeds = self.tourney_seeds_df[
                self.tourney_seeds_df["TeamID"] == team_id
            ]
            avg_seed = float(team_seeds["Seed"].mean()) if not team_seeds.empty else 0.0
        else:
            avg_seed = 0.0

        return {
            "appearances": total_games,
            "wins": wins,
            "losses": losses,
            "win_pct": wins / total_games if total_games > 0 else 0.0,
            "avg_seed": avg_seed,
        }

    def get_matchup_history(
        self, team1: Union[str, int], team2: Union[str, int]
    ) -> Dict[str, Any]:
        """Get historical matchup data between two teams."""
        if self.tourney_results_df is None:
            return {}

        # Convert team names to IDs if necessary
        team1_id = team1 if isinstance(team1, int) else self._get_team_id(team1)
        team2_id = team2 if isinstance(team2, int) else self._get_team_id(team2)

        if team1_id is None or team2_id is None:
            return {}

        # Get all games between these teams
        matchups = self.tourney_results_df[
            (
                (self.tourney_results_df["WTeamID"] == team1_id)
                & (self.tourney_results_df["LTeamID"] == team2_id)
            )
            | (
                (self.tourney_results_df["WTeamID"] == team2_id)
                & (self.tourney_results_df["LTeamID"] == team1_id)
            )
        ]

        total_games = len(matchups)
        if total_games == 0:
            return {}

        # Calculate head-to-head stats
        team1_wins = len(
            matchups[
                (matchups["WTeamID"] == team1_id) | (matchups["LTeamID"] == team2_id)
            ]
        )

        # Calculate average margin
        margins = []
        for _, game in matchups.iterrows():
            if game["WTeamID"] == team1_id:
                margins.append(game["WScore"] - game["LScore"])
            else:
                margins.append(game["LScore"] - game["WScore"])

        avg_margin = float(np.mean(margins)) if margins else 0.0

        return {
            "games": total_games,
            "team1_wins": team1_wins,
            "team2_wins": total_games - team1_wins,
            "avg_margin": avg_margin,
        }

    def get_seed_matchup_stats(self, seed1: int, seed2: int) -> Dict[str, Any]:
        """Get historical statistics for matchups between seeds."""
        if self.tourney_results_df is None or self.tourney_seeds_df is None:
            return {}

        # Get all games between these seeds
        seed_matchups = pd.merge(
            self.tourney_results_df,
            self.tourney_seeds_df[["Season", "TeamID", "Seed"]],
            left_on=["Season", "WTeamID"],
            right_on=["Season", "TeamID"],
        )
        seed_matchups = pd.merge(
            seed_matchups,
            self.tourney_seeds_df[["Season", "TeamID", "Seed"]],
            left_on=["Season", "LTeamID"],
            right_on=["Season", "TeamID"],
            suffixes=("_winner", "_loser"),
        )

        # Filter for games between these seeds
        matchups = seed_matchups[
            (
                (seed_matchups["Seed_winner"] == seed1)
                & (seed_matchups["Seed_loser"] == seed2)
            )
            | (
                (seed_matchups["Seed_winner"] == seed2)
                & (seed_matchups["Seed_loser"] == seed1)
            )
        ]

        total_games = len(matchups)
        if total_games == 0:
            return {}

        # Calculate stats
        higher_seed_wins = len(
            matchups[((matchups["Seed_winner"] < matchups["Seed_loser"]))]
        )

        return {
            "total_games": total_games,
            "higher_seed_wins": higher_seed_wins,
            "upset_percentage": (
                (total_games - higher_seed_wins) / total_games * 100
                if total_games > 0
                else 0.0
            ),
        }

    def _get_team_id(self, team_name: str) -> Optional[int]:
        """Get team ID from name."""
        if self.teams_df is None:
            return None
        team = self.teams_df[self.teams_df["TeamName"] == team_name]
        return int(team["TeamID"].iloc[0]) if not team.empty else None
