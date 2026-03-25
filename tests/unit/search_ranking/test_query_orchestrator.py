# FILE: tests/unit/search_ranking/test_query_orchestrator.py
# MODULE: MODULE-003-01 — Query Orchestrator
# EPIC: EPIC-003 — Search & Ranking
# RESPONSIBILITY: Reserve unit tests for query-orchestration acceptance criteria.
# EXPORTS: Unit test stub.
# DEPENDS_ON: search_ranking/query_orchestrator.py.
# ACCEPTANCE_CRITERIA:
#   - Query job-state boundaries are testable from this unit boundary.
#   - Partial-failure handling remains explicitly assertable.
# HUMAN_REVIEW: No.

from search_ranking.query_orchestrator import orchestrate_query


def _ok_executor(source: dict, query: dict, timeout_seconds: float) -> dict:
	return {"results": [{"title": f"result-{source['site_id']}"}]}


def test_rejects_query_longer_than_1000_characters() -> None:
	query = {"text": "x" * 1001, "categoryID": "book"}
	result = orchestrate_query(
		query=query,
		validation_result={"is_valid": True, "dependency_chain_validated": True},
		eligible_sources=[{"site_id": "s1", "is_search_eligible": True}],
		source_query_executor=_ok_executor,
	)

	assert result["aggregatedResults"]["completionStatus"] == "rejected"
	assert result["aggregatedResults"]["rejectionReason"] == "query_too_long"


def test_rejects_when_validation_gate_token_invalid() -> None:
	query = {"text": "math book", "categoryID": "book"}
	result = orchestrate_query(
		query=query,
		validation_result={"is_valid": False, "dependency_chain_validated": True},
		eligible_sources=[{"site_id": "s1", "is_search_eligible": True}],
		source_query_executor=_ok_executor,
	)

	assert result["aggregatedResults"]["completionStatus"] == "rejected"
	assert result["aggregatedResults"]["rejectionReason"] == "validation_gate_failed"


def test_queries_only_eligible_sources() -> None:
	called_sites: list[str] = []

	def executor(source: dict, query: dict, timeout_seconds: float) -> dict:
		called_sites.append(source["site_id"])
		return {"results": [{"value": source["site_id"]}]}

	query = {"text": "pencil", "categoryID": "general supplies"}
	result = orchestrate_query(
		query=query,
		validation_result={"is_valid": True, "dependency_chain_validated": True},
		eligible_sources=[
			{"site_id": "eligible-1", "is_search_eligible": True},
			{"site_id": "blocked-1", "is_search_eligible": False},
			{"site_id": "eligible-2", "is_search_eligible": True},
		],
		source_query_executor=executor,
	)

	assert called_sites == ["eligible-1", "eligible-2"]
	assert result["sourceMetadata"]["queriedCount"] == 2


def test_timeout_from_one_source_produces_partial_results() -> None:
	def executor(source: dict, query: dict, timeout_seconds: float) -> dict:
		if source["site_id"] == "slow":
			raise TimeoutError("timeout")
		return {"results": [{"title": "ok"}]}

	result = orchestrate_query(
		query={"text": "history", "categoryID": "book"},
		validation_result={"is_valid": True, "dependency_chain_validated": True},
		eligible_sources=[
			{"site_id": "fast", "is_search_eligible": True},
			{"site_id": "slow", "is_search_eligible": True},
		],
		source_query_executor=executor,
	)

	assert result["aggregatedResults"]["completionStatus"] == "partial"
	assert result["sourceMetadata"]["timeoutCount"] == 1
	assert len(result["aggregatedResults"]["resultChunks"]) == 1


def test_buffer_limit_keeps_querying_sources_and_marks_overflow() -> None:
	def executor(source: dict, query: dict, timeout_seconds: float) -> dict:
		return {"results": [{"r": 1}, {"r": 2}]}

	result = orchestrate_query(
		query={"text": "notebook", "categoryID": "notebook"},
		validation_result={"is_valid": True, "dependency_chain_validated": True},
		eligible_sources=[
			{"site_id": "s1", "is_search_eligible": True},
			{"site_id": "s2", "is_search_eligible": True},
		],
		source_query_executor=executor,
		max_result_buffer=3,
	)

	assert len(result["aggregatedResults"]["resultChunks"]) == 3
	assert result["sourceMetadata"]["bufferOverflowed"] is True
	assert result["sourceMetadata"]["droppedResultsCount"] == 1


def test_dispatch_window_within_50ms_for_all_sources() -> None:
	result = orchestrate_query(
		query={"text": "geography", "categoryID": "book"},
		validation_result={"is_valid": True, "dependency_chain_validated": True},
		eligible_sources=[
			{"site_id": "a", "is_search_eligible": True},
			{"site_id": "b", "is_search_eligible": True},
			{"site_id": "c", "is_search_eligible": True},
		],
		source_query_executor=_ok_executor,
	)

	assert result["sourceMetadata"]["dispatchWindowMs"] <= 50.0
