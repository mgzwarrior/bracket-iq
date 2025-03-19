# bracket_iq/models.py
import uuid
from datetime import date
from enum import Enum

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


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

    def __init__(self, id, label):
        self.id = id
        self.label = label

    @classmethod
    def from_value(cls, value):
        for member in cls:
            if member.id == value:
                return member
        raise ValueError(f"{value} is not a valid {cls.__name__}")

    @classmethod
    def get_points(cls, round_value):
        """Returns the points awarded for a correct prediction in this round."""
        points_map = {
            cls.FIRST_FOUR.id: 0,  # First Four games don't count for scoring
            cls.ROUND_OF_64.id: 1,
            cls.ROUND_OF_32.id: 2,
            cls.SWEET_16.id: 4,
            cls.ELITE_8.id: 8,
            cls.FINAL_FOUR.id: 16,
            cls.CHAMPIONSHIP.id: 32,
        }
        return points_map.get(round_value, 0)

    @property
    def value(self):
        return self.id

    def __str__(self):
        return self.label


class Tournament(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    year = models.IntegerField(default=date.today().year)
    name = models.CharField(max_length=100, default="NCAA March Madness")
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        app_label = "bracket_iq"
        unique_together = ("year", "name")
        ordering = ["-year"]

    def __str__(self):
        return f"{self.name}"


class Team(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=20)
    mascot = models.CharField(max_length=100)

    class Meta:
        app_label = "bracket_iq"

    def __str__(self):
        return f"{self.name}"


class Bracket(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default="My Bracket")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def score(self):
        """Calculate the total score for this bracket."""
        return sum(prediction.points_earned for prediction in self.predictions.all())

    @property
    def max_possible_score(self):
        """Calculate the maximum possible remaining score."""
        remaining_points = 0
        for prediction in self.predictions.all():
            if prediction.game.winner is None:  # Game hasn't been played yet
                remaining_points += Round.get_points(prediction.game.round)
        return self.score + remaining_points

    def __str__(self):
        return f"{self.user.username}'s {self.tournament} Bracket"

    class Meta:
        app_label = "bracket_iq"
        unique_together = ("tournament", "user", "name")
        ordering = ["-created_at"]


class Game(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    bracket = models.ForeignKey(Bracket, on_delete=models.CASCADE)
    round = models.IntegerField(choices=[(r.value, r.label) for r in Round])
    region = models.CharField(max_length=20, choices=Region.choices)
    game_number = models.IntegerField()
    seed1 = models.IntegerField()
    team1 = models.ForeignKey(
        Team,
        related_name="team1_games",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    seed2 = models.IntegerField()
    team2 = models.ForeignKey(
        Team,
        related_name="team2_games",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    winner = models.ForeignKey(
        Team, related_name="games_won", on_delete=models.CASCADE, null=True, blank=True
    )
    score1 = models.IntegerField(null=True, blank=True)
    score2 = models.IntegerField(null=True, blank=True)
    game_date = models.DateTimeField(null=True)
    next_game = models.ForeignKey(
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
        return f"Game {self.game_number}: {self.team1} vs {self.team2}"

    class Meta:
        ordering = ["tournament", "round", "game_number"]


class Prediction(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="predictions")
    bracket = models.ForeignKey(
        Bracket, on_delete=models.CASCADE, related_name="predictions"
    )
    predicted_winner = models.ForeignKey(Team, on_delete=models.CASCADE)
    is_correct = models.BooleanField(default=False)
    points_earned = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def points_earned(self):
        """Calculate points earned for this prediction."""
        if not self.is_correct or not self.game.winner:
            return 0
        return Round.get_points(self.game.round)

    def clean(self):
        if self.predicted_winner not in [self.game.team1, self.game.team2]:
            raise ValidationError(
                "Predicted winner must be one of the teams playing in the game"
            )

    def __str__(self):
        return f"{self.bracket.user.username}'s prediction for {self.game}"

    class Meta:
        app_label = "bracket_iq"
        unique_together = ("game", "bracket")
        ordering = ["game__round", "game__game_number"]
