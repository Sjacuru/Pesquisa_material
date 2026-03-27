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
	assert set(items[0]["fields"].keys()) == {
		"name",
		"category",
		"quantity",
		"isbn",
		"school_exclusive",
		"required_sellers",
		"preferred_sellers",
		"exclusive_source",
	}


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

	assert len(first) == len(second)
	for first_item, second_item in zip(first, second):
		assert first_item["line_index"] == second_item["line_index"]
		assert first_item["line_text"] == second_item["line_text"]
		assert first_item["fields"] == second_item["fields"]
		assert first_item["decision_source"] == second_item["decision_source"] == "deterministic"
		assert first_item["directive_confidence"] == second_item["directive_confidence"]
		assert first_item["directive_resolved"] == second_item["directive_resolved"]


def test_stage_a_contract_fields_are_present() -> None:
	document = {
		"content_type": "application/pdf",
		"text": "Uniforme escolar somente Loja Alpha",
	}

	items = extract_item_candidates(document, _category_matrix())
	item = items[0]

	assert item["decision_source"] == "deterministic"
	assert isinstance(item["directive_confidence"], float)
	assert 0.0 <= item["directive_confidence"] <= 1.0
	assert isinstance(item["directive_resolved"], bool)
	assert item["requires_human_review"] is None
	assert item["llm_rationale"] is None
	assert item["llm_model_id"] is None
	assert item["directive_extraction_timestamp"] is not None
	assert isinstance(item["document_notation_rules"], dict)


def test_ac2_applicable_category_field_is_present_per_item() -> None:
	document = {
		"content_type": "application/pdf",
		"text": "Apostila de Geografia 1 un\nCaderno brochura 2 un",
	}

	items = extract_item_candidates(document, _category_matrix())

	for item in items:
		assert item["fields"]["category"]["value"] != ""
		assert item["fields"]["category"]["confidence"] >= 0.0


def test_ac1_exclusivity_defaults_when_no_marker_exists() -> None:
	document = {
		"content_type": "application/pdf",
		"text": "Caderno universitario 2 un",
	}

	items = extract_item_candidates(document, _category_matrix())
	fields = items[0]["fields"]

	assert fields["school_exclusive"]["value"] is False
	assert fields["required_sellers"]["value"] == []
	assert fields["preferred_sellers"]["value"] == []


def test_ac1_exclusivity_and_preferences_are_extracted_from_line_notation() -> None:
	document = {
		"content_type": "application/pdf",
		"text": "Uniforme escolar somente Loja Alpha preferencial: Loja Beta, Loja Gama",
	}

	items = extract_item_candidates(document, _category_matrix())
	fields = items[0]["fields"]

	assert fields["school_exclusive"]["value"] is True
	assert fields["required_sellers"]["value"] == ["Loja Alpha"]
	assert fields["preferred_sellers"]["value"] == ["Loja Beta", "Loja Gama"]
	assert fields["exclusive_source"]["value"] == "document_notation"
