# FILE: web/apps.py
# MODULE: Web App Configuration
# RESPONSIBILITY: Configure the web app and initialize background services
from django.apps import AppConfig


class WebConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "web"

    def ready(self):
        """Initialize background services when Django starts."""
        # Silently skip - job runner will be started on first request via middleware
        pass


