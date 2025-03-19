# Development Workflow

This document outlines the development workflow for the BracketIQ project, including how to set up pre-commit hooks, run tests, and ensure code quality.

## Pre-commit Hooks

Pre-commit hooks help ensure that your code meets quality standards before it's committed to the repository. Our pre-commit hooks run various checks, including:

- Django system checks
- Code style checks (Black, Flake8)
- Linting with Pylint
- Type checking with Mypy
- Django tests

### Installing Pre-commit Hooks

To install the pre-commit hooks, run:

```bash
./scripts/install-hooks
```

This will:
1. Install the pre-commit hook in your local `.git/hooks` directory
2. Install all necessary development dependencies

Once installed, the hooks will run automatically before each commit. If any check fails, the commit will be prevented until the issues are fixed.

## Running Checks Manually

### All Checks

To run all checks manually:

```bash
./scripts/check
```

### Specific Checks

You can run specific checks by using the `-t` option:

```bash
./scripts/check -t django,pep,lint
```

Available checks:
- `django`: Django system checks
- `pep`: Code style checks (Black, Flake8)
- `lint`: Linting with Pylint
- `type`: Type checking with Mypy
- `test`: Django tests

### Fail Fast

To stop checking after the first failure:

```bash
./scripts/check -f
```

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

All of these checks also run in our GitHub Actions CI pipeline for every pull request and push to the main branch. The workflow configuration can be found in `.github/workflows/python-ci.yml`.

## Code Quality Tools

### Black

[Black](https://black.readthedocs.io/) is used for code formatting. It enforces a consistent style across the codebase.

To format code with Black:

```bash
black .
```

### Flake8

[Flake8](https://flake8.pycqa.org/) is used for style guide enforcement. It checks for various style issues and potential errors.

To run Flake8:

```bash
flake8 .
```

### Pylint

[Pylint](https://pylint.pycqa.org/) is a more comprehensive linter that checks for errors, enforces coding standards, and looks for code smells.

To run Pylint:

```bash
pylint --rcfile=setup.cfg bracket_iq
```

### Mypy

[Mypy](https://mypy.readthedocs.io/) is used for static type checking. It helps catch type-related errors before runtime.

To run Mypy:

```bash
mypy .
```

## Development Dependencies

All development dependencies are listed in the `requirements-dev.txt` file. To install them:

```bash
pip install -r requirements-dev.txt
``` 