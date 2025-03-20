# bracket_iq/models.py
import uuid
from datetime import date
from enum import Enum

from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class Region(models.TextChoices):
    EAST = "EAST", "East"
    WEST = "WEST", "West"
    MIDWEST = "MIDWEST", "Midwest"
    SOUTH = "SOUTH", "South"
    FIRST_FOUR = "FIRST_FOUR", "First Four"


class Round(Enum):
    FIRST_FOUR = (0, "First Four")
    ROUND_OF_64 = (1, "Round of 64")
    ROUND_OF_32 = (2, "Round of 32")
    SWEET_16 = (3, "Sweet 16")
    ELITE_8 = (4, "Elite Eight")
    FINAL_FOUR = (5, "Final Four")
    CHAMPIONSHIP = (6, "Championship")

    def __init__(self, round_id, label):
        self.round_id = round_id
        self.label = label

    @classmethod
    def from_value(cls, value):
        for member in cls:
            if member.round_id == value:
                return member
        raise ValueError(f"{value} is not a valid {cls.__name__}")

    @classmethod
    def get_points(cls, round_value):
        """Returns the points awarded for a correct prediction in this round."""
        points_map = {
            cls.FIRST_FOUR.round_id: 0,  # First Four games don't count for scoring
            cls.ROUND_OF_64.round_id: 1,
            cls.ROUND_OF_32.round_id: 2,
            cls.SWEET_16.round_id: 4,
            cls.ELITE_8.round_id: 8,
            cls.FINAL_FOUR.round_id: 16,
            cls.CHAMPIONSHIP.round_id: 32,
        }
        return points_map.get(round_value, 0)

    @property
    def value(self):
        return self.round_id

    def __str__(self):
        return self.label


class Tournament(models.Model):
    uuid: models.UUIDField = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True
    )
    year: models.IntegerField = models.IntegerField(default=date.today().year)
    name: models.CharField = models.CharField(
        max_length=100, default="NCAA March Madness"
    )
    start_date: models.DateField = models.DateField()
    end_date: models.DateField = models.DateField()

    class Meta:
        app_label = "bracket_iq"
        unique_together = ("year", "name")
        ordering = ["-year"]

    def __str__(self):
        return f"{self.name}"


class Team(models.Model):
    uuid: models.UUIDField = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True
    )
    name: models.CharField = models.CharField(max_length=100)
    short_name: models.CharField = models.CharField(max_length=20)
    mascot: models.CharField = models.CharField(max_length=100)

    class Meta:
        app_label = "bracket_iq"
        ordering = ["name"]  # Sort teams from A-Z

    def __str__(self):
        return f"{self.name}"


class Bracket(models.Model):
    uuid: models.UUIDField = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True
    )
    tournament: models.ForeignKey = models.ForeignKey(
        Tournament, on_delete=models.CASCADE
    )
    user: models.ForeignKey = models.ForeignKey(User, on_delete=models.CASCADE)
    name: models.CharField = models.CharField(max_length=100, default="My Bracket")
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    @property
    def score(self):
        """Calculate the total score for this bracket."""
        predictions = Prediction.objects.filter(bracket=self)
        return sum(prediction.points_earned for prediction in predictions)

    @property
    def max_possible_score(self):
        """Calculate the maximum possible remaining score."""
        remaining_points = 0
        predictions = Prediction.objects.filter(bracket=self)
        for prediction in predictions:
            if prediction.game.winner is None:  # Game hasn't been played yet
                remaining_points += Round.get_points(prediction.game.round)
        return self.score + remaining_points

    def __str__(self):
        user_name = (
            getattr(self.user, "username", "Unknown User")
            if self.user
            else "Unknown User"
        )
        tournament_name = (
            getattr(self.tournament, "name", "Unknown Tournament")
            if self.tournament
            else "Unknown Tournament"
        )
        return f"{user_name}'s {tournament_name} Bracket"

    class Meta:
        app_label = "bracket_iq"
        unique_together = ("tournament", "user", "name")
        ordering = ["-created_at"]


class Game(models.Model):
    tournament: models.ForeignKey = models.ForeignKey(
        Tournament, on_delete=models.CASCADE
    )
    bracket: models.ForeignKey = models.ForeignKey(Bracket, on_delete=models.CASCADE)
    round: models.IntegerField = models.IntegerField(
        choices=[(r.value, r.label) for r in Round]
    )
    region: models.CharField = models.CharField(max_length=20, choices=Region.choices)
    game_number: models.IntegerField = models.IntegerField()
    seed1: models.IntegerField = models.IntegerField(null=True, blank=True)
    team1: models.ForeignKey = models.ForeignKey(
        Team,
        related_name="team1_games",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    seed2: models.IntegerField = models.IntegerField(null=True, blank=True)
    team2: models.ForeignKey = models.ForeignKey(
        Team,
        related_name="team2_games",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    winner: models.ForeignKey = models.ForeignKey(
        Team, related_name="games_won", on_delete=models.CASCADE, null=True, blank=True
    )
    score1: models.IntegerField = models.IntegerField(null=True, blank=True)
    score2: models.IntegerField = models.IntegerField(null=True, blank=True)
    game_date: models.DateTimeField = models.DateTimeField(null=True)
    next_game: models.ForeignKey = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True
    )

    def clean(self):
        if self.winner and self.winner not in [self.team1, self.team2]:
            raise ValidationError("Winner must be one of the teams playing in the game")
        if (self.score1 is None) != (self.score2 is None):
            raise ValidationError("Both scores must be entered together")
        if self.score1 is not None and self.score2 is not None:
            if self.winner is None:
                raise ValidationError("Winner must be set if scores are entered")
            if self.score1 > self.score2 and self.winner != self.team1:
                raise ValidationError("Winner must be team1 if team1's score is higher")
            if self.score2 > self.score1 and self.winner != self.team2:
                raise ValidationError("Winner must be team2 if team2's score is higher")

    def __str__(self):
        team1_name = self.team1.name if self.team1 else "TBD"
        team2_name = self.team2.name if self.team2 else "TBD"
        return f"Game {self.game_number}: {team1_name} vs {team2_name}"

    class Meta:
        ordering = ["tournament", "round", "game_number"]


class Prediction(models.Model):
    game: models.ForeignKey = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name="predictions"
    )
    bracket: models.ForeignKey = models.ForeignKey(
        Bracket, on_delete=models.CASCADE, related_name="predictions"
    )
    predicted_winner: models.ForeignKey = models.ForeignKey(
        Team, on_delete=models.CASCADE
    )
    is_correct: models.BooleanField = models.BooleanField(default=False)
    points_earned: models.IntegerField = models.IntegerField(default=0)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    @property
    def calculate_points(self):
        """Calculate points earned for this prediction."""
        if not self.is_correct or not self.game:
            return 0

        if hasattr(self.game, "round") and getattr(self.game, "winner", None):
            return Round.get_points(self.game.round)
        return 0

    def clean(self):
        if self.game and self.predicted_winner:
            team1 = getattr(self.game, "team1", None)
            team2 = getattr(self.game, "team2", None)

            if team1 and team2 and self.predicted_winner not in [team1, team2]:
                raise ValidationError(
                    "Predicted winner must be one of the teams playing in the game"
                )

    def __str__(self):
        bracket_user = "Unknown User"
        if self.bracket:
            bracket = self.bracket
            # Get the associated user model if any
            try:
                if hasattr(bracket, "user") and bracket.user is not None:
                    username = getattr(bracket.user, "username", "Unknown User")
                    bracket_user = username
            except (AttributeError, TypeError):
                pass

        game_info = "Unknown Game"
        if self.game and hasattr(self.game, "game_number"):
            game_info = f"Game {self.game.game_number}"

        return f"{bracket_user}'s prediction for {game_info}"

    class Meta:
        app_label = "bracket_iq"
        unique_together = ("game", "bracket")
        ordering = ["game__round", "game__game_number"]


class BracketGame(models.Model):
    """Tracks which teams should appear in each game based on predictions within a specific bracket."""
    bracket = models.ForeignKey(Bracket, on_delete=models.CASCADE, related_name='bracket_games')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='bracket_games')
    team1: models.ForeignKey = models.ForeignKey(Team, related_name='bracket_games_team1', null=True, blank=True, on_delete=models.SET_NULL)
    team2: models.ForeignKey = models.ForeignKey(Team, related_name='bracket_games_team2', null=True, blank=True, on_delete=models.SET_NULL)
    team1_seed = models.IntegerField(null=True, blank=True)
    team2_seed = models.IntegerField(null=True, blank=True)
    winner = models.ForeignKey(Team, related_name='bracket_games_won', null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "bracket_iq"
        unique_together = ['bracket', 'game']
        ordering = ['game__game_number']

    def __str__(self):
        team1_name = self.team1.name if self.team1 else "TBD"
        team2_name = self.team2.name if self.team2 else "TBD"
        return f"{self.bracket.name} - Game {self.game.game_number}: {team1_name} vs {team2_name}"
