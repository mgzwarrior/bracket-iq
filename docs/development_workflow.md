# Development Workflow

This document outlines the development workflow for the BracketIQ project, including how to set up pre-commit hooks, run tests, and ensure code quality.

## Pre-commit Hooks

Pre-commit hooks help ensure that your code meets quality standards before it's committed to the repository. Our pre-commit hooks run various checks using the `scripts/check` script, which includes:

- Code formatting with Black
- Basic linting with Flake8
- Advanced linting with Pylint
- Type checking with Mypy

### Installing Pre-commit Hooks

To install the pre-commit hooks, run:

```bash
./scripts/install-hooks
```

This will:
1. Install the pre-commit hook in your local `.git/hooks` directory
2. Install all necessary development dependencies from `requirements-dev.txt`

Once installed, the hooks will run automatically before each commit. If any check fails, the commit will be prevented until the issues are fixed.

## Running Checks Manually

### All Checks

To run all code quality checks manually:

```bash
./scripts/check
```

This script will:
1. Run code formatting with Black
2. Run basic linting with Flake8
3. Run advanced linting with Pylint (with auto-installation if needed)
4. Run type checking with Mypy (with auto-installation if needed)

If any tools are missing, the script will attempt to install them automatically.

## Running Tests

The project includes a dedicated test script with various options for running tests.

### Basic Test Run

To run all tests:

```bash
./scripts/test
```

### Test Options

The test script supports several options:

- `-v`, `--verbose`: Run tests with more verbose output
- `-k`, `--keep-db`: Keep the test database between runs
- `-f`, `--failfast`: Stop tests after the first failure
- `-p`, `--parallel`: Run tests in parallel
- `-c`, `--coverage`: Run tests with coverage analysis
- `-r`, `--report`: Generate a coverage report (run after using `-c`)

Examples:

```bash
# Run tests with verbose output
./scripts/test -v

# Run tests with coverage analysis
./scripts/test -c

# Generate coverage report after running tests with coverage
./scripts/test -r

# Run specific tests
./scripts/test path/to/test
```

## Continuous Integration

All of these checks and tests run in our GitHub Actions CI pipeline for every pull request and push to the main branch. The workflow is configured in `.github/workflows/python-ci.yml` and includes:

1. Setting up Python 3.10 (required for Django 5+)
2. Installing dependencies including development tools
3. Running Django system checks
4. Running all code quality checks via `./scripts/check`
5. Running tests with coverage via `./scripts/test --coverage`
6. Generating and uploading a coverage report

## Code Quality Tools

### Black

[Black](https://black.readthedocs.io/) is used for code formatting. It enforces a consistent style across the codebase.

This is included in the `scripts/check` script, but you can also run it directly:

```bash
black bracket_iq
```

### Flake8

[Flake8](https://flake8.pycqa.org/) is used for style guide enforcement. It checks for various style issues and potential errors.

This is included in the `scripts/check` script, but you can also run it directly:

```bash
flake8 bracket_iq --count --select=E9,F63,F7,F82 --show-source --statistics
```

### Pylint

[Pylint](https://pylint.pycqa.org/) is a more comprehensive linter that checks for errors, enforces coding standards, and looks for code smells.

This is included in the `scripts/check` script, but you can also run it directly:

```bash
pylint --rcfile=setup.cfg bracket_iq
```

### Mypy

[Mypy](https://mypy.readthedocs.io/) is used for static type checking. It helps catch type-related errors before runtime.

This is included in the `scripts/check` script, but you can also run it directly:

```bash
mypy bracket_iq
```

## Development Dependencies

All development dependencies are listed in the `requirements-dev.txt` file, which includes:

- Black for code formatting
- Flake8 for basic linting
- Pylint for advanced linting
- Mypy for type checking
- Django-stubs for Django type definitions
- Coverage for test coverage analysis
- Pre-commit for managing Git hooks

To install all development dependencies:

```bash
pip install -r requirements-dev.txt
``` 