from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from datetime import date
from ..models import Team, Bracket, Game, Prediction, Round, Tournament, Region


class TeamModelTests(TestCase):
    """
    Test suite for Team models - the foundation of March Madness!
    Just like Selection Sunday, we need to make sure our teams are
    properly set up before the madness begins.
    """

    def setUp(self):
        # Every Cinderella story starts with a team
        self.team = Team.objects.create(name="Test Team")

    def test_team_creation(self):
        """Test that teams are created properly, like a well-executed recruiting class."""
        self.assertEqual(self.team.name, "Test Team")
        self.assertTrue(isinstance(self.team, Team))
        self.assertEqual(str(self.team), "Test Team")


class BracketModelTests(TestCase):
    """
    Test suite for Bracket models - where dreams are made and busted!
    Like filling out your bracket on Selection Sunday, we need to ensure
    everything is perfect before the tournament tips off.
    """

    def setUp(self):
        # Every bracket needs a passionate fan behind it
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.bracket = Bracket.objects.create(user=self.user)

    def test_bracket_creation(self):
        """Test bracket creation - the moment every March Madness fan lives for!"""
        self.assertTrue(isinstance(self.bracket, Bracket))
        self.assertEqual(self.bracket.user, self.user)
        self.assertIsNotNone(self.bracket.uuid)
        self.assertEqual(
            self.bracket.year, date.today().year
        )  # Ready for this year's tournament


class GameModelTests(TestCase):
    """
    Test suite for Game models - where the magic happens!
    From buzzer-beaters to historic upsets, every tournament game
    needs to be properly tracked.
    """

    def setUp(self):
        # Setting up an epic 1 vs 16 matchup
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.bracket = Bracket.objects.create(user=self.user)
        self.team1 = Team.objects.create(name="Team 1")  # Our 1 seed powerhouse
        self.team2 = Team.objects.create(name="Team 2")  # The hopeful underdog
        self.game = Game.objects.create(
            seed1=1,
            team1=self.team1,
            seed2=16,
            team2=self.team2,
            round=Round.FIRST_FOUR.value,
            year=2024,
            game_number=1,
            bracket=self.bracket,
        )

    def test_game_creation(self):
        """Test game creation - setting the stage for March Madness glory!"""
        self.assertTrue(isinstance(self.game, Game))
        self.assertEqual(self.game.team1.name, "Team 1")
        self.assertEqual(self.game.team2.name, "Team 2")
        self.assertEqual(self.game.seed1, 1)
        self.assertEqual(self.game.seed2, 16)
        self.assertEqual(self.game.round, Round.FIRST_FOUR.value)
        self.assertIsNone(self.game.winner)  # The tension before tip-off!

    def test_game_winner(self):
        """Test setting game winners - the moment that makes or breaks brackets!"""
        self.game.winner = self.team1  # The favorite prevails
        self.game.save()
        self.assertEqual(self.game.winner, self.team1)


class PredictionModelTests(TestCase):
    """
    Test suite for Prediction models - where bracketologists put their
    expertise to the test! Will you call the next big upset?
    """

    def setUp(self):
        # Setting up a classic tournament matchup
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.bracket = Bracket.objects.create(user=self.user)
        self.team1 = Team.objects.create(name="Team 1")
        self.team2 = Team.objects.create(name="Team 2")
        self.game = Game.objects.create(
            seed1=1,
            team1=self.team1,
            seed2=16,
            team2=self.team2,
            round=Round.FIRST_FOUR.value,
            year=2024,
            game_number=1,
            bracket=self.bracket,
        )
        # Making our bold prediction
        self.prediction = Prediction.objects.create(
            game=self.game, predicted_winner=self.team1, bracket=self.bracket
        )

    def test_prediction_creation(self):
        """Test prediction creation - putting your bracket wisdom on the line!"""
        self.assertTrue(isinstance(self.prediction, Prediction))
        self.assertEqual(self.prediction.predicted_winner, self.team1)
        self.assertEqual(self.prediction.game, self.game)
        self.assertEqual(self.prediction.bracket, self.bracket)


class SeedTeamRelationshipTest(TestCase):
    def setUp(self):
        self.team = Team.objects.create(
            name="Gonzaga", short_name="GON", mascot="Bulldogs"
        )

    def test_team_seed_relationship(self):
        """Tests the relationship between Team and seeds"""
        # This test is no longer relevant since Seed and SeedList models have been removed
        # We'll test Game seed assignments instead
        game = Game.objects.create(
            round=Round.ROUND_OF_64.value,
            year=2024,
            game_number=1,
            seed1=1,
            team1=self.team,
            seed2=16,
            team2=None,
        )

        # Verify seeds are correctly assigned in games
        self.assertEqual(game.seed1, 1)
        self.assertEqual(game.seed2, 16)
        self.assertEqual(game.team1, self.team)
        self.assertIsNone(game.team2)

    def test_multiple_teams_per_seed(self):
        """Test multiple teams can have the same seed in different regions"""
        # Create another team
        team2 = Team.objects.create(name="Kansas", short_name="KAN", mascot="Jayhawks")

        # Create games with same seeds but different teams/regions
        game1 = Game.objects.create(
            round=Round.ROUND_OF_64.value,
            year=2024,
            game_number=1,
            region=Region.EAST.value,
            seed1=1,
            team1=self.team,
        )

        game2 = Game.objects.create(
            round=Round.ROUND_OF_64.value,
            year=2024,
            game_number=2,
            region=Region.WEST.value,
            seed1=1,
            team1=team2,
        )

        # Verify both teams can have the same seed in different regions
        self.assertEqual(game1.seed1, game2.seed1)
        self.assertNotEqual(game1.team1, game2.team1)
        self.assertNotEqual(game1.region, game2.region)
