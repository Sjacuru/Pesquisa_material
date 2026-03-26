# FILE: config/settings.py
# MODULE: config — Application Settings
# EPIC: Architecture — Runtime Configuration
# RESPONSIBILITY: Define the application settings boundary and environment-loading contract for the scaffold.
# EXPORTS: Settings object boundary for the Django application.
# DEPENDS_ON: .env.example, platform/database.py, platform/storage.py, platform/observability.py.
# ACCEPTANCE_CRITERIA:
#   - Runtime configuration sources are explicitly identified.
#   - No secrets are hard-coded in the scaffold.
# HUMAN_REVIEW: Yes — security-sensitive runtime configuration.

from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "local-dev-only-change-me")
DEBUG = os.getenv("APP_DEBUG", "true").lower() == "true"
WEBSEARCH_ENABLED = os.getenv("WEBSEARCH_ENABLED", "true").lower() == "true"
SCHOOL_EXCLUSIVE_ENABLED = os.getenv("SCHOOL_EXCLUSIVE_ENABLED", "false").lower() == "true"

ALLOWED_HOSTS = [host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if host.strip()]

INSTALLED_APPS = [
	"django.contrib.contenttypes",
	"django.contrib.staticfiles",
	"persistence.apps.PersistenceConfig",
]

MIDDLEWARE = [
	"django.middleware.security.SecurityMiddleware",
	"django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
	{
		"BACKEND": "django.template.backends.django.DjangoTemplates",
		"DIRS": [BASE_DIR / "web" / "templates"],
		"APP_DIRS": True,
		"OPTIONS": {
			"context_processors": [
				"django.template.context_processors.request",
			],
		},
	}
]
WSGI_APPLICATION = None
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
	"default": {
		"ENGINE": "django.db.backends.sqlite3",
		"NAME": BASE_DIR / "var" / "dev.sqlite3",
	}
}

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
