from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model

from ..models import (
    Team,
    Game,
    Tournament,
    Bracket,
    Prediction,
    Round,
    Region,
)

User = get_user_model()


class NCAAscoringTests(TestCase):
    """Test suite for NCAA scoring methodology implementation."""

    @classmethod
    def setUpTestData(cls):
        """Set up data for all tests in this class."""
        # Create teams for testing
        cls.teams = {
            "team1": Team.objects.create(
                name="Team 1", short_name="T1", mascot="Mascot 1"
            ),
            "team2": Team.objects.create(
                name="Team 2", short_name="T2", mascot="Mascot 2"
            ),
        }

        # Create tournament
        cls.tournament = Tournament.objects.create(
            name="Test Tournament",
            year=2024,
            start_date=date.today(),
            end_date=date.today(),
        )

        # Create user
        cls.user = User.objects.create_user(username="testuser", password="testpass123")

        # Create bracket
        cls.bracket = Bracket.objects.create(
            tournament=cls.tournament, user=cls.user, name="Test Bracket"
        )

    def test_ncaa_scoring_methodology(self):
        """Test that the scoring system follows the NCAA's methodology exactly."""
        # Create games for each round
        games = {}
        for round_value, _ in Round.__members__.items():
            game = Game.objects.create(
                tournament=self.tournament,
                bracket=self.bracket,
                round=Round[round_value].value,
                region=Region.EAST,
                game_number=1,
                team1=self.teams["team1"],
                team2=self.teams["team2"],
                seed1=1,
                seed2=2,
            )
            games[round_value] = game

            # Create a prediction for each game
            prediction = Prediction.objects.create(
                bracket=self.bracket, game=game, predicted_winner=self.teams["team1"]
            )

            # Set the winner to match the prediction
            game.winner = self.teams["team1"]
            game.save()

            # Refresh prediction from database to get updated is_correct value
            prediction.refresh_from_db()

            # Verify points are calculated correctly
            expected_points = Round.get_points(Round[round_value].value)
            self.assertEqual(prediction.calculate_points, expected_points)

            # Verify the points are saved
            prediction.refresh_from_db()
            self.assertEqual(prediction.points_earned, expected_points)
            self.assertTrue(prediction.is_correct)

        # Verify total bracket score
        total_score = 63  # 1 + 2 + 4 + 8 + 16 + 32 points for rounds 1-6
        self.bracket.refresh_from_db()  # Refresh bracket to get updated score
        self.assertEqual(self.bracket.score, total_score)

    def test_incorrect_predictions(self):
        """Test that incorrect predictions earn 0 points."""
        # Create a game
        game = Game.objects.create(
            tournament=self.tournament,
            bracket=self.bracket,
            round=Round.ROUND_OF_64.value,
            region=Region.EAST,
            game_number=1,
            team1=self.teams["team1"],
            team2=self.teams["team2"],
            seed1=1,
            seed2=2,
        )

        # Create a prediction for team1
        prediction = Prediction.objects.create(
            bracket=self.bracket, game=game, predicted_winner=self.teams["team1"]
        )

        # Set the winner to team2 (different from prediction)
        game.winner = self.teams["team2"]
        game.save()

        # Verify no points are earned for incorrect prediction
        self.assertEqual(prediction.calculate_points, 0)
        prediction.refresh_from_db()
        self.assertEqual(prediction.points_earned, 0)
        self.assertFalse(prediction.is_correct)

    def test_first_four_scoring(self):
        """Test that First Four games don't count for scoring."""
        # Create a First Four game
        game = Game.objects.create(
            tournament=self.tournament,
            bracket=self.bracket,
            round=Round.FIRST_FOUR.value,
            region=Region.FIRST_FOUR,
            game_number=1,
            team1=self.teams["team1"],
            team2=self.teams["team2"],
            seed1=1,
            seed2=2,
        )

        # Create a prediction
        prediction = Prediction.objects.create(
            bracket=self.bracket, game=game, predicted_winner=self.teams["team1"]
        )

        # Set the winner to match the prediction
        game.winner = self.teams["team1"]
        game.save()

        # Verify First Four games earn 0 points
        self.assertEqual(prediction.calculate_points, 0)
        prediction.refresh_from_db()
        self.assertEqual(prediction.points_earned, 0)
        self.assertTrue(
            prediction.is_correct
        )  # Still marked as correct, just no points
