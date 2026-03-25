# FILE: tests/integration/test_upload_to_search_readiness.py
# MODULE: integration — Upload to Search Readiness Flow
# EPIC: EPIC-001 + EPIC-003 — Cross-Component Flow
# RESPONSIBILITY: Reserve integration tests for upload-to-search-readiness flow boundaries.
# EXPORTS: Integration test stub.
# DEPENDS_ON: intake_canonicalization/, search_ranking/.
# ACCEPTANCE_CRITERIA:
#   - Upload-to-search-ready handoff remains testable at integration level.
#   - Review-required and blocked states remain representable across components.
# HUMAN_REVIEW: No.

from intake_canonicalization.confidence_gating_router import split_by_confidence
from intake_canonicalization.missing_isbn_search_gate import apply_missing_isbn_search_gate
from intake_canonicalization.pdf_ingestion_field_extraction import extract_item_candidates
from search_ranking.query_orchestrator import orchestrate_query


def _category_matrix() -> dict[str, dict[str, str]]:
	return {
		"book": {"id": "book"},
		"general supplies": {"id": "general supplies"},
	}


def _to_confidence_items(extracted_items: list[dict]) -> list[dict]:
	items: list[dict] = []
	for extracted in extracted_items:
		fields = extracted.get("fields", {})
		category = fields.get("category", {})
		isbn = fields.get("isbn", {})
		name = fields.get("name", {})
		items.append(
			{
				"item_id": f"line-{extracted.get('line_index')}",
				"name": name.get("value"),
				"category": category.get("value"),
				"isbn": isbn.get("value"),
				"confidence": float(category.get("confidence", 0.0)),
			}
		)
	return items


def _ok_executor(source: dict, query: dict, timeout_seconds: float) -> dict:
	return {
		"results": [
			{
				"title": f"{query.get('text', '')}-{source.get('site_id')}",
			}
		]
	}


def test_upload_to_search_flow_represents_review_required_and_blocked_states() -> None:
	uploaded_pdf_document = {
		"content_type": "application/pdf",
		"text": "Livro de matemática\nItem diverso sem marcador",
	}

	extracted = extract_item_candidates(uploaded_pdf_document, _category_matrix())
	accepted, review_queue, rejected = split_by_confidence(_to_confidence_items(extracted))

	assert len(rejected) == 0
	assert len(review_queue) == 1
	assert review_queue[0]["gate_route"] == "review"

	search_eligible, search_blocked = apply_missing_isbn_search_gate(
		eligible_items_precheck=accepted,
		isbn_validated_items=[],
		user_isbn_completion_events=[],
	)

	assert search_eligible == []
	assert len(search_blocked) == 1
	assert search_blocked[0]["search_gate_state"] == "review_required"
	assert search_blocked[0]["search_gate_reason"] == "missing_or_invalid_isbn"


def test_upload_to_search_ready_items_handoff_into_query_execution() -> None:
	uploaded_pdf_document = {
		"content_type": "application/pdf",
		"text": "Livro ISBN 9780306406157",
	}

	extracted = extract_item_candidates(uploaded_pdf_document, _category_matrix())
	accepted, review_queue, rejected = split_by_confidence(_to_confidence_items(extracted))

	assert len(accepted) == 1
	assert review_queue == []
	assert rejected == []

	search_eligible, search_blocked = apply_missing_isbn_search_gate(
		eligible_items_precheck=accepted,
		isbn_validated_items=[],
		user_isbn_completion_events=[],
	)

	assert len(search_eligible) == 1
	assert search_blocked == []
	assert search_eligible[0]["search_gate_state"] == "search_eligible"

	result = orchestrate_query(
		query={"text": str(search_eligible[0].get("name") or ""), "categoryID": search_eligible[0]["category"]},
		validation_result={"is_valid": True, "dependency_chain_validated": True},
		eligible_sources=[
			{"site_id": "site-1", "is_search_eligible": True},
			{"site_id": "site-2", "is_search_eligible": False},
		],
		source_query_executor=_ok_executor,
	)

	assert result["aggregatedResults"]["completionStatus"] == "complete"
	assert result["sourceMetadata"]["queriedCount"] == 1
	assert len(result["aggregatedResults"]["resultChunks"]) == 1
