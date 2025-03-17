# backend/backend/forms.py
from django import forms
from .models import Team, Tournament, Game, Bracket, Prediction
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class GameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ['team1', 'team2', 'region', 'round', 'game_number']

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class BracketForm(forms.ModelForm):
    class Meta:
        model = Bracket
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }

class PredictionForm(forms.ModelForm):
    predicted_winner = forms.ModelChoiceField(queryset=None, widget=forms.RadioSelect)

    class Meta:
        model = Prediction
        fields = ['predicted_winner']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.game:
            teams = []
            if self.instance.game.team1:
                teams.append(self.instance.game.team1)
            if self.instance.game.team2:
                teams.append(self.instance.game.team2)
            self.fields['predicted_winner'].queryset = Team.objects.filter(id__in=[team.id for team in teams])
            if teams:
                self.fields['predicted_winner'].label = f"{teams[0].name} vs {teams[1].name if len(teams) > 1 else 'TBD'}"