from django.db import models


class Team(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    nickname = models.CharField(max_length=200)


