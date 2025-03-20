"""Tests for the historical analysis module."""
import unittest
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np
from bracket_iq.analysis.historical import HistoricalAnalyzer
from bracket_iq.models import Team

class TestHistoricalAnalyzer(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.analyzer = HistoricalAnalyzer()
        
        # Mock teams for testing
        self.team1 = Team(name="Duke", id="DUKE")
        self.team2 = Team(name="Kentucky", id="KENT")
        
        # Sample tournament data for mocking
        self.sample_tournament_data = pd.DataFrame({
            'Season': [2022, 2022, 2021, 2021],
            'WTeamID': ['DUKE', 'KENT', 'DUKE', 'DUKE'],
            'LTeamID': ['KENT', 'OTHER', 'OTHER2', 'OTHER3'],
            'WScore': [75, 80, 85, 90],
            'LScore': [70, 75, 80, 85],
            'WSeed': [1, 4, 2, 1],
            'LSeed': [8, 5, 7, 16]
        })
        
        # Sample advanced stats for mocking
        self.sample_advanced_stats = {
            'offensive_efficiency': 110.5,
            'defensive_efficiency': 95.2,
            'tempo': 70.1,
            'experience': 2.5,
            'bench_minutes': 35.2,
            'effective_fg_pct': 0.54,
            'turnover_pct': 0.15,
            'offensive_reb_pct': 0.33,
            'ft_rate': 0.35
        }
        
        # Sample matchup factors for mocking
        self.sample_matchup_factors = {
            'seed_advantage': 0.65,
            'style_matchup': 0.5,
            'offensive_advantage': 5.2,
            'defensive_advantage': 3.1,
            'tempo_factor': 2.5,
            'experience_advantage': 0.8,
            'expected_point_diff': 4.5,
            'close_game_likelihood': 0.35
        }

    @patch('bracket_iq.services.march_ml_mania_data.MarchMLManiaDataService')
    @patch('bracket_iq.services.bracketology_data.BracketologyDataService')
    def test_predict_winner(self, mock_bracketology, mock_march_ml_mania):
        """Test the predict_winner method with both data services."""
        # Configure mocks
        mock_march_ml_mania.return_value.get_tournament_history.return_value = self.sample_tournament_data
        mock_bracketology.return_value.get_matchup_factors.return_value = self.sample_matchup_factors
        
        # Test prediction
        winner, confidence = self.analyzer.predict_winner(self.team1, self.team2, 1, 4)
        
        self.assertIsInstance(winner, Team)
        self.assertIsInstance(confidence, float)
        self.assertTrue(0 <= confidence <= 100)
        
        # Verify both services were called
        mock_march_ml_mania.return_value.get_tournament_history.assert_called()
        mock_bracketology.return_value.get_matchup_factors.assert_called()

    @patch('bracket_iq.services.march_ml_mania_data.MarchMLManiaDataService')
    @patch('bracket_iq.services.bracketology_data.BracketologyDataService')
    def test_get_upset_probability(self, mock_bracketology, mock_march_ml_mania):
        """Test upset probability calculation using both datasets."""
        # Configure mocks
        mock_bracketology.return_value.get_upset_probability.return_value = 0.15
        mock_march_ml_mania.return_value.get_seed_matchup_history.return_value = pd.DataFrame({
            'upset': [True, False, False, False, False]
        })
        
        # Test various seed matchups
        prob_1_16 = self.analyzer.get_upset_probability(1, 16)
        prob_4_5 = self.analyzer.get_upset_probability(4, 5)
        
        self.assertTrue(0 <= prob_1_16 <= 1)
        self.assertTrue(0 <= prob_4_5 <= 1)
        # 1 vs 16 should have lower upset probability than 4 vs 5
        self.assertLess(prob_1_16, prob_4_5)
        
        # Test invalid inputs
        with self.assertRaises(ValueError):
            self.analyzer.get_upset_probability(0, 17)
        with self.assertRaises(ValueError):
            self.analyzer.get_upset_probability(5, 4)

    @patch('bracket_iq.services.march_ml_mania_data.MarchMLManiaDataService')
    @patch('bracket_iq.services.bracketology_data.BracketologyDataService')
    def test_get_team_tournament_stats(self, mock_bracketology, mock_march_ml_mania):
        """Test comprehensive team statistics calculation."""
        # Configure mocks
        mock_march_ml_mania.return_value.get_tournament_history.return_value = self.sample_tournament_data
        mock_bracketology.return_value.get_team_advanced_stats.return_value = self.sample_advanced_stats
        
        # Test stats calculation
        stats = self.analyzer.get_team_tournament_stats(self.team1)
        
        # Verify basic stats
        self.assertIn('games_played', stats)
        self.assertIn('wins', stats)
        self.assertIn('win_percentage', stats)
        self.assertTrue(0 <= stats['win_percentage'] <= 1)
        
        # Verify advanced stats
        self.assertIn('offensive_efficiency', stats)
        self.assertIn('defensive_efficiency', stats)
        self.assertIn('tempo', stats)
        self.assertIn('experience', stats)

    @patch('bracket_iq.services.march_ml_mania_data.MarchMLManiaDataService')
    @patch('bracket_iq.services.bracketology_data.BracketologyDataService')
    def test_get_matchup_analysis(self, mock_bracketology, mock_march_ml_mania):
        """Test detailed matchup analysis."""
        # Configure mocks
        mock_bracketology.return_value.get_matchup_factors.return_value = self.sample_matchup_factors
        mock_march_ml_mania.return_value.get_head_to_head.return_value = pd.DataFrame({
            'winner_id': ['DUKE', 'KENT', 'DUKE'],
            'point_diff': [5, -3, 8]
        })
        
        # Test analysis
        analysis = self.analyzer.get_matchup_analysis(self.team1, self.team2, 1, 4)
        
        # Verify head-to-head stats
        self.assertIn('head_to_head_win_pct', analysis)
        self.assertIn('head_to_head_avg_margin', analysis)
        self.assertTrue(0 <= analysis['head_to_head_win_pct'] <= 1)
        
        # Verify matchup factors
        self.assertIn('seed_advantage', analysis)
        self.assertIn('offensive_advantage', analysis)
        self.assertIn('defensive_advantage', analysis)
        self.assertIn('experience_advantage', analysis)

    def test_score_calculation(self):
        """Test the internal score calculation methods."""
        # Test Kaggle score calculation
        kaggle_score = self.analyzer._calculate_kaggle_score(self.team1, 1)
        self.assertTrue(0 <= kaggle_score <= 1)
        
        # Test final score calculation
        final_score = self.analyzer._calculate_final_score(
            kaggle_score=0.7,
            matchup_factors=self.sample_matchup_factors,
            is_team1=True
        )
        self.assertTrue(0 <= final_score <= 1)
        
        # Test with empty matchup factors
        fallback_score = self.analyzer._calculate_final_score(
            kaggle_score=0.7,
            matchup_factors={},
            is_team1=True
        )
        self.assertEqual(fallback_score, 0.7)

if __name__ == '__main__':
    unittest.main() 