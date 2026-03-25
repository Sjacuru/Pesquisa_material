# FILE: tests/unit/intake_canonicalization/test_duplicate_resolution_coordinator.py
# MODULE: MODULE-001-04 — Duplicate Resolution Coordinator
# EPIC: EPIC-001 — Data Extraction & Validation
# RESPONSIBILITY: Reserve unit tests for duplicate coordination acceptance criteria.
# EXPORTS: Unit test stub.
# DEPENDS_ON: intake_canonicalization/duplicate_resolution_coordinator.py.
# ACCEPTANCE_CRITERIA:
#   - Duplicate and ambiguous-merge outcomes remain separately testable.
#   - Review-routing behavior can be asserted without implementation leakage.
# HUMAN_REVIEW: No.

from intake_canonicalization.duplicate_resolution_coordinator import resolve_duplicates


def test_ac1_exact_duplicates_merge_into_single_canonical_item() -> None:
	items = [
		{"category": "book", "title": "Matematica 6", "isbn": "978123", "quantity_normalization": {"normalized_quantity": 1, "normalized_unit": "un"}},
		{"category": "book", "title": "Matematica 6", "isbn": "978123", "quantity_normalization": {"normalized_quantity": 1, "normalized_unit": "un"}},
	]

	canonical_item_list, probable_duplicate_queue = resolve_duplicates(items)

	assert len(canonical_item_list) == 1
	assert len(probable_duplicate_queue) == 0
	assert canonical_item_list[0]["merge_trace"]["merged_count"] == 2


def test_ac1_exact_merge_is_deterministic_first_occurrence_wins() -> None:
	items = [
		{"category": "book", "title": "Alpha", "isbn": "111", "payload": "first", "quantity_normalization": {"normalized_quantity": 1, "normalized_unit": "un"}},
		{"category": "book", "title": "Alpha", "isbn": "111", "payload": "second", "quantity_normalization": {"normalized_quantity": 1, "normalized_unit": "un"}},
	]

	canonical_item_list, _ = resolve_duplicates(items)

	assert canonical_item_list[0]["payload"] == "first"


def test_ac2_probable_duplicates_route_to_review_queue() -> None:
	items = [
		{"category": "book", "title": "Ciencias 7", "isbn": "AAA", "quantity_normalization": {"normalized_quantity": 1, "normalized_unit": "un"}},
		{"category": "book", "title": "Ciencias 7", "isbn": "BBB", "quantity_normalization": {"normalized_quantity": 1, "normalized_unit": "un"}},
	]

	canonical_item_list, probable_duplicate_queue = resolve_duplicates(items)

	assert len(canonical_item_list) == 1
	assert len(probable_duplicate_queue) == 1
	assert probable_duplicate_queue[0]["duplicate_reason"] == "probable_duplicate"


def test_ac2_probable_queue_item_is_not_auto_merged() -> None:
	items = [
		{"category": "book", "title": "Historia", "isbn": "X1", "quantity_normalization": {"normalized_quantity": 1, "normalized_unit": "un"}},
		{"category": "book", "title": "Historia", "isbn": "X2", "quantity_normalization": {"normalized_quantity": 1, "normalized_unit": "un"}},
	]

	canonical_item_list, probable_duplicate_queue = resolve_duplicates(items)

	assert canonical_item_list[0]["isbn"] == "X1"
	assert probable_duplicate_queue[0]["isbn"] == "X2"


def test_ac3_merge_trace_records_all_merged_positions_once() -> None:
	items = [
		{"category": "supply", "name": "lapis", "isbn": "", "quantity_normalization": {"normalized_quantity": 12, "normalized_unit": "un"}},
		{"category": "supply", "name": "lapis", "isbn": "", "quantity_normalization": {"normalized_quantity": 12, "normalized_unit": "un"}},
		{"category": "supply", "name": "lapis", "isbn": "", "quantity_normalization": {"normalized_quantity": 12, "normalized_unit": "un"}},
	]

	canonical_item_list, _ = resolve_duplicates(items)
	trace = canonical_item_list[0]["merge_trace"]

	assert trace["merged_count"] == 3
	assert trace["source_positions"] == [0, 1, 2]


def test_ac3_no_silent_loss_all_items_accounted_for() -> None:
	items = [
		{"category": "book", "title": "Geo", "isbn": "A1", "quantity_normalization": {"normalized_quantity": 1, "normalized_unit": "un"}},
		{"category": "book", "title": "Geo", "isbn": "A1", "quantity_normalization": {"normalized_quantity": 1, "normalized_unit": "un"}},
		{"category": "book", "title": "Geo", "isbn": "A2", "quantity_normalization": {"normalized_quantity": 1, "normalized_unit": "un"}},
		{"category": "book", "title": "Portugues", "isbn": "B1", "quantity_normalization": {"normalized_quantity": 1, "normalized_unit": "un"}},
	]

	canonical_item_list, probable_duplicate_queue = resolve_duplicates(items)

	canonical_sources = sum(
		item["merge_trace"]["merged_count"] for item in canonical_item_list
	)
	queued_sources = len(probable_duplicate_queue)

	assert canonical_sources + queued_sources == len(items)


def test_uses_name_when_title_missing_for_keying() -> None:
	items = [
		{"category": "supply", "name": "borracha branca", "quantity_normalization": {"normalized_quantity": 1, "normalized_unit": "un"}},
		{"category": "supply", "name": "borracha branca", "quantity_normalization": {"normalized_quantity": 1, "normalized_unit": "un"}},
	]

	canonical_item_list, probable_duplicate_queue = resolve_duplicates(items)

	assert len(canonical_item_list) == 1
	assert len(probable_duplicate_queue) == 0
