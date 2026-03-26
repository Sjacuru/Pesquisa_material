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

from web.views import exclusivity_demo, exclusivity_review, health, upload_workflow


urlpatterns = [
	path("", health, name="health"),
	path("workflow/upload/", upload_workflow, name="upload-workflow"),
	path("workflow/exclusivity/demo/", exclusivity_demo, name="exclusivity-demo"),
	path("workflow/exclusivity/review/", exclusivity_review, name="exclusivity-review"),
]
