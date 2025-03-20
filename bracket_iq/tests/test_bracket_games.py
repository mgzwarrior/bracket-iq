from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages

from ..models import (
    Team,
    Game,
    Bracket,
    Prediction,
    Round,
    Tournament,
    Region,
    BracketGame,
)

User = get_user_model()


# pylint: disable=too-many-instance-attributes
class BracketGameTests(TestCase):
    """
    Test suite for BracketGame functionality - ensuring that bracket games
    are properly created and updated as users make their predictions.
    """

    def setUp(self):
        """Set up test data for bracket game tests."""
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")

        # Create tournament
        self.tournament = Tournament.objects.create(
            year=2024,
            name="NCAA March Madness",
            start_date="2024-03-19",
            end_date="2024-04-08",
        )

        # Create teams
        self.team1 = Team.objects.create(name="Team 1", short_name="T1", mascot="Lions")
        self.team2 = Team.objects.create(
            name="Team 2", short_name="T2", mascot="Eagles"
        )
        self.team3 = Team.objects.create(name="Team 3", short_name="T3", mascot="Bears")
        self.team4 = Team.objects.create(
            name="Team 4", short_name="T4", mascot="Tigers"
        )

        # Create bracket
        self.bracket = Bracket.objects.create(
            user=self.user, tournament=self.tournament, name="Test Bracket"
        )

        # Create games structure
        self._create_test_games()

    def _create_test_games(self):
        """Helper method to create the game structure for testing."""
        # Create second round game
        self.game2 = Game.objects.create(
            tournament=self.tournament,
            bracket=self.bracket,
            round=Round.ROUND_OF_32.value,
            region=Region.EAST,
            game_number=2,
            seed1=3,
            team1=self.team3,
            seed2=2,
            team2=self.team4,
        )

        # Create first round game
        self.game1 = Game.objects.create(
            tournament=self.tournament,
            bracket=self.bracket,
            round=Round.ROUND_OF_64.value,
            region=Region.EAST,
            game_number=1,
            seed1=1,
            team1=self.team1,
            seed2=2,
            team2=self.team2,
            next_game=self.game2,
        )

        # Create bracket game for game1 with teams and seeds
        self.bracket_game1 = BracketGame.objects.create(
            bracket=self.bracket,
            game=self.game1,
            team1=self.game1.team1,
            team2=self.game1.team2,
            team1_seed=self.game1.seed1,
            team2_seed=self.game1.seed2,
        )

        # Create bracket game for game2 without teams (will be populated by predictions)
        self.bracket_game2 = BracketGame.objects.create(
            bracket=self.bracket,
            game=self.game2,
        )

    def test_create_prediction_updates_next_bracket_game(self):
        """Test that creating a prediction updates the next bracket game correctly."""
        # Create prediction for first game
        post_data = {
            "bracket": self.bracket.id,
            "game": self.game1.id,
            "winner": self.team1.id,
        }
        response = self.client.post(reverse("create_prediction"), post_data)

        # Check response
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse("display_bracket", args=[self.bracket.id])
        )

        # Check messages
        messages_list = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), "Prediction created successfully")

        # Refresh bracket game from database
        self.bracket_game2.refresh_from_db()

        # Verify next bracket game was updated correctly
        # The winner should be set as team1 since it's the first prediction
        self.assertEqual(self.bracket_game2.team1, self.team1)
        self.assertEqual(self.bracket_game2.team1_seed, self.game1.seed1)

    def test_create_prediction_with_other_game_winner(self):
        """Test that creating predictions for both games updates the next bracket game correctly."""
        # Create prediction for first game
        post_data = {
            "bracket": self.bracket.id,
            "game": self.game1.id,
            "winner": self.team1.id,
        }
        self.client.post(reverse("create_prediction"), post_data)

        # Refresh bracket game from database
        self.bracket_game2.refresh_from_db()

        # Verify bracket game was updated correctly
        # team1 should be set from game1's prediction
        self.assertEqual(self.bracket_game2.team1, self.team1)
        self.assertEqual(self.bracket_game2.team1_seed, self.game1.seed1)

        # Verify first prediction was created
        prediction1 = Prediction.objects.get(game=self.game1)
        self.assertEqual(prediction1.predicted_winner, self.team1)

    def test_create_prediction_with_invalid_winner(self):
        """Test that creating a prediction with an invalid winner is rejected."""
        # Create prediction with invalid winner (team not in game)
        post_data = {
            "bracket": self.bracket.id,
            "game": self.game1.id,
            "winner": self.team3.id,  # Team3 is not in game1
        }
        response = self.client.post(reverse("create_prediction"), post_data)

        # Check response
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse("display_bracket", args=[self.bracket.id])
        )

        # Check messages
        messages_list = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), "Invalid winner selection")

        # Verify no prediction was created
        self.assertFalse(Prediction.objects.filter(game=self.game1).exists())

    def test_create_prediction_without_winner(self):
        """Test that creating a prediction without a winner is rejected."""
        # Create prediction without winner
        post_data = {
            "bracket": self.bracket.id,
            "game": self.game1.id,
        }
        response = self.client.post(reverse("create_prediction"), post_data)

        # Check response
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse("display_bracket", args=[self.bracket.id])
        )

        # Check messages
        messages_list = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), "Please select a winner")

        # Verify no prediction was created
        self.assertFalse(Prediction.objects.filter(game=self.game1).exists())

    def test_create_prediction_for_nonexistent_game(self):
        """Test that creating a prediction for a nonexistent game is rejected."""
        # Create prediction for nonexistent game
        post_data = {
            "bracket": self.bracket.id,
            "game": 99999,  # Nonexistent game ID
            "winner": self.team1.id,
        }
        response = self.client.post(reverse("create_prediction"), post_data)

        # Check response
        self.assertEqual(response.status_code, 404)

        # Verify no prediction was created
        self.assertFalse(Prediction.objects.exists())
