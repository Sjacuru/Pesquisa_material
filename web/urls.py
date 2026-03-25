# FILE: web/urls.py
# MODULE: support — Delivery Layer Routes
# EPIC: Architecture — Server-Rendered Delivery
# RESPONSIBILITY: Reserve the route-registration boundary for server-rendered workflows.
# EXPORTS: Delivery-layer route mapping placeholders.
# DEPENDS_ON: web/views.py.
# ACCEPTANCE_CRITERIA:
#   - Delivery routes are separated from domain modules.
#   - Route ownership remains within approved user workflows only.
# HUMAN_REVIEW: No.

from django.urls import path

from web.views import health


urlpatterns = [
	path("", health, name="health"),
]
