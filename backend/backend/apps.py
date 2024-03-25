# backend/backend/apps.py
from django.apps import AppConfig
from django.core.management import call_command
from django.db.utils import OperationalError

class BackendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend'

    def ready(self):
        try:
            # Check if the 'teams' table exists
            from .models import Team
            if not Team.objects.exists():
                # If the 'teams' table does not exist or is empty, run the 'seed_teams' command
                call_command('seed_teams')
        except OperationalError:
            # The 'teams' table does not exist yet, do nothing
            pass