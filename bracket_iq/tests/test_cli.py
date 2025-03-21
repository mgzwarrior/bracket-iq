"""Unit tests for the CLI module."""

import unittest
from unittest.mock import Mock, patch
import json
import tempfile
import os

from bracket_iq.cli import (
    predict_matchup,
    batch_predict,
    simulate_tournament,
    get_upset_probability,
    get_team_stats,
    main,
)
from bracket_iq.models import Team


class TestCLI(unittest.TestCase):
    """Test cases for the CLI module."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.sample_prediction = {
            "winner": "Duke",
            "confidence": 75.5,
            "analysis": {
                "head_to_head_win_pct": 0.6,
                "head_to_head_avg_margin": 5.2,
                "seed_advantage": 0.65,
                "offensive_advantage": 3.2,
                "defensive_advantage": 2.1,
                "experience_advantage": 0.8,
            },
        }

        self.sample_team_stats = {
            "games_played": 45,
            "wins": 35,
            "losses": 10,
            "win_percentage": 0.778,
            "points_scored": 75.5,
            "points_allowed": 65.2,
            "avg_seed": 2.5,
        }

        # Sample CSV content for batch predictions
        self.batch_csv_content = (
            "team1,team2,seed1,seed2\n"
            "Duke,North Carolina,2,7\n"
            "Kentucky,Kansas,1,4\n"
            "Gonzaga,Baylor,3,3\n"
        )

        # Sample CSV content for tournament simulation
        self.tournament_csv_content = (
            "team,seed,region\n"
            "Gonzaga,1,West\n"
            "Baylor,1,South\n"
            "Michigan,1,East\n"
            "Illinois,1,Midwest\n"
            "Iowa,2,West\n"
            "Ohio State,2,South\n"
            "Alabama,2,East\n"
            "Houston,2,Midwest\n"
        )

    @patch("bracket_iq.cli.HistoricalAnalyzer")
    def test_predict_matchup(self, mock_analyzer):
        """Test predicting a single matchup."""
        # Configure mock
        mock_analyzer.return_value.predict_winner.return_value = (
            Team(name="Duke", id="DUKE"),
            75.5,
        )
        mock_analyzer.return_value.get_matchup_analysis.return_value = (
            self.sample_prediction["analysis"]
        )

        # Test prediction
        result = predict_matchup("Duke", "North Carolina", 2, 7)

        # Verify result
        self.assertEqual(result["winner"], "Duke")
        self.assertEqual(result["confidence"], 75.5)
        self.assertIn("analysis", result)

        # Verify analyzer was called correctly
        mock_analyzer.return_value.predict_winner.assert_called_once()
        mock_analyzer.return_value.get_matchup_analysis.assert_called_once()

    @patch("bracket_iq.cli.predict_matchup")
    def test_batch_predict(self, mock_predict):
        """Test batch prediction from CSV file."""
        # Configure mock
        mock_predict.return_value = self.sample_prediction

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, encoding="utf-8"
        ) as input_file:
            input_file.write(self.batch_csv_content)
            input_file.flush()

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, encoding="utf-8"
        ) as output_file:
            # Test batch prediction
            results = batch_predict(
                input_file.name, output_file.name, "HISTORICAL_ANALYSIS"
            )

        # Verify results
        self.assertEqual(len(results), 3)  # Three matchups in CSV
        for result in results:
            self.assertIn("winner", result)
            self.assertIn("confidence", result)
            self.assertIn("analysis", result)

        # Verify output file
        with open(output_file.name, "r", encoding="utf-8") as f:
            saved_results = json.load(f)
            self.assertEqual(len(saved_results), 3)

        # Clean up
        os.unlink(input_file.name)
        os.unlink(output_file.name)

        # Verify predict_matchup was called for each row
        self.assertEqual(mock_predict.call_count, 3)

    @patch("bracket_iq.cli.predict_matchup")
    def test_simulate_tournament(self, mock_predict):
        """Test tournament simulation."""
        # Configure mock
        mock_predict.return_value = self.sample_prediction

        # Create a temporary CSV file with valid tournament data
        tournament_csv_content = "team,seed\nDuke,1\nUNC,2\nKentucky,3\nKansas,4\n"
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, encoding="utf-8"
        ) as teams_file:
            teams_file.write(tournament_csv_content)
            teams_file.flush()

            try:
                # Test simulation
                results = simulate_tournament(teams_file.name, "HISTORICAL_ANALYSIS")

                # Verify results structure
                self.assertIn("rounds", results)
                self.assertIn("champion", results)
                self.assertIn("upsets", results)

                # Verify rounds were processed
                self.assertTrue(len(results["rounds"]) > 0)
                self.assertIsNotNone(results["champion"])
            finally:
                os.unlink(teams_file.name)

    @patch("bracket_iq.cli.HistoricalAnalyzer")
    def test_get_upset_probability(self, mock_analyzer):
        """Test upset probability calculation."""
        # Configure mock
        mock_analyzer.return_value.get_upset_probability.return_value = 0.15

        # Test valid seeds
        result = get_upset_probability(2, 15)
        self.assertEqual(result["higher_seed"], 2)
        self.assertEqual(result["lower_seed"], 15)
        self.assertEqual(result["upset_probability"], 0.15)

        # Test invalid seeds
        with self.assertRaises(ValueError):
            get_upset_probability(16, 1)  # Higher seed should be lower number
        with self.assertRaises(ValueError):
            get_upset_probability(0, 17)  # Invalid seed numbers

    @patch("bracket_iq.cli.HistoricalAnalyzer")
    def test_get_team_stats(self, mock_analyzer):
        """Test retrieving team statistics."""
        # Configure mock
        mock_analyzer.return_value.get_team_tournament_stats.return_value = (
            self.sample_team_stats
        )

        # Test stats retrieval
        result = get_team_stats("Duke")

        # Verify result
        self.assertEqual(result["team"], "Duke")
        self.assertEqual(result["stats"], self.sample_team_stats)

        # Verify analyzer was called correctly
        mock_analyzer.return_value.get_team_tournament_stats.assert_called_once()

    @patch("bracket_iq.cli.predict_matchup")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_predict_command(self, mock_args, mock_predict):
        """Test main function with predict command."""
        # Configure mocks
        mock_args.return_value = Mock(
            command="predict",
            team1="Duke",
            team2="North Carolina",
            seed1=2,
            seed2=7,
            strategy="HISTORICAL_ANALYSIS",
            verbose=False,
            output=None,
        )
        mock_predict.return_value = self.sample_prediction

        # Test main function
        exit_code = main()

        # Verify successful execution
        self.assertEqual(exit_code, 0)
        mock_predict.assert_called_once_with(
            "Duke", "North Carolina", 2, 7, "HISTORICAL_ANALYSIS"
        )

    @patch("bracket_iq.cli.batch_predict")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_batch_command(self, mock_args, mock_batch):
        """Test main function with batch command."""
        # Configure mocks
        mock_args.return_value = Mock(
            command="batch",
            input="matchups.csv",
            output="predictions.json",
            strategy="HISTORICAL_ANALYSIS",
            verbose=False,
        )
        mock_batch.return_value = [self.sample_prediction]

        # Test main function
        exit_code = main()

        # Verify successful execution
        self.assertEqual(exit_code, 0)
        mock_batch.assert_called_once_with(
            "matchups.csv", "predictions.json", "HISTORICAL_ANALYSIS"
        )

    @patch("bracket_iq.cli.simulate_tournament")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_simulate_command(self, mock_args, mock_simulate):
        """Test main function with simulate command."""
        # Configure mocks
        mock_args.return_value = Mock(
            command="simulate",
            teams="teams.csv",
            strategy="HISTORICAL_ANALYSIS",
            verbose=False,
            output=None,
        )
        mock_simulate.return_value = {"rounds": [], "champion": "Duke", "upsets": []}

        # Test main function
        exit_code = main()

        # Verify successful execution
        self.assertEqual(exit_code, 0)
        mock_simulate.assert_called_once_with("teams.csv", "HISTORICAL_ANALYSIS")

    def test_main_invalid_command(self):
        """Test main function with invalid command."""
        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = Mock(command=None, verbose=False)

            # Test main function
            exit_code = main()

            # Should return error code when no command is provided
            self.assertEqual(exit_code, 1)

    def test_main_error_handling(self):
        """Test error handling in main function."""
        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = Mock(
                command="predict",
                team1="Invalid",
                team2="Team",
                seed1=99,  # Invalid seed
                seed2=1,
                strategy="HISTORICAL_ANALYSIS",
                verbose=True,
                output=None,
            )

            # Test main function with invalid input
            exit_code = main()

            # Should return error code
            self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
