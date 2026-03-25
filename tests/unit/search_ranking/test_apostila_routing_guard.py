# FILE: tests/unit/search_ranking/test_apostila_routing_guard.py
# MODULE: MODULE-003-04 — Apostila Routing Guard
# EPIC: EPIC-003 — Search & Ranking
# RESPONSIBILITY: Reserve unit tests for Apostila-routing acceptance criteria.
# EXPORTS: Unit test stub.
# DEPENDS_ON: search_ranking/apostila_routing_guard.py.
# ACCEPTANCE_CRITERIA:
#   - Apostila routing restrictions remain testable from this unit boundary.
#   - Routing behavior remains separate from ranking behavior.
# HUMAN_REVIEW: No.

from copy import deepcopy

from search_ranking.apostila_routing_guard import route_apostila_results


def _sample_ranked_results() -> dict:
	return {
		"results": [
			{"result_id": "r1", "source_id": "s1", "classification_label": "Apostila", "normalized_score": 90.0},
			{"result_id": "r2", "source_id": "s2", "classification_label": "Textbook", "normalized_score": 80.0},
			{"result_id": "r3", "source_id": "s3", "classification_label": "apostila", "normalized_score": 70.0},
		]
	}


def _sample_material_classifications() -> dict[str, str]:
	return {
		"r1": "Apostila",
		"r2": "Textbook",
		"r3": "Apostila",
	}


def _sample_provenance_index() -> dict[str, dict]:
	return {
		"r1": {"source_id": "s1", "extraction_timestamp": "2026-03-25T10:00:00+00:00", "apostila_id": "ap-001"},
		"r3": {"source_id": "s3", "extraction_timestamp": "2026-03-25T10:05:00+00:00", "apostila_id": "ap-003"},
	}


def test_apostila_results_are_routed_to_apostila_tier() -> None:
	output = route_apostila_results(
		ranked_results=_sample_ranked_results(),
		material_classifications=_sample_material_classifications(),
		provenance_index=_sample_provenance_index(),
	)

	assert output["apostilaResults"]["tier"] == "apostila"
	assert len(output["apostilaResults"]["results"]) == 2


def test_apostila_without_provenance_is_rejected_with_reason() -> None:
	ranked = {"results": [{"result_id": "missing", "source_id": "sx", "classification_label": "Apostila"}]}
	output = route_apostila_results(
		ranked_results=ranked,
		material_classifications={"missing": "Apostila"},
		provenance_index={},
	)

	assert len(output["apostilaResults"]["results"]) == 0
	assert output["routingMetrics"]["apostilaRejectedCount"] == 1
	assert output["apostilaRejections"][0]["reason"] == "missing_provenance_chain"


def test_apostila_metadata_is_injected_for_all_included_apostila_results() -> None:
	output = route_apostila_results(
		ranked_results=_sample_ranked_results(),
		material_classifications=_sample_material_classifications(),
		provenance_index=_sample_provenance_index(),
	)

	for item in output["apostilaResults"]["results"]:
		assert item["apostila_metadata"]["source_attribution_mandatory"] is True
		assert item["attribution_link_locked"] is True


def test_non_apostila_results_bypass_without_metadata_mutation() -> None:
	ranked = _sample_ranked_results()
	original_non_apostila = deepcopy(ranked["results"][1])
	output = route_apostila_results(
		ranked_results=ranked,
		material_classifications=_sample_material_classifications(),
		provenance_index=_sample_provenance_index(),
	)

	assert len(output["genericResults"]["results"]) == 1
	generic_item = output["genericResults"]["results"][0]
	assert generic_item == original_non_apostila
	assert "apostila_metadata" not in generic_item


def test_routing_is_deterministic_for_same_input() -> None:
	first = route_apostila_results(
		ranked_results=_sample_ranked_results(),
		material_classifications=_sample_material_classifications(),
		provenance_index=_sample_provenance_index(),
	)
	second = route_apostila_results(
		ranked_results=_sample_ranked_results(),
		material_classifications=_sample_material_classifications(),
		provenance_index=_sample_provenance_index(),
	)

	assert first == second
