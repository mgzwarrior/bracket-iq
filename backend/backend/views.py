# views.py
import datetime

import random
from itertools import combinations

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .forms import SeedListForm, GameForm
from .models import Team, Game, Bracket, Prediction, SeedList, Seed, Round


@login_required(login_url='login')
def home(request):
    # Get all SeedList objects
    seed_lists = SeedList.objects.all()

    # Pass the seed lists to the template
    return render(request, 'home.html', {'seed_lists': seed_lists})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile(request):
    # Get all brackets for the current user
    brackets = Bracket.objects.filter(user=request.user)

    # Pass the brackets to the template
    return render(request, 'profile.html', {'brackets': brackets})

@login_required
def create_seed_list(request):
    if request.method == 'POST':
        form = SeedListForm(request.POST)
        if form.is_valid():
            seed_list = form.save()

            # Select 68 teams randomly from the Team objects
            all_teams = list(Team.objects.all())
            if len(all_teams) < 68:
                messages.error(request, 'Not enough teams in the database. Please add more teams.')
                return redirect('home')
            selected_teams = random.sample(all_teams, 68)

            # Create a list of seeds 1-9 and 11-15, each repeated 4 times
            seeds = list(range(1, 10)) + list(range(11, 16))
            seeds = seeds * 4

            # Extend this list with seeds 10 and 16, each repeated 6 times
            seeds.extend([10, 16] * 6)

            # Shuffle this list to randomize the order of the seeds
            random.shuffle(seeds)

            # Create a Seed object for each selected team with a true_seed from 1 to 68 and a seed from the shuffled list
            for i, team in enumerate(selected_teams, start=1):
                Seed.objects.create(team=team, true_seed=i, seed_list=seed_list, seed=seeds[i-1])

            messages.success(request, 'SeedList created successfully.')
            return redirect('home')
    else:
        form = SeedListForm()
    return render(request, 'create_seed_list_form.html', {'form': form})

@login_required
def display_seed_list(request, id):
    # Get the SeedList object for the given ID
    seed_list = SeedList.objects.get(id=id)

    # Get all Seed objects associated with this seed list
    seeds = Seed.objects.filter(seed_list=seed_list).order_by('true_seed')

    # Pass the seed list and seeds to the template
    return render(request, 'display_seed_list.html', {'seed_list': seed_list, 'seeds': seeds})

@login_required
def delete_seed_list(request, seed_list_id):
    if request.method == 'POST':
        seed_list = get_object_or_404(SeedList, id=seed_list_id)
        seed_list.delete()
        messages.success(request, 'SeedList deleted successfully.')
        return redirect('home')

@login_required
@require_POST
def create_bracket(request, seed_list_id):
    seed_list = get_object_or_404(SeedList, id=seed_list_id)

    # Create a new Bracket object
    bracket = Bracket.objects.create(user=request.user, year=seed_list.year)

    # Initialize game_number
    game_number = 1

    # Create the "First Four" round games
    for seed in [10, 16]:
        seeds = Seed.objects.filter(seed_list=seed_list, seed=seed)
        teams = [seed.team for seed in seeds]
        for team1, team2 in combinations(teams, 2):
            game = Game.objects.create(team1=team1, team2=team2, round=Round.FIRST_FOUR.value, bracket=bracket, year=seed_list.year, game_number=game_number)
            game_number += 1
            # Create a prediction for the game
            Prediction.objects.create(game=game, predicted_winner=team1, bracket=bracket)

    # Create the "Round of 64" round games
    selected_teams = set()
    for seed in range(1, 17):
        if seed not in [10, 16]:
            teams1 = [seed.team for seed in seed_list.seeds.filter(seed=seed) if seed.team not in selected_teams]
            teams2 = [seed.team for seed in seed_list.seeds.filter(seed=17-seed) if seed.team not in selected_teams]
            for team1, team2 in zip(teams1, teams2):
                game = Game.objects.create(team1=team1, team2=team2, round=Round.ROUND_OF_64.value, bracket=bracket, year=seed_list.year, game_number=game_number)
                game_number += 1
                # Create a prediction for the game
                Prediction.objects.create(game=game, predicted_winner=team2, bracket=bracket)
                # Add the teams to the set of selected teams
                selected_teams.add(team1)
                selected_teams.add(team2)

    messages.success(request, 'Bracket created successfully.')
    return redirect('display_bracket', id=bracket.id)

@login_required
def create_bracket_form(request):
    # Get all SeedList objects
    seed_lists = SeedList.objects.all()

    # Pass the seed lists to the template
    return render(request, 'create_bracket_form.html', {'seed_lists': seed_lists})

@login_required
def create_first_four(request):
    # Get the selected seedlist
    seedlist_id = request.POST.get('seedlist')
    seedlist = get_object_or_404(SeedList, id=seedlist_id)

    seeds10 = Seed.objects.filter(seed_list=seedlist, seed=10)
    seeds16 = Seed.objects.filter(seed_list=seedlist, seed=16)

    # Get the teams with seeds 10 and 16
    teams10 = [seed.team for seed in seeds10]
    teams16 = [seed.team for seed in seeds16]

    # Split the teams into two lists for the games
    teams10_game1 = teams10[:2]
    teams10_game2 = teams10[2:]
    teams16_game1 = teams16[:2]
    teams16_game2 = teams16[2:]

    # Create a list of numbers for the games
    games = list(range(1, 5))

    # Pass the teams and games to the template
    return render(request, 'create_first_four.html', {'teams10_game1': teams10_game1, 'teams10_game2': teams10_game2, 'teams16_game1': teams16_game1, 'teams16_game2': teams16_game2, 'games': games})

# views.py
@login_required
@require_POST
def create_bracket_from_form(request):
    # Get the selected seedlist
    seedlist_id = request.POST.get('seedlist')
    seedlist = get_object_or_404(SeedList, id=seedlist_id)

    # Create a new Bracket object
    bracket = Bracket.objects.create(user=request.user, year=seedlist.year)

    # Create the games and predictions
    for i in range(1, 69):
        team1_id = request.POST.get(f'game{i}team1')
        team2_id = request.POST.get(f'game{i}team2')
        team1 = get_object_or_404(Team, id=team1_id)
        team2 = get_object_or_404(Team, id=team2_id)
        round = Round.FIRST_FOUR.value if i <= 4 else Round.ROUND_OF_64.value
        game = Game.objects.create(team1=team1, team2=team2, round=round, bracket=bracket, year=seedlist.year, game_number=i)
        # Create a prediction for the game
        Prediction.objects.create(game=game, predicted_winner=team1, bracket=bracket)

    messages.success(request, 'Bracket created successfully.')
    return redirect('display_bracket', id=bracket.id)

@login_required
def create_live_bracket(request, game_number=1):
    if request.method == 'POST':
        form = GameForm(request.POST)
        if form.is_valid():
            # Get or create a Bracket object for the current user
            bracket, created = Bracket.objects.get_or_create(user=request.user)
            if game_number >= 1 and game_number < 5:
                round = Round.FIRST_FOUR.value
            # Create a new game
            Game.objects.create(seed1=form.cleaned_data['seed1'], team1=form.cleaned_data['team1'], seed2=form.cleaned_data['seed2'], team2=form.cleaned_data['team2'], game_number=game_number, bracket=bracket, round=round, year=datetime.date.today().year)
            # Redirect to the next game creation page or the completed bracket page
            if game_number < 68:
                return redirect('create_live_bracket', game_number=game_number+1)
            else:
                return redirect('display_bracket')
    else:
        form = GameForm()

    return render(request, 'create_live_bracket.html', {'form': form, 'game_number': game_number})

@login_required
def display_bracket(request, id):
    bracket = Bracket.objects.get(id=id)
    games = Game.objects.filter(bracket=bracket).order_by('game_number')
    predictions = Prediction.objects.filter(bracket=bracket)
    print(bracket)
    print(games)
    print(predictions)
    return render(request, 'display_bracket.html', {'bracket': bracket, 'games': games, 'predictions': predictions})

@login_required
@require_POST
def delete_bracket(request, id):
    bracket = get_object_or_404(Bracket, id=id)
    bracket.delete()
    return redirect('home')
