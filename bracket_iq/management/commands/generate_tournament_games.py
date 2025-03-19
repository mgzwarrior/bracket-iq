from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from bracket_iq.models import Tournament, Team, Game, Region, Round
from django.db.models import Q


class Command(BaseCommand):
    help = "Generates tournament games and their relationships"

    def handle(self, *args, **options):
        # Get the most recent tournament
        tournament = Tournament.objects.latest("start_date")

        # Game numbers start after First Four (which are games 1-4)
        game_number = 5

        # Dictionary to store games by round for linking
        games_by_round = {
            Round.FIRST_FOUR.value: {},
            Round.ROUND_OF_64.value: {},
            Round.ROUND_OF_32.value: {},
            Round.SWEET_16.value: {},
            Round.ELITE_8.value: {},
            Round.FINAL_FOUR.value: {},
            Round.CHAMPIONSHIP.value: {},
        }

        # Create Round of 64 games
        round_64_date = datetime(2025, 3, 20, 12, 0)  # Start at noon on March 20
        for region in Region.choices:
            region_code = region[0]

            # Filter for teams in the tournament - this would need to be added to Team model
            # or customized to fit your actual data model
            teams = Team.objects.all()[
                :16
            ]  # Simplified - you would need proper filtering

            # Create matchups (1v16, 8v9, 5v12, 4v13, 6v11, 3v14, 7v10, 2v15)
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

            team_index = 0
            for seed1, seed2 in matchups:
                # Get teams for this matchup
                team1 = teams[team_index]
                team2 = teams[team_index + 1]
                team_index += 2

                # Create game
                game = Game.objects.create(
                    tournament=tournament,
                    region=region_code,
                    round=Round.ROUND_OF_64.value,
                    game_number=game_number,
                    seed1=seed1,
                    team1=team1,
                    seed2=seed2,
                    team2=team2,
                    game_date=round_64_date,
                )

                # Store for linking in next rounds
                games_by_round[Round.ROUND_OF_64.value][game_number] = game

                # Increment game number and date
                game_number += 1
                round_64_date += timedelta(hours=2)  # Space games 2 hours apart

        # Continue with the rest of the tournament structure
        self.create_subsequent_rounds(tournament, games_by_round, game_number)

        self.stdout.write(self.style.SUCCESS("Tournament games generated successfully"))

    def create_subsequent_rounds(self, tournament, games_by_round, game_number):
        # Create Round of 32 (winners of Round of 64)
        # Implement the logic to create subsequent rounds
        pass
