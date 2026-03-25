# FILE: tests/unit/search_ranking/test_ranking_engine.py
# MODULE: MODULE-003-03 — Ranking Engine
# EPIC: EPIC-003 — Search & Ranking
# RESPONSIBILITY: Reserve unit tests for ranking acceptance criteria.
# EXPORTS: Unit test stub.
# DEPENDS_ON: search_ranking/ranking_engine.py.
# ACCEPTANCE_CRITERIA:
#   - Delivered-price and trust ranking inputs remain testable.
#   - Ranking results remain assertable without retrieval-layer coupling.
# HUMAN_REVIEW: No.

import pytest

from search_ranking.ranking_engine import rank_results


def _weights() -> dict[str, float]:
	return {
		"reputation_weight": 0.25,
		"recency_weight": 0.25,
		"similarity_weight": 0.25,
		"classification_weight": 0.25,
	}


def test_deterministic_scoring_same_input_same_output() -> None:
	classified = {
		"results": [
			{"source_id": "s1", "title": "Algebra Textbook", "classification_label": "Textbook", "recency_days": 10},
			{"source_id": "s2", "title": "Workbook Algebra", "classification_label": "Workbook", "recency_days": 20},
		]
	}
	reputation = {"s1": 0.1, "s2": 0.2}

	first = rank_results(classified, _weights(), reputation, query_text="algebra")
	second = rank_results(classified, _weights(), reputation, query_text="algebra")

	assert first == second


def test_all_results_are_scored_without_filtering() -> None:
	classified = {
		"results": [
			{"source_id": "a", "title": "A", "classification_label": "Other"},
			{"source_id": "b", "title": "B", "classification_label": "Other"},
			{"source_id": "c", "title": "C", "classification_label": "Other"},
		]
	}
	output = rank_results(classified, _weights(), {}, query_text="x")
	assert len(output["rankedResults"]["results"]) == 3


def test_normalized_scores_are_in_0_to_100_and_order_preserved() -> None:
	classified = {
		"results": [
			{"source_id": "s1", "title": "Exact Match", "classification_label": "Textbook", "recency_days": 1},
			{"source_id": "s2", "title": "Weak Match", "classification_label": "Other", "recency_days": 300},
		]
	}
	reputation = {"s1": 0.0, "s2": 0.9}

	output = rank_results(classified, _weights(), reputation, query_text="exact match")
	results = output["rankedResults"]["results"]

	assert results[0]["normalized_score"] >= results[1]["normalized_score"]
	assert 0.0 <= results[0]["normalized_score"] <= 100.0
	assert 0.0 <= results[1]["normalized_score"] <= 100.0


def test_stable_sort_for_tied_scores_keeps_input_order() -> None:
	classified = {
		"results": [
			{"source_id": "s1", "title": "Same", "classification_label": "Other"},
			{"source_id": "s2", "title": "Same", "classification_label": "Other"},
			{"source_id": "s3", "title": "Same", "classification_label": "Other"},
		]
	}

	output = rank_results(classified, _weights(), {}, query_text="none")
	ordered_sources = [item["source_id"] for item in output["rankedResults"]["results"]]
	assert ordered_sources == ["s1", "s2", "s3"]


def test_low_confidence_flag_applies_below_25th_percentile() -> None:
	classified = {
		"results": [
			{"source_id": "good", "title": "good match", "classification_label": "Textbook", "recency_days": 1},
			{"source_id": "mid", "title": "mid", "classification_label": "Other", "recency_days": 200},
			{"source_id": "bad", "title": "bad", "classification_label": "Other", "recency_days": 365},
		]
	}
	reputation = {"good": 0.0, "mid": 0.5, "bad": 1.0}

	output = rank_results(classified, _weights(), reputation, query_text="good")
	flags = output["rankedResults"]["lowConfidenceFlags"]

	assert any(flags)


def test_weights_validation_rejects_invalid_sum() -> None:
	invalid = {
		"reputation_weight": 0.5,
		"recency_weight": 0.5,
		"similarity_weight": 0.5,
		"classification_weight": 0.5,
	}

	with pytest.raises(ValueError):
		rank_results({"results": []}, invalid, {}, query_text="")


def test_weights_validation_rejects_zero_weight() -> None:
	invalid = {
		"reputation_weight": 0.0,
		"recency_weight": 0.4,
		"similarity_weight": 0.3,
		"classification_weight": 0.3,
	}

	with pytest.raises(ValueError):
		rank_results({"results": []}, invalid, {}, query_text="")


def test_missing_reputation_uses_neutral_fallback() -> None:
	classified = {
		"results": [
			{"source_id": "unknown-source", "title": "A", "classification_label": "Other"}
		]
	}

	output = rank_results(classified, _weights(), {}, query_text="A")
	assert len(output["rankedResults"]["results"]) == 1
	assert output["rankedResults"]["results"][0]["composite_score"] > 0


def test_portuguese_classification_labels_are_supported_in_scoring() -> None:
	classified = {
		"results": [
			{"source_id": "s1", "title": "Livro de Matemática", "classification_label": "Livro Didático", "recency_days": 10},
			{"source_id": "s2", "title": "Guia", "classification_label": "Referência", "recency_days": 10},
		]
	}

	output = rank_results(classified, _weights(), {"s1": 0.0, "s2": 0.0}, query_text="matemática")
	results = output["rankedResults"]["results"]

	assert len(results) == 2
	assert results[0]["classification_label"] in {"Livro Didático", "Referência"}
