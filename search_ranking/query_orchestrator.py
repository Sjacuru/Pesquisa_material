# FILE: search_ranking/query_orchestrator.py
# MODULE: MODULE-003-01 — Query Orchestrator
# EPIC: EPIC-003 — Search & Ranking
# RESPONSIBILITY: Coordinate multi-source query execution and track job-level search state.
# EXPORTS: Query orchestration stub.
# DEPENDS_ON: intake_canonicalization/category_rules_eligibility_validator.py, intake_canonicalization/missing_isbn_search_gate.py, source_governance/search_eligibility_site_filter.py, platform/job_runner.py.
# ACCEPTANCE_CRITERIA:
#   - Multi-source query coordination remains explicit.
#   - Partial-failure and job-state boundaries are represented separately from ranking.
# HUMAN_REVIEW: Yes — performance-critical external fan-out.

from __future__ import annotations

import time


MAX_QUERY_LENGTH = 1000
MAX_RESULT_BUFFER = 100_000
SOURCE_TIMEOUT_SECONDS = 5.0


def _is_valid_validation_token(validation_result: object) -> bool:
	if isinstance(validation_result, bool):
		return validation_result
	if isinstance(validation_result, dict):
		return bool(validation_result.get("is_valid", False)) and bool(
			validation_result.get("dependency_chain_validated", False)
		)
	return False


def _is_source_eligible(source: dict) -> bool:
	if "is_search_eligible" in source:
		return bool(source.get("is_search_eligible"))
	trust_status = str(source.get("trust_classification_status", "")).lower()
	is_suspended = bool(source.get("is_suspended", False))
	if trust_status == "blocked":
		return False
	if is_suspended:
		return False
	return True


def orchestrate_query(
	query: dict,
	validation_result: object,
	eligible_sources: list[dict],
	source_query_executor,
	max_result_buffer: int = MAX_RESULT_BUFFER,
	source_timeout_seconds: float = SOURCE_TIMEOUT_SECONDS,
	exclusivity_context: dict | None = None,
) -> dict[str, object]:
	"""
	Coordinate source queries and aggregate partial results for classifier stage.

	source_query_executor signature:
	  (source: dict, query: dict, timeout_seconds: float) -> dict
"""
	query_text = str(query.get("text") or "")
	if len(query_text) > MAX_QUERY_LENGTH:
		return {
			"aggregatedResults": {
				"resultChunks": [],
				"completionStatus": "rejected",
				"rejectionReason": "query_too_long",
			},
			"sourceMetadata": {
				"queriedCount": 0,
				"timeoutCount": 0,
				"errorCount": 0,
				"sourceUnavailableEvents": [],
				"dispatchWindowMs": 0.0,
				"bufferOverflowed": False,
				"droppedResultsCount": 0,
			},
		}

	if not _is_valid_validation_token(validation_result):
		return {
			"aggregatedResults": {
				"resultChunks": [],
				"completionStatus": "rejected",
				"rejectionReason": "validation_gate_failed",
			},
			"sourceMetadata": {
				"queriedCount": 0,
				"timeoutCount": 0,
				"errorCount": 0,
				"sourceUnavailableEvents": [],
				"dispatchWindowMs": 0.0,
				"bufferOverflowed": False,
				"droppedResultsCount": 0,
			},
		}

	if isinstance(exclusivity_context, dict):
		resolution_status = str(exclusivity_context.get("resolution_status") or "").lower()
		if resolution_status == "review_required":
			return {
				"aggregatedResults": {
					"resultChunks": [],
					"completionStatus": "review_required",
					"rejectionReason": str(exclusivity_context.get("resolution_reason") or "school_exclusivity_review_required"),
				},
				"sourceMetadata": {
					"queriedCount": 0,
					"timeoutCount": 0,
					"errorCount": 0,
					"sourceUnavailableEvents": [],
					"dispatchWindowMs": 0.0,
					"bufferOverflowed": False,
					"droppedResultsCount": 0,
					"exclusivityApplied": True,
				},
			}

	filtered_sources = [source for source in eligible_sources if _is_source_eligible(source)]

	if isinstance(exclusivity_context, dict):
		mandatory_sources = exclusivity_context.get("mandatory_sources") or []
		school_exclusive = bool(exclusivity_context.get("school_exclusive", False))
		if mandatory_sources:
			allowed = {
				str(site_id).strip().lower()
				for site_id in mandatory_sources
				if str(site_id).strip()
			}
			filtered_sources = [
				source
				for source in filtered_sources
				if str(source.get("site_id") or source.get("id") or "").strip().lower() in allowed
			]
		elif school_exclusive:
			return {
				"aggregatedResults": {
					"resultChunks": [],
					"completionStatus": "review_required",
					"rejectionReason": str(exclusivity_context.get("resolution_reason") or "no_active_required_sellers"),
				},
				"sourceMetadata": {
					"queriedCount": 0,
					"timeoutCount": 0,
					"errorCount": 0,
					"sourceUnavailableEvents": [],
					"dispatchWindowMs": 0.0,
					"bufferOverflowed": False,
					"droppedResultsCount": 0,
					"exclusivityApplied": True,
				},
			}

	timeout_count = 0
	error_count = 0
	source_unavailable_events: list[dict] = []
	result_chunks: list[dict] = []
	buffer_overflowed = False
	dropped_results_count = 0

	dispatch_base = time.monotonic()
	dispatch_times: list[float] = []

	for source in filtered_sources:
		dispatch_time = dispatch_base
		dispatch_times.append(dispatch_time)
		source_id = str(source.get("site_id") or source.get("id") or "unknown")

		try:
			response = source_query_executor(source, query, source_timeout_seconds)
		except TimeoutError:
			timeout_count += 1
			source_unavailable_events.append(
				{"site_id": source_id, "reason": "timeout", "timeout_seconds": source_timeout_seconds}
			)
			continue
		except Exception:
			error_count += 1
			source_unavailable_events.append({"site_id": source_id, "reason": "error"})
			continue

		if bool(response.get("timed_out", False)):
			timeout_count += 1
			source_unavailable_events.append(
				{"site_id": source_id, "reason": "timeout", "timeout_seconds": source_timeout_seconds}
			)
			continue

		if response.get("error"):
			error_count += 1
			source_unavailable_events.append({"site_id": source_id, "reason": "error"})
			continue

		for result in response.get("results", []):
			if len(result_chunks) < max_result_buffer:
				result_chunks.append({"source_id": source_id, "result": result})
			else:
				buffer_overflowed = True
				dropped_results_count += 1

	dispatch_window_ms = 0.0
	if dispatch_times:
		dispatch_window_ms = round((max(dispatch_times) - min(dispatch_times)) * 1000, 2)

	completion_status = "complete"
	if timeout_count > 0 or error_count > 0 or buffer_overflowed:
		completion_status = "partial"

	return {
		"aggregatedResults": {
			"resultChunks": result_chunks,
			"completionStatus": completion_status,
		},
		"sourceMetadata": {
			"queriedCount": len(filtered_sources),
			"timeoutCount": timeout_count,
			"errorCount": error_count,
			"sourceUnavailableEvents": source_unavailable_events,
			"dispatchWindowMs": dispatch_window_ms,
			"bufferOverflowed": buffer_overflowed,
			"droppedResultsCount": dropped_results_count,
			"exclusivityApplied": isinstance(exclusivity_context, dict),
		},
	}
