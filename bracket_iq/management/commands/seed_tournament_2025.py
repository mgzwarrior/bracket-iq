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
                ("San Diego State", "North Carolina", Region.WEST, 11),
            ]

            # Dictionary to store region seeds - removed seeds where First Four games will determine them
            region_seeds = {
                Region.SOUTH: {
                    1: "Auburn",
                    8: "Louisville",
                    9: "Creighton",
                    5: "Michigan",
                    12: "UC San Diego",
                    4: "Texas A&M",
                    13: "Yale",
                    6: "Mississippi",
                    3: "Iowa State",
                    14: "Lipscomb",
                    7: "Marquette",
                    10: "New Mexico",
                    2: "Michigan State",
                    15: "Bryant",
                },
                Region.EAST: {
                    1: "Duke",
                    8: "Mississippi State",
                    9: "Baylor",
                    5: "Oregon",
                    12: "Liberty",
                    4: "Arizona",
                    13: "Akron",
                    6: "BYU",
                    11: "VCU",
                    3: "Wisconsin",
                    14: "Montana",
                    7: "Saint Mary's",
                    10: "Vanderbilt",
                    2: "Alabama",
                    15: "Robert Morris",
                },
                Region.WEST: {
                    1: "Florida",
                    8: "Connecticut",
                    9: "Oklahoma",
                    5: "Memphis",
                    12: "Colorado State",
                    4: "Maryland",
                    13: "Grand Canyon",
                    6: "Missouri",
                    3: "Texas Tech",
                    14: "UNC Wilmington",
                    7: "Kansas",
                    10: "Arkansas",
                    2: "St. John's",
                    15: "Nebraska Omaha",
                },
                Region.MIDWEST: {
                    1: "Houston",
                    8: "Gonzaga",
                    9: "Georgia",
                    5: "Clemson",
                    12: "McNeese State",
                    4: "Purdue",
                    13: "High Point",
                    6: "Illinois",
                    3: "Kentucky",
                    14: "Troy",
                    7: "UCLA",
                    10: "Utah State",
                    2: "Tennessee",
                    15: "Wofford",
                },
            }

            # Create seeds and initial games
            game_number = 1

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
                    + timedelta(
                        hours=(game_number - 1) * 2.5
                    ),  # Games staggered by 2.5 hours
                )
                first_four_games[(region, seed_num)] = game
                game_number += 1

            # Create first round (Round of 64) games
            round_of_64_start = timezone.make_aware(
                datetime(2025, 3, 21, 12, 0)
            )  # Start at noon ET on March 21
            # Initialize games_per_region with actual Region values
            games_per_region: Dict[Region, List[Game]] = {
                Region.SOUTH: [],
                Region.EAST: [],
                Region.MIDWEST: [],
                Region.WEST: [],
            }

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
                        # Get the First Four game
                        ff_game = first_four_games.get(
                            (region, seed1)
                        ) or first_four_games.get((region, seed2))
                        # Get the non-First Four team
                        other_seed = seed1 if seed2 in [11, 16] else seed2
                        other_team = (
                            Team.objects.filter(name=seeds[other_seed]).first()
                            if other_seed in seeds
                            else None
                        )

                        # Create the Round of 64 game with the known team
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
                            + timedelta(hours=len(games_per_region[region])),
                        )
                        # Link the First Four game to this game
                        ff_game.next_game = game
                        ff_game.save()
                    else:
                        # Regular matchup - check if both teams are in the seeds dictionary
                        team1 = (
                            Team.objects.filter(name=seeds[seed1]).first()
                            if seed1 in seeds
                            else None
                        )
                        team2 = (
                            Team.objects.filter(name=seeds[seed2]).first()
                            if seed2 in seeds
                            else None
                        )

                        if (
                            seed1 in seeds
                            and seed2 in seeds
                            and (not team1 or not team2)
                        ):
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
                            + timedelta(hours=len(games_per_region[region])),
                        )

                    games_per_region[region].append(game)
                    game_number += 1

            self.stdout.write(SUCCESS("Successfully seeded 2025 tournament data"))
