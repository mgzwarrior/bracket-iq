# bracket_iq/apps.py
from django.apps import AppConfig, apps
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
def seed_initial_data(**kwargs):  # pylint: disable=unused-argument
    """Seed initial data after migrations are applied.

    Args:
        **kwargs: Required by Django's signal system but not used
    """
    try:
        # Get the Team model from our app
        Team = apps.get_model("bracket_iq", "Team")
        if not Team.objects.exists():
            call_command("seed_teams")
    except (OperationalError, ProgrammingError):
        # Database isn't ready or table doesn't exist yet
        pass
