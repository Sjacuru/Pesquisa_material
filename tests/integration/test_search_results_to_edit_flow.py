# FILE: tests/integration/test_search_results_to_edit_flow.py
# MODULE: integration — Search Results to Edit Flow
# EPIC: EPIC-003 + EPIC-004 — Cross-Component Flow
# RESPONSIBILITY: Reserve integration tests for ranked-result handoff into the user-edit workflow.
# EXPORTS: Integration test stub.
# DEPENDS_ON: search_ranking/, workflow_export/.
# ACCEPTANCE_CRITERIA:
#   - Ranked-result handoff into editable workflow remains testable.
#   - Edit-boundary rules remain enforceable across the integration boundary.
# HUMAN_REVIEW: No.

from search_ranking.match_classifier import classify_matches
from search_ranking.ranking_engine import rank_results
from workflow_export.user_edit_handler import handle_user_edit


def _result_queue(titles_and_isbns: list[tuple[str, str]]) -> dict:
	return {
		"resultChunks": [
			{"source_id": f"src-{i}", "result": {"title": title, "isbn": isbn}}
			for i, (title, isbn) in enumerate(titles_and_isbns)
		]
	}


def _reputation_index_all_healthy(classified: dict) -> dict[str, object]:
	return {
		item["source_id"]: 0.0
		for item in classified.get("classifiedResults", {}).get("results", [])
	}


def test_ranked_result_can_be_handed_off_to_edit_handler() -> None:
	result_queue = _result_queue([("ISBN History of Time", "9780553380163"), ("General Science", "")])
	classified = classify_matches(result_queue)
	ranked = rank_results(
		classified_results=classified["classifiedResults"],
		score_weights=None,
		source_reputation_index=_reputation_index_all_healthy(classified),
		query_text="history of time",
	)

	top_result = ranked["rankedResults"]["results"][0]
	material_item = {"result_id": top_result["result_id"], "title": top_result.get("title", "")}

	edit_store: list[dict] = []
	result = handle_user_edit(
		material_item=material_item,
		edit_request={"fieldName": "notes", "oldValue": "", "newValue": "Teacher recommended.", "reasonNote": ""},
		user_context={"userId": "user-1", "sessionId": "s1", "role": "editor"},
		category_contract={"book", "dictionary", "notebook", "apostila", "general supplies"},
		local_edit_store=edit_store,
	)

	assert result["editResult"]["status"] == "accepted"
	assert len(edit_store) == 1


def test_immutable_source_field_is_blocked_at_edit_boundary_for_ranked_item() -> None:
	result_queue = _result_queue([("Sample Book", "9780306406157")])
	classified = classify_matches(result_queue)
	ranked = rank_results(
		classified_results=classified["classifiedResults"],
		score_weights=None,
		source_reputation_index=_reputation_index_all_healthy(classified),
	)

	top_result = ranked["rankedResults"]["results"][0]
	material_item = {"result_id": top_result["result_id"]}

	edit_store: list[dict] = []
	result = handle_user_edit(
		material_item=material_item,
		edit_request={"fieldName": "source_id", "oldValue": "src-0", "newValue": "tampered", "reasonNote": ""},
		user_context={"userId": "user-1", "sessionId": "s1", "role": "editor"},
		category_contract={"book"},
		local_edit_store=edit_store,
	)

	assert result["editResult"]["status"] == "rejected"
	assert result["editResult"]["reasonCode"] == "immutable_field"
	assert edit_store == []
