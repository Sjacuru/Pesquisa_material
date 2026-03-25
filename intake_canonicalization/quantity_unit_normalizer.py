# FILE: intake_canonicalization/quantity_unit_normalizer.py
# MODULE: MODULE-001-03 — Quantity & Unit Normalizer
# EPIC: EPIC-001 — Data Extraction & Validation
# RESPONSIBILITY: Normalize extracted quantities and units into canonical forms.
# EXPORTS: Quantity and unit normalization stub.
# DEPENDS_ON: intake_canonicalization/confidence_gating_router.py.
# ACCEPTANCE_CRITERIA:
#   - Canonical quantity/unit outputs are separated from raw extracted values.
#   - Ambiguous normalization cases remain representable for review.
# HUMAN_REVIEW: No.

from __future__ import annotations

import re

# Canonical unit set as defined in PRD Decision Sheet.
CANONICAL_UNITS: frozenset[str] = frozenset(
	{"un", "pacote", "caixa", "g", "kg", "ml", "L", "cm", "mm"}
)

# Maps lowercase input unit strings to their canonical form.
_UNIT_ALIASES: dict[str, str] = {
	# un (unit / unidade)
	"un": "un",
	"unidade": "un",
	"unidades": "un",
	"und": "un",
	"unid": "un",
	"pc": "un",
	"pcs": "un",
	"piece": "un",
	"unit": "un",
	"units": "un",
	# pacote (pack)
	"pacote": "pacote",
	"pct": "pacote",
	"pack": "pacote",
	# caixa (box)
	"caixa": "caixa",
	"cx": "caixa",
	"cxa": "caixa",
	"box": "caixa",
	# g (gram)
	"g": "g",
	"grama": "g",
	"gramas": "g",
	"gram": "g",
	"grams": "g",
	# kg (kilogram)
	"kg": "kg",
	"quilograma": "kg",
	"quilogramas": "kg",
	"kilo": "kg",
	"kilogram": "kg",
	"kilograms": "kg",
	# ml (milliliter)
	"ml": "ml",
	"mililitro": "ml",
	"mililitros": "ml",
	"milliliter": "ml",
	"milliliters": "ml",
	# L (liter) — lowercase "l" maps to canonical "L"
	"l": "L",
	"litro": "L",
	"litros": "L",
	"liter": "L",
	"liters": "L",
	"lt": "L",
	# cm (centimeter)
	"cm": "cm",
	"centimetro": "cm",
	"centimetros": "cm",
	"centimeter": "cm",
	"centimeters": "cm",
	# mm (millimeter)
	"mm": "mm",
	"milimetro": "mm",
	"milimetros": "mm",
	"millimeter": "mm",
	"millimeters": "mm",
}

# Matches an optional leading number (integer or decimal with . or ,) followed by
# an optional unit string composed of Latin letters including accented characters.
_QTY_UNIT_PATTERN = re.compile(
	r"^\s*([\d]+(?:[.,]\d+)?)\s*([a-zA-Z\u00C0-\u00FF]*)\s*$"
)


def normalize_quantity_unit(raw_value: str) -> dict[str, object]:
	"""
	Normalize a single raw quantity+unit string to its canonical form.

	Returns a dict with keys:
	  raw              — original input (AC3: traceability)
	  raw_quantity     — parsed numeric value or None if unparseable
	  raw_unit         — parsed unit string or None if absent/unparseable
	  normalized_quantity — canonical quantity or None when review is required
	  normalized_unit     — canonical unit string or None when review is required
	  status           — "normalized" or "review_required" (AC2)
	"""
	stripped = (raw_value or "").strip()
	match = _QTY_UNIT_PATTERN.match(stripped)

	if not match:
		return {
			"raw": raw_value,
			"raw_quantity": None,
			"raw_unit": None,
			"normalized_quantity": None,
			"normalized_unit": None,
			"status": "review_required",
		}

	qty_str = match.group(1).replace(",", ".")
	raw_quantity = float(qty_str)
	raw_unit_str = match.group(2).strip() or None

	if raw_unit_str is None:
		# No unit present — ambiguous, route to review (AC2).
		return {
			"raw": raw_value,
			"raw_quantity": raw_quantity,
			"raw_unit": None,
			"normalized_quantity": None,
			"normalized_unit": None,
			"status": "review_required",
		}

	canonical_unit = _UNIT_ALIASES.get(raw_unit_str.lower())

	if canonical_unit is None:
		# Unrecognized unit — route to review without auto-normalizing (AC2).
		return {
			"raw": raw_value,
			"raw_quantity": raw_quantity,
			"raw_unit": raw_unit_str,
			"normalized_quantity": None,
			"normalized_unit": None,
			"status": "review_required",
		}

	# AC1: recognized unit → canonical form. AC3: raw values preserved.
	return {
		"raw": raw_value,
		"raw_quantity": raw_quantity,
		"raw_unit": raw_unit_str,
		"normalized_quantity": raw_quantity,
		"normalized_unit": canonical_unit,
		"status": "normalized",
	}


def normalize_batch(
	accepted_fields: list[dict],
) -> tuple[list[dict], list[dict]]:
	"""
	Normalize the 'quantity' field of each item in accepted_fields.

	Returns (normalized_items, normalization_review_items):
	  normalized_items          — items whose quantity resolved to a canonical unit
	  normalization_review_items — items that could not be auto-normalized (AC2)

	Each returned item carries an added 'quantity_normalization' key with the
	full normalization result dict for traceability (AC3).
	"""
	normalized_items: list[dict] = []
	normalization_review_items: list[dict] = []

	for item in accepted_fields:
		raw_qty_value = str(item.get("quantity", ""))
		result = normalize_quantity_unit(raw_qty_value)
		enriched = {**item, "quantity_normalization": result}

		if result["status"] == "normalized":
			normalized_items.append(enriched)
		else:
			normalization_review_items.append(enriched)

	return normalized_items, normalization_review_items
