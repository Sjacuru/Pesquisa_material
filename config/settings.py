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

from django.db.backends.signals import connection_created
from django.dispatch import receiver


BASE_DIR = Path(__file__).resolve().parent.parent


def _sqlite_name_from_env() -> Path:
	url = str(os.getenv("DATABASE_URL", "")).strip()
	if url.startswith("sqlite:///"):
		raw = url.removeprefix("sqlite:///")
		path = Path(raw)
		if not path.is_absolute():
			path = BASE_DIR / raw
		return path
	return BASE_DIR / "var" / "dev.sqlite3"

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "local-dev-only-change-me")
DEBUG = os.getenv("APP_DEBUG", "true").lower() == "true"
WEBSEARCH_ENABLED = os.getenv("WEBSEARCH_ENABLED", "true").lower() == "true"
SCHOOL_EXCLUSIVE_ENABLED = os.getenv("SCHOOL_EXCLUSIVE_ENABLED", "false").lower() == "true"
ASYNC_SEARCH_ENABLED = os.getenv("ASYNC_SEARCH_ENABLED", "true").lower() == "true"

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
		"NAME": _sqlite_name_from_env(),
		"CONN_MAX_AGE": 0,
		"OPTIONS": {
			"timeout": 10,
			"check_same_thread": False,
		},
	}
}


@receiver(connection_created)
def _enable_sqlite_wal(sender, connection, **kwargs) -> None:
	if connection.vendor != "sqlite":
		return
	with connection.cursor() as cursor:
		cursor.execute("PRAGMA journal_mode=WAL;")

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
