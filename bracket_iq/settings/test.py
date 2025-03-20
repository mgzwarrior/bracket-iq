"""
Test settings for bracket_iq project.
"""

import os
import sys
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Add the parent directory to sys.path
sys.path.insert(0, str(BASE_DIR))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-test-key-8675309-test-key"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ["*"]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "bracket_iq",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "bracket_iq.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "bracket_iq/templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "bracket_iq.wsgi.application"

# Determine the database host based on environment
# Default to 'localhost' for local development
# Use 'db' when running in Docker
# Can be overridden by TEST_DB_HOST environment variable
DB_HOST = os.environ.get("TEST_DB_HOST")
if DB_HOST is None:
    if os.environ.get("DOCKER_CONTAINER") == "true":
        DB_HOST = "db"
    elif os.environ.get("GITHUB_ACTIONS") == "true":
        DB_HOST = "localhost"
    else:
        DB_HOST = "localhost"

# Database configuration
DATABASES = {
    "default": {
        "ENGINE": os.environ.get("TEST_DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.environ.get("TEST_DB_NAME", "bracket_iq"),
        "USER": os.environ.get("TEST_DB_USER", "postgres"),
        "PASSWORD": os.environ.get("TEST_DB_PASSWORD", "postgres"),
        "HOST": DB_HOST,
        "PORT": os.environ.get("TEST_DB_PORT", "5432"),
    }
}

# For SQLite, use in-memory database if specified
if os.environ.get("TEST_DB_ENGINE") == "django.db.backends.sqlite3":
    if os.environ.get("TEST_DB_NAME") == ":memory:":
        DATABASES["default"]["NAME"] = ":memory:"
    elif not os.environ.get("TEST_DB_NAME"):
        DATABASES["default"]["NAME"] = ":memory:"
    # No need for other database settings with SQLite
    DATABASES["default"]["USER"] = ""
    DATABASES["default"]["PASSWORD"] = ""
    DATABASES["default"]["HOST"] = ""
    DATABASES["default"]["PORT"] = ""

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Disable password hashing to speed up tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Media settings
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
