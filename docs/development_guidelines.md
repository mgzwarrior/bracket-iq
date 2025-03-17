# Development Guidelines for bracket-iq 🏀

## Project Philosophy
bracket-iq isn't just another tournament bracket tool - it's your ultimate March Madness companion! We're building this with the same passion that makes us fill out multiple brackets, stay up late watching mid-major conference tournaments, and believe that this year might finally be the year a 16-seed makes a deep run.

## Test-Driven Development (TDD)

### The Full-Court Press Approach
Just like a good defensive strategy, our development process follows a strict TDD approach:

1. **Write the Test First** (Pre-game preparation)
   ```python
   def test_cinderella_detection(self):
       bracket = Bracket.objects.create(year=2024)
       # Test that our system can identify potential Cinderella teams
       self.assertTrue(bracket.has_cinderella_potential(team="Loyola Chicago"))
   ```

2. **Watch it Fail** (First Half)
   - Run the test and see it fail
   - Understand what's missing, just like watching game film

3. **Write the Code** (Second Half)
   - Implement the minimum code needed to make the test pass
   - Keep it clean, like a well-executed fast break

4. **Run the Tests** (Final Score)
   - All tests should pass
   - No technical fouls (linting errors)

### Test Categories

#### Model Tests
- Team stats and rankings
- Bracket validation
- Game outcomes
- Historical performance

#### View Tests
- Bracket creation flows
- Tournament visualization
- Real-time score updates
- Prediction interfaces

#### Integration Tests
- Full tournament simulations
- Multi-bracket comparisons
- Historical analysis

## Code Style

### The Bracket-IQ Way
- Clear, descriptive variable names (prefer `final_four_teams` over `ff_t`)
- Document your functions like you're breaking down a game plan
- Keep methods focused like a sharp-shooter - one responsibility per function

### Example Documentation
```python
def calculate_upset_probability(higher_seed, lower_seed):
    """
    Calculates the probability of an upset based on historical tournament data.
    
    Just like the 2018 UMBC vs Virginia game taught us - no team is safe! This
    algorithm considers factors like:
    - Historical seed matchup results
    - Current season performance
    - Tournament experience
    
    Args:
        higher_seed (Team): The favored team (lower seed number)
        lower_seed (Team): The underdog (higher seed number)
        
    Returns:
        float: Probability of an upset (0.0 to 1.0)
    """
```

## Feature Development Process

1. **Scout Report** (Planning)
   - Document the feature requirements
   - Write acceptance criteria
   - Plan test cases

2. **Practice** (Development)
   ```python
   # First, write your tests
   def test_new_feature():
       # Test setup
       # Assertions
   
   # Then implement the feature
   def new_feature():
       # Implementation
   ```

3. **Game Time** (Code Review)
   - Clean, tested code
   - Documentation updated
   - Tests passing

## Documentation

### Required Documentation for New Features
1. Technical design document
2. Test coverage report
3. User guide updates
4. API documentation (if applicable)

### Example Feature Documentation
```markdown
# Cinderella Detection Algorithm

## Overview
This feature helps identify potential Cinderella teams in the tournament
by analyzing historical upset patterns, current season statistics, and
team matchup data.

## Implementation
- Uses machine learning model trained on historical tournament data
- Considers factors like:
  - Conference strength
  - Road game performance
  - Experience in close games
  - Tournament history

## Testing
See `tests/test_cinderella_detection.py` for test cases and examples.
```

Remember: We're not just writing code - we're building the ultimate March Madness companion! Every feature should reflect our love for the game and the madness of the tournament. 🏀🎯 