# FILE: tests/unit/intake_canonicalization/test_category_rules_eligibility_validator.py
# MODULE: MODULE-001-05 — Category Rules & Eligibility Validator
# EPIC: EPIC-001 — Data Extraction & Validation
# RESPONSIBILITY: Reserve unit tests for category-rule and search-eligibility acceptance criteria.
# EXPORTS: Unit test stub.
# DEPENDS_ON: intake_canonicalization/category_rules_eligibility_validator.py.
# ACCEPTANCE_CRITERIA:
#   - Required and forbidden category rules are testable from this boundary.
#   - Eligibility-state outputs remain assertable without delivery-layer coupling.
# HUMAN_REVIEW: No.

from intake_canonicalization.category_rules_eligibility_validator import (
	validate_category_eligibility,
	validate_item_against_category_rules,
)


def _matrix() -> dict[str, dict[str, str]]:
	return {
		"book": {
			"name": "R",
			"isbn": "HC",
			"subject": "R",
			"publisher": "O",
			"forbidden_field": "F",
		},
		"apostila": {
			"name": "R",
			"isbn": "F",
		},
	}


def test_ac1_missing_required_routes_to_review_required() -> None:
	item = {"category": "book", "name": "", "subject": "matematica", "isbn": "978123"}

	result = validate_item_against_category_rules(item, _matrix())

	assert result["state"] == "review_required"
	assert "missing_required:name" in result["reasons"]


def test_ac1_missing_required_blocks_eligible_output() -> None:
	items = [{"category": "book", "name": "", "subject": "matematica", "isbn": "978123"}]

	eligible_items_precheck, review_required_items, invalid_items = validate_category_eligibility(items, _matrix())

	assert eligible_items_precheck == []
	assert len(review_required_items) == 1
	assert invalid_items == []


def test_ac2_forbidden_field_present_routes_to_review_required() -> None:
	item = {
		"category": "book",
		"name": "ciencias",
		"subject": "ciencias",
		"isbn": "978123",
		"forbidden_field": "unexpected",
	}

	result = validate_item_against_category_rules(item, _matrix())

	assert result["state"] == "review_required"
	assert "forbidden_present:forbidden_field" in result["reasons"]


def test_ac2_forbidden_violation_blocks_auto_accept() -> None:
	items = [{"category": "apostila", "name": "modulo 1", "isbn": "978123"}]

	eligible_items_precheck, review_required_items, invalid_items = validate_category_eligibility(items, _matrix())

	assert eligible_items_precheck == []
	assert len(review_required_items) == 1
	assert invalid_items == []


def test_ac3_hard_constraint_failures_mark_item_invalid() -> None:
	item = {
		"category": "book",
		"name": "portugues",
		"subject": "portugues",
		"isbn": "",
		"hard_constraint_failures": ["isbn_missing"],
		"confidence": 0.99,
	}

	result = validate_item_against_category_rules(item, _matrix())

	assert result["state"] == "invalid"
	assert "hard_constraint_failure:isbn_missing" in result["reasons"]


def test_ac3_hard_constraint_override_even_when_confidence_high() -> None:
	items = [
		{
			"category": "book",
			"name": "historia",
			"subject": "historia",
			"isbn": "978123",
			"hard_constraints_passed": False,
			"confidence": 0.98,
		}
	]

	eligible_items_precheck, review_required_items, invalid_items = validate_category_eligibility(items, _matrix())

	assert eligible_items_precheck == []
	assert review_required_items == []
	assert len(invalid_items) == 1
	assert invalid_items[0]["eligibility_state"] == "invalid"


def test_eligible_item_goes_to_precheck_output() -> None:
	items = [{"category": "book", "name": "geografia", "subject": "geo", "isbn": "978123"}]

	eligible_items_precheck, review_required_items, invalid_items = validate_category_eligibility(items, _matrix())

	assert len(eligible_items_precheck) == 1
	assert review_required_items == []
	assert invalid_items == []
	assert eligible_items_precheck[0]["eligibility_state"] == "eligible"


def test_unknown_category_routes_to_review_required() -> None:
	items = [{"category": "unknown", "name": "item x"}]

	eligible_items_precheck, review_required_items, invalid_items = validate_category_eligibility(items, _matrix())

	assert eligible_items_precheck == []
	assert len(review_required_items) == 1
	assert invalid_items == []
	assert "unknown_category" in review_required_items[0]["eligibility_reasons"]
