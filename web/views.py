# FILE: web/views.py
# MODULE: support — Delivery Layer Views
# EPIC: Architecture — Server-Rendered Delivery
# RESPONSIBILITY: Reserve the server-rendered request-entry boundary for approved user workflows.
# EXPORTS: Delivery-layer view placeholders for upload, review, search, edit, and export flows.
# DEPENDS_ON: intake_canonicalization/, source_governance/, search_ranking/, workflow_export/.
# ACCEPTANCE_CRITERIA:
#   - User-facing workflow entry points are clearly separated from domain logic.
#   - Only approved high-level workflows are represented by this delivery boundary.
# HUMAN_REVIEW: Yes — user-facing workflow entry layer.

from django.http import HttpRequest, JsonResponse


def health(request: HttpRequest) -> JsonResponse:
	return JsonResponse({"status": "ok", "phase": "scaffold"})
