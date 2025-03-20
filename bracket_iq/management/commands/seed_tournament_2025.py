from datetime import datetime, timedelta
from typing import Dict, List

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.utils.termcolors import make_style

from bracket_iq.models import Tournament, Team, Game, Region, Round, Bracket

User = get_user_model()

# Create styles for output
SUCCESS = make_style(fg="green")
ERROR = make_style(fg="red")


class Command(BaseCommand):
    help = "Seeds the 2025 NCAA Tournament data"

    # pylint: disable=too-many-statements
    def handle(self, *args, **options):
        with transaction.atomic():
            # Get or create the system admin user to own the official bracket
            admin_user, created = User.objects.get_or_create(
                username="system", defaults={"is_staff": True, "is_superuser": True}
            )
            if created:
                admin_user.set_password("not-a-real-account")
                admin_user.save()

            # Create the 2025 tournament with timezone-aware dates
            tournament, created = Tournament.objects.get_or_create(
                year=2025,
                name="2025 NCAA March Madness",
                defaults={
                    "start_date": datetime(
                        2025, 3, 18
                    ).date(),  # First Four starts March 18
                    "end_date": datetime(
                        2025, 4, 7
                    ).date(),  # Championship game on April 7
                },
            )

            # Create the official tournament bracket owned by system user
            official_bracket = Bracket.objects.create(
                tournament=tournament,
                user=admin_user,
                name="Official 2025 Tournament Results",  # Clear name indicating this is the official bracket
            )

            # First Four matchups - these teams will compete for spots in the main bracket
            # Format: (team1, team2, region to play into, seed to play for)
            first_four = [
                # Lowest-ranked conference champions (65 vs 66, 67 vs 68)
                ("Alabama State", "Saint Francis (PA)", Region.SOUTH, 16),
                ("American University", "Mount St. Mary's", Region.EAST, 16),
                # Lowest-ranked at-large teams
                ("Texas", "Xavier", Region.MIDWEST, 11),
                ("San Diego State", "North Carolina", Region.SOUTH, 11),
            ]

            # Dictionary to store region seeds - sorted numerically 1-16
            region_seeds = {
                Region.SOUTH: {
                    1: "Auburn",
                    2: "Michigan State",
                    3: "Iowa State",
                    4: "Texas A&M",
                    5: "Michigan",
                    6: "Mississippi",
                    7: "Marquette",
                    8: "Louisville",
                    9: "Creighton",
                    10: "New Mexico",
                    11: "San Diego State/North Carolina",  # First Four
                    12: "UC San Diego",
                    13: "Yale",
                    14: "Lipscomb",
                    15: "Bryant",
                    16: "Alabama State/Saint Francis",  # First Four
                },
                Region.EAST: {
                    1: "Duke",
                    2: "Alabama",
                    3: "Wisconsin",
                    4: "Arizona",
                    5: "Oregon",
                    6: "BYU",
                    7: "Saint Mary's",
                    8: "Mississippi State",
                    9: "Baylor",
                    10: "Vanderbilt",
                    11: "VCU",
                    12: "Liberty",
                    13: "Akron",
                    14: "Montana",
                    15: "Robert Morris",
                    16: "American/Mount St. Mary's",  # First Four
                },
                Region.WEST: {
                    1: "Florida",
                    2: "St. John's",
                    3: "Texas Tech",
                    4: "Maryland",
                    5: "Memphis",
                    6: "Missouri",
                    7: "Kansas",
                    8: "Connecticut",
                    9: "Oklahoma",
                    10: "Arkansas",
                    11: "Drake",
                    12: "Colorado State",
                    13: "Grand Canyon",
                    14: "UNC Wilmington",
                    15: "Nebraska Omaha",
                    16: "Norfolk State",
                },
                Region.MIDWEST: {
                    1: "Houston",
                    2: "Tennessee",
                    3: "Kentucky",
                    4: "Purdue",
                    5: "Clemson",
                    6: "Illinois",
                    7: "UCLA",
                    8: "Gonzaga",
                    9: "Georgia",
                    10: "Utah State",
                    11: "Texas/Xavier",  # First Four
                    12: "McNeese State",
                    13: "High Point",
                    14: "Troy",
                    15: "Wofford",
                    16: "Southern Illinois Edwardsville",
                },
            }

            # Create seeds and initial games
            game_number = 1
            games_by_round: Dict[int, List[Game]] = (
                {}
            )  # Track games by round for easy reference

            # First, create First Four games
            first_four_games = {}  # Track First Four games by region and seed
            first_four_start = timezone.make_aware(
                datetime(2025, 3, 18, 19, 0)
            )  # 7 PM ET start

            for team1_name, team2_name, region, seed_num in first_four:
                # Get teams
                team1 = Team.objects.filter(name=team1_name).first()
                team2 = Team.objects.filter(name=team2_name).first()

                if not team1 or not team2:
                    raise ValueError(
                        f"Could not find teams: {team1_name} or {team2_name}"
                    )

                # Create First Four game with timezone-aware datetime
                game = Game.objects.create(
                    tournament=tournament,
                    bracket=official_bracket,
                    region=region,
                    round=Round.FIRST_FOUR.value,
                    game_number=game_number,
                    seed1=seed_num,
                    team1=team1,
                    seed2=seed_num,
                    team2=team2,
                    game_date=first_four_start
                    + timedelta(hours=(game_number - 1) * 2.5),
                )
                first_four_games[(region, seed_num)] = game
                game_number += 1

            # Create Round of 64 games
            round_of_64_start = timezone.make_aware(
                datetime(2025, 3, 21, 12, 0)
            )  # Start at noon ET on March 21
            games_by_round[Round.ROUND_OF_64.value] = []

            for region, seeds in region_seeds.items():
                # Create games in seed order (1v16, 8v9, 5v12, 4v13, 6v11, 3v14, 7v10, 2v15)
                matchups = [
                    (1, 16),
                    (8, 9),
                    (5, 12),
                    (4, 13),
                    (6, 11),
                    (3, 14),
                    (7, 10),
                    (2, 15),
                ]

                for seed1, seed2 in matchups:
                    # For seeds involved in First Four games, create placeholder games
                    if (region, seed1) in first_four_games or (
                        region,
                        seed2,
                    ) in first_four_games:
                        ff_game = first_four_games.get(
                            (region, seed1)
                        ) or first_four_games.get((region, seed2))
                        other_seed = seed1 if seed2 in [11, 16] else seed2
                        other_team = (
                            Team.objects.filter(name=seeds[other_seed]).first()
                            if other_seed in seeds
                            and "/" not in seeds[other_seed]  # Skip First Four teams
                            else None
                        )

                        # Create the Round of 64 game first
                        game = Game.objects.create(
                            tournament=tournament,
                            bracket=official_bracket,
                            region=region,
                            round=Round.ROUND_OF_64.value,
                            game_number=game_number,
                            seed1=seed1,
                            team1=other_team if seed1 == other_seed else None,
                            seed2=seed2,
                            team2=other_team if seed2 == other_seed else None,
                            game_date=round_of_64_start
                            + timedelta(
                                hours=len(games_by_round[Round.ROUND_OF_64.value])
                            ),
                        )
                        # Update the First Four game to point to this Round of 64 game
                        ff_game.next_game = game
                        ff_game.save()
                    else:
                        team1 = (
                            Team.objects.filter(name=seeds[seed1]).first()
                            if seed1 in seeds
                            and "/" not in seeds[seed1]  # Skip First Four teams
                            else None
                        )
                        team2 = (
                            Team.objects.filter(name=seeds[seed2]).first()
                            if seed2 in seeds
                            and "/" not in seeds[seed2]  # Skip First Four teams
                            else None
                        )

                        # Check if both seeds exist and are not First Four teams
                        seeds_exist = seed1 in seeds and seed2 in seeds
                        not_first_four = (
                            "/" not in seeds[seed1] and "/" not in seeds[seed2]
                        )
                        teams_missing = not team1 or not team2

                        if seeds_exist and not_first_four and teams_missing:
                            raise ValueError(
                                f"Could not find teams for {region} {seed1} vs {seed2}"
                            )

                        game = Game.objects.create(
                            tournament=tournament,
                            bracket=official_bracket,
                            region=region,
                            round=Round.ROUND_OF_64.value,
                            game_number=game_number,
                            seed1=seed1,
                            team1=team1,
                            seed2=seed2,
                            team2=team2,
                            game_date=round_of_64_start
                            + timedelta(
                                hours=len(games_by_round[Round.ROUND_OF_64.value])
                            ),
                        )

                    games_by_round[Round.ROUND_OF_64.value].append(game)
                    game_number += 1

            # Create Round of 32 games
            round_of_32_start = timezone.make_aware(datetime(2025, 3, 23, 12, 0))
            games_by_round[Round.ROUND_OF_32.value] = []

            for region in Region:
                region_games = [
                    g
                    for g in games_by_round[Round.ROUND_OF_64.value]
                    if g.region == region
                ]
                for i in range(0, len(region_games), 2):
                    # Get the Round of 64 games that will feed into this game
                    game1 = region_games[i]
                    game2 = region_games[i + 1]

                    game = Game.objects.create(
                        tournament=tournament,
                        bracket=official_bracket,
                        region=region,
                        round=Round.ROUND_OF_32.value,
                        game_number=game_number,
                        game_date=round_of_32_start
                        + timedelta(hours=len(games_by_round[Round.ROUND_OF_32.value])),
                    )
                    game1.next_game = game
                    game2.next_game = game
                    games_by_round[Round.ROUND_OF_32.value].append(game)
                    game_number += 1

            # Create Sweet 16 games
            sweet_16_start = timezone.make_aware(datetime(2025, 3, 28, 19, 0))
            games_by_round[Round.SWEET_16.value] = []

            for region in Region:
                region_games = [
                    g
                    for g in games_by_round[Round.ROUND_OF_32.value]
                    if g.region == region
                ]
                for i in range(0, len(region_games), 2):
                    game = Game.objects.create(
                        tournament=tournament,
                        bracket=official_bracket,
                        region=region,
                        round=Round.SWEET_16.value,
                        game_number=game_number,
                        game_date=sweet_16_start
                        + timedelta(hours=len(games_by_round[Round.SWEET_16.value])),
                    )
                    region_games[i].next_game = game
                    region_games[i + 1].next_game = game
                    games_by_round[Round.SWEET_16.value].append(game)
                    game_number += 1

            # Create Elite 8 games
            elite_8_start = timezone.make_aware(datetime(2025, 3, 30, 19, 0))
            games_by_round[Round.ELITE_8.value] = []

            for region in Region:
                region_games = [
                    g
                    for g in games_by_round[Round.SWEET_16.value]
                    if g.region == region
                ]
                for i in range(0, len(region_games), 2):
                    game = Game.objects.create(
                        tournament=tournament,
                        bracket=official_bracket,
                        region=region,
                        round=Round.ELITE_8.value,
                        game_number=game_number,
                        game_date=elite_8_start
                        + timedelta(hours=len(games_by_round[Round.ELITE_8.value])),
                    )
                    region_games[i].next_game = game
                    region_games[i + 1].next_game = game
                    games_by_round[Round.ELITE_8.value].append(game)
                    game_number += 1

            # Create Final Four games
            final_four_start = timezone.make_aware(datetime(2025, 4, 5, 19, 0))
            games_by_round[Round.FINAL_FOUR.value] = []

            # Create Final Four games with proper region matchups
            final_four_matchups = [
                (Region.SOUTH, Region.EAST),
                (Region.WEST, Region.MIDWEST),
            ]

            for region1, region2 in final_four_matchups:
                region1_game = next(
                    g
                    for g in games_by_round[Round.ELITE_8.value]
                    if g.region == region1
                )
                region2_game = next(
                    g
                    for g in games_by_round[Round.ELITE_8.value]
                    if g.region == region2
                )

                game = Game.objects.create(
                    tournament=tournament,
                    bracket=official_bracket,
                    round=Round.FINAL_FOUR.value,
                    game_number=game_number,
                    game_date=final_four_start
                    + timedelta(hours=len(games_by_round[Round.FINAL_FOUR.value])),
                )
                region1_game.next_game = game
                region1_game.save()
                region2_game.next_game = game
                region2_game.save()
                games_by_round[Round.FINAL_FOUR.value].append(game)
                game_number += 1

            # Create Championship game
            championship_start = timezone.make_aware(datetime(2025, 4, 7, 21, 0))
            championship = Game.objects.create(
                tournament=tournament,
                bracket=official_bracket,
                round=Round.CHAMPIONSHIP.value,
                game_number=game_number,
                game_date=championship_start,
            )

            # Link Final Four games to Championship
            for game in games_by_round[Round.FINAL_FOUR.value]:
                game.next_game = championship
                game.save()

            self.stdout.write(SUCCESS("Successfully seeded 2025 tournament data"))
