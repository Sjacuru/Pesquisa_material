import pytest

from intake_canonicalization.stage_a_ingestion_pipeline import process_stage_a_ingestion


def _category_matrix() -> dict[str, dict[str, str]]:
	return {
		"book": {"name": "R", "isbn": "HC", "quantity": "R"},
		"dictionary": {"name": "R", "isbn": "HC", "quantity": "O"},
		"apostila": {"name": "R", "isbn": "F", "quantity": "O"},
		"notebook": {"name": "R", "quantity": "R"},
		"general supplies": {"name": "R", "quantity": "R"},
	}


def test_stage_a_unknown_file_routes_to_review_required() -> None:
	result = process_stage_a_ingestion(
		uploaded_document={
			"filename": "weird.bin",
			"content_type": "application/octet-stream",
			"file_bytes": b"UNKNOWN_CONTENT",
		},
		category_matrix_reference=_category_matrix(),
	)

	assert result["route_mode"] == "review_required"
	assert result["extracted_items"][0]["requires_human_review"] is True


def test_stage_a_pdf_native_path_runs_module_001_01() -> None:
	result = process_stage_a_ingestion(
		uploaded_document={
			"filename": "lista.pdf",
			"content_type": "application/pdf",
			"text": "Livro de Matemática ISBN 978-0-306-40615-7 1 un",
			"file_bytes": b"%PDF" + b"x" * 150000,
		},
		category_matrix_reference=_category_matrix(),
	)

	assert result["route_mode"] == "native_text"
	assert len(result["extracted_items"]) >= 1
	assert "fields" in result["extracted_items"][0]


def test_stage_a_pdf_ocr_path_runs_module_001_13() -> None:
	result = process_stage_a_ingestion(
		uploaded_document={
			"filename": "scan.pdf",
			"content_type": "application/pdf",
			"file_bytes": (
				b"%PDF-1.4\n"
				b"/XObject << /Im1 1 0 R /Im2 2 0 R >>\n"
				b"/Subtype /Image\n"
				b"/Subtype /Image\n"
				b"Do Do Do\n"
			),
			"document_images": [b"image-1" * 10],
			"source_document_id": "doc-scan-1",
		},
		category_matrix_reference=_category_matrix(),
	)

	assert result["route_mode"] == "ocr"
	assert result["detected_type"] == "pdf"
	assert "ocr_output" in result


def test_stage_a_docx_is_routed_and_marked_review_until_extractor_ready() -> None:
	result = process_stage_a_ingestion(
		uploaded_document={
			"filename": "lista.docx",
			"content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
			"file_bytes": b"PK\x03\x04" + b"x" * 100,
		},
		category_matrix_reference=_category_matrix(),
	)

	assert result["detected_type"] == "docx"
	assert result["route_mode"] == "review_required"
	assert "not_yet_implemented" in result["extracted_items"][0]["gate_reason"]


def test_stage_a_can_include_downstream_confidence_validation() -> None:
	result = process_stage_a_ingestion(
		uploaded_document={
			"filename": "lista.pdf",
			"content_type": "application/pdf",
			"text": "Livro ISBN 9780306406157",
			"file_bytes": b"%PDF" + b"x" * 150000,
		},
		category_matrix_reference=_category_matrix(),
		include_downstream_validation=True,
	)

	assert "confidence_handoff_items" in result
	assert "confidence_gating" in result
	assert "counts" in result["confidence_gating"]
	counts = result["confidence_gating"]["counts"]
	assert counts["accepted"] + counts["review_queue"] + counts["rejected"] == len(result["confidence_handoff_items"])
