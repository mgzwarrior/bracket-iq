import os
import django

# Initialize Django before any test modules are imported
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bracket_iq.settings.test")
django.setup()
