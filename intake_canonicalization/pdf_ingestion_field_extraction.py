# FILE: intake_canonicalization/pdf_ingestion_field_extraction.py
# MODULE: MODULE-001-01 — PDF Ingestion & Field Extraction
# EPIC: EPIC-001 — Data Extraction & Validation
# RESPONSIBILITY: Ingest uploaded PDFs and expose extracted item candidates for downstream validation.
# EXPORTS: Extraction service stub.
# DEPENDS_ON: platform/storage.py, platform/observability.py.
# ACCEPTANCE_CRITERIA:
#   - Uploaded PDF inputs are accepted only through the defined intake boundary.
#   - Extracted item candidates are emitted through a deterministic module interface.
# HUMAN_REVIEW: Yes — mixed-document parsing correctness requires expert review.

from __future__ import annotations

import re


def _clamp_confidence(value: float) -> float:
	if value < 0.0:
		return 0.0
	if value > 1.0:
		return 1.0
	return round(value, 2)


def _normalize_space(value: str) -> str:
	return " ".join((value or "").strip().split())


def _decode_pdf_text(uploaded_pdf_document: dict) -> str:
	content_type = str(uploaded_pdf_document.get("content_type") or "").lower()
	if content_type != "application/pdf":
		raise ValueError("uploaded_pdf_document must declare content_type='application/pdf'")

	if isinstance(uploaded_pdf_document.get("text"), str):
		return uploaded_pdf_document["text"]

	if isinstance(uploaded_pdf_document.get("content_bytes"), (bytes, bytearray)):
		return uploaded_pdf_document["content_bytes"].decode("utf-8", errors="ignore")

	raise ValueError("uploaded_pdf_document must contain either 'text' or 'content_bytes'")


def _line_category(line_text: str, category_matrix_reference: dict[str, dict[str, str]]) -> tuple[str, float]:
	lower = line_text.lower()

	if "isbn" in lower or "livro" in lower:
		if "book" in category_matrix_reference:
			return "book", 0.96

	if "dictionary" in lower or "dicionario" in lower:
		if "dictionary" in category_matrix_reference:
			return "dictionary", 0.96

	if "apostila" in lower:
		if "apostila" in category_matrix_reference:
			return "apostila", 0.95

	if "caderno" in lower:
		if "notebook" in category_matrix_reference:
			return "notebook", 0.9

	if "lapis" in lower or "lápis" in lower or "borracha" in lower:
		if "general supplies" in category_matrix_reference:
			return "general supplies", 0.88

	if category_matrix_reference:
		first_category = next(iter(category_matrix_reference.keys()))
		return first_category, 0.75

	return "unknown", 0.7


def _extract_quantity_field(line_text: str) -> tuple[str, float]:
	match = re.search(r"\b(\d+(?:[.,]\d+)?)\s*(un|unidade|unidades|g|kg|ml|l|cm|mm|pacote|caixa)?\b", line_text, re.IGNORECASE)
	if not match:
		return "", 0.0
	value = _normalize_space(match.group(0))
	return value, 0.87


def _extract_isbn_field(line_text: str) -> tuple[str, float]:
	match = re.search(r"(?:isbn\s*[:\-]?\s*)?([0-9Xx\-\s]{10,20})", line_text)
	if not match:
		return "", 0.0
	raw_value = _normalize_space(match.group(1))
	digits_only = re.sub(r"[^0-9Xx]", "", raw_value)
	if len(digits_only) not in (10, 13):
		return "", 0.0
	return raw_value, 0.93


def extract_item_candidates(
	uploaded_pdf_document: dict,
	category_matrix_reference: dict[str, dict[str, str]],
) -> list[dict]:
	"""
	Deterministic extraction boundary for mixed-format PDF input.

	Returns one extracted item candidate per non-empty text line.
	Each extracted field includes a confidence score in [0.00, 1.00].
	"""
	pdf_text = _decode_pdf_text(uploaded_pdf_document)
	lines = [_normalize_space(line) for line in pdf_text.splitlines() if _normalize_space(line)]

	extracted_items: list[dict] = []

	for line_index, line_text in enumerate(lines):
		category_value, category_conf = _line_category(line_text, category_matrix_reference)
		quantity_value, quantity_conf = _extract_quantity_field(line_text)
		isbn_value, isbn_conf = _extract_isbn_field(line_text)
		name_value = line_text
		name_conf = 0.85

		fields = {
			"name": {
				"value": name_value,
				"confidence": _clamp_confidence(name_conf),
			},
			"category": {
				"value": category_value,
				"confidence": _clamp_confidence(category_conf),
			},
			"quantity": {
				"value": quantity_value,
				"confidence": _clamp_confidence(quantity_conf),
			},
			"isbn": {
				"value": isbn_value,
				"confidence": _clamp_confidence(isbn_conf),
			},
		}

		extracted_items.append(
			{
				"line_index": line_index,
				"line_text": line_text,
				"fields": fields,
			}
		)

	return extracted_items
