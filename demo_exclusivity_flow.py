from __future__ import annotations

from search_ranking.query_orchestrator import orchestrate_query
from search_ranking.school_exclusivity_resolver import resolve_school_exclusivity


def _executor(source: dict, query: dict, timeout_seconds: float) -> dict:
	return {
		"results": [
			{
				"title": f"{query.get('text', '')} @ {source.get('site_id')}",
			}
		]
	}


def _print_block(title: str, payload: dict) -> None:
	print(f"\n=== {title} ===")
	for key, value in payload.items():
		print(f"{key}: {value}")


def run_demo() -> None:
	print("School Exclusivity Demo Runbook")
	print("Scenario A: eligible")
	print("Scenario B: review_required")

	active_sources = [
		{"site_id": "seller-a", "is_search_eligible": True},
		{"site_id": "seller-b", "is_search_eligible": True},
	]

	scenario_a_item = {
		"item_id": "item-a",
		"name": "Uniforme escolar",
		"school_exclusive": True,
		"required_sellers": ["seller-a"],
		"preferred_sellers": ["seller-b"],
		"exclusive_source": "document_notation",
	}
	resolution_a = resolve_school_exclusivity(item=scenario_a_item, active_sources=active_sources)
	orchestrated_a = orchestrate_query(
		query={"text": scenario_a_item["name"], "categoryID": "general supplies"},
		validation_result={"is_valid": True, "dependency_chain_validated": True},
		eligible_sources=active_sources,
		source_query_executor=_executor,
		exclusivity_context={
			"school_exclusive": resolution_a["resolved_item"]["school_exclusive"],
			"resolution_status": resolution_a["resolution_status"],
			"resolution_reason": resolution_a["resolution_reason"],
			"mandatory_sources": resolution_a["mandatory_sources"],
		},
	)

	_print_block(
		"Scenario A Resolution",
		{
			"resolution_status": resolution_a["resolution_status"],
			"resolution_reason": resolution_a["resolution_reason"],
			"mandatory_sources": resolution_a["mandatory_sources"],
			"preferred_sources": resolution_a["preferred_sources"],
		},
	)
	_print_block(
		"Scenario A Query",
		{
			"completion_status": orchestrated_a["aggregatedResults"]["completionStatus"],
			"queried_count": orchestrated_a["sourceMetadata"]["queriedCount"],
			"result_count": len(orchestrated_a["aggregatedResults"]["resultChunks"]),
		},
	)

	scenario_b_item = {
		"item_id": "item-b",
		"name": "Uniforme esportivo",
		"school_exclusive": True,
		"required_sellers": ["seller-x"],
		"preferred_sellers": [],
		"exclusive_source": "document_notation",
	}
	resolution_b = resolve_school_exclusivity(item=scenario_b_item, active_sources=active_sources)
	orchestrated_b = orchestrate_query(
		query={"text": scenario_b_item["name"], "categoryID": "general supplies"},
		validation_result={"is_valid": True, "dependency_chain_validated": True},
		eligible_sources=active_sources,
		source_query_executor=_executor,
		exclusivity_context={
			"school_exclusive": resolution_b["resolved_item"]["school_exclusive"],
			"resolution_status": resolution_b["resolution_status"],
			"resolution_reason": resolution_b["resolution_reason"],
			"mandatory_sources": resolution_b["mandatory_sources"],
		},
	)

	_print_block(
		"Scenario B Resolution",
		{
			"resolution_status": resolution_b["resolution_status"],
			"resolution_reason": resolution_b["resolution_reason"],
			"mandatory_sources": resolution_b["mandatory_sources"],
			"conflicts": resolution_b["conflicts"],
		},
	)
	_print_block(
		"Scenario B Query",
		{
			"completion_status": orchestrated_b["aggregatedResults"]["completionStatus"],
			"rejection_reason": orchestrated_b["aggregatedResults"].get("rejectionReason"),
			"queried_count": orchestrated_b["sourceMetadata"]["queriedCount"],
		},
	)


if __name__ == "__main__":
	run_demo()
