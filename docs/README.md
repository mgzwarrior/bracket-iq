# BracketIQ 🏀

Your intelligent March Madness bracket assistant! BracketIQ helps you create, manage, and analyze your tournament brackets with advanced analytics and machine learning.

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 15+
- Docker and Docker Compose (optional, for containerized development)

### Option 1: Docker Development (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/bracket-iq.git
   cd bracket-iq
   ```

2. Make scripts executable:
   ```bash
   chmod +x scripts/*
   ```

3. Run the setup script:
   ```bash
   ./scripts/setup
   ```

That's it! The setup script will:
- Create necessary directories
- Configure environment settings
- Build and start Docker containers
- Set up the database
- Run migrations
- Create a superuser (if needed)

Your development environment will be ready at http://localhost:8000

### Option 2: Local Development

1. Install PostgreSQL:
   ```bash
   # macOS
   brew install postgresql@15
   brew services start postgresql@15

   # Linux
   sudo apt-get install postgresql
   sudo service postgresql start
   ```

2. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/bracket-iq.git
   cd bracket-iq
   ```

3. Make scripts executable:
   ```bash
   chmod +x scripts/*
   ```

4. Run the local setup script:
   ```bash
   ./scripts/setup -l
   ```

The setup script will:
- Create necessary directories
- Configure environment settings for local development
- Create a virtual environment
- Install dependencies
- Set up the database
- Run migrations
- Create a superuser (if needed)

Start the development server:
```bash
./scripts/manage runserver
```

## Development Tools

The `scripts` directory contains helpful tools for development:

- `./scripts/setup`: Set up your development environment
  - Automatically creates a superuser with username `appuser` and password `testpass123`
- `./scripts/manage`: Run Django management commands
- `./scripts/test`: Run tests
- `./scripts/lint`: Run linting checks
- `./scripts/shell`: Open a Python shell
- `./scripts/dbshell`: Open a database shell
- `./scripts/start`: Start all services (Docker mode)
- `./scripts/stop`: Stop all services (Docker mode)
- `./scripts/cleanup`: Clean up build files, caches and Docker artifacts
- `./scripts/teardown`: Completely tear down the Docker environment and delete all related data

### Environment Management

To reset your development environment:

#### Cleanup (Recommended for regular use)

The cleanup script removes cache files and unnecessary Docker artifacts without completely resetting your database:

```bash
./scripts/cleanup
```

Use the `-y` flag to skip confirmation prompts:
```bash
./scripts/cleanup -y
```

#### Complete Teardown

For a complete reset that removes all containers, volumes, and data:

```bash
./scripts/teardown
```

Use the `-f` flag to force teardown or `-y` to skip confirmation prompts:
```bash
./scripts/teardown -f -y
```

After teardown, you'll need to run the setup script again to recreate your environment:
```bash
./scripts/setup
```

## Common Setup Issues

### Database Connection Issues

- Ensure PostgreSQL is installed and running
- Check database credentials in `.env`
- For Docker: ensure the database container is running (`docker compose ps`)
- For local: ensure PostgreSQL service is running

### Docker Issues

- Ensure Docker Desktop is running
- Try stopping and removing containers: `docker compose down`
- Rebuild containers: `docker compose build`

### Permission Issues

- Make sure scripts are executable: `chmod +x scripts/*`
- For database issues: ensure your PostgreSQL user has necessary permissions

### Static Files

Static files are automatically collected during setup. If you need to recollect:
```bash
# Docker
./scripts/manage collectstatic

# Local
python manage.py collectstatic
```

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and development process.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Overview

BracketIQ is a Django-based web application that helps basketball fans create and manage their March Madness brackets with intelligent analytics. The application uses machine learning to provide insights and predictions, helping users make informed decisions about their bracket picks.

## Features

- 🏀 Create and manage tournament brackets
- 📊 Generate seed lists with intelligent team rankings
- 📈 Track bracket performance in real-time
- 🤖 Advanced analytics and ML-powered predictions
- 🔄 Real-time tournament updates

## Tournament Seeding

### Command Line Seeding

To seed the tournament data for a specific year, use the following commands:

1. First, ensure your database is clean of any existing tournament data:
   ```bash
   # Using Docker
   ./scripts/manage shell -c "from bracket_iq.models import Tournament, Team; Tournament.objects.all().delete(); Team.objects.all().delete()"
   
   # Local development
   python manage.py shell -c "from bracket_iq.models import Tournament, Team; Tournament.objects.all().delete(); Team.objects.all().delete()"
   ```

2. Seed the teams database:
   ```bash
   # Using Docker
   ./scripts/manage seed_teams
   
   # Local development
   python manage.py seed_teams
   ```

3. Seed the tournament data:
   ```bash
   # Using Docker
   ./scripts/manage seed_tournament_2025
   
   # Local development
   python manage.py seed_tournament_2025
   ```

The seeding process will:
- Create the tournament entry for the specified year
- Set up all regions (South, East, West, Midwest)
- Create seed lists with team rankings
- Generate First Four matchups
- Set up the initial tournament bracket structure

### Web Interface

You can also seed tournaments through the admin interface at `/admin/bracket_iq/tournament/seed/`.
This provides a simple form to:
1. Select the tournament year
2. Review and confirm team seedings
3. Generate the tournament structure

Note: Web seeding requires admin privileges.

## Tech Stack

- **Backend**: Python 3.8+, Django 4.2
- **Database**: PostgreSQL (production), SQLite (development)
- **Infrastructure**: Docker, Docker Compose
- **Frontend**: Modern responsive UI with Django templates
- **Development**: Pre-commit hooks, IPython shell

## Project Structure

```
bracket-iq/
├── bracket_iq/           # Main Django application
│   ├── management/       # Custom Django commands
│   ├── migrations/       # Database migrations
│   ├── static/          # Static assets (CSS, JS, images)
│   ├── templates/       # HTML templates
│   ├── tests/           # Test suite
│   ├── models.py        # Database models
│   ├── views.py         # View controllers
│   ├── urls.py          # URL routing
│   └── forms.py         # Form definitions
├── scripts/             # Development and utility scripts
│   ├── utils/           # Script utilities
│   ├── tools           # Shared script functions
│   ├── setup           # Project setup script
│   ├── start           # Start services
│   ├── stop            # Stop services
│   ├── install         # Dependency management
│   ├── migrate         # Database migrations
│   ├── console         # Django shell
│   └── manage          # Django management
├── docs/               # Documentation
├── .github/            # GitHub workflows and templates
├── docker/             # Docker configuration
│   ├── Dockerfile      # Main service definition
│   └── compose.yml     # Service orchestration
├── .env-dist           # Environment template
├── .gitignore         # Git ignore rules
├── .pre-commit-config.yaml  # Pre-commit hooks
├── manage.py          # Django CLI
├── requirements.txt   # Python dependencies
└── LICENSE           # MIT License
```

## Development Workflow

For detailed information about our development workflow, including:
- Setting up pre-commit hooks
- Running tests and code quality checks
- Continuous integration

Please refer to the [Development Workflow](./development_workflow.md) documentation.