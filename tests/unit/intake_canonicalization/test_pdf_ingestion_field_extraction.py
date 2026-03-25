# FILE: tests/unit/intake_canonicalization/test_pdf_ingestion_field_extraction.py
# MODULE: MODULE-001-01 — PDF Ingestion & Field Extraction
# EPIC: EPIC-001 — Data Extraction & Validation
# RESPONSIBILITY: Reserve unit tests for extraction intake acceptance criteria.
# EXPORTS: Unit test stub.
# DEPENDS_ON: intake_canonicalization/pdf_ingestion_field_extraction.py.
# ACCEPTANCE_CRITERIA:
#   - Extraction acceptance criteria are testable from this unit boundary.
#   - No live external file-processing dependency is required by the stub.
# HUMAN_REVIEW: No.

import pytest

from intake_canonicalization.pdf_ingestion_field_extraction import extract_item_candidates


def _category_matrix() -> dict[str, dict[str, str]]:
	return {
		"book": {"name": "R", "isbn": "HC", "quantity": "R"},
		"dictionary": {"name": "R", "isbn": "HC", "quantity": "O"},
		"apostila": {"name": "R", "isbn": "F", "quantity": "O"},
		"notebook": {"name": "R", "quantity": "R"},
		"general supplies": {"name": "R", "quantity": "R"},
	}


def test_ac1_valid_pdf_text_extracts_item_lines_with_fields() -> None:
	document = {
		"content_type": "application/pdf",
		"text": "Livro de Matemática ISBN 978-0-306-40615-7 1 un\nCaderno universitário 2 un",
	}

	items = extract_item_candidates(document, _category_matrix())

	assert len(items) == 2
	assert "fields" in items[0]
	assert set(items[0]["fields"].keys()) == {"name", "category", "quantity", "isbn"}


def test_ac1_valid_pdf_bytes_extracts_items_without_external_dependency() -> None:
	document = {
		"content_type": "application/pdf",
		"content_bytes": b"Apostila de Historia 1 un\nLapis preto 12 un",
	}

	items = extract_item_candidates(document, _category_matrix())

	assert len(items) == 2
	assert items[0]["line_index"] == 0
	assert items[1]["line_index"] == 1


def test_ac1_non_pdf_content_type_is_rejected() -> None:
	document = {
		"content_type": "text/plain",
		"text": "Livro de matemática",
	}

	with pytest.raises(ValueError):
		extract_item_candidates(document, _category_matrix())


def test_ac1_missing_text_and_bytes_is_rejected() -> None:
	document = {"content_type": "application/pdf"}

	with pytest.raises(ValueError):
		extract_item_candidates(document, _category_matrix())


def test_ac2_every_extracted_field_includes_confidence_in_valid_range() -> None:
	document = {
		"content_type": "application/pdf",
		"text": "Dictionary English ISBN 9780306406157 1 un\nBorracha branca 3 un",
	}

	items = extract_item_candidates(document, _category_matrix())

	for item in items:
		for field_payload in item["fields"].values():
			assert "confidence" in field_payload
			confidence = field_payload["confidence"]
			assert 0.0 <= confidence <= 1.0


def test_ac2_output_is_deterministic_for_same_input() -> None:
	document = {
		"content_type": "application/pdf",
		"text": "Livro de Ciências ISBN 9780306406157 1 un\nLapis 10 un",
	}

	first = extract_item_candidates(document, _category_matrix())
	second = extract_item_candidates(document, _category_matrix())

	assert first == second


def test_ac2_applicable_category_field_is_present_per_item() -> None:
	document = {
		"content_type": "application/pdf",
		"text": "Apostila de Geografia 1 un\nCaderno brochura 2 un",
	}

	items = extract_item_candidates(document, _category_matrix())

	for item in items:
		assert item["fields"]["category"]["value"] != ""
		assert item["fields"]["category"]["confidence"] >= 0.0
