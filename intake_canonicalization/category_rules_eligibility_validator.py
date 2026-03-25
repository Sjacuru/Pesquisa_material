# FILE: intake_canonicalization/category_rules_eligibility_validator.py
# MODULE: MODULE-001-05 — Category Rules & Eligibility Validator
# EPIC: EPIC-001 — Data Extraction & Validation
# RESPONSIBILITY: Enforce category required/forbidden rules and determine search eligibility.
# EXPORTS: Category validation and eligibility stub.
# DEPENDS_ON: intake_canonicalization/duplicate_resolution_coordinator.py.
# ACCEPTANCE_CRITERIA:
#   - Required and forbidden field rules are represented explicitly.
#   - Search eligibility is gated by validated category-state boundaries.
# HUMAN_REVIEW: Yes — domain-rule correctness gate.

from __future__ import annotations


def _has_value(value: object) -> bool:
	if value is None:
		return False
	if isinstance(value, str):
		return value.strip() != ""
	if isinstance(value, (list, tuple, set, dict)):
		return len(value) > 0
	return True


def _normalize_category(value: object) -> str:
	return str(value or "").strip().lower()


def validate_item_against_category_rules(
	item: dict,
	category_rules_matrix: dict[str, dict[str, str]],
) -> dict[str, object]:
	category = _normalize_category(item.get("category"))
	rules_for_category = category_rules_matrix.get(category)

	if not rules_for_category:
		return {
			"state": "review_required",
			"reasons": ["unknown_category"],
		}

	reasons: list[str] = []

	for field_name, rule_type in rules_for_category.items():
		rule = str(rule_type or "").strip().upper()
		field_has_value = _has_value(item.get(field_name))

		if rule == "R" and not field_has_value:
			reasons.append(f"missing_required:{field_name}")

		if rule == "F" and field_has_value:
			reasons.append(f"forbidden_present:{field_name}")

	hard_constraint_failures = item.get("hard_constraint_failures")
	if isinstance(hard_constraint_failures, list) and len(hard_constraint_failures) > 0:
		return {
			"state": "invalid",
			"reasons": [f"hard_constraint_failure:{failure}" for failure in hard_constraint_failures],
		}

	if item.get("hard_constraints_passed") is False:
		return {
			"state": "invalid",
			"reasons": ["hard_constraint_failure:generic"],
		}

	if reasons:
		return {
			"state": "review_required",
			"reasons": reasons,
		}

	return {
		"state": "eligible",
		"reasons": [],
	}


def validate_category_eligibility(
	canonical_item_list: list[dict],
	category_rules_matrix: dict[str, dict[str, str]],
) -> tuple[list[dict], list[dict], list[dict]]:
	eligible_items_precheck: list[dict] = []
	review_required_items: list[dict] = []
	invalid_items: list[dict] = []

	for item in canonical_item_list:
		decision = validate_item_against_category_rules(item, category_rules_matrix)
		enriched = {
			**item,
			"eligibility_state": decision["state"],
			"eligibility_reasons": decision["reasons"],
		}

		if decision["state"] == "eligible":
			eligible_items_precheck.append(enriched)
		elif decision["state"] == "review_required":
			review_required_items.append(enriched)
		else:
			invalid_items.append(enriched)

	return eligible_items_precheck, review_required_items, invalid_items
