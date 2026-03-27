# FILE: intake_canonicalization/confidence_gating_router.py
# MODULE: MODULE-001-02 — Confidence Gating Router
# EPIC: EPIC-001 — Data Extraction & Validation
# RESPONSIBILITY: Route extracted records by confidence band into automatic acceptance or review-required paths.
# EXPORTS: Confidence routing stub.
# DEPENDS_ON: intake_canonicalization/pdf_ingestion_field_extraction.py.
# ACCEPTANCE_CRITERIA:
#   - Confidence-band routing boundaries are explicit.
#   - Review-required records remain distinguishable from auto-accepted records.
# HUMAN_REVIEW: No.

from __future__ import annotations

ACCEPT_THRESHOLD = 0.90
REVIEW_THRESHOLD = 0.70


def route_confidence(confidence: float) -> str:
	"""Route a confidence score to one of: accept, review, reject."""
	if confidence >= ACCEPT_THRESHOLD:
		return "accept"
	if confidence >= REVIEW_THRESHOLD:
		return "review"
	return "reject"


def split_by_confidence(
	extracted_items_with_confidence: list[dict],
) -> tuple[list[dict], list[dict], list[dict]]:
	"""
	Split extracted items by confidence band.

	Input item contract (minimal): {"confidence": <float>, ...}
	Returns: (accepted_fields, review_queue_fields, rejected_fields)
	"""
	accepted_fields: list[dict] = []
	review_queue_fields: list[dict] = []
	rejected_fields: list[dict] = []

	for item in extracted_items_with_confidence:
		if bool(item.get("requires_human_review", False)):
			enriched_item = {**item, "gate_route": "review", "gate_reason": "directive_resolution_required"}
			review_queue_fields.append(enriched_item)
			continue

		confidence = float(item.get("confidence", 0.0))
		route = route_confidence(confidence)
		enriched_item = {**item, "gate_route": route}

		if route == "accept":
			accepted_fields.append(enriched_item)
		elif route == "review":
			review_queue_fields.append(enriched_item)
		else:
			rejected_fields.append(enriched_item)

	return accepted_fields, review_queue_fields, rejected_fields
