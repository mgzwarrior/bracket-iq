# backend/backend/forms.py
from django import forms
from .models import SeedList, Team


class SeedListForm(forms.ModelForm):
    class Meta:
        model = SeedList
        fields = ['year']

class GameForm(forms.Form):
    seed1 = forms.IntegerField(min_value=1, max_value=16)
    team1 = forms.ModelChoiceField(queryset=Team.objects.all())
    seed2 = forms.IntegerField(min_value=1, max_value=16)
    team2 = forms.ModelChoiceField(queryset=Team.objects.all())