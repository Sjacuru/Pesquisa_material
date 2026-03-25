# FILE: search_ranking/apostila_routing_guard.py
# MODULE: MODULE-003-04 — Apostila Routing Guard
# EPIC: EPIC-003 — Search & Ranking
# RESPONSIBILITY: Enforce Apostila-specific routing restrictions over ranked search outputs.
# EXPORTS: Apostila routing guard stub.
# DEPENDS_ON: search_ranking/ranking_engine.py, intake_canonicalization/duplicate_resolution_coordinator.py.
# ACCEPTANCE_CRITERIA:
#   - Apostila routing restrictions remain explicit.
#   - Routing logic remains separate from ranking behavior.
# HUMAN_REVIEW: No.

from __future__ import annotations

from copy import deepcopy

from search_ranking.text_normalization import normalize_text


_APOSTILA_LABELS = {
	"apostila",
	"apostille",
	"handout",
}


def _is_apostila_label(label: object) -> bool:
	return normalize_text(label) in _APOSTILA_LABELS


def route_apostila_results(
	ranked_results: dict,
	material_classifications: dict[str, str],
	provenance_index: dict[str, dict],
) -> dict[str, object]:
	"""
	Route apostila and non-apostila results into separate presentation tiers.
	"""
	ranked_items = ranked_results.get("results", []) if isinstance(ranked_results, dict) else []

	apostila_results: list[dict] = []
	apostila_attribution_metadata: list[dict] = []
	generic_results: list[dict] = []
	apostila_rejections: list[dict] = []

	for item in ranked_items:
		result_id = str(item.get("result_id") or "")
		classification_label = material_classifications.get(result_id, item.get("classification_label", ""))

		if not _is_apostila_label(classification_label):
			generic_results.append(deepcopy(item))
			continue

		if not result_id:
			apostila_rejections.append(
				{
					"result_id": "",
					"reason": "missing_result_id",
				}
			)
			continue

		provenance = provenance_index.get(result_id)
		if provenance is None:
			apostila_rejections.append(
				{
					"result_id": result_id,
					"reason": "missing_provenance_chain",
				}
			)
			continue

		routed_item = deepcopy(item)
		attribution_metadata = {
			"result_id": result_id,
			"source_attribution_mandatory": True,
			"original_source_id": provenance.get("source_id"),
			"original_extraction_timestamp": provenance.get("extraction_timestamp"),
			"apostila_identifier": provenance.get("apostila_id") or result_id,
		}

		routed_item["apostila_metadata"] = attribution_metadata
		routed_item["attribution_link_locked"] = True

		apostila_results.append(routed_item)
		apostila_attribution_metadata.append(attribution_metadata)

	return {
		"apostilaResults": {
			"results": apostila_results,
			"attributionMetadata": apostila_attribution_metadata,
			"tier": "apostila",
		},
		"genericResults": {
			"results": generic_results,
			"tier": "generic",
		},
		"routingMetrics": {
			"apostilaCount": len(apostila_results),
			"apostilaRejectedCount": len(apostila_rejections),
			"genericCount": len(generic_results),
		},
		"apostilaRejections": apostila_rejections,
	}
