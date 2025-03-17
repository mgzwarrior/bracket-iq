from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from bracket_iq.models import Tournament, Team, Game, SeedList, Seed, Region, Round

class Command(BaseCommand):
    help = 'Generates tournament games and their relationships'

    def handle(self, *args, **options):
        # Get the most recent tournament
        tournament = Tournament.objects.latest('start_date')
        seed_list = tournament.seedlist

        # Game numbers start after First Four (which are games 1-4)
        game_number = 5

        # Dictionary to store games by round for linking
        games_by_round = {
            Round.FIRST_FOUR.value: {},
            Round.ROUND_OF_64.value: {},
            Round.ROUND_OF_32.value: {},
            Round.SWEET_SIXTEEN.value: {},
            Round.ELITE_EIGHT.value: {},
            Round.FINAL_FOUR.value: {},
            Round.CHAMPIONSHIP.value: {}
        }

        # Create Round of 64 games
        round_64_date = datetime(2025, 3, 20, 12, 0)  # Start at noon on March 20
        for region in Region.choices:
            region_code = region[0]
            seeds = Seed.objects.filter(seed_list=seed_list, region=region_code).order_by('seed')
            
            # Create matchups (1v16, 8v9, 5v12, 4v13, 6v11, 3v14, 7v10, 2v15)
            matchups = [(1,16), (8,9), (5,12), (4,13), (6,11), (3,14), (7,10), (2,15)]
            
            for seed1, seed2 in matchups:
                # Get teams for this matchup
                team1 = seeds.get(seed=seed1).team
                team2 = seeds.get(seed=seed2).team
                
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
                    game_date=round_64_date
                )
                
                games_by_round[Round.ROUND_OF_64.value][game_number] = game
                game_number += 1
                round_64_date += timedelta(hours=2)  # Space games 2 hours apart
        
        # Create placeholder games for later rounds
        rounds = [
            (Round.ROUND_OF_32, datetime(2025, 3, 22, 12, 0)),
            (Round.SWEET_SIXTEEN, datetime(2025, 3, 27, 19, 0)),
            (Round.ELITE_EIGHT, datetime(2025, 3, 29, 18, 0)),
            (Round.FINAL_FOUR, datetime(2025, 4, 5, 18, 0)),
            (Round.CHAMPIONSHIP, datetime(2025, 4, 7, 21, 0))
        ]

        for round_enum, start_date in rounds:
            games_in_round = len(games_by_round[round_enum.value - 1]) // 2
            for i in range(games_in_round):
                game = Game.objects.create(
                    tournament=tournament,
                    region=Region.FIRST_FOUR if round_enum.value >= Round.FINAL_FOUR.value else Region.EAST,  # Placeholder region
                    round=round_enum.value,
                    game_number=game_number,
                    game_date=start_date + timedelta(hours=2 * i)
                )
                games_by_round[round_enum.value][game_number] = game
                game_number += 1

        # Link games together
        for round_value in range(Round.ROUND_OF_64.value, Round.CHAMPIONSHIP.value):
            current_round_games = sorted(games_by_round[round_value].items())
            next_round_games = sorted(games_by_round[round_value + 1].items())
            
            for i in range(0, len(current_round_games), 2):
                if i + 1 < len(current_round_games):
                    game1 = current_round_games[i][1]
                    game2 = current_round_games[i + 1][1]
                    next_game = next_round_games[i // 2][1]
                    
                    game1.next_game = next_game
                    game2.next_game = next_game
                    game1.save()
                    game2.save()

        self.stdout.write(self.style.SUCCESS('Successfully generated tournament games')) 