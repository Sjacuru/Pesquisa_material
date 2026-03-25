# FILE: intake_canonicalization/duplicate_resolution_coordinator.py
# MODULE: MODULE-001-04 — Duplicate Resolution Coordinator
# EPIC: EPIC-001 — Data Extraction & Validation
# RESPONSIBILITY: Coordinate duplicate detection outcomes and route ambiguous merges to review.
# EXPORTS: Duplicate coordination stub.
# DEPENDS_ON: intake_canonicalization/quantity_unit_normalizer.py.
# ACCEPTANCE_CRITERIA:
#   - Duplicate outcomes remain distinguishable from unresolved merge candidates.
#   - Ambiguous cases are routed to review rather than auto-collapsed.
# HUMAN_REVIEW: Yes — duplicate logic affects canonical list integrity.

from __future__ import annotations

from copy import deepcopy


def _normalized_text(value: object) -> str:
	text = str(value or "").strip().lower()
	return " ".join(text.split())


def _primary_label(item: dict) -> str:
	return _normalized_text(item.get("title") or item.get("name"))


def _normalized_qty_unit(item: dict) -> tuple[str, str]:
	norm = item.get("quantity_normalization") if isinstance(item.get("quantity_normalization"), dict) else {}
	qty = norm.get("normalized_quantity")
	unit = norm.get("normalized_unit")
	return _normalized_text(qty), _normalized_text(unit)


def _exact_duplicate_key(item: dict) -> tuple[str, ...]:
	qty, unit = _normalized_qty_unit(item)
	return (
		_normalized_text(item.get("category")),
		_primary_label(item),
		_normalized_text(item.get("isbn")),
		qty,
		unit,
		_normalized_text(item.get("specifications")),
	)


def _probable_duplicate_key(item: dict) -> tuple[str, ...]:
	return (
		_normalized_text(item.get("category")),
		_primary_label(item),
	)


def resolve_duplicates(
	normalized_items: list[dict],
) -> tuple[list[dict], list[dict]]:
	"""
	Resolve duplicates into:
	  - canonical_item_list
	  - probable_duplicate_queue

	AC1: exact duplicates merge deterministically (first occurrence wins).
	AC2: probable duplicates route to review queue.
	AC3: merge trace is explicit to avoid silent loss.
	"""
	canonical_item_list: list[dict] = []
	probable_duplicate_queue: list[dict] = []

	exact_key_to_canonical_index: dict[tuple[str, ...], int] = {}
	probable_key_to_exact_keys: dict[tuple[str, ...], set[tuple[str, ...]]] = {}

	for position, item in enumerate(normalized_items):
		exact_key = _exact_duplicate_key(item)
		probable_key = _probable_duplicate_key(item)

		if exact_key in exact_key_to_canonical_index:
			canonical_index = exact_key_to_canonical_index[exact_key]
			canonical = canonical_item_list[canonical_index]
			trace = canonical.setdefault("merge_trace", {"source_positions": [canonical.get("source_position", 0)], "merged_count": 1})
			if position not in trace["source_positions"]:
				trace["source_positions"].append(position)
				trace["merged_count"] += 1
			continue

		known_exact_keys_for_probable = probable_key_to_exact_keys.setdefault(probable_key, set())
		if len(known_exact_keys_for_probable) > 0 and exact_key not in known_exact_keys_for_probable:
			queue_item = deepcopy(item)
			queue_item["duplicate_reason"] = "probable_duplicate"
			queue_item["source_position"] = position
			probable_duplicate_queue.append(queue_item)
			continue

		canonical_item = deepcopy(item)
		canonical_item["source_position"] = position
		canonical_item["merge_trace"] = {"source_positions": [position], "merged_count": 1}
		canonical_item_list.append(canonical_item)

		canonical_index = len(canonical_item_list) - 1
		exact_key_to_canonical_index[exact_key] = canonical_index
		known_exact_keys_for_probable.add(exact_key)

	return canonical_item_list, probable_duplicate_queue
