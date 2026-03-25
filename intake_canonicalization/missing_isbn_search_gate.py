# FILE: intake_canonicalization/missing_isbn_search_gate.py
# MODULE: MODULE-001-07 — Missing-ISBN Search Gate
# EPIC: EPIC-001 — Data Extraction & Validation
# RESPONSIBILITY: Block search when mandatory ISBN information remains unresolved.
# EXPORTS: Search-gating stub for missing ISBN cases.
# DEPENDS_ON: intake_canonicalization/category_rules_eligibility_validator.py, intake_canonicalization/isbn_normalization_validation.py.
# ACCEPTANCE_CRITERIA:
#   - Search blocking remains explicit for mandatory missing-ISBN cases.
#   - Search-ready state remains distinguishable from blocked state.
# HUMAN_REVIEW: No.

from __future__ import annotations

from intake_canonicalization.isbn_normalization_validation import classify_isbn


ISBN_REQUIRED_CATEGORIES = {"book", "dictionary"}


def _normalize_category(value: object) -> str:
	return str(value or "").strip().lower()


def _extract_validated_isbn_by_item(
	isbn_validated_items: list[dict],
) -> dict[object, bool]:
	result: dict[object, bool] = {}
	for item in isbn_validated_items:
		item_id = item.get("item_id")
		if item_id is None:
			continue
		is_valid = bool(item.get("is_valid", False))
		result[item_id] = is_valid
	return result


def _extract_valid_completion_by_item(
	user_isbn_completion_events: list[dict],
) -> dict[object, str]:
	result: dict[object, str] = {}
	for event in user_isbn_completion_events:
		item_id = event.get("item_id")
		if item_id is None:
			continue

		raw_isbn = str(event.get("isbn") or event.get("completed_isbn") or "")
		classification = classify_isbn(raw_isbn)
		if classification["is_valid"]:
			result[item_id] = str(classification["normalized"])
	return result


def apply_missing_isbn_search_gate(
	eligible_items_precheck: list[dict],
	isbn_validated_items: list[dict],
	user_isbn_completion_events: list[dict],
) -> tuple[list[dict], list[dict]]:
	search_eligible_items: list[dict] = []
	search_blocked_items: list[dict] = []

	validated_status_by_item_id = _extract_validated_isbn_by_item(isbn_validated_items)
	valid_completion_by_item_id = _extract_valid_completion_by_item(user_isbn_completion_events)

	for item in eligible_items_precheck:
		category = _normalize_category(item.get("category"))
		item_id = item.get("item_id")

		if category not in ISBN_REQUIRED_CATEGORIES:
			search_eligible_items.append(
				{**item, "search_gate_state": "search_eligible", "search_gate_reason": "isbn_not_required"}
			)
			continue

		raw_isbn = str(item.get("isbn") or "")
		inline_isbn_valid = bool(classify_isbn(raw_isbn)["is_valid"])
		validated_isbn_valid = bool(validated_status_by_item_id.get(item_id, False))

		if inline_isbn_valid or validated_isbn_valid:
			search_eligible_items.append(
				{**item, "search_gate_state": "search_eligible", "search_gate_reason": "isbn_valid"}
			)
			continue

		completed_normalized_isbn = valid_completion_by_item_id.get(item_id)
		if completed_normalized_isbn:
			search_eligible_items.append(
				{
					**item,
					"isbn": completed_normalized_isbn,
					"search_gate_state": "search_eligible",
					"search_gate_reason": "isbn_completed_valid",
				}
			)
			continue

		search_blocked_items.append(
			{
				**item,
				"search_gate_state": "review_required",
				"search_gate_reason": "missing_or_invalid_isbn",
			}
		)

	return search_eligible_items, search_blocked_items
