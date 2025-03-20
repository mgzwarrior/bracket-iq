# BracketIQ Command Line Interface

BracketIQ provides a powerful command-line interface for making NCAA tournament predictions using historical data analysis. This document explains how to use the CLI tool effectively.

## Installation

Before using the CLI, ensure you have installed BracketIQ and its dependencies:

```bash
pip install -r requirements.txt
```

## Basic Usage

The CLI provides five main commands:
- `predict`: Predict the winner of a matchup between two teams
- `batch`: Process multiple matchups from a CSV file
- `simulate`: Simulate an entire tournament bracket
- `upset`: Calculate the probability of an upset between two seeds
- `stats`: Get comprehensive tournament statistics for a team

### Global Options

These options are available for all commands:

- `-v, --verbose`: Enable verbose logging for debugging
- `-o, --output FILE`: Save results to a JSON file instead of printing to console

## Command Reference

### Predict Matchup

Predict the winner of a game between two teams:

```bash
python -m bracket_iq.cli predict TEAM1 TEAM2 SEED1 SEED2 [--strategy STRATEGY]
```

Arguments:
- `TEAM1`: Name of the first team
- `TEAM2`: Name of the second team
- `SEED1`: Seed of the first team (1-16)
- `SEED2`: Seed of the second team (1-16)
- `--strategy`: Prediction strategy to use (default: HISTORICAL_ANALYSIS)

Example:
```bash
python -m bracket_iq.cli predict "Duke" "North Carolina" 2 7
```

Output:
```json
{
  "winner": "Duke",
  "confidence": 0.75,
  "analysis": {
    "historical_matchups": 5,
    "tournament_experience": {
      "Duke": 45,
      "North Carolina": 42
    },
    "seed_advantage": 0.65,
    "recent_performance": {
      "Duke": 0.8,
      "North Carolina": 0.6
    }
  }
}
```

### Batch Prediction

Process multiple matchups from a CSV file:

```bash
python -m bracket_iq.cli batch INPUT.csv OUTPUT.json [--strategy STRATEGY]
```

Arguments:
- `INPUT.csv`: CSV file containing matchups to predict
- `OUTPUT.json`: JSON file to store results
- `--strategy`: Prediction strategy to use (default: HISTORICAL_ANALYSIS)

The input CSV should have the following format:
```csv
team1,team2,seed1,seed2
Duke,North Carolina,2,7
Kentucky,Kansas,1,4
Gonzaga,Baylor,3,3
```

Example:
```bash
python -m bracket_iq.cli batch matchups.csv predictions.json
```

Output will be saved to the specified JSON file with predictions for each matchup.

### Tournament Simulation

Simulate an entire tournament bracket:

```bash
python -m bracket_iq.cli simulate TEAMS.csv [--strategy STRATEGY]
```

Arguments:
- `TEAMS.csv`: CSV file containing teams and their seeds
- `--strategy`: Prediction strategy to use (default: HISTORICAL_ANALYSIS)

The input CSV should have the following format:
```csv
team,seed,region
Gonzaga,1,West
Baylor,1,South
Michigan,1,East
Illinois,1,Midwest
...
```

Example:
```bash
python -m bracket_iq.cli simulate tournament_teams.csv -o bracket.json
```

The output includes:
- Predictions for each round
- The tournament champion
- List of predicted upsets
- Confidence scores for each matchup

Example output:
```json
{
  "rounds": [
    {
      "name": "Round of 64",
      "games": [
        {
          "matchup": "Gonzaga (1) vs Norfolk State (16)",
          "winner": "Gonzaga",
          "confidence": 0.99
        },
        // ... more games
      ]
    },
    // ... more rounds
  ],
  "champion": "Gonzaga",
  "upsets": [
    {
      "round": "Round of 32",
      "winner": "Oregon",
      "loser": "Iowa",
      "winner_seed": 7,
      "loser_seed": 2
    }
    // ... more upsets
  ]
}
```

### Upset Probability

Calculate the probability of a lower seed beating a higher seed:

```bash
python -m bracket_iq.cli upset HIGHER_SEED LOWER_SEED
```

Arguments:
- `HIGHER_SEED`: Better seed (lower number, 1-16)
- `LOWER_SEED`: Worse seed (higher number, 1-16)

Example:
```bash
python -m bracket_iq.cli upset 2 15
```

Output:
```json
{
  "higher_seed": 2,
  "lower_seed": 15,
  "upset_probability": 0.037
}
```

### Team Statistics

Get comprehensive tournament statistics for a team:

```bash
python -m bracket_iq.cli stats TEAM
```

Arguments:
- `TEAM`: Name of the team

Example:
```bash
python -m bracket_iq.cli stats "Kentucky"
```

Output:
```json
{
  "team": "Kentucky",
  "stats": {
    "tournament_appearances": 59,
    "championships": 8,
    "final_four_appearances": 17,
    "win_percentage": 0.761,
    "average_seed": 3.4,
    "upset_rate": 0.15
  }
}
```

## File Formats

### Batch Prediction CSV
Required columns:
- `team1`: Name of first team
- `team2`: Name of second team
- `seed1`: Seed of first team (1-16)
- `seed2`: Seed of second team (1-16)

### Tournament Teams CSV
Required columns:
- `team`: Team name
- `seed`: Team's seed (1-16)
- `region`: Tournament region (optional)

## Error Handling

The CLI will provide informative error messages when:
- Team names are not found in the database
- Invalid seed numbers are provided (must be 1-16)
- Data cannot be loaded or processed
- Invalid command syntax is used
- CSV files have incorrect format or missing columns

Use the `-v` flag to get more detailed error information when problems occur.

## Examples

1. Predict a first-round matchup with detailed output:
```bash
python -m bracket_iq.cli predict "Gonzaga" "Grand Canyon" 3 14 -v
```

2. Process multiple matchups from a file:
```bash
python -m bracket_iq.cli batch matchups.csv predictions.json --strategy HISTORICAL_ANALYSIS
```

3. Simulate an entire tournament:
```bash
python -m bracket_iq.cli simulate tournament_teams.csv -o full_bracket.json
```

4. Check upset probability for a classic 5-12 matchup:
```bash
python -m bracket_iq.cli upset 5 12
```

5. Get comprehensive stats for a team and save to file:
```bash
python -m bracket_iq.cli stats "Kansas" -o kansas_stats.json
```

6. Compare multiple matchups by saving predictions:
```bash
python -m bracket_iq.cli predict "Purdue" "Fairleigh Dickinson" 1 16 -o game1.json
python -m bracket_iq.cli predict "Arizona" "Princeton" 2 15 -o game2.json
``` 