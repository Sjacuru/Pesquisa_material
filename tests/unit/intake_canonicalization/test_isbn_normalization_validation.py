# FILE: tests/unit/intake_canonicalization/test_isbn_normalization_validation.py
# MODULE: MODULE-001-06 — ISBN Normalization & Validation
# EPIC: EPIC-001 — Data Extraction & Validation
# RESPONSIBILITY: Reserve unit tests for ISBN normalization and validation acceptance criteria.
# EXPORTS: Unit test stub.
# DEPENDS_ON: intake_canonicalization/isbn_normalization_validation.py.
# ACCEPTANCE_CRITERIA:
#   - ISBN normalization outcomes are testable from this unit boundary.
#   - Invalid ISBN states remain explicitly assertable.
# HUMAN_REVIEW: No.

from intake_canonicalization.isbn_normalization_validation import (
	classify_isbn,
	is_exact_isbn_match,
	is_valid_isbn10,
	is_valid_isbn13,
	normalize_isbn,
)


def test_normalize_isbn_removes_separators_spaces_and_punctuation() -> None:
	assert normalize_isbn("978-85 359.0277-3") == "9788535902773"


def test_valid_isbn10_is_accepted() -> None:
	assert is_valid_isbn10("8535902775") is True


def test_valid_isbn13_is_accepted() -> None:
	assert is_valid_isbn13("9780306406157") is True


def test_invalid_length_is_rejected() -> None:
	assert is_valid_isbn10("123") is False
	assert is_valid_isbn13("123") is False


def test_classify_returns_invalid_for_non_isbn_formats() -> None:
	result = classify_isbn("ABC-123")
	assert result["is_valid"] is False
	assert result["format"] == "INVALID"


def test_exact_isbn_match_uses_normalized_equality() -> None:
	assert is_exact_isbn_match("978-85-359-0277-3", "9788535902773") is True


def test_exact_isbn_match_rejects_different_values() -> None:
	assert is_exact_isbn_match("9788535902773", "9788535902774") is False
