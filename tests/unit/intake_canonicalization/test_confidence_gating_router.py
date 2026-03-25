# FILE: tests/unit/intake_canonicalization/test_confidence_gating_router.py
# MODULE: MODULE-001-02 — Confidence Gating Router
# EPIC: EPIC-001 — Data Extraction & Validation
# RESPONSIBILITY: Reserve unit tests for confidence-routing acceptance criteria.
# EXPORTS: Unit test stub.
# DEPENDS_ON: intake_canonicalization/confidence_gating_router.py.
# ACCEPTANCE_CRITERIA:
#   - Confidence routing outcomes are testable from this unit boundary.
#   - Review-required and auto-accept states remain distinguishable.
# HUMAN_REVIEW: No.

from intake_canonicalization.confidence_gating_router import (
	route_confidence,
	split_by_confidence,
)


def test_ac1_confidence_equal_090_routes_to_accept() -> None:
	assert route_confidence(0.90) == "accept"


def test_ac1_confidence_above_090_routes_to_accept() -> None:
	assert route_confidence(0.95) == "accept"


def test_ac2_confidence_equal_070_routes_to_review() -> None:
	assert route_confidence(0.70) == "review"


def test_ac2_confidence_089_routes_to_review() -> None:
	assert route_confidence(0.89) == "review"


def test_ac3_confidence_below_070_routes_to_reject() -> None:
	assert route_confidence(0.69) == "reject"


def test_ac3_confidence_zero_routes_to_reject() -> None:
	assert route_confidence(0.00) == "reject"


def test_split_by_confidence_routes_items_to_three_outputs() -> None:
	items = [
		{"item_id": "a1", "confidence": 0.95},
		{"item_id": "r1", "confidence": 0.80},
		{"item_id": "x1", "confidence": 0.20},
	]

	accepted_fields, review_queue_fields, rejected_fields = split_by_confidence(items)

	assert [item["item_id"] for item in accepted_fields] == ["a1"]
	assert [item["item_id"] for item in review_queue_fields] == ["r1"]
	assert [item["item_id"] for item in rejected_fields] == ["x1"]


def test_split_by_confidence_marks_gate_route_for_traceability() -> None:
	items = [
		{"item_id": "a1", "confidence": 0.90},
		{"item_id": "r1", "confidence": 0.75},
		{"item_id": "x1", "confidence": 0.50},
	]

	accepted_fields, review_queue_fields, rejected_fields = split_by_confidence(items)

	assert accepted_fields[0]["gate_route"] == "accept"
	assert review_queue_fields[0]["gate_route"] == "review"
	assert rejected_fields[0]["gate_route"] == "reject"


def test_split_by_confidence_uses_default_zero_when_missing_confidence() -> None:
	items = [{"item_id": "m1"}]

	accepted_fields, review_queue_fields, rejected_fields = split_by_confidence(items)

	assert accepted_fields == []
	assert review_queue_fields == []
	assert len(rejected_fields) == 1
	assert rejected_fields[0]["item_id"] == "m1"
	assert rejected_fields[0]["gate_route"] == "reject"
