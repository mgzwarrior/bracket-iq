# Historical Tournament Analysis

The historical analysis module provides sophisticated prediction capabilities for March Madness tournament games using historical data from the [Kaggle March Machine Learning Mania](https://www.kaggle.com/competitions/march-machine-learning-mania-2025) dataset.

## Features

- Tournament history analysis
- Head-to-head matchup analysis
- Seed matchup statistics
- Upset probability calculations
- Detailed team statistics

## Quick Start

```python
from bracket_iq.analysis.historical import HistoricalAnalyzer

# Initialize the analyzer
analyzer = HistoricalAnalyzer()

# Predict a matchup
winner, confidence = analyzer.predict_winner(team1, team2, seed1, seed2)
print(f"Predicted winner: {winner.name} with {confidence:.1f}% confidence")

# Get upset probability
upset_chance = analyzer.get_upset_probability(1, 16)
print(f"Chance of 16 seed upsetting 1 seed: {upset_chance:.1%}")

# Get team's tournament history
stats = analyzer.get_team_tournament_stats(team)
print(f"Tournament win percentage: {stats['win_percentage']:.1%}")
```

## Prediction Model

The prediction model uses a weighted combination of several factors:

1. **Tournament Success (25%)**
   - Historical tournament win percentage
   - Points scored and allowed
   - Tournament performance trends

2. **Seed Advantage (30%)**
   - Current seed strength
   - Historical seed performance
   - Normalized seed factor

3. **Head-to-Head History (15%)**
   - Direct matchup results
   - Regular season and tournament games
   - Recent games weighted more heavily

4. **Seed Matchup History (20%)**
   - Historical performance of seed matchups
   - Upset rates and resistance
   - Point differentials

5. **Experience Bonus (10%)**
   - Number of tournament appearances
   - Recent tournament success
   - Maximum 10% bonus

## Data Sources

The analysis uses historical NCAA tournament data from 1985-present, including:
- Tournament game results
- Regular season results
- Team information
- Tournament seeds
- Detailed game statistics

## API Reference

### HistoricalAnalyzer

#### `predict_winner(team1: Team, team2: Team, seed1: int, seed2: int) -> Tuple[Team, float]`
Predicts the winner of a matchup and returns confidence percentage.

**Parameters:**
- `team1`: First team in the matchup
- `team2`: Second team in the matchup
- `seed1`: Tournament seed of first team
- `seed2`: Tournament seed of second team

**Returns:**
- Tuple of (predicted_winner, confidence_percentage)

#### `get_upset_probability(higher_seed: int, lower_seed: int) -> float`
Calculates the probability of an upset for a given seed matchup.

**Parameters:**
- `higher_seed`: The numerically lower seed (better team)
- `lower_seed`: The numerically higher seed (underdog)

**Returns:**
- Probability of upset as float between 0 and 1

#### `get_team_tournament_stats(team: Team) -> Dict`
Returns detailed tournament statistics for a team.

**Parameters:**
- `team`: Team to analyze

**Returns:**
Dictionary containing:
- `games_played`: Total tournament games
- `wins`: Tournament wins
- `losses`: Tournament losses
- `win_percentage`: Tournament win percentage
- `points_scored`: Total points scored
- `points_allowed`: Total points allowed
- `avg_scoring_margin`: Average scoring margin
- `appearances`: Number of tournament appearances
- `average_seed`: Average tournament seed

## Example Usage

### Basic Prediction
```python
analyzer = HistoricalAnalyzer()

# Predict 1 vs 16 seed matchup
winner, confidence = analyzer.predict_winner(one_seed, sixteen_seed, 1, 16)
```

### Upset Analysis
```python
# Analyze potential upsets
for seed in range(1, 5):
    upset_prob = analyzer.get_upset_probability(seed, seed + 4)
    print(f"{seed+4} seed upset probability vs {seed} seed: {upset_prob:.1%}")
```

### Tournament History
```python
# Get team's tournament history
stats = analyzer.get_team_tournament_stats(team)
print(f"Tournament appearances: {stats['appearances']}")
print(f"Win percentage: {stats['win_percentage']:.1%}")
print(f"Average seed: {stats['average_seed']:.1f}")
```

## Installation

Ensure you have the required data files in your project:
1. Download the Kaggle March Madness dataset
2. Place the files in a directory named `march-machine-learning-mania-2025`
3. Install required packages:
```bash
pip install pandas numpy
``` 