# FILE: config/urls.py
# MODULE: config — Root URL Configuration
# EPIC: Architecture — Delivery Wiring
# RESPONSIBILITY: Define the root route-registration boundary for the scaffold.
# EXPORTS: Project-level URL registration contract.
# DEPENDS_ON: web/urls.py.
# ACCEPTANCE_CRITERIA:
#   - Route ownership is delegated to the delivery layer.
#   - No business logic is implemented in route registration.
# HUMAN_REVIEW: No.

from django.urls import include, path


urlpatterns = [
	path("", include("web.urls")),
]
