#!/usr/bin/env python3
"""Command-line interface for BracketIQ predictions."""
import argparse
import json
import logging
import csv
import sys
from typing import Dict, List, Any, Union
import pandas as pd  # type: ignore

from bracket_iq.models import Team, BracketStrategy
from bracket_iq.analysis.historical import HistoricalAnalyzer

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Configure logging settings."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def predict_matchup(
    team1: str,
    team2: str,
    seed1: int,
    seed2: int,
    strategy: str = "HISTORICAL_ANALYSIS",
) -> Dict[str, Any]:
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

        return {"winner": winner.name, "confidence": confidence, "analysis": analysis}

    raise ValueError(f"Strategy {strategy} not implemented yet")


def batch_predict(
    input_file: str, output_file: str, strategy: str
) -> List[Dict[str, Any]]:
    """Process multiple matchups from a CSV file."""
    results: List[Dict[str, Any]] = []

    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                result = predict_matchup(
                    row["team1"],
                    row["team2"],
                    int(row["seed1"]),
                    int(row["seed2"]),
                    strategy,
                )
                result["team1"] = row["team1"]
                result["team2"] = row["team2"]
                results.append(result)
            except Exception as e:
                logger.error("Error processing matchup %s: %s", row, str(e))
                continue

    # Save results
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results


def simulate_tournament(
    teams_file: str, strategy: str = "HISTORICAL_ANALYSIS"
) -> Dict[str, Any]:
    """Simulate a tournament given a list of teams and seeds.

    Args:
        teams_file: Path to CSV file containing teams and seeds
        strategy: Strategy to use for predictions (default: HISTORICAL_ANALYSIS)

    Returns:
        Dictionary containing tournament results
    """
    # Load teams from CSV
    teams_df = pd.read_csv(teams_file)
    teams = list(zip(teams_df["team"].tolist(), teams_df["seed"].astype(int).tolist()))

    # Initialize tournament state
    rounds = []
    upsets = []
    current_teams = teams.copy()

    # Simulate rounds until we have a champion
    while len(current_teams) > 1:
        next_round_teams = []
        round_results = []

        # Process matchups in current round
        for i in range(0, len(current_teams), 2):
            # Handle case where we have an odd number of teams
            if i + 1 >= len(current_teams):
                # Last team automatically advances
                next_round_teams.append(current_teams[i])
                round_results.append(
                    {
                        "team1": current_teams[i][0],
                        "seed1": current_teams[i][1],
                        "team2": "BYE",
                        "seed2": 16,
                        "winner": current_teams[i][0],
                        "confidence": 100.0,
                    }
                )
                continue

            team1, seed1 = current_teams[i]
            team2, seed2 = current_teams[i + 1]

            # Predict winner
            prediction = predict_matchup(team1, team2, seed1, seed2, strategy)
            winner = prediction["winner"]
            confidence = prediction["confidence"]

            # Check for upset
            if (winner == team1 and seed1 > seed2) or (
                winner == team2 and seed2 > seed1
            ):
                upsets.append(
                    {
                        "winner": winner,
                        "winner_seed": seed1 if winner == team1 else seed2,
                        "loser": team2 if winner == team1 else team1,
                        "loser_seed": seed2 if winner == team1 else seed1,
                    }
                )

            # Record round result
            round_results.append(
                {
                    "team1": team1,
                    "seed1": seed1,
                    "team2": team2,
                    "seed2": seed2,
                    "winner": winner,
                    "confidence": confidence,
                }
            )

            # Add winner to next round
            next_round_teams.append((winner, seed1 if winner == team1 else seed2))

        # Store round results and update current teams
        rounds.append(round_results)
        current_teams = next_round_teams

    # Return tournament results
    return {
        "rounds": rounds,
        "champion": current_teams[0][0] if current_teams else None,
        "upsets": upsets,
    }


def get_upset_probability(higher_seed: int, lower_seed: int) -> Dict[str, float]:
    """Get upset probability for a seed matchup."""
    # Validate seeds
    if not (1 <= higher_seed <= 16 and 1 <= lower_seed <= 16):
        raise ValueError("Seeds must be between 1 and 16")
    if higher_seed >= lower_seed:
        raise ValueError("Higher seed must be a lower number than lower seed")

    analyzer = HistoricalAnalyzer()
    prob = analyzer.get_upset_probability(higher_seed, lower_seed)

    return {
        "higher_seed": float(higher_seed),
        "lower_seed": float(lower_seed),
        "upset_probability": prob,
    }


def get_team_stats(team_name: str) -> Dict[str, Any]:
    """Get comprehensive statistics for a team."""
    team = Team(name=team_name, id=team_name.upper())
    analyzer = HistoricalAnalyzer()
    stats = analyzer.get_team_tournament_stats(team)

    return {"team": team_name, "stats": stats}


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="BracketIQ Prediction CLI")

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Predict matchup command
    predict_parser = subparsers.add_parser(
        "predict", help="Predict winner of a matchup"
    )
    predict_parser.add_argument("team1", help="First team name")
    predict_parser.add_argument("team2", help="Second team name")
    predict_parser.add_argument("seed1", type=int, help="First team's seed (1-16)")
    predict_parser.add_argument("seed2", type=int, help="Second team's seed (1-16)")
    predict_parser.add_argument(
        "--strategy",
        choices=[s.value for s in BracketStrategy],
        default="HISTORICAL_ANALYSIS",
        help="Prediction strategy to use",
    )

    # Batch prediction command
    batch_parser = subparsers.add_parser(
        "batch", help="Process multiple matchups from CSV"
    )
    batch_parser.add_argument("input", help="Input CSV file with matchups")
    batch_parser.add_argument("output", help="Output JSON file for results")
    batch_parser.add_argument(
        "--strategy",
        choices=[s.value for s in BracketStrategy],
        default="HISTORICAL_ANALYSIS",
        help="Prediction strategy to use",
    )

    # Tournament simulation command
    simulate_parser = subparsers.add_parser(
        "simulate", help="Simulate entire tournament"
    )
    simulate_parser.add_argument("teams", help="CSV file with teams and seeds")
    simulate_parser.add_argument(
        "--strategy",
        choices=[s.value for s in BracketStrategy],
        default="HISTORICAL_ANALYSIS",
        help="Strategy to use for predictions",
    )

    # Upset probability command
    upset_parser = subparsers.add_parser("upset", help="Get upset probability")
    upset_parser.add_argument(
        "higher_seed", type=int, help="Better seed (lower number)"
    )
    upset_parser.add_argument("lower_seed", type=int, help="Worse seed (higher number)")

    # Team stats command
    stats_parser = subparsers.add_parser("stats", help="Get team statistics")
    stats_parser.add_argument("team", help="Team name")

    # Global options
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument("-o", "--output", help="Output file for results (JSON format)")

    args = parser.parse_args()
    setup_logging(args.verbose)

    try:
        # Execute requested command
        result: Union[Dict[str, Any], List[Dict[str, Any]]]
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
        elif args.command == "exit":
            sys.exit(0)
        else:
            parser.print_help()
            return 1

        # Output results
        if args.output and args.command not in [
            "batch"
        ]:  # batch handles its own output
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
        else:
            print(json.dumps(result, indent=2))

    except Exception as e:
        logger.error("Error: %s", str(e))
        if args.verbose:
            logger.exception("Detailed error:")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
