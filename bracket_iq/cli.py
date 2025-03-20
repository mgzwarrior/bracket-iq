#!/usr/bin/env python3
"""Command-line interface for BracketIQ predictions."""
import argparse
import json
import logging
import csv
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from bracket_iq.models import Team, BracketStrategy, Round
from bracket_iq.analysis.historical import HistoricalAnalyzer

logger = logging.getLogger(__name__)

def setup_logging(verbose: bool = False):
    """Configure logging settings."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def predict_matchup(team1: str, team2: str, seed1: int, seed2: int, 
                   strategy: str = "HISTORICAL_ANALYSIS") -> Dict:
    """Predict the winner of a matchup using the specified strategy."""
    # Create team objects
    team1_obj = Team(name=team1, id=team1.upper())
    team2_obj = Team(name=team2, id=team2.upper())
    
    # Initialize analyzer based on strategy
    if strategy == "HISTORICAL_ANALYSIS":
        analyzer = HistoricalAnalyzer()
        winner, confidence = analyzer.predict_winner(team1_obj, team2_obj, seed1, seed2)
        
        # Get detailed analysis
        analysis = analyzer.get_matchup_analysis(team1_obj, team2_obj, seed1, seed2)
        
        return {
            "winner": winner.name,
            "confidence": confidence,
            "analysis": analysis
        }
    else:
        raise ValueError(f"Strategy {strategy} not implemented yet")

def batch_predict(input_file: str, output_file: str, strategy: str) -> List[Dict]:
    """Process multiple matchups from a CSV file."""
    results = []
    
    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                result = predict_matchup(
                    row['team1'],
                    row['team2'],
                    int(row['seed1']),
                    int(row['seed2']),
                    strategy
                )
                result['team1'] = row['team1']
                result['team2'] = row['team2']
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing matchup {row}: {e}")
                continue
    
    # Save results
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

def simulate_tournament(teams_file: str, strategy: str) -> Dict:
    """Simulate an entire tournament bracket."""
    # Load teams and seeds from CSV
    with open(teams_file, 'r') as f:
        reader = csv.DictReader(f)
        teams = list(reader)
    
    results = {
        "rounds": [],
        "champion": None,
        "upsets": []
    }
    
    # Process each round
    current_teams = teams
    for round_type in Round:
        if round_type == Round.FIRST_FOUR:
            continue
            
        round_results = []
        next_round_teams = []
        
        # Process each matchup in the round
        for i in range(0, len(current_teams), 2):
            team1 = current_teams[i]
            team2 = current_teams[i + 1]
            
            prediction = predict_matchup(
                team1['team'],
                team2['team'],
                int(team1['seed']),
                int(team2['seed']),
                strategy
            )
            
            # Track upsets
            if (int(team1['seed']) < int(team2['seed']) and prediction['winner'] == team2['team']) or \
               (int(team2['seed']) < int(team1['seed']) and prediction['winner'] == team1['team']):
                results['upsets'].append({
                    'round': round_type.label,
                    'winner': prediction['winner'],
                    'loser': team1['team'] if prediction['winner'] == team2['team'] else team2['team'],
                    'winner_seed': team2['seed'] if prediction['winner'] == team2['team'] else team1['seed'],
                    'loser_seed': team1['seed'] if prediction['winner'] == team2['team'] else team2['seed']
                })
            
            round_results.append({
                'matchup': f"{team1['team']} ({team1['seed']}) vs {team2['team']} ({team2['seed']})",
                'winner': prediction['winner'],
                'confidence': prediction['confidence']
            })
            
            # Add winner to next round
            next_round_teams.append({
                'team': prediction['winner'],
                'seed': team1['seed'] if prediction['winner'] == team1['team'] else team2['seed']
            })
        
        results['rounds'].append({
            'name': round_type.label,
            'games': round_results
        })
        
        current_teams = next_round_teams
        
        # If we've reached the championship game, store the champion
        if round_type == Round.CHAMPIONSHIP:
            results['champion'] = current_teams[0]['team']
    
    return results

def get_upset_probability(higher_seed: int, lower_seed: int) -> Dict:
    """Get upset probability for a seed matchup."""
    analyzer = HistoricalAnalyzer()
    prob = analyzer.get_upset_probability(higher_seed, lower_seed)
    
    return {
        "higher_seed": higher_seed,
        "lower_seed": lower_seed,
        "upset_probability": prob
    }

def get_team_stats(team_name: str) -> Dict:
    """Get comprehensive statistics for a team."""
    team = Team(name=team_name, id=team_name.upper())
    analyzer = HistoricalAnalyzer()
    stats = analyzer.get_team_tournament_stats(team)
    
    return {
        "team": team_name,
        "stats": stats
    }

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="BracketIQ - NCAA Tournament Prediction Tool"
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Predict matchup command
    predict_parser = subparsers.add_parser("predict", help="Predict winner of a matchup")
    predict_parser.add_argument("team1", help="First team name")
    predict_parser.add_argument("team2", help="Second team name")
    predict_parser.add_argument("seed1", type=int, help="First team's seed (1-16)")
    predict_parser.add_argument("seed2", type=int, help="Second team's seed (1-16)")
    predict_parser.add_argument(
        "--strategy", 
        choices=[s.value for s in BracketStrategy],
        default="HISTORICAL_ANALYSIS",
        help="Prediction strategy to use"
    )
    
    # Batch prediction command
    batch_parser = subparsers.add_parser("batch", help="Process multiple matchups from CSV")
    batch_parser.add_argument("input", help="Input CSV file with matchups")
    batch_parser.add_argument("output", help="Output JSON file for results")
    batch_parser.add_argument(
        "--strategy",
        choices=[s.value for s in BracketStrategy],
        default="HISTORICAL_ANALYSIS",
        help="Prediction strategy to use"
    )
    
    # Tournament simulation command
    simulate_parser = subparsers.add_parser("simulate", help="Simulate entire tournament")
    simulate_parser.add_argument("teams", help="CSV file with teams and seeds")
    simulate_parser.add_argument(
        "--strategy",
        choices=[s.value for s in BracketStrategy],
        default="HISTORICAL_ANALYSIS",
        help="Prediction strategy to use"
    )
    
    # Upset probability command
    upset_parser = subparsers.add_parser("upset", help="Get upset probability")
    upset_parser.add_argument("higher_seed", type=int, help="Better seed (lower number)")
    upset_parser.add_argument("lower_seed", type=int, help="Worse seed (higher number)")
    
    # Team stats command
    stats_parser = subparsers.add_parser("stats", help="Get team statistics")
    stats_parser.add_argument("team", help="Team name")
    
    # Global options
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file for results (JSON format)"
    )
    
    args = parser.parse_args()
    setup_logging(args.verbose)
    
    try:
        # Execute requested command
        if args.command == "predict":
            result = predict_matchup(
                args.team1, args.team2, args.seed1, args.seed2, args.strategy
            )
        elif args.command == "batch":
            result = batch_predict(args.input, args.output, args.strategy)
        elif args.command == "simulate":
            result = simulate_tournament(args.teams, args.strategy)
        elif args.command == "upset":
            result = get_upset_probability(args.higher_seed, args.lower_seed)
        elif args.command == "stats":
            result = get_team_stats(args.team)
        else:
            parser.print_help()
            return
        
        # Output results
        if args.output and args.command not in ["batch"]:  # batch handles its own output
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
        else:
            print(json.dumps(result, indent=2))
            
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            logger.exception("Detailed error:")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 