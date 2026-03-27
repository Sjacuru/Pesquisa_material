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

from web.views import (
	batch_export,
	batch_export_download,
	exclusivity_demo,
	exclusivity_review,
	health,
	item_edit,
	item_search_results,
	job_status,
	run_item_search,
	upload_workflow,
)


urlpatterns = [
	path("", health, name="health"),
	path("workflow/upload/", upload_workflow, name="upload-workflow"),
	path("workflow/exclusivity/demo/", exclusivity_demo, name="exclusivity-demo"),
	path("workflow/exclusivity/review/", exclusivity_review, name="exclusivity-review"),
	path("item/<int:item_id>/search-results/", item_search_results, name="item-search-results"),
	path("item/<int:item_id>/search/run/", run_item_search, name="run-item-search"),
	path("jobs/<str:job_id>/status/", job_status, name="job-status"),
	path("item/<int:item_id>/edit/", item_edit, name="item-edit"),
	path("batch/<int:batch_id>/export/", batch_export, name="batch-export"),
	path("batch/<int:batch_id>/export/download/", batch_export_download, name="batch-export-download"),
]
