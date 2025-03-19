from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import Team, Bracket, Game, Prediction, Round, Tournament, Region


class ViewTests(TestCase):
    """
    Test suite for our bracket-iq views - the interface where March Madness
    comes to life! Just like watching the games courtside, these tests ensure
    our users get the best possible tournament experience.
    """

    def setUp(self):
        """Set up our tournament environment - like Selection Sunday preparations!"""
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="12345")
        # Creating our tournament contenders
        self.team1 = Team.objects.create(name="Team 1")  # Our blue blood program
        self.team2 = Team.objects.create(name="Team 2")  # The cinderella hopeful
        # Setting up the tournament field
        self.tournament = Tournament.objects.create(
            year=2024,
            name="NCAA March Madness",
            start_date="2024-03-19",
            end_date="2024-04-08",
        )

        # Create a game directly (without using SeedList and Seed)
        self.game = Game.objects.create(
            tournament=self.tournament,
            round=Round.FIRST_FOUR.value,
            region=Region.FIRST_FOUR,
            game_number=1,
            seed1=1,
            team1=self.team1,
            seed2=16,
            team2=self.team2,
        )

    def test_home_view(self):
        """Test the home view - our tournament central!"""
        # Test unauthenticated access - like trying to get in without a ticket
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

        # Test authenticated access - now we're in the arena!
        self.client.login(username="testuser", password="12345")
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")

        # Check for new UI elements
        self.assertContains(response, "Welcome to BracketIQ")
        self.assertContains(response, 'class="bracket-container"')
        self.assertContains(response, 'class="seed-list-grid"')

    def test_profile_view(self):
        """Test the profile view - where bracketologists check their predictions!"""
        # Test unauthenticated access
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

        # Test authenticated access - time to see your bracket performance
        self.client.login(username="testuser", password="12345")
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile.html")

        # Check for styled elements
        self.assertContains(response, 'class="container"')

    def test_create_bracket_form_view(self):
        """Test bracket creation form - the moment of truth for every fan!"""
        # Test unauthenticated access
        response = self.client.get(reverse("create_bracket"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

        # Test authenticated access - time to make those tough picks
        self.client.login(username="testuser", password="12345")
        response = self.client.get(reverse("create_bracket"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "create_bracket_form.html")
        self.assertIn("seed_lists", response.context)

        # Check for form styling
        self.assertContains(response, 'class="form-container"')

    def test_create_bracket_view(self):
        """Test bracket creation - where March Madness dreams begin!"""
        self.client.login(username="testuser", password="12345")
        response = self.client.post(
            reverse("create_bracket", args=[self.game.tournament.id])
        )
        self.assertEqual(response.status_code, 302)  # Redirect to display_bracket

        # Verify bracket was created - your picks are locked in!
        bracket = Bracket.objects.filter(user=self.user).first()
        self.assertIsNotNone(bracket)
        self.assertEqual(bracket.tournament.year, 2024)

        # Follow redirect and check for success message styling
        response = self.client.get(response.url)
        self.assertContains(response, 'class="message message-success"')

    def test_display_bracket_view(self):
        """Test bracket display - showcase your tournament predictions!"""
        self.client.login(username="testuser", password="12345")
        bracket = Bracket.objects.create(user=self.user, tournament=self.tournament)
        # Setting up a classic 1 vs 16 matchup
        game = Game.objects.create(
            seed1=1,
            team1=self.team1,
            seed2=16,
            team2=self.team2,
            round=Round.FIRST_FOUR.value,
            year=2024,
            game_number=1,
            bracket=bracket,
        )
        # Making our bold prediction
        prediction = Prediction.objects.create(
            game=game,
            predicted_winner=self.team1,  # Going with the favorite
            bracket=bracket,
        )

        response = self.client.get(reverse("display_bracket", args=[bracket.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "display_bracket.html")
        self.assertIn("bracket", response.context)
        self.assertIn("games", response.context)
        self.assertIn("predictions", response.context)

        # Check for styled elements
        self.assertContains(response, 'class="bracket-container"')
        self.assertContains(response, 'class="team-card"')

    def test_delete_bracket_view(self):
        """Test bracket deletion - sometimes you need a fresh start!"""
        self.client.login(username="testuser", password="12345")
        bracket = Bracket.objects.create(user=self.user, tournament=self.tournament)

        # Test deletion - when your picks just didn't pan out
        response = self.client.post(reverse("delete_bracket", args=[bracket.id]))
        self.assertEqual(response.status_code, 302)  # Redirect to home

        # Verify bracket was deleted - time for redemption in next year's tournament
        self.assertFalse(Bracket.objects.filter(id=bracket.id).exists())

        # Follow redirect and check for success message styling
        response = self.client.get(response.url)
        self.assertContains(response, 'class="message"')

    def test_create_live_bracket_view(self):
        """Test live bracket creation - for the real-time tournament action!"""
        self.client.login(username="testuser", password="12345")

        # Test GET request - preparing for tip-off
        response = self.client.get(reverse("create_live_bracket"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "create_live_bracket.html")

        # Check for form styling
        self.assertContains(response, 'class="form-container"')

        # Test POST request - game time!
        data = {
            "seed1": 1,
            "team1": self.team1.id,
            "seed2": 16,
            "team2": self.team2.id,
        }
        response = self.client.post(reverse("create_live_bracket", args=[1]), data)
        self.assertEqual(
            response.status_code, 302
        )  # Redirect to next game or display_bracket
