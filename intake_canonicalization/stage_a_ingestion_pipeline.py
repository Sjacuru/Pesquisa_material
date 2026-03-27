# FILE: intake_canonicalization/stage_a_ingestion_pipeline.py
# MODULE: STAGE-A ORCHESTRATION (Chunk 4 / FR-024)
# RESPONSIBILITY: Orchestrate MODULE-001-11, MODULE-001-12, MODULE-001-13 before confidence gating.

from __future__ import annotations

from intake_canonicalization.confidence_gating_router import split_by_confidence
from intake_canonicalization.file_type_detection_router import detect_file_type
from intake_canonicalization.ocr_extraction_processor import extract_with_ocr
from intake_canonicalization.pdf_coverage_layout_router import route_pdf_coverage
from intake_canonicalization.pdf_ingestion_field_extraction import extract_item_candidates


def _build_review_item(reason: str, detected_type: str = "unknown") -> dict:
	return {
		"line_index": -1,
		"line_text": "",
		"detected_type": detected_type,
		"extraction_source": "routing",
		"gate_route": "review",
		"gate_reason": reason,
		"requires_human_review": True,
		"confidence": 0.0,
	}


def _to_float(value: object, default: float = 0.0) -> float:
	try:
		return float(value)
	except (TypeError, ValueError):
		return default


def _normalize_native_item_for_confidence(item: dict) -> dict:
	fields = dict(item.get("fields") or {})
	category = dict(fields.get("category") or {})
	name = dict(fields.get("name") or {})
	isbn = dict(fields.get("isbn") or {})

	confidence = _to_float(category.get("confidence"), 0.0)
	return {
		"item_id": f"line-{item.get('line_index', -1)}",
		"line_index": int(item.get("line_index", -1)),
		"name": name.get("value") or item.get("line_text") or "",
		"category": category.get("value"),
		"isbn": isbn.get("value"),
		"confidence": confidence,
		"extraction_source": "native_text",
		"requires_human_review": bool(item.get("requires_human_review", False)),
	}


def _normalize_ocr_item_for_confidence(item: dict, fallback_index: int) -> dict:
	confidence = _to_float(item.get("confidence"), 0.0)
	status = str(item.get("status") or "").lower()
	requires_review = status == "review_required"
	page_number = int(item.get("page_number", fallback_index))
	return {
		"item_id": f"ocr-page-{page_number}-{fallback_index}",
		"line_index": page_number,
		"name": item.get("text") or "",
		"category": None,
		"isbn": None,
		"confidence": confidence,
		"extraction_source": item.get("extraction_source") or "ocr",
		"requires_human_review": requires_review,
		"gate_reason": item.get("failure_reason") if requires_review else None,
	}


def _normalize_uploaded_document(uploaded_document: dict) -> dict:
	filename = str(uploaded_document.get("filename") or "")
	content_type = uploaded_document.get("content_type")
	file_bytes = uploaded_document.get("file_bytes")
	if file_bytes is None and isinstance(uploaded_document.get("content_bytes"), (bytes, bytearray)):
		file_bytes = bytes(uploaded_document["content_bytes"])
	if file_bytes is None and isinstance(uploaded_document.get("text"), str):
		file_bytes = uploaded_document["text"].encode("utf-8")
	if file_bytes is None:
		file_bytes = b""
	return {
		"filename": filename,
		"content_type": content_type,
		"file_bytes": file_bytes,
		"text": uploaded_document.get("text"),
	}


def _with_downstream_validation(stage_a_result: dict, include_downstream_validation: bool) -> dict:
	if not include_downstream_validation:
		return stage_a_result

	handoff_items = to_confidence_handoff_items(stage_a_result)
	accepted, review_queue, rejected = split_by_confidence(handoff_items)

	result = dict(stage_a_result)
	result["confidence_handoff_items"] = handoff_items
	result["confidence_gating"] = {
		"accepted": accepted,
		"review_queue": review_queue,
		"rejected": rejected,
		"counts": {
			"accepted": len(accepted),
			"review_queue": len(review_queue),
			"rejected": len(rejected),
		},
	}
	return result


def _with_persistence(
	stage_a_result: dict,
	persist_to_db: bool,
	source_filename: str,
	persistence_notes: str = "",
) -> dict:
	if not persist_to_db:
		return stage_a_result

	from persistence.repositories import persist_stage_a_result

	persistence_result = persist_stage_a_result(
		stage_a_result=stage_a_result,
		source_filename=source_filename,
		notes=persistence_notes,
	)

	result = dict(stage_a_result)
	result["persistence"] = {
		"upload_batch_public_id": str(persistence_result["upload_batch"].public_id),
		"upload_batch_id": persistence_result["upload_batch"].id,
		"status": persistence_result["status"],
		"canonical_item_count": len(persistence_result["canonical_items"]),
	}
	return result


def process_stage_a_ingestion(
	uploaded_document: dict,
	category_matrix_reference: dict[str, dict[str, str]],
	directive_runtime_config: dict | None = None,
	llm_invoke_fn=None,
	audit_log: list[dict] | None = None,
	llm_call_log: list[dict] | None = None,
	include_downstream_validation: bool = False,
	persist_to_db: bool = False,
	persistence_notes: str = "",
) -> dict:
	"""
	Stage A orchestration for Chunk 4 / FR-024.

	Flow:
	1) MODULE-001-11: detect file type
	2) If PDF: MODULE-001-12 coverage router
	3) If OCR route: MODULE-001-13 OCR extraction
	4) If native PDF route: MODULE-001-01 extraction
	"""
	normalized = _normalize_uploaded_document(uploaded_document)
	file_detection = detect_file_type(
		{
			"file_bytes": normalized["file_bytes"],
			"filename": normalized["filename"],
			"content_type": normalized["content_type"],
			"context": {
				"upload_id": str(uploaded_document.get("upload_id") or ""),
				"user_id": uploaded_document.get("user_id"),
			},
		}
	)

	detected_type = file_detection.get("detected_type", "unknown")
	route_target = file_detection.get("route_target", "review_required")

	if detected_type == "unknown" or route_target == "review_required":
		result = _with_downstream_validation({
			"route_mode": "review_required",
			"detected_type": detected_type,
			"routing": file_detection,
			"extracted_items": [
				_build_review_item(
					reason=file_detection.get("error_reason") or "file_type_uncertain",
					detected_type=detected_type,
				)
			],
		}, include_downstream_validation)
		return _with_persistence(result, persist_to_db, normalized["filename"], persistence_notes)

	if detected_type in ("docx", "xlsx"):
		result = _with_downstream_validation({
			"route_mode": "review_required",
			"detected_type": detected_type,
			"routing": file_detection,
			"extracted_items": [
				_build_review_item(
					reason=f"{detected_type}_routing_ready_extraction_not_yet_implemented",
					detected_type=detected_type,
				)
			],
		}, include_downstream_validation)
		return _with_persistence(result, persist_to_db, normalized["filename"], persistence_notes)

	pdf_routing = route_pdf_coverage(
		{
			"pdf_bytes": normalized["file_bytes"],
			"filename": normalized["filename"],
			"context": {
				"upload_id": str(uploaded_document.get("upload_id") or ""),
				"user_id": uploaded_document.get("user_id"),
				"extraction_config": {"ocr_enabled": True, "coverage_threshold": 0.70},
			},
		}
	)

	route_mode = pdf_routing.get("route_mode", "native_text")
	if route_mode == "ocr":
		ocr_out = extract_with_ocr(
			{
				"document_images": list(uploaded_document.get("document_images") or []),
				"source_document_id": str(uploaded_document.get("source_document_id") or normalized["filename"]),
				"context": {
					"upload_id": str(uploaded_document.get("upload_id") or ""),
					"page_numbers": list(uploaded_document.get("page_numbers") or []),
					"ocr_config": {
						"primary_engine": "tesseract",
						"fallback_enabled": False,
					},
				},
			}
		)
		result = _with_downstream_validation({
			"route_mode": "ocr",
			"detected_type": "pdf",
			"routing": file_detection,
			"pdf_routing": pdf_routing,
			"ocr_output": ocr_out,
			"extracted_items": ocr_out.get("extracted_items", []),
		}, include_downstream_validation)
		return _with_persistence(result, persist_to_db, normalized["filename"], persistence_notes)

	pdf_document = {
		"content_type": "application/pdf",
		"filename": normalized["filename"],
	}
	if isinstance(uploaded_document.get("text"), str):
		pdf_document["text"] = uploaded_document["text"]
	else:
		pdf_document["content_bytes"] = normalized["file_bytes"]

	native_items = extract_item_candidates(
		uploaded_pdf_document=pdf_document,
		category_matrix_reference=category_matrix_reference,
		directive_runtime_config=directive_runtime_config,
		llm_invoke_fn=llm_invoke_fn,
		audit_log=audit_log,
		llm_call_log=llm_call_log,
	)
	result = _with_downstream_validation({
		"route_mode": "native_text",
		"detected_type": "pdf",
		"routing": file_detection,
		"pdf_routing": pdf_routing,
		"extracted_items": native_items,
	}, include_downstream_validation)
	return _with_persistence(result, persist_to_db, normalized["filename"], persistence_notes)


def to_confidence_handoff_items(stage_a_result: dict) -> list[dict]:
	"""
	A4 adapter: normalize Stage A output to MODULE-001-02 confidence-gating input.

	Output contract (per item):
	- item_id, name, category, isbn, confidence
	- extraction_source (native_text|ocr|routing)
	- requires_human_review (optional)
	- gate_reason (optional)
	"""
	route_mode = str(stage_a_result.get("route_mode") or "")
	extracted_items = list(stage_a_result.get("extracted_items") or [])

	if route_mode == "native_text":
		return [_normalize_native_item_for_confidence(item) for item in extracted_items]

	if route_mode == "ocr":
		return [_normalize_ocr_item_for_confidence(item, index) for index, item in enumerate(extracted_items)]

	# review_required or fallback route
	normalized: list[dict] = []
	for index, item in enumerate(extracted_items):
		normalized.append(
			{
				"item_id": f"review-{index}",
				"line_index": int(item.get("line_index", -1)),
				"name": item.get("line_text") or "",
				"category": item.get("detected_type"),
				"isbn": None,
				"confidence": _to_float(item.get("confidence"), 0.0),
				"extraction_source": item.get("extraction_source") or "routing",
				"requires_human_review": True,
				"gate_reason": item.get("gate_reason") or "stage_a_review_required",
			}
		)
	return normalized
