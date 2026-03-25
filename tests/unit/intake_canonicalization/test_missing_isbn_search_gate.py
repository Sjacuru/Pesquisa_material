# FILE: tests/unit/intake_canonicalization/test_missing_isbn_search_gate.py
# MODULE: MODULE-001-07 — Missing-ISBN Search Gate
# EPIC: EPIC-001 — Data Extraction & Validation
# RESPONSIBILITY: Reserve unit tests for missing-ISBN search-gating acceptance criteria.
# EXPORTS: Unit test stub.
# DEPENDS_ON: intake_canonicalization/missing_isbn_search_gate.py.
# ACCEPTANCE_CRITERIA:
#   - Blocked and search-ready states are testable from this unit boundary.
#   - ISBN gating behavior remains explicit for mandatory cases.
# HUMAN_REVIEW: No.

from intake_canonicalization.missing_isbn_search_gate import apply_missing_isbn_search_gate


def test_ac1_book_missing_isbn_is_blocked_from_search() -> None:
	eligible_items_precheck = [{"item_id": "b1", "category": "book", "isbn": ""}]

	search_eligible_items, search_blocked_items = apply_missing_isbn_search_gate(
		eligible_items_precheck=eligible_items_precheck,
		isbn_validated_items=[],
		user_isbn_completion_events=[],
	)

	assert search_eligible_items == []
	assert len(search_blocked_items) == 1
	assert search_blocked_items[0]["search_gate_state"] == "review_required"
	assert search_blocked_items[0]["search_gate_reason"] == "missing_or_invalid_isbn"


def test_ac1_dictionary_invalid_isbn_is_blocked_from_search() -> None:
	eligible_items_precheck = [{"item_id": "d1", "category": "dictionary", "isbn": "ABC-123"}]

	search_eligible_items, search_blocked_items = apply_missing_isbn_search_gate(
		eligible_items_precheck=eligible_items_precheck,
		isbn_validated_items=[],
		user_isbn_completion_events=[],
	)

	assert search_eligible_items == []
	assert len(search_blocked_items) == 1
	assert search_blocked_items[0]["item_id"] == "d1"


def test_ac2_valid_user_completion_unblocks_book_item() -> None:
	eligible_items_precheck = [{"item_id": "b2", "category": "book", "isbn": ""}]
	completion_events = [{"item_id": "b2", "isbn": "978-0-306-40615-7"}]

	search_eligible_items, search_blocked_items = apply_missing_isbn_search_gate(
		eligible_items_precheck=eligible_items_precheck,
		isbn_validated_items=[],
		user_isbn_completion_events=completion_events,
	)

	assert len(search_eligible_items) == 1
	assert search_blocked_items == []
	assert search_eligible_items[0]["search_gate_reason"] == "isbn_completed_valid"
	assert search_eligible_items[0]["isbn"] == "9780306406157"


def test_ac2_prevalidated_isbn_item_is_search_eligible() -> None:
	eligible_items_precheck = [{"item_id": "b3", "category": "book", "isbn": ""}]
	isbn_validated_items = [{"item_id": "b3", "is_valid": True}]

	search_eligible_items, search_blocked_items = apply_missing_isbn_search_gate(
		eligible_items_precheck=eligible_items_precheck,
		isbn_validated_items=isbn_validated_items,
		user_isbn_completion_events=[],
	)

	assert len(search_eligible_items) == 1
	assert search_blocked_items == []
	assert search_eligible_items[0]["search_gate_reason"] == "isbn_valid"


def test_ac3_invalid_completion_keeps_item_review_required() -> None:
	eligible_items_precheck = [{"item_id": "b4", "category": "book", "isbn": ""}]
	completion_events = [{"item_id": "b4", "isbn": "invalid"}]

	search_eligible_items, search_blocked_items = apply_missing_isbn_search_gate(
		eligible_items_precheck=eligible_items_precheck,
		isbn_validated_items=[],
		user_isbn_completion_events=completion_events,
	)

	assert search_eligible_items == []
	assert len(search_blocked_items) == 1
	assert search_blocked_items[0]["search_gate_state"] == "review_required"


def test_non_book_and_non_dictionary_items_are_not_blocked_by_isbn_gate() -> None:
	eligible_items_precheck = [
		{"item_id": "n1", "category": "notebook", "isbn": ""},
		{"item_id": "a1", "category": "apostila", "isbn": ""},
	]

	search_eligible_items, search_blocked_items = apply_missing_isbn_search_gate(
		eligible_items_precheck=eligible_items_precheck,
		isbn_validated_items=[],
		user_isbn_completion_events=[],
	)

	assert len(search_eligible_items) == 2
	assert search_blocked_items == []
	assert all(item["search_gate_reason"] == "isbn_not_required" for item in search_eligible_items)
