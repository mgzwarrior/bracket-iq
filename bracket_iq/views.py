# views.py
from typing import Dict, List, Union, Optional

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db import transaction
from django.http import JsonResponse
from django.core.paginator import Paginator

from .forms import CustomUserCreationForm
from .models import Team, Game, Bracket, Prediction, Round, Tournament, BracketGame


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
    bracket_name = request.POST.get("bracket_name", "").strip()

    if not bracket_name:
        messages.error(request, "Bracket name is required.")
        return redirect("create_bracket_form")

    # Create a new bracket for this user and tournament
    bracket = Bracket.objects.create(
        user=request.user, tournament=tournament, name=bracket_name
    )

    # Get all games for this tournament
    games = Game.objects.filter(tournament=tournament).order_by("round", "game_number")

    # Create bracket games for each game
    for game in games:
        BracketGame.objects.create(
            bracket=bracket,
            game=game,
            team1=game.team1,
            team2=game.team2,
            team1_seed=game.seed1,
            team2_seed=game.seed2,
        )

    messages.success(
        request,
        "Bracket created successfully. You can now start making your predictions!",
    )
    return redirect("display_bracket", bracket_id=bracket.id)


@login_required
def create_bracket_form(request):
    if request.method == "POST":
        tournament_id = request.POST.get("tournament")
        if tournament_id:
            # Instead of redirecting, we'll render the create_bracket view directly
            return create_bracket(request, tournament_id)

        messages.error(request, "Please select a tournament.")

    # Get all active tournaments for the form
    tournaments = Tournament.objects.all().order_by("-year")
    return render(
        request, "bracket_iq/create_bracket.html", {"tournaments": tournaments}
    )


@login_required
def display_bracket(request, bracket_id):
    # Get the bracket or return 404
    bracket = get_object_or_404(Bracket, pk=bracket_id)

    # Get all games and predictions for this bracket
    games = Game.objects.filter(tournament=bracket.tournament).order_by(
        "round", "game_number"
    )

    # Get all bracket games for this bracket
    bracket_games = {
        bg.game_id: bg for bg in BracketGame.objects.filter(bracket=bracket)
    }

    # Organize predictions by round for easier rendering
    predictions_by_round: Dict[
        int, List[Dict[str, Union[Game, Optional[Prediction], Optional[BracketGame]]]]
    ] = {}

    for game in games:
        round_value = game.round
        if round_value not in predictions_by_round:
            predictions_by_round[round_value] = []

        # Find prediction if it exists
        try:
            prediction = Prediction.objects.get(bracket=bracket, game=game)
        except Prediction.DoesNotExist:
            prediction = None

        # Get bracket game if it exists
        bracket_game = bracket_games.get(game.id)

        # Add game to display regardless of team status
        predictions_by_round[round_value].append(
            {
                "game": game,
                "prediction": prediction,
                "bracket_game": bracket_game,
            }
        )

    # Sort games within each round by prediction status and game number
    for round_value, predictions in predictions_by_round.items():
        predictions_by_round[round_value] = sorted(
            predictions,
            key=lambda p: (p["prediction"] is not None, p["game"].game_number),
        )

    # Sort rounds by completion status
    sorted_rounds = []
    for round_value, predictions in predictions_by_round.items():
        # Calculate percentage of games predicted in this round
        total_games = len(predictions)
        predicted_games = sum(1 for p in predictions if p["prediction"] is not None)
        completion_percentage = predicted_games / total_games if total_games > 0 else 0

        sorted_rounds.append(
            {
                "round_value": round_value,
                "predictions": predictions,
                "completion_percentage": completion_percentage,
            }
        )

    # Sort rounds - incomplete rounds first, then by round value for tiebreaker
    sorted_rounds.sort(
        key=lambda x: (x["completion_percentage"] == 1, x["round_value"])
    )

    # Create a dictionary mapping round values to their labels
    round_names = {}
    for round_enum in Round:
        round_names[round_enum.value] = round_enum.label

    # Create a new sorted dictionary for predictions_by_round
    sorted_predictions = {}
    for round_data in sorted_rounds:
        sorted_predictions[round_data["round_value"]] = round_data["predictions"]

    context = {
        "bracket": bracket,
        "predictions_by_round": sorted_predictions,
        "round_names": round_names,
        "round_completion": {
            r["round_value"]: r["completion_percentage"] for r in sorted_rounds
        },
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

                    # Update the next game with the winners
                    if game.team1_id == int(winner_id):
                        next_game.team1_id = winner_id
                        next_game.seed1 = game.seed1
                    else:
                        next_game.team2_id = winner_id
                        next_game.seed2 = game.seed2

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

    # Organize predictions by round
    predictions_by_round: Dict[int, List[Dict[str, Union[Game, Prediction]]]] = {}
    for prediction in predictions:
        round_value = prediction.game.round
        if round_value not in predictions_by_round:
            predictions_by_round[round_value] = []
        predictions_by_round[round_value].append(
            {
                "game": prediction.game,
                "prediction": prediction,
            }
        )

    # Create a dictionary mapping round values to their labels
    round_names = {}
    for round_enum in Round:
        round_names[round_enum.value] = round_enum.label

    context = {
        "bracket": bracket,
        "predictions_by_round": predictions_by_round,
        "round_names": round_names,
    }

    return render(request, "bracket_iq/view_bracket.html", context)


@login_required
@require_POST
def update_prediction(request, prediction_id):
    # Get the prediction
    prediction = get_object_or_404(Prediction, pk=prediction_id)
    bracket = prediction.bracket

    # Get the game and new predicted winner
    game_id = request.POST.get("game")
    winner_id = request.POST.get("winner")

    if not game_id or not winner_id:
        return JsonResponse({"success": False, "error": "Missing game or winner ID"})

    # Update the prediction
    try:
        game = Game.objects.get(pk=game_id)
        winner = Team.objects.get(pk=winner_id)

        # Get the bracket game to verify teams
        bracket_game = get_object_or_404(BracketGame, bracket=bracket, game=game)

        # Verify this is a valid choice
        if winner not in [bracket_game.team1, bracket_game.team2]:
            return JsonResponse({"success": False, "error": "Invalid winner selection"})

        with transaction.atomic():
            # Update the prediction
            prediction.predicted_winner = winner
            prediction.save()

            # If this game has a next game, update the teams in the next bracket game
            if game.next_game:
                next_game = game.next_game
                other_game = (
                    Game.objects.filter(next_game=next_game).exclude(id=game.id).first()
                )

                # Get or create the next bracket game
                next_bracket_game, _ = BracketGame.objects.get_or_create(
                    bracket=bracket,
                    game=next_game,
                )

                # Update the next bracket game's teams based on the predictions
                # If this game has another game feeding into the same next game,
                # we need to coordinate which team slot to fill
                if other_game:
                    # First game in the pair (lower game number) updates team1
                    if game.game_number < other_game.game_number:
                        next_bracket_game.team1 = winner
                        next_bracket_game.team1_seed = (
                            bracket_game.team1_seed
                            if winner == bracket_game.team1
                            else bracket_game.team2_seed
                        )
                    # Second game in the pair (higher game number) updates team2
                    else:
                        next_bracket_game.team2 = winner
                        next_bracket_game.team2_seed = (
                            bracket_game.team1_seed
                            if winner == bracket_game.team1
                            else bracket_game.team2_seed
                        )
                else:
                    # If this is the only game feeding into the next game,
                    # update team1 if it's empty, otherwise update team2
                    if next_bracket_game.team1 is None:
                        next_bracket_game.team1 = winner
                        next_bracket_game.team1_seed = (
                            bracket_game.team1_seed
                            if winner == bracket_game.team1
                            else bracket_game.team2_seed
                        )
                    else:
                        next_bracket_game.team2 = winner
                        next_bracket_game.team2_seed = (
                            bracket_game.team1_seed
                            if winner == bracket_game.team1
                            else bracket_game.team2_seed
                        )

                next_bracket_game.save()

        return JsonResponse({"success": True})
    except (Game.DoesNotExist, Team.DoesNotExist):
        return JsonResponse({"success": False, "error": "Game or Team not found"})


def list_brackets(request):
    query_brackets = Bracket.objects.all().order_by("-created_at")
    paginator = Paginator(query_brackets, 10)  # Show 10 brackets per page

    page = request.GET.get("page")
    page_obj = paginator.get_page(page)

    return render(request, "list_brackets.html", {"brackets": page_obj})


@login_required
@require_POST
def create_prediction(request):
    # Get the bracket and game
    bracket = get_object_or_404(
        Bracket, id=request.POST.get("bracket"), user=request.user
    )
    game = get_object_or_404(Game, id=request.POST.get("game"))
    winner_id = request.POST.get("winner")

    if not winner_id:
        messages.error(request, "Please select a winner")
        return redirect("display_bracket", bracket_id=bracket.id)

    # Get the bracket game to verify teams
    bracket_game = get_object_or_404(BracketGame, bracket=bracket, game=game)

    # Verify this is a valid choice
    winner = get_object_or_404(Team, id=winner_id)
    if winner not in [bracket_game.team1, bracket_game.team2]:
        messages.error(request, "Invalid winner selection")
        return redirect("display_bracket", bracket_id=bracket.id)

    # Create or update the prediction
    _, _ = Prediction.objects.update_or_create(
        bracket=bracket, game=game, defaults={"predicted_winner": winner}
    )

    # If this game has a next game, update the teams in the next bracket game
    if game.next_game:
        next_game = game.next_game
        other_game = (
            Game.objects.filter(next_game=next_game).exclude(id=game.id).first()
        )

        # Get or create the next bracket game
        next_bracket_game, _ = BracketGame.objects.get_or_create(
            bracket=bracket,
            game=next_game,
        )

        # Update the next bracket game's teams based on the predictions
        # If this game has another game feeding into the same next game,
        # we need to coordinate which team slot to fill
        if other_game:
            # First game in the pair (lower game number) updates team1
            if game.game_number < other_game.game_number:
                next_bracket_game.team1 = winner
                next_bracket_game.team1_seed = (
                    bracket_game.team1_seed
                    if winner == bracket_game.team1
                    else bracket_game.team2_seed
                )
            # Second game in the pair (higher game number) updates team2
            else:
                next_bracket_game.team2 = winner
                next_bracket_game.team2_seed = (
                    bracket_game.team1_seed
                    if winner == bracket_game.team1
                    else bracket_game.team2_seed
                )
        else:
            # If this is the only game feeding into the next game,
            # update team1 if it's empty, otherwise update team2
            if next_bracket_game.team1 is None:
                next_bracket_game.team1 = winner
                next_bracket_game.team1_seed = (
                    bracket_game.team1_seed
                    if winner == bracket_game.team1
                    else bracket_game.team2_seed
                )
            else:
                next_bracket_game.team2 = winner
                next_bracket_game.team2_seed = (
                    bracket_game.team1_seed
                    if winner == bracket_game.team1
                    else bracket_game.team2_seed
                )

        next_bracket_game.save()

    messages.success(request, "Prediction created successfully")
    return redirect("display_bracket", bracket_id=bracket.id)
