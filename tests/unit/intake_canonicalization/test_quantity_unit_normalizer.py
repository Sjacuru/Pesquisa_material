# FILE: tests/unit/intake_canonicalization/test_quantity_unit_normalizer.py
# MODULE: MODULE-001-03 — Quantity & Unit Normalizer
# EPIC: EPIC-001 — Data Extraction & Validation
# RESPONSIBILITY: Reserve unit tests for quantity and unit normalization acceptance criteria.
# EXPORTS: Unit test stub.
# DEPENDS_ON: intake_canonicalization/quantity_unit_normalizer.py.
# ACCEPTANCE_CRITERIA:
#   - Canonical unit normalization remains testable from this unit boundary.
#   - Ambiguous normalization cases can be asserted distinctly.
# HUMAN_REVIEW: No.

import pytest

from intake_canonicalization.quantity_unit_normalizer import (
	CANONICAL_UNITS,
	normalize_batch,
	normalize_quantity_unit,
)


# ---------------------------------------------------------------------------
# AC1 — Recognized units normalize to the canonical set only
# ---------------------------------------------------------------------------


def test_ac1_integer_with_canonical_unit_un() -> None:
	result = normalize_quantity_unit("2 un")
	assert result["status"] == "normalized"
	assert result["normalized_unit"] == "un"
	assert result["normalized_unit"] in CANONICAL_UNITS


def test_ac1_alias_unidade_normalizes_to_un() -> None:
	result = normalize_quantity_unit("3 unidades")
	assert result["status"] == "normalized"
	assert result["normalized_unit"] == "un"


def test_ac1_alias_pct_normalizes_to_pacote() -> None:
	result = normalize_quantity_unit("1 pct")
	assert result["status"] == "normalized"
	assert result["normalized_unit"] == "pacote"


def test_ac1_alias_cx_normalizes_to_caixa() -> None:
	result = normalize_quantity_unit("2 cx")
	assert result["status"] == "normalized"
	assert result["normalized_unit"] == "caixa"


def test_ac1_compact_form_500g_normalizes_to_g() -> None:
	result = normalize_quantity_unit("500g")
	assert result["status"] == "normalized"
	assert result["normalized_unit"] == "g"


def test_ac1_kg_normalizes_to_canonical_kg() -> None:
	result = normalize_quantity_unit("1 kg")
	assert result["status"] == "normalized"
	assert result["normalized_unit"] == "kg"


def test_ac1_ml_normalizes_to_canonical_ml() -> None:
	result = normalize_quantity_unit("250 ml")
	assert result["status"] == "normalized"
	assert result["normalized_unit"] == "ml"


def test_ac1_liter_alias_normalizes_to_L() -> None:
	result = normalize_quantity_unit("2 litros")
	assert result["status"] == "normalized"
	assert result["normalized_unit"] == "L"


def test_ac1_lowercase_l_normalizes_to_canonical_L() -> None:
	result = normalize_quantity_unit("1 l")
	assert result["status"] == "normalized"
	assert result["normalized_unit"] == "L"


def test_ac1_cm_normalizes_to_canonical_cm() -> None:
	result = normalize_quantity_unit("30 cm")
	assert result["status"] == "normalized"
	assert result["normalized_unit"] == "cm"


def test_ac1_mm_normalizes_to_canonical_mm() -> None:
	result = normalize_quantity_unit("10 mm")
	assert result["status"] == "normalized"
	assert result["normalized_unit"] == "mm"


def test_ac1_normalized_unit_is_always_in_canonical_set() -> None:
	"""All recognized inputs must resolve to a unit inside CANONICAL_UNITS."""
	samples = [
		"1 un", "1 unidade", "2 pacote", "1 caixa",
		"100 g", "2 kg", "500 ml", "1 L", "30 cm", "5 mm",
	]
	for sample in samples:
		result = normalize_quantity_unit(sample)
		assert result["status"] == "normalized", f"Expected normalized for '{sample}'"
		assert result["normalized_unit"] in CANONICAL_UNITS, (
			f"Unit '{result['normalized_unit']}' not in CANONICAL_UNITS for '{sample}'"
		)


def test_ac1_decimal_quantity_with_comma_separator() -> None:
	"""Brazilian decimal comma (1,5 kg) should parse correctly."""
	result = normalize_quantity_unit("1,5 kg")
	assert result["status"] == "normalized"
	assert result["normalized_quantity"] == 1.5
	assert result["normalized_unit"] == "kg"


# ---------------------------------------------------------------------------
# AC2 — Ambiguous / unsupported conversions route to review, not auto-normalized
# ---------------------------------------------------------------------------


def test_ac2_unrecognized_unit_routes_to_review() -> None:
	result = normalize_quantity_unit("3 xyz")
	assert result["status"] == "review_required"
	assert result["normalized_unit"] is None
	assert result["normalized_quantity"] is None


def test_ac2_bare_number_without_unit_routes_to_review() -> None:
	"""A number with no unit is ambiguous and must not be auto-normalized."""
	result = normalize_quantity_unit("5")
	assert result["status"] == "review_required"
	assert result["normalized_unit"] is None


def test_ac2_non_parseable_string_routes_to_review() -> None:
	result = normalize_quantity_unit("dois quilos")
	assert result["status"] == "review_required"
	assert result["normalized_unit"] is None


def test_ac2_empty_string_routes_to_review() -> None:
	result = normalize_quantity_unit("")
	assert result["status"] == "review_required"


def test_ac2_batch_separates_review_items_correctly() -> None:
	items = [
		{"name": "caderno", "quantity": "2 un"},
		{"name": "lapis", "quantity": "12 xyz"},   # unrecognized unit
		{"name": "borracha", "quantity": "5"},       # ambiguous — no unit
	]
	normalized, review = normalize_batch(items)
	assert len(normalized) == 1
	assert len(review) == 2
	assert normalized[0]["name"] == "caderno"


def test_ac2_review_items_are_not_auto_normalized_in_batch() -> None:
	items = [{"name": "item_a", "quantity": "3 unknown_unit"}]
	normalized, review = normalize_batch(items)
	assert len(normalized) == 0
	assert review[0]["quantity_normalization"]["normalized_unit"] is None


# ---------------------------------------------------------------------------
# AC3 — Both original and normalized values are preserved for traceability
# ---------------------------------------------------------------------------


def test_ac3_raw_value_preserved_on_success() -> None:
	result = normalize_quantity_unit("2 unidades")
	assert result["raw"] == "2 unidades"
	assert result["raw_unit"] == "unidades"
	assert result["raw_quantity"] == 2.0


def test_ac3_raw_value_preserved_on_review() -> None:
	result = normalize_quantity_unit("3 xyz")
	assert result["raw"] == "3 xyz"
	assert result["raw_quantity"] == 3.0
	assert result["raw_unit"] == "xyz"


def test_ac3_batch_preserves_original_item_fields() -> None:
	items = [{"name": "caderno", "quantity": "2 un", "subject": "matematica"}]
	normalized, _ = normalize_batch(items)
	item = normalized[0]
	assert item["name"] == "caderno"
	assert item["subject"] == "matematica"
	assert item["quantity"] == "2 un"


def test_ac3_batch_adds_normalization_result_key() -> None:
	items = [{"name": "cola", "quantity": "1 un"}]
	normalized, _ = normalize_batch(items)
	assert "quantity_normalization" in normalized[0]
	norm = normalized[0]["quantity_normalization"]
	assert norm["raw"] == "1 un"
	assert norm["normalized_unit"] == "un"
	assert norm["normalized_quantity"] == 1.0
