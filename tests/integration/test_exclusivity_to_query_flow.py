from search_ranking.query_orchestrator import orchestrate_query
from search_ranking.school_exclusivity_resolver import resolve_school_exclusivity


def _executor(source: dict, query: dict, timeout_seconds: float) -> dict:
	return {"results": [{"title": f"{query.get('text', '')}-{source['site_id']}"}]}


def test_exclusive_item_routes_only_to_required_active_seller() -> None:
	active_sources = [
		{"site_id": "seller-a", "is_search_eligible": True},
		{"site_id": "seller-b", "is_search_eligible": True},
	]
	resolution = resolve_school_exclusivity(
		item={
			"item_id": "i1",
			"school_exclusive": True,
			"required_sellers": ["seller-a"],
			"preferred_sellers": ["seller-b"],
			"exclusive_source": "document_notation",
		},
		active_sources=active_sources,
	)

	result = orchestrate_query(
		query={"text": "uniforme", "categoryID": "general supplies"},
		validation_result={"is_valid": True, "dependency_chain_validated": True},
		eligible_sources=active_sources,
		source_query_executor=_executor,
		exclusivity_context={
			"school_exclusive": resolution["resolved_item"]["school_exclusive"],
			"resolution_status": resolution["resolution_status"],
			"resolution_reason": resolution["resolution_reason"],
			"mandatory_sources": resolution["mandatory_sources"],
		},
	)

	assert result["aggregatedResults"]["completionStatus"] == "complete"
	assert result["sourceMetadata"]["queriedCount"] == 1
	assert len(result["aggregatedResults"]["resultChunks"]) == 1
	assert result["aggregatedResults"]["resultChunks"][0]["source_id"] == "seller-a"


def test_exclusive_item_without_active_required_seller_routes_review_required() -> None:
	active_sources = [{"site_id": "seller-a", "is_search_eligible": True}]
	resolution = resolve_school_exclusivity(
		item={
			"item_id": "i2",
			"school_exclusive": True,
			"required_sellers": ["seller-x"],
			"exclusive_source": "document_notation",
		},
		active_sources=active_sources,
	)

	result = orchestrate_query(
		query={"text": "uniforme", "categoryID": "general supplies"},
		validation_result={"is_valid": True, "dependency_chain_validated": True},
		eligible_sources=active_sources,
		source_query_executor=_executor,
		exclusivity_context={
			"school_exclusive": resolution["resolved_item"]["school_exclusive"],
			"resolution_status": resolution["resolution_status"],
			"resolution_reason": resolution["resolution_reason"],
			"mandatory_sources": resolution["mandatory_sources"],
		},
	)

	assert result["aggregatedResults"]["completionStatus"] == "review_required"
	assert result["aggregatedResults"]["rejectionReason"] == "no_active_required_sellers"
	assert result["sourceMetadata"]["queriedCount"] == 0
