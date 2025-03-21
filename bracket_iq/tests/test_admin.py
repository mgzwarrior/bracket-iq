from unittest import mock
from datetime import date

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.admin.sites import AdminSite
import django.db

from ..models import (
    Team,
    Game,
    Tournament,
    Bracket,
    Prediction,
    Round,
    BracketStrategy,
    Region,
)
from ..admin import GameAdmin, GameForm


class MockRequest:
    """Mock request for testing admin actions."""

    def __init__(self, user=None):
        self.user = user


class GameAdminTests(TestCase):
    """
    Test suite for Game admin functionality - ensuring that admins
    can properly set game winners and update the tournament bracket.
    """

    # Class constants
    TOURNAMENT_YEAR = 2024
    TOURNAMENT_NAME = "NCAA March Madness"
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "password"
    USER_USERNAME = "testuser"
    USER_PASSWORD = "12345"

    @classmethod
    def setUpTestData(cls):
        """Set up data for all tests in this class."""
        # Create teams for testing - these won't change between tests
        cls.teams = {
            "team1": Team.objects.create(
                name="Team 1", short_name="T1", mascot="Tigers"
            ),
            "team2": Team.objects.create(
                name="Team 2", short_name="T2", mascot="Bears"
            ),
            "team3": Team.objects.create(
                name="Team 3", short_name="T3", mascot="Lions"
            ),
            "team4": Team.objects.create(
                name="Team 4", short_name="T4", mascot="Eagles"
            ),
        }

        # Create tournament
        cls.tournament = Tournament.objects.create(
            year=cls.TOURNAMENT_YEAR,
            name=cls.TOURNAMENT_NAME,
            start_date="2024-03-19",
            end_date="2024-04-08",
        )

        # Create user accounts
        User = get_user_model()
        cls.admin_user = User.objects.create_superuser(
            username=cls.ADMIN_USERNAME,
            email="admin@example.com",
            password=cls.ADMIN_PASSWORD,
        )
        cls.regular_user = User.objects.create_user(
            username=cls.USER_USERNAME, password=cls.USER_PASSWORD
        )

    def setUp(self):
        """Set up test data for Game admin tests."""
        # Set up client and login admin
        self.client = Client()
        self.client.login(username=self.ADMIN_USERNAME, password=self.ADMIN_PASSWORD)

        # Create mock request
        self.request = MockRequest(user=self.admin_user)

        # Create admin site instance
        self.game_admin = GameAdmin(Game, AdminSite())

        # Create bracket
        self.bracket = Bracket.objects.create(
            user=self.regular_user, tournament=self.tournament, name="Test Bracket"
        )

        # Create games structure for testing
        self._create_test_games()

        # Create prediction
        self.prediction = Prediction.objects.create(
            game=self.game1, bracket=self.bracket, predicted_winner=self.teams["team1"]
        )

    def _create_test_games(self):
        """Helper method to create the game structure for testing."""
        # Create second round game first
        self.game2 = Game.objects.create(
            tournament=self.tournament,
            bracket=self.bracket,
            round=Round.ELITE_8.round_id,
            region="EAST",
            game_number=2,
            seed1=3,  # Using a temporary seed
            team1=self.teams["team3"],  # Using a temporary team that will be replaced
            seed2=2,
            team2=self.teams["team4"],
            game_date="2024-03-30T18:00:00Z",
        )

        # Create first round game
        self.game1 = Game.objects.create(
            tournament=self.tournament,
            bracket=self.bracket,
            round=Round.SWEET_16.round_id,
            region="EAST",
            game_number=1,
            seed1=1,
            team1=self.teams["team1"],
            seed2=2,
            team2=self.teams["team2"],
            next_game=self.game2,
            game_date="2024-03-25T18:00:00Z",
        )

    def test_game_form_winner_choices(self):
        """Test that GameForm only allows selecting relevant teams as winner."""
        form = GameForm(instance=self.game1)

        # Check that only the two teams playing in the game are in the queryset
        self.assertEqual(form.fields["winner"].queryset.count(), 2)
        self.assertIn(self.teams["team1"], form.fields["winner"].queryset)
        self.assertIn(self.teams["team2"], form.fields["winner"].queryset)
        self.assertNotIn(self.teams["team3"], form.fields["winner"].queryset)
        self.assertNotIn(self.teams["team4"], form.fields["winner"].queryset)

    def test_set_game_winner_action(self):
        """Test the admin action to set a game winner."""
        # Create POST data for the action
        post_data = {
            "action": "set_game_winner",
            "_selected_action": [self.game1.id],
        }

        # Get the changelist URL
        url = reverse("admin:bracket_iq_game_changelist")

        # Test action request
        response = self.client.post(url, post_data, follow=True)

        # Verify response contains our game
        self.assertContains(response, "Team 1")
        self.assertContains(response, "Team 2")

        # Now simulate selecting a winner and submitting the form
        post_data = {
            "action": "set_game_winner",
            "apply": "1",
            "_selected_action": [self.game1.id],
            f"winner_{self.game1.id}": str(self.teams["team1"].id),
            f"score1_{self.game1.id}": "75",
            f"score2_{self.game1.id}": "68",
        }

        response = self.client.post(url, post_data, follow=True)

        # Verify success message
        self.assertContains(response, "Set Team 1 as winner")

        # Verify database updates
        self.game1.refresh_from_db()
        self.prediction.refresh_from_db()

        # Check game winner and scores set correctly
        self.assertEqual(self.game1.winner, self.teams["team1"])
        self.assertEqual(self.game1.score1, 75)
        self.assertEqual(self.game1.score2, 68)

        # Check prediction marked correct
        self.assertTrue(self.prediction.is_correct)
        self.assertGreater(self.prediction.points_earned, 0)

        # Check next game updated with winner - implementation detail depends on the admin logic
        # Since next_game already has a team1, the winner should actually be set as team2
        # Just test that the action correctly handles next_game updates
        self.game2.refresh_from_db()
        self.assertTrue(
            (self.game2.team1 == self.teams["team1"] and self.game2.seed1 == 1)
            or (self.game2.team2 == self.teams["team1"] and self.game2.seed2 == 1)
        )

    def test_save_model_updates_predictions(self):
        """Test that saving a Game model through admin updates predictions."""
        # Setup a form for editing the game
        form = GameForm(
            instance=self.game1,
            data={
                "tournament": self.tournament.id,
                "bracket": self.bracket.id,
                "round": self.game1.round,
                "region": self.game1.region,
                "game_number": self.game1.game_number,
                "seed1": self.game1.seed1,
                "team1": self.teams["team1"].id,
                "seed2": self.game1.seed2,
                "team2": self.teams["team2"].id,
                "winner": self.teams["team2"].id,  # Changed winner to team2
                "score1": 70,
                "score2": 72,
                "game_date": self.game1.game_date,
                "next_game": self.game2.id,
            },
        )

        self.assertTrue(form.is_valid(), form.errors)

        # Save the game through admin
        game = form.save(commit=False)
        self.game_admin.save_model(self.request, game, form, change=True)

        # Refresh data from database
        self.game1.refresh_from_db()
        self.prediction.refresh_from_db()

        # Check game winner and scores
        self.assertEqual(self.game1.winner, self.teams["team2"])
        self.assertEqual(self.game1.score1, 70)
        self.assertEqual(self.game1.score2, 72)

        # Check prediction marked incorrect
        self.assertFalse(self.prediction.is_correct)
        self.assertEqual(self.prediction.points_earned, 0)

        # Check next game updated with winner
        self.game2.refresh_from_db()
        self.assertTrue(
            (self.game2.team1 == self.teams["team2"] and self.game2.seed1 == 2)
            or (self.game2.team2 == self.teams["team2"] and self.game2.seed2 == 2)
        )

    def test_admin_template_rendering(self):
        """Test the set_game_winner template renders correctly."""
        # Get the set_game_winner template URL
        post_data = {
            "action": "set_game_winner",
            "_selected_action": [self.game1.id],
        }

        url = reverse("admin:bracket_iq_game_changelist")
        response = self.client.post(url, post_data, follow=True)

        # Check template rendering elements
        self.assertContains(response, "Choose Game Winner")
        self.assertContains(response, "Select the winner for each game below")
        self.assertContains(response, "Team 1")
        self.assertContains(response, "Team 2")
        self.assertContains(response, "Score:")
        self.assertContains(response, "Save Winners & Scores")

        # Check form structure
        self.assertContains(response, f"winner_{self.game1.id}")
        self.assertContains(response, f"score1_{self.game1.id}")
        self.assertContains(response, f"score2_{self.game1.id}")

    def test_winner_with_invalid_scores(self):
        """Test handling invalid scores when setting a winner."""
        post_data = {
            "action": "set_game_winner",
            "apply": "1",
            "_selected_action": [self.game1.id],
            f"winner_{self.game1.id}": str(self.teams["team1"].id),
            f"score1_{self.game1.id}": "invalid",  # Invalid score
            f"score2_{self.game1.id}": "68",
        }

        url = reverse("admin:bracket_iq_game_changelist")
        response = self.client.post(url, post_data, follow=True)

        # Check error message is shown
        self.assertContains(response, "Error processing game")

        # Game should not be updated
        self.game1.refresh_from_db()
        self.assertIsNone(self.game1.winner)
        self.assertIsNone(self.game1.score1)
        self.assertIsNone(self.game1.score2)

    def test_ncaa_scoring_methodology(self):
        """Test that the scoring system follows the NCAA's methodology exactly."""
        # Create a tournament and teams
        tournament = Tournament.objects.create(
            name="Test Tournament",
            year=2024,
            start_date=date.today(),
            end_date=date.today(),
        )

        teams = {
            "team1": Team.objects.create(
                name="Team 1", short_name="T1", mascot="Mascot 1"
            ),
            "team2": Team.objects.create(
                name="Team 2", short_name="T2", mascot="Mascot 2"
            ),
            "team3": Team.objects.create(
                name="Team 3", short_name="T3", mascot="Mascot 3"
            ),
            "team4": Team.objects.create(
                name="Team 4", short_name="T4", mascot="Mascot 4"
            ),
        }

        # Create a bracket
        bracket = Bracket.objects.create(
            tournament=tournament, user=self.regular_user, name="Test Bracket"
        )

        # Create games for each round
        games = {}
        for round_value, _ in Round.__members__.items():
            game = Game.objects.create(
                tournament=tournament,
                bracket=bracket,
                round=Round[round_value].value,
                region=Region.EAST,
                game_number=1,
                team1=teams["team1"],
                team2=teams["team2"],
                seed1=1,
                seed2=2,
            )
            games[round_value] = game

            # Create a prediction for each game
            prediction = Prediction.objects.create(
                bracket=bracket, game=game, predicted_winner=teams["team1"]
            )

            # Set the winner to match the prediction
            game.winner = teams["team1"]
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
        bracket.refresh_from_db()  # Refresh bracket to get updated score
        self.assertEqual(bracket.score, total_score)


class AdminSiteTests(TestCase):
    """
    Test suite for the admin interface.
    """

    def setUp(self):
        self.client = Client()
        UserModel = get_user_model()
        self.admin_user = UserModel.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )
        self.client.login(username="admin", password="adminpass123")
        self.regular_user = UserModel.objects.create_user(
            username="user", email="user@example.com", password="userpass123"
        )

    def test_admin_login(self):
        """Test admin login functionality."""
        # Logout first
        self.client.logout()

        # Try to access the admin index page - using the custom admin URL
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)  # Redirect to login

        # Login again
        logged_in = self.client.login(username="admin", password="adminpass123")
        self.assertTrue(logged_in)

        # Now should be able to access the admin index
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)

    def test_tournament_management(self):
        """Test the tournament management page is accessible."""
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)
        # Check for tournament management elements
        self.assertContains(response, "Tournament Management")


class BracketGenerationTests(TestCase):
    """Test suite for bracket generation functionality and error handling."""

    @classmethod
    def setUpTestData(cls):
        """Set up data for all tests in this class."""
        # Create admin user
        User = get_user_model()
        cls.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="password"
        )

        # Create a tournament
        cls.tournament = Tournament.objects.create(
            year=2024,
            name="Test Tournament",
            start_date="2024-03-19",
            end_date="2024-04-08",
        )

    def setUp(self):
        """Set up before each test."""
        self.client = Client()
        self.client.login(username="admin", password="password")
        self.url = reverse("admin:generate_brackets")

    def test_nonexistent_tournament_error(self):
        """Test error handling when tournament doesn't exist."""
        response = self.client.post(
            self.url,
            {
                "tournament": "999999",  # Non-existent tournament ID
                "strategy": BracketStrategy.RANDOM.value,
                "num_brackets": "1",
                "user_prefix": "Test",
            },
        )

        self.assertContains(response, "Tournament with ID 999999 does not exist")
        self.assertEqual(Bracket.objects.count(), 0)

    def test_invalid_strategy_error(self):
        """Test error handling when strategy is invalid."""
        response = self.client.post(
            self.url,
            {
                "tournament": str(self.tournament.id),
                "strategy": "INVALID_STRATEGY",
                "num_brackets": "1",
                "user_prefix": "Test",
            },
        )

        self.assertContains(response, "Invalid strategy: INVALID_STRATEGY")
        self.assertEqual(Bracket.objects.count(), 0)

    def test_invalid_num_brackets_error(self):
        """Test error handling when number of brackets is invalid."""
        response = self.client.post(
            self.url,
            {
                "tournament": str(self.tournament.id),
                "strategy": BracketStrategy.RANDOM.value,
                "num_brackets": "invalid",
                "user_prefix": "Test",
            },
        )

        self.assertContains(response, "Invalid number of brackets: invalid")
        self.assertEqual(Bracket.objects.count(), 0)

    def test_database_error_handling(self):
        """Test handling of database errors during bracket creation."""
        with mock.patch("django.db.models.Model.save") as mock_save:
            # Configure the mock to raise a database error
            mock_save.side_effect = django.db.Error("Test DB Error")

            # Make the request
            response = self.client.post(
                self.url,
                {
                    "tournament": str(self.tournament.id),
                    "strategy": BracketStrategy.RANDOM.value,
                    "num_brackets": "1",
                    "user_prefix": "Test",
                },
            )

            # Verify the error message is shown
            self.assertContains(
                response, "Database error while creating bracket: Test DB Error"
            )
            # Verify no brackets were created
            self.assertEqual(Bracket.objects.count(), 0)
