"""Tests for the historical analysis module."""

import unittest
from unittest.mock import Mock, patch
import pandas as pd  # type: ignore
import numpy as np  # type: ignore
from bracket_iq.analysis.historical import HistoricalAnalyzer
from bracket_iq.models import Team


class TestHistoricalAnalyzer(unittest.TestCase):
    @patch("bracket_iq.analysis.historical.MarchMLManiaDataService")
    @patch("bracket_iq.analysis.historical.BracketologyDataService")
    def setUp(self, mock_bracketology_cls, mock_march_ml_mania_cls):
        """Set up test fixtures before each test method."""
        # Configure mocks
        self.mock_march_ml_mania = mock_march_ml_mania_cls.return_value
        self.mock_bracketology = mock_bracketology_cls.return_value

        # Create analyzer with mocked services
        self.analyzer = HistoricalAnalyzer()

        # Mock teams for testing
        self.team1 = Team(name="Duke", id="DUKE")
        self.team2 = Team(name="Kentucky", id="KENT")

        # Sample tournament data for mocking
        self.sample_tournament_data = pd.DataFrame(
            {
                "Season": [2022, 2022, 2021, 2021],
                "WTeamID": ["DUKE", "KENT", "DUKE", "DUKE"],
                "LTeamID": ["KENT", "OTHER", "OTHER2", "OTHER3"],
                "WScore": [75, 80, 85, 90],
                "LScore": [70, 75, 80, 85],
                "WSeed": [1, 4, 2, 1],
                "LSeed": [8, 5, 7, 16],
            }
        )

        # Sample advanced stats for mocking
        self.sample_advanced_stats = {
            "offensive_efficiency": 110.5,
            "defensive_efficiency": 95.2,
            "tempo": 70.1,
            "experience": 2.5,
            "bench_minutes": 35.2,
            "effective_fg_pct": 0.54,
            "turnover_pct": 0.15,
            "offensive_reb_pct": 0.33,
            "ft_rate": 0.35,
        }

        # Sample matchup factors for mocking
        self.sample_matchup_factors = {
            "seed_advantage": 0.65,
            "style_matchup": 0.5,
            "offensive_advantage": 5.2,
            "defensive_advantage": -2.1,
            "momentum": 0.8,
            "experience": 0.4,
        }

        # Configure mock return values
        self.mock_march_ml_mania.get_tournament_history.return_value = {
            "appearances": 5,
            "wins": 10,
            "losses": 5,
            "win_pct": 0.667,
            "avg_seed": 3.5,
            "best_finish": "Final Four",
        }
        self.mock_march_ml_mania.get_matchup_history.return_value = {
            "games": 3,
            "team1_wins": 2,
            "team2_wins": 1,
            "avg_margin": 5.5,
        }
        self.mock_bracketology.get_advanced_stats.return_value = (
            self.sample_advanced_stats
        )

    def test_predict_winner(self):
        """Test winner prediction."""
        winner, confidence = self.analyzer.predict_winner(self.team1, self.team2, 1, 8)
        self.assertIsInstance(winner, Team)
        self.assertIsInstance(confidence, float)
        self.assertTrue(0 <= confidence <= 1)

    def test_get_upset_probability(self):
        """Test upset probability calculation."""
        prob = self.analyzer.get_upset_probability(1, 16)
        self.assertIsInstance(prob, float)
        self.assertTrue(0 <= prob <= 1)

    def test_get_team_tournament_stats(self):
        """Test retrieving team tournament statistics."""
        stats = self.analyzer.get_team_tournament_stats(self.team1)
        self.assertIsInstance(stats, dict)
        self.assertIn("appearances", stats)
        self.assertIn("wins", stats)
        self.assertIn("losses", stats)

    def test_get_matchup_analysis(self):
        """Test matchup analysis."""
        analysis = self.analyzer.get_matchup_analysis(self.team1, self.team2, 1, 8)
        self.assertIsInstance(analysis, dict)
        self.assertIn("historical_matchups", analysis)
        self.assertIn("team_comparisons", analysis)

    def test_score_calculation(self):
        """Test score calculation."""
        # Test with various inputs
        score = self.analyzer._calculate_final_score(
            historical_weight=0.4,
            statistical_weight=0.6,
            historical_score=0.8,
            statistical_score=0.6,
        )
        self.assertIsInstance(score, float)
        self.assertTrue(0 <= score <= 1)

        # Test with edge cases
        score = self.analyzer._calculate_final_score(
            historical_weight=1.0,
            statistical_weight=0.0,
            historical_score=0.5,
            statistical_score=0.0,
        )
        self.assertEqual(score, 0.5)


if __name__ == "__main__":
    unittest.main()
