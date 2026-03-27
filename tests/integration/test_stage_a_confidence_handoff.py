from intake_canonicalization.confidence_gating_router import split_by_confidence
from intake_canonicalization.stage_a_ingestion_pipeline import (
	process_stage_a_ingestion,
	to_confidence_handoff_items,
)


def _category_matrix() -> dict[str, dict[str, str]]:
	return {
		"book": {"id": "book"},
		"general supplies": {"id": "general supplies"},
	}


def test_a4_native_stage_a_handoff_preserves_native_source_and_routes() -> None:
	stage_a = process_stage_a_ingestion(
		uploaded_document={
			"filename": "lista.pdf",
			"content_type": "application/pdf",
			"text": "Livro ISBN 9780306406157",
			"file_bytes": (
				b"%PDF-1.4\n"
				b"BT /F1 12 Tf 50 700 Tm (Livro ISBN 9780306406157) Tj ET\n"
				b"BT /F1 12 Tf 50 680 Tm (Linha 2) Tj ET\n"
				b"BT /F1 12 Tf 50 660 Tm (Linha 3) Tj ET\n"
			),
		},
		category_matrix_reference=_category_matrix(),
	)

	handoff_items = to_confidence_handoff_items(stage_a)
	assert len(handoff_items) >= 1
	assert all(item["extraction_source"] == "native_text" for item in handoff_items)

	accepted, review_queue, rejected = split_by_confidence(handoff_items)
	assert len(accepted) + len(review_queue) + len(rejected) == len(handoff_items)


def test_a4_ocr_stage_a_handoff_preserves_ocr_source_and_review_markers() -> None:
	stage_a = process_stage_a_ingestion(
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
			"document_images": [b"ocr page one", b""],
			"source_document_id": "ocr-doc-1",
			"page_numbers": [4, 6],
		},
		category_matrix_reference=_category_matrix(),
	)

	assert stage_a["route_mode"] == "ocr"
	handoff_items = to_confidence_handoff_items(stage_a)
	assert len(handoff_items) >= 1
	assert all(item["extraction_source"] == "ocr" for item in handoff_items)
	assert any(item.get("requires_human_review") for item in handoff_items)

	accepted, review_queue, rejected = split_by_confidence(handoff_items)
	assert len(accepted) + len(review_queue) + len(rejected) == len(handoff_items)
	assert any(item.get("gate_route") == "review" for item in review_queue)


def test_a4_review_required_handoff_is_forced_to_review_queue() -> None:
	stage_a = process_stage_a_ingestion(
		uploaded_document={
			"filename": "unknown.bin",
			"content_type": "application/octet-stream",
			"file_bytes": b"NOT_A_KNOWN_TYPE",
		},
		category_matrix_reference=_category_matrix(),
	)

	assert stage_a["route_mode"] == "review_required"
	handoff_items = to_confidence_handoff_items(stage_a)
	assert len(handoff_items) == 1
	assert handoff_items[0]["requires_human_review"] is True
	assert handoff_items[0]["extraction_source"] == "routing"

	accepted, review_queue, rejected = split_by_confidence(handoff_items)
	assert accepted == []
	assert rejected == []
	assert len(review_queue) == 1
	assert review_queue[0]["gate_route"] == "review"
