# FILE: config/asgi.py
# MODULE: support — ASGI Gateway
# EPIC: Architecture — Runtime Entry Point
# RESPONSIBILITY: Reserve the ASGI gateway boundary for the application runtime.
# EXPORTS: ASGI application gateway placeholder.
# DEPENDS_ON: config/settings.py.
# ACCEPTANCE_CRITERIA:
#   - The runtime gateway is clearly identified for local-first deployment.
#   - No application behavior is implemented in the gateway file.
# HUMAN_REVIEW: No.

import os

from django.core.asgi import get_asgi_application


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
