from django.test import TestCase
from django.contrib.auth import get_user_model

from ..models import Team, Bracket, Game, Prediction, Round, Tournament, Region

User = get_user_model()


class TeamModelTests(TestCase):
    """
    Test suite for Team models - the foundation of March Madness!
    Just like Selection Sunday, we need to make sure our teams are
    properly set up before the madness begins.
    """

    def setUp(self):
        # Every Cinderella story starts with a team
        self.team = Team.objects.create(
            name="Test Team", short_name="TST", mascot="Testers"
        )

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
        self.tournament = Tournament.objects.create(
            year=2024,
            name="NCAA March Madness",
            start_date="2024-03-19",
            end_date="2024-04-08",
        )
        self.bracket = Bracket.objects.create(
            user=self.user, tournament=self.tournament, name="My Test Bracket"
        )

    def test_bracket_creation(self):
        """Test bracket creation - the moment every March Madness fan lives for!"""
        self.assertTrue(isinstance(self.bracket, Bracket))
        self.assertEqual(self.bracket.tournament, self.tournament)
        self.assertEqual(self.bracket.user, self.user)


class GameModelTests(TestCase):
    """
    Test suite for Game models - the heart-pounding matchups that define March Madness!
    Just like game day preparation, we need to ensure our games are
    set up correctly before the ball is tipped.
    """

    def setUp(self):
        # Creating the stage for an epic tournament game
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.tournament = Tournament.objects.create(
            year=2024,
            name="NCAA March Madness",
            start_date="2024-03-19",
            end_date="2024-04-08",
        )
        self.bracket = Bracket.objects.create(
            user=self.user, tournament=self.tournament
        )
        self.team1 = Team.objects.create(
            name="Team 1", short_name="TM1", mascot="Lions"
        )  # Our 1 seed powerhouse
        self.team2 = Team.objects.create(
            name="Team 2", short_name="TM2", mascot="Eagles"
        )  # The hopeful underdog
        self.game = Game.objects.create(
            seed1=1,
            team1=self.team1,
            seed2=16,
            team2=self.team2,
            round=Round.FIRST_FOUR.value,
            region=Region.FIRST_FOUR,
            game_number=1,
            bracket=self.bracket,
            tournament=self.tournament,
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
        self.tournament = Tournament.objects.create(
            year=2024,
            name="NCAA March Madness",
            start_date="2024-03-19",
            end_date="2024-04-08",
        )
        self.bracket = Bracket.objects.create(
            user=self.user, tournament=self.tournament
        )
        self.team1 = Team.objects.create(
            name="Team 1", short_name="TM1", mascot="Lions"
        )
        self.team2 = Team.objects.create(
            name="Team 2", short_name="TM2", mascot="Eagles"
        )
        self.game = Game.objects.create(
            tournament=self.tournament,
            bracket=self.bracket,
            round=Round.ROUND_OF_64.value,
            region=Region.EAST,
            game_number=1,
            seed1=1,
            team1=self.team1,
            seed2=16,
            team2=self.team2,
        )
        self.prediction = Prediction.objects.create(
            game=self.game, bracket=self.bracket, predicted_winner=self.team1
        )

    def test_prediction_creation(self):
        """Test prediction creation - putting your bracket knowledge to the test!"""
        self.assertTrue(isinstance(self.prediction, Prediction))
        self.assertEqual(self.prediction.predicted_winner, self.team1)
        self.assertFalse(self.prediction.is_correct)  # Awaiting the outcome

    def test_prediction_correct(self):
        """Test correct predictions - the sweet sound of picking a winner!"""
        # Game result matches the prediction
        self.game.winner = self.team1
        self.game.save()
        self.prediction.is_correct = True
        self.prediction.save()
        self.assertTrue(self.prediction.is_correct)


class SeedTeamRelationshipTest(TestCase):
    """Tests for the relationship between Teams and their Seeds"""

    def setUp(self):
        self.team = Team.objects.create(
            name="Kansas", short_name="KAN", mascot="Jayhawks"
        )
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.tournament = Tournament.objects.create(
            year=2024,
            name="NCAA March Madness",
            start_date="2024-03-19",
            end_date="2024-04-08",
        )
        self.bracket = Bracket.objects.create(
            user=self.user, tournament=self.tournament
        )

    def test_team_seed_relationship(self):
        """Tests the relationship between Team and seeds"""
        # This test is no longer relevant since Seed and SeedList models have been removed
        # We'll test Game seed assignments instead
        game = Game.objects.create(
            round=Round.ROUND_OF_64.value,
            region=Region.EAST,
            game_number=1,
            seed1=1,
            team1=self.team,
            seed2=16,
            team2=None,
            tournament=self.tournament,
            bracket=self.bracket,
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
            region=Region.EAST,
            game_number=1,
            seed1=1,
            team1=self.team,
            seed2=16,
            team2=None,
            tournament=self.tournament,
            bracket=self.bracket,
        )

        game2 = Game.objects.create(
            round=Round.ROUND_OF_64.value,
            region=Region.WEST,
            game_number=2,
            seed1=1,
            team1=team2,
            seed2=16,
            team2=None,
            tournament=self.tournament,
            bracket=self.bracket,
        )

        # Verify both teams can have seed 1 in different regions
        self.assertEqual(game1.seed1, 1)
        self.assertEqual(game2.seed1, 1)
        self.assertEqual(game1.team1, self.team)
        self.assertEqual(game2.team1, team2)
