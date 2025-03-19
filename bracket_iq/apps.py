# bracket_iq/apps.py
from django.apps import AppConfig
from django.core.management import call_command
from django.db.utils import OperationalError, ProgrammingError
from django.db import connection


class BracketIQConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bracket_iq"

    def ready(self):
        try:
            # Check if the teams table exists first
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'bracket_iq_team'
                    );
                """
                )
                table_exists = cursor.fetchone()[0]

            if table_exists:
                # Only check for teams if the table exists
                from .models import Team

                if not Team.objects.exists():
                    call_command("seed_teams")

        except (OperationalError, ProgrammingError):
            # Database isn't ready or table doesn't exist yet
            pass
