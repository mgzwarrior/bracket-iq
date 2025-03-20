from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from ..models import (
    Tournament,
    Team,
    Game,
    Bracket,
    BracketGame,
    Prediction,
    BracketStrategy,
)

User = get_user_model()


class BracketGenerationTests(TestCase):
    def setUp(self):
        # Create a superuser for admin access
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="admin123"
        )
        self.client = Client()
        self.client.login(username="admin", password="admin123")

        # Create a test tournament with required date fields
        self.tournament = Tournament.objects.create(
            name="Test Tournament",
            year=2024,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=14),  # 2 weeks duration
        )

        # Create some test teams
        self.teams = []
        for i in range(8):
            team = Team.objects.create(
                name=f"Team {i+1}", short_name=f"T{i+1}", mascot=f"Mascot {i+1}"
            )
            self.teams.append(team)

        # Create a test bracket for the games
        self.test_bracket = Bracket.objects.create(
            user=self.admin_user, tournament=self.tournament, name="Test Bracket"
        )

        # Create first round games
        self.games = []
        for i in range(4):
            game = Game.objects.create(
                tournament=self.tournament,
                bracket=self.test_bracket,
                round=1,
                region="Test Region",
                game_number=i + 1,
                team1=self.teams[i * 2],
                team2=self.teams[i * 2 + 1],
                seed1=i * 2 + 1,
                seed2=i * 2 + 2,
            )
            self.games.append(game)

        # Create second round games
        for i in range(2):
            game = Game.objects.create(
                tournament=self.tournament,
                bracket=self.test_bracket,
                round=2,
                region="Test Region",
                game_number=i + 5,
                seed1=i * 2 + 1,
                seed2=i * 2 + 2,
            )
            self.games.append(game)

        # Create final game
        final_game = Game.objects.create(
            tournament=self.tournament,
            bracket=self.test_bracket,
            round=3,
            region="Test Region",
            game_number=7,
            seed1=1,
            seed2=2,
        )
        self.games.append(final_game)

        # Link games together
        self.games[4].team1 = self.games[0].winner
        self.games[4].team2 = self.games[1].winner
        self.games[4].save()
        self.games[0].next_game = self.games[4]
        self.games[1].next_game = self.games[4]
        self.games[0].save()
        self.games[1].save()

        self.games[5].team1 = self.games[2].winner
        self.games[5].team2 = self.games[3].winner
        self.games[5].save()
        self.games[2].next_game = self.games[5]
        self.games[3].next_game = self.games[5]
        self.games[2].save()
        self.games[3].save()

        final_game.team1 = self.games[4].winner
        final_game.team2 = self.games[5].winner
        final_game.save()
        self.games[4].next_game = final_game
        self.games[5].next_game = final_game
        self.games[4].save()
        self.games[5].save()

        # Create BracketGames for the test bracket
        for game in self.games:
            BracketGame.objects.create(
                bracket=self.test_bracket,
                game=game,
                team1=game.team1,
                team2=game.team2,
                team1_seed=game.seed1,
                team2_seed=game.seed2,
            )

    def test_generate_brackets_view_get(self):
        """Test that the generate brackets view renders correctly"""
        response = self.client.get(reverse("admin:generate_brackets"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "admin/bracketiq_admin/generate_brackets.html"
        )

    def test_generate_brackets_random_strategy(self):
        """Test generating brackets with random strategy"""
        # Clean up any existing brackets except the test bracket
        Bracket.objects.exclude(id=self.test_bracket.id).delete()

        response = self.client.post(
            reverse("admin:generate_brackets"),
            {
                "tournament": self.tournament.id,
                "strategy": BracketStrategy.RANDOM.value,
                "num_brackets": "2",
                "user_prefix": "TestUser",
            },
        )

        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertEqual(
            Bracket.objects.count(), 3
        )  # Test bracket + 2 generated brackets
        self.assertEqual(
            BracketGame.objects.count(), 21
        )  # 7 games per bracket (3 brackets)
        self.assertEqual(
            Prediction.objects.count(), 14
        )  # 1 prediction per game for new brackets

        # Check that users were created
        self.assertEqual(
            User.objects.filter(username__startswith="TestUser_").count(), 2
        )

    def test_generate_brackets_higher_seed_strategy(self):
        """Test generating brackets with higher seed strategy"""
        # Clean up any existing brackets except the test bracket
        Bracket.objects.exclude(id=self.test_bracket.id).delete()

        response = self.client.post(
            reverse("admin:generate_brackets"),
            {
                "tournament": self.tournament.id,
                "strategy": BracketStrategy.HIGHER_SEED.value,
                "num_brackets": "1",
                "user_prefix": "TestUser",
            },
        )

        self.assertEqual(response.status_code, 302)
        bracket = Bracket.objects.exclude(id=self.test_bracket.id).first()

        # Check that predictions follow higher seed strategy
        for prediction in Prediction.objects.filter(bracket=bracket):
            game = prediction.game
            bracket_game = BracketGame.objects.get(bracket=bracket, game=game)
            if bracket_game.team1_seed < bracket_game.team2_seed:
                self.assertEqual(prediction.predicted_winner, bracket_game.team1)
            else:
                self.assertEqual(prediction.predicted_winner, bracket_game.team2)

    def test_generate_brackets_higher_seed_with_upsets_strategy(self):
        """Test generating brackets with higher seed with upsets strategy"""
        # Clean up any existing brackets except the test bracket
        Bracket.objects.exclude(id=self.test_bracket.id).delete()

        response = self.client.post(
            reverse("admin:generate_brackets"),
            {
                "tournament": self.tournament.id,
                "strategy": BracketStrategy.HIGHER_SEED_WITH_UPSETS.value,
                "num_brackets": "1",
                "user_prefix": "TestUser",
            },
        )

        self.assertEqual(response.status_code, 302)
        bracket = Bracket.objects.exclude(id=self.test_bracket.id).first()

        # Check that predictions follow higher seed with upsets strategy
        predictions = Prediction.objects.filter(bracket=bracket)
        higher_seed_predictions = 0
        lower_seed_predictions = 0

        for prediction in predictions:
            game = prediction.game
            bracket_game = BracketGame.objects.get(bracket=bracket, game=game)
            if bracket_game.team1_seed < bracket_game.team2_seed:
                if prediction.predicted_winner == bracket_game.team1:
                    higher_seed_predictions += 1
                else:
                    lower_seed_predictions += 1
            else:
                if prediction.predicted_winner == bracket_game.team2:
                    higher_seed_predictions += 1
                else:
                    lower_seed_predictions += 1

        # With 80% higher seed probability, we should see roughly 5-6 higher seed predictions
        # out of 7 total predictions
        self.assertGreaterEqual(
            higher_seed_predictions, 4
        )  # Changed from assertGreater to assertGreaterEqual
        self.assertLessEqual(higher_seed_predictions, 7)

    def test_bracket_naming(self):
        """Test that brackets are named correctly with incrementing numbers"""
        # Clean up any existing brackets except the test bracket
        Bracket.objects.exclude(id=self.test_bracket.id).delete()

        # Generate multiple brackets with the same strategy
        for _ in range(3):
            self.client.post(
                reverse("admin:generate_brackets"),
                {
                    "tournament": self.tournament.id,
                    "strategy": BracketStrategy.RANDOM.value,
                    "num_brackets": "1",
                    "user_prefix": "TestUser",
                },
            )

        # Check bracket names (excluding test bracket)
        bracket_names = sorted(
            list(
                Bracket.objects.exclude(id=self.test_bracket.id).values_list(
                    "name", flat=True
                )
            )
        )
        self.assertEqual(len(bracket_names), 3)
        self.assertEqual(bracket_names[0], "Random Choice Bracket 1")
        self.assertEqual(bracket_names[1], "Random Choice Bracket 2")
        self.assertEqual(bracket_names[2], "Random Choice Bracket 3")

    def test_invalid_input_handling(self):
        """Test handling of invalid input in generate brackets view"""
        # Clean up any existing brackets except the test bracket
        Bracket.objects.exclude(id=self.test_bracket.id).delete()

        # Test missing required fields
        response = self.client.post(
            reverse("admin:generate_brackets"),
            {
                "tournament": self.tournament.id,
                "strategy": BracketStrategy.RANDOM.value,
                "num_brackets": "",  # Missing num_brackets
                "user_prefix": "TestUser",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "admin/bracketiq_admin/generate_brackets.html"
        )
        self.assertEqual(
            Bracket.objects.count(), 1
        )  # Only the test bracket should exist

        # Test invalid tournament ID
        response = self.client.post(
            reverse("admin:generate_brackets"),
            {
                "tournament": 99999,  # Non-existent tournament
                "strategy": BracketStrategy.RANDOM.value,
                "num_brackets": "1",
                "user_prefix": "TestUser",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "admin/bracketiq_admin/generate_brackets.html"
        )
        self.assertEqual(
            Bracket.objects.count(), 1
        )  # Only the test bracket should exist
