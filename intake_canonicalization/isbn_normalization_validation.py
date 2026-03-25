# FILE: intake_canonicalization/isbn_normalization_validation.py
# MODULE: MODULE-001-06 — ISBN Normalization & Validation
# EPIC: EPIC-001 — Data Extraction & Validation
# RESPONSIBILITY: Normalize ISBN identifiers and validate their structural readiness for search.
# EXPORTS: ISBN normalization and validation stub.
# DEPENDS_ON: intake_canonicalization/quantity_unit_normalizer.py.
# ACCEPTANCE_CRITERIA:
#   - ISBN normalization is separated from category-rule validation.
#   - Invalid ISBN states remain explicit for downstream handling.
# HUMAN_REVIEW: No.

from __future__ import annotations

import re


def normalize_isbn(raw_value: str) -> str:
	cleaned = re.sub(r"[^0-9Xx]", "", (raw_value or ""))
	return cleaned.upper()


def is_valid_isbn10(value: str) -> bool:
	if len(value) != 10:
		return False
	if not re.fullmatch(r"\d{9}[\dX]", value):
		return False

	total = 0
	for index, character in enumerate(value):
		digit = 10 if character == "X" else int(character)
		total += digit * (10 - index)

	return total % 11 == 0


def is_valid_isbn13(value: str) -> bool:
	if len(value) != 13:
		return False
	if not value.isdigit():
		return False

	total = 0
	for index, character in enumerate(value[:12]):
		weight = 1 if index % 2 == 0 else 3
		total += int(character) * weight

	expected_check_digit = (10 - (total % 10)) % 10
	return expected_check_digit == int(value[12])


def classify_isbn(raw_value: str) -> dict[str, str | bool]:
	normalized = normalize_isbn(raw_value)

	if is_valid_isbn10(normalized):
		return {
			"raw": raw_value,
			"normalized": normalized,
			"is_valid": True,
			"format": "ISBN-10",
		}

	if is_valid_isbn13(normalized):
		return {
			"raw": raw_value,
			"normalized": normalized,
			"is_valid": True,
			"format": "ISBN-13",
		}

	return {
		"raw": raw_value,
		"normalized": normalized,
		"is_valid": False,
		"format": "INVALID",
	}


def is_exact_isbn_match(left: str, right: str) -> bool:
	left_normalized = normalize_isbn(left)
	right_normalized = normalize_isbn(right)
	return left_normalized == right_normalized
