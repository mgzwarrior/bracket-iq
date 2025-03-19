# views.py
import datetime

import random
from itertools import combinations

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db import transaction
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.urls import reverse

from .forms import GameForm, BracketForm, PredictionForm
from .models import Team, Game, Bracket, Prediction, Round, Tournament
from .forms import CustomUserCreationForm


@login_required(login_url="login")
def home(request):
    # Get all tournaments
    tournaments = Tournament.objects.all().order_by("-year")
    return render(request, "home.html", {"tournaments": tournaments})


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            messages.success(request, f"Account created for {username}!")
            return redirect("login")
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def profile(request):
    # Get all brackets for the current user
    brackets = Bracket.objects.filter(user=request.user)

    # Pass the brackets to the template
    return render(request, "profile.html", {"brackets": brackets})


@login_required
@require_POST
def create_bracket(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)

    # Create a new bracket for this user and tournament
    bracket = Bracket.objects.create(user=request.user, tournament=tournament)

    # Get all games for this tournament
    games = Game.objects.filter(tournament=tournament).order_by("round", "game_number")

    # Create predictions for each game
    for game in games:
        Prediction.objects.create(
            bracket=bracket,
            game=game,
            predicted_winner=game.team1 if game.team1 else None,
        )

    messages.success(request, "Bracket created successfully.")
    return redirect("display_bracket", bracket_id=bracket.id)


@login_required
def create_bracket_form(request):
    if request.method == "POST":
        tournament_id = request.POST.get("tournament")
        if tournament_id:
            return redirect("create_bracket", tournament_id=tournament_id)
        else:
            messages.error(request, "Please select a tournament.")

    # Get all active tournaments for the form
    tournaments = Tournament.objects.all().order_by("-year")
    return render(
        request, "bracket_iq/create_bracket.html", {"tournaments": tournaments}
    )


@login_required
def create_live_bracket(request, game_number=1):
    if request.method == "POST":
        form = GameForm(request.POST)
        if form.is_valid():
            # Get or create a Bracket object for the current user
            bracket, created = Bracket.objects.get_or_create(user=request.user)
            if game_number >= 1 and game_number < 5:
                round = Round.FIRST_FOUR.value
            # Create a new game
            Game.objects.create(
                seed1=form.cleaned_data["seed1"],
                team1=form.cleaned_data["team1"],
                seed2=form.cleaned_data["seed2"],
                team2=form.cleaned_data["team2"],
                game_number=game_number,
                bracket=bracket,
                round=round,
                year=datetime.date.today().year,
            )
            # Redirect to the next game creation page or the completed bracket page
            if game_number < 68:
                return redirect("create_live_bracket", game_number=game_number + 1)
            else:
                return redirect("display_bracket")
    else:
        form = GameForm()

    return render(
        request, "create_live_bracket.html", {"form": form, "game_number": game_number}
    )


@login_required
def display_bracket(request, bracket_id):
    bracket = get_object_or_404(Bracket, id=bracket_id)
    predictions = Prediction.objects.filter(bracket=bracket).select_related("game")

    # Group predictions by round
    predictions_by_round = {}
    for prediction in predictions:
        round_num = prediction.game.round
        if round_num not in predictions_by_round:
            predictions_by_round[round_num] = []
        predictions_by_round[round_num].append(prediction)

    # Sort predictions within each round by game number
    for round_num in predictions_by_round:
        predictions_by_round[round_num].sort(key=lambda p: p.game.game_number)

    context = {
        "bracket": bracket,
        "predictions_by_round": predictions_by_round,
        "rounds": Round,
    }
    return render(request, "display_bracket.html", context)


@login_required
@require_POST
def delete_bracket(request, bracket_id):
    bracket = get_object_or_404(Bracket, id=bracket_id)
    if bracket.user != request.user:
        messages.error(request, "You do not have permission to delete this bracket.")
        return redirect("home")

    bracket.delete()
    messages.success(request, "Bracket deleted successfully.")
    return redirect("home")


@login_required
def fill_bracket(request, bracket_id):
    bracket = get_object_or_404(Bracket, id=bracket_id, user=request.user)
    tournament = bracket.tournament

    # Get all games organized by round and region
    games_by_round = {}
    for round_enum in Round:
        games = Game.objects.filter(
            tournament=tournament, round=round_enum.value
        ).order_by("game_number")

        if round_enum.value >= Round.FINAL_FOUR.value:
            # Final Four and Championship are special cases
            games_by_round[round_enum] = {"Final": list(games)}
        else:
            # Group other rounds by region
            games_by_round[round_enum] = {}
            for game in games:
                region = game.region
                if region not in games_by_round[round_enum]:
                    games_by_round[round_enum][region] = []
                games_by_round[round_enum][region].append(game)

    # Get existing predictions
    predictions = {
        pred.game_id: pred.predicted_winner
        for pred in Prediction.objects.filter(bracket=bracket)
    }

    if request.method == "POST":
        game_id = request.POST.get("game_id")
        winner_id = request.POST.get("winner")

        if game_id and winner_id:
            game = get_object_or_404(Game, id=game_id)
            with transaction.atomic():
                # Update or create prediction for this game
                Prediction.objects.update_or_create(
                    bracket=bracket,
                    game=game,
                    defaults={"predicted_winner_id": winner_id},
                )

                # If this game has a next game, update the teams in the next game
                if game.next_game:
                    next_game = game.next_game
                    other_game = (
                        Game.objects.filter(next_game=next_game)
                        .exclude(id=game.id)
                        .first()
                    )

                    other_winner = None
                    if other_game:
                        other_pred = Prediction.objects.filter(
                            bracket=bracket, game=other_game
                        ).first()
                        if other_pred:
                            other_winner = other_pred.predicted_winner

                    # Update the next game with the winners
                    if game.team1_id == int(winner_id):
                        next_game.team1_id = winner_id
                        next_game.seed1 = game.seed1
                    else:
                        next_game.team2_id = winner_id
                        next_game.seed2 = game.seed2

                    if other_winner:
                        if other_game.team1 == other_winner:
                            next_game.team1 = other_winner
                            next_game.seed1 = other_game.seed1
                        else:
                            next_game.team2 = other_winner
                            next_game.seed2 = other_game.seed2

                    next_game.save()

            return redirect("fill_bracket", bracket_id=bracket.id)

    context = {
        "bracket": bracket,
        "games_by_round": games_by_round,
        "predictions": predictions,
        "rounds": Round,
    }

    return render(request, "bracket_iq/fill_bracket.html", context)


@login_required
def view_bracket(request, bracket_id):
    bracket = get_object_or_404(Bracket, id=bracket_id)
    predictions = Prediction.objects.filter(bracket=bracket).select_related(
        "game", "predicted_winner"
    )

    context = {
        "bracket": bracket,
        "predictions": predictions,
    }

    return render(request, "bracket_iq/view_bracket.html", context)


@login_required
def seed_tournament(request):
    """View for seeding a new tournament through the web interface."""
    if not request.user.is_staff:
        messages.error(request, "You must be an admin to seed tournaments.")
        return redirect("home")

    if request.method == "POST":
        year = request.POST.get("year")
        if not year:
            messages.error(request, "Year is required.")
            return redirect("seed_tournament")

        try:
            # Clear existing data
            with transaction.atomic():
                Tournament.objects.filter(year=year).delete()

                # Run the seeding command
                from django.core.management import call_command

                call_command("seed_teams")
                call_command("seed_tournament_2025")

                messages.success(request, f"Successfully seeded {year} tournament.")
                return redirect("admin:bracket_iq_tournament_changelist")
        except Exception as e:
            messages.error(request, f"Error seeding tournament: {str(e)}")
            return redirect("seed_tournament")

    # GET request - show the form
    current_year = datetime.datetime.now().year
    years = range(
        current_year, current_year + 5
    )  # Allow seeding up to 5 years in advance
    return render(request, "admin/seed_tournament.html", {"years": years})


@login_required
@require_POST
def update_prediction(request, prediction_id):
    prediction = get_object_or_404(Prediction, id=prediction_id)
    if prediction.bracket.user != request.user:
        return JsonResponse({"error": "Permission denied"}, status=403)

    form = PredictionForm(request.POST, instance=prediction)
    if form.is_valid():
        form.save()
        return JsonResponse({"success": True})
    return JsonResponse({"error": form.errors}, status=400)


def list_brackets(request):
    brackets = Bracket.objects.all().order_by("-created_at")
    paginator = Paginator(brackets, 10)  # Show 10 brackets per page

    page = request.GET.get("page")
    brackets = paginator.get_page(page)

    return render(request, "list_brackets.html", {"brackets": brackets})
