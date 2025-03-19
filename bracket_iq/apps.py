# bracket_iq/apps.py
from django.apps import AppConfig
from django.conf import settings
from django.core.management import call_command
from django.db.models.signals import post_migrate
from django.db.utils import OperationalError, ProgrammingError
from django.dispatch import receiver


class BracketIQConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bracket_iq"

    def ready(self):
        # Skip database checks during testing, migrations, and other non-runtime scenarios
        # to avoid the RuntimeWarning
        if settings.configured and (
            "test" in settings.SETTINGS_MODULE
            or "migrat" in " ".join(settings.INSTALLED_APPS)
            or any(
                cmd in " ".join(settings.INSTALLED_APPS)
                for cmd in ["makemigrations", "migrate", "collectstatic"]
            )
        ):
            return

        # Register signal handler for post_migrate
        post_migrate.connect(seed_initial_data, sender=self)


@receiver(post_migrate)
def seed_initial_data(sender, **kwargs):
    """Seed initial data after migrations are applied."""
    try:
        # Only check for teams after migrations have been applied
        # Import the model from sender to avoid circular imports
        Team = sender.get_model("Team") if hasattr(sender, "get_model") else None
        if Team and not Team.objects.exists():
            call_command("seed_teams")
    except (OperationalError, ProgrammingError):
        # Database isn't ready or table doesn't exist yet
        pass
