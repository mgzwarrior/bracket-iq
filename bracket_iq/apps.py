# bracket_iq/apps.py
from django.apps import AppConfig
from django.core.management import call_command
from django.db.utils import OperationalError, ProgrammingError
from django.db import connection


class BracketIQConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bracket_iq"

    def ready(self):
        # Import this at runtime to avoid circular imports
        from django.conf import settings
        
        # Skip database checks during testing, migrations, and other non-runtime scenarios
        # to avoid the RuntimeWarning
        if settings.configured and (
            'test' in settings.SETTINGS_MODULE or 
            'migrat' in ' '.join(settings.INSTALLED_APPS) or
            any(cmd in ' '.join(settings.INSTALLED_APPS) for cmd in ['makemigrations', 'migrate', 'collectstatic'])
        ):
            return
        
        # Use a deferred loading approach instead of checking immediately
        from django.db.models.signals import post_migrate
        from django.dispatch import receiver
        
        @receiver(post_migrate, sender=self)
        def seed_initial_data(sender, **kwargs):
            try:
                # Only check for teams after migrations have been applied
                Team = sender.get_model("Team")
                if not Team.objects.exists():
                    call_command("seed_teams")
            except (OperationalError, ProgrammingError):
                # Database isn't ready or table doesn't exist yet
                pass
