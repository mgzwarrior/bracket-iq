# models.py
import uuid
from datetime import date
from enum import Enum

from django.db import models
from django.contrib.auth.models import User

class Round(Enum):
    FIRST_FOUR = 1, 'First Four'
    ROUND_OF_64 = 2, 'Round of 64'
    ROUND_OF_32 = 3, 'Round of 32'
    SWEET_SIXTEEN = 4, 'Sweet Sixteen'
    ELITE_EIGHT = 5, 'Elite Eight'
    FINAL_FOUR = 6, 'Final Four'
    CHAMPIONSHIP = 7, 'Championship'

    def __new__(cls, value, name):
        obj = object.__new__(cls)
        obj._value_ = value
        obj._name_ = name
        return obj

    def __int__(self):
        return self.value

    def __str__(self):
        return self.name

class Team(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Bracket(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    year = models.IntegerField(default=date.today().year)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Game(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    seed1 = models.IntegerField()
    team1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='team1')
    seed2 = models.IntegerField()
    team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='team2')
    winner = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='winner', null=True)
    round = models.IntegerField(choices=[(round.value, round.name) for round in Round])
    year = models.IntegerField()  # New field
    game_number = models.IntegerField()  # New field
    bracket = models.ForeignKey(Bracket, on_delete=models.CASCADE, related_name='games')  # New field

    class Meta:
        unique_together = ('bracket', 'game_number')  # Ensure unique game numbers per bracket

class Prediction(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    predicted_winner = models.ForeignKey(Team, on_delete=models.CASCADE)
    bracket = models.ForeignKey(Bracket, on_delete=models.CASCADE, related_name='predictions')

class Seed(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    seed = models.IntegerField()
    true_seed = models.IntegerField(unique=True)
    seed_list = models.ForeignKey('SeedList', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('true_seed', 'seed_list')

class SeedList(models.Model):
    year = models.IntegerField(default=date.today().year, unique=True)
    seeds = models.ManyToManyField(Seed)