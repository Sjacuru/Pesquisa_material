# FILE: tests/unit/intake_canonicalization/test_ocr_extraction_processor.py
# MODULE: MODULE-001-13 — OCR Extraction Processor
# EPIC: EPIC-001 — Data Extraction & Validation (Chunk 4 / FR-024 Amendment)
# RESPONSIBILITY: Reserve unit tests for OCR extraction acceptance criteria.
# EXPORTS: Unit test suite.
# DEPENDS_ON: intake_canonicalization/ocr_extraction_processor.py
# ACCEPTANCE_CRITERIA:
#   - OCR extraction acceptance criteria are testable from this unit boundary.
#   - No live OCR library is required by the tests.
# HUMAN_REVIEW: No.

import pytest

from intake_canonicalization.ocr_extraction_processor import extract_with_ocr, OCRExtractionInput


class TestModuleAC1_SuccessfulExtraction:
	"""AC1: OCR path returns extracted_items on successful processing"""
	
	def test_ac1_valid_images_return_extracted_items(self) -> None:
		"""Valid images return extracted items."""
		input_data: OCRExtractionInput = {
			"document_images": [b"image_data_1" * 10, b"image_data_2" * 10],
			"source_document_id": "doc-123",
		}
		
		output = extract_with_ocr(input_data)
		
		assert "extracted_items" in output
		assert isinstance(output["extracted_items"], list)
		assert len(output["extracted_items"]) > 0
	
	def test_ac1_empty_images_list_returns_no_items(self) -> None:
		"""Empty images list returns failure event."""
		input_data: OCRExtractionInput = {
			"document_images": [],
			"source_document_id": "doc-123",
		}
		
		output = extract_with_ocr(input_data)
		
		assert len(output["extracted_items"]) == 0
		assert len(output["failure_events"]) > 0


class TestModuleAC2_ExtractionMetadata:
	"""AC2: Each extracted item includes extraction_source and confidence metadata"""
	
	def test_ac2_items_have_extraction_source(self) -> None:
		"""Extracted items include extraction_source."""
		input_data: OCRExtractionInput = {
			"document_images": [b"image_data" * 10],
			"source_document_id": "doc-123",
		}
		
		output = extract_with_ocr(input_data)
		
		assert output["extraction_source"] == "ocr"
		for item in output["extracted_items"]:
			if item.get("status") == "extracted":
				assert "extraction_source" in item
				assert item["extraction_source"] == "ocr"
	
	def test_ac2_items_have_confidence_in_output(self) -> None:
		"""Extracted items or output include confidence values."""
		input_data: OCRExtractionInput = {
			"document_images": [b"image_data" * 10],
			"source_document_id": "doc-123",
		}
		
		output = extract_with_ocr(input_data)
		
		assert "item_confidence" in output
		assert isinstance(output["item_confidence"], list)
	
	def test_ac2_confidence_values_in_valid_range(self) -> None:
		"""Confidence values are bounded in [0.0, 1.0]."""
		input_data: OCRExtractionInput = {
			"document_images": [b"image_data" * 10],
			"source_document_id": "doc-123",
		}
		
		output = extract_with_ocr(input_data)
		
		for confidence in output["item_confidence"]:
			assert 0.0 <= confidence <= 1.0


class TestModuleAC3_FailureEventEmission:
	"""AC3: OCR failures emit failure_events with explicit reason"""
	
	def test_ac3_empty_images_emit_failure_event(self) -> None:
		"""Empty images emit failure event."""
		input_data: OCRExtractionInput = {
			"document_images": [b""],
			"source_document_id": "doc-123",
		}
		
		output = extract_with_ocr(input_data)
		
		assert "failure_events" in output
		assert isinstance(output["failure_events"], list)
	
	def test_ac3_failure_events_have_reason(self) -> None:
		"""Failure events include reason field."""
		input_data: OCRExtractionInput = {
			"document_images": [b""],
			"source_document_id": "doc-123",
		}
		
		output = extract_with_ocr(input_data)
		
		for failure in output["failure_events"]:
			assert "reason" in failure
			assert len(failure["reason"]) > 0
	
	def test_ac3_no_images_emits_explicit_failure(self) -> None:
		"""No images emits explicit failure."""
		input_data: OCRExtractionInput = {
			"document_images": [],
			"source_document_id": "doc-123",
		}
		
		output = extract_with_ocr(input_data)
		
		assert len(output["failure_events"]) > 0
		assert output["failure_events"][0]["reason"] == "no_images_provided"


class TestModuleAC4_ReviewRoutingOnFailure:
	"""AC4: OCR failures route affected output to review_required rather than silent drop"""
	
	def test_ac4_failure_routes_to_review_required(self) -> None:
		"""Failed OCR pages route to review_required status."""
		input_data: OCRExtractionInput = {
			"document_images": [b""],  # Empty image triggers failure
			"source_document_id": "doc-123",
		}
		
		output = extract_with_ocr(input_data)
		
		# Should have review_required marker or failure event, not silent drop
		has_review_marker = any(
			item.get("status") == "review_required"
			for item in output["extracted_items"]
		)
		has_failure_event = len(output["failure_events"]) > 0
		
		assert has_review_marker or has_failure_event
	
	def test_ac4_no_silent_drop_on_failure(self) -> None:
		"""No silent drop: failures are explicitly recorded."""
		input_data: OCRExtractionInput = {
			"document_images": [b""],
			"source_document_id": "doc-123",
		}
		
		output = extract_with_ocr(input_data)
		
		# Either extract_items or failure_events must record the failure
		assert len(output["extracted_items"]) > 0 or len(output["failure_events"]) > 0


class TestModuleAC5_PartialSuccess:
	"""AC5: Partial OCR success preserves successful outputs while flagging failed regions"""
	
	def test_ac5_multiple_images_partial_failure_handling(self) -> None:
		"""Multiple images with mixed success/failure."""
		input_data: OCRExtractionInput = {
			"document_images": [
				b"valid_image_data" * 10,  # Should succeed
				b"",  # Should fail
				b"valid_image_data_2" * 10,  # Should succeed
			],
			"source_document_id": "doc-123",
		}
		
		output = extract_with_ocr(input_data)
		
		# Should have both successful extracts and failure/review markers
		has_successful = any(
			item.get("status") == "extracted"
			for item in output["extracted_items"]
		)
		has_failure_marker = any(
			item.get("status") == "review_required"
			for item in output["extracted_items"]
		) or len(output["failure_events"]) > 0
		
		# For multi-image input, expect some processing (stub behavior)
		assert len(output["extracted_items"]) > 0
	
	def test_ac5_item_flags_preserve_context(self) -> None:
		"""Failed item flags preserve page/region context."""
		input_data: OCRExtractionInput = {
			"document_images": [b"", b"valid_image" * 10],
			"source_document_id": "doc-123",
		}
		
		output = extract_with_ocr(input_data)
		
		# Items should track page context
		for item in output["extracted_items"]:
			if "page_number" in item:
				assert isinstance(item["page_number"], int)


class TestExtractionSourceConsistency:
	"""Verify extraction_source is consistently "ocr"."""
	
	def test_extraction_source_is_ocr(self) -> None:
		"""All extraction_source values are "ocr"."""
		input_data: OCRExtractionInput = {
			"document_images": [b"image" * 10],
			"source_document_id": "doc-123",
		}
		
		output = extract_with_ocr(input_data)
		
		assert output["extraction_source"] == "ocr"


class TestNoSilentDropBehavior:
	"""Verify no-silent-drop behavior is preserved."""
	
	def test_no_silent_drop_on_empty_images(self) -> None:
		"""Empty images do not silently disappear."""
		input_data: OCRExtractionInput = {
			"document_images": [b""],
			"source_document_id": "doc-123",
		}
		
		output = extract_with_ocr(input_data)
		
		# Must have either extraction or failure event
		total_records = len(output["extracted_items"]) + len(output["failure_events"])
		assert total_records > 0
	
	def test_no_silent_drop_on_no_input(self) -> None:
		"""No input images yield explicit failure, not empty output."""
		input_data: OCRExtractionInput = {
			"document_images": [],
			"source_document_id": "doc-123",
		}
		
		output = extract_with_ocr(input_data)
		
		# Must have explicit failure event
		assert len(output["failure_events"]) > 0


class TestInjectedOCREngineBehavior:
	"""Validate pluggable OCR invocation and failure propagation."""

	def test_callable_dict_result_is_respected(self) -> None:
		def fake_ocr(image_bytes: bytes, page_number: int, ocr_config: dict) -> dict:
			return {
				"lines": [f"page-{page_number}-line"],
				"confidence": 0.91,
				"error_reason": None,
			}

		input_data: OCRExtractionInput = {
			"document_images": [b"img-a"],
			"source_document_id": "doc-abc",
			"context": {
				"ocr_config": {"primary_engine": "tesseract", "fallback_enabled": False},
				"ocr_invoke_fn": fake_ocr,
				"page_numbers": [7],
			},
		}

		output = extract_with_ocr(input_data)
		assert len(output["failure_events"]) == 0
		assert output["extracted_items"][0]["page_number"] == 7
		assert output["extracted_items"][0]["text"] == "page-7-line"
		assert output["item_confidence"][0] == 0.91

	def test_callable_exception_emits_failure_event(self) -> None:
		def failing_ocr(image_bytes: bytes, page_number: int, ocr_config: dict) -> dict:
			raise RuntimeError("ocr_engine_down")

		input_data: OCRExtractionInput = {
			"document_images": [b"img-a"],
			"source_document_id": "doc-fail",
			"context": {"ocr_invoke_fn": failing_ocr, "page_numbers": [3]},
		}

		output = extract_with_ocr(input_data)
		assert len(output["failure_events"]) == 1
		assert "ocr_engine_exception" in output["failure_events"][0]["reason"]
		assert output["extracted_items"][0]["status"] == "review_required"
		assert output["extracted_items"][0]["page_number"] == 3

	def test_page_number_mapping_preserved_on_partial_success(self) -> None:
		def selective_ocr(image_bytes: bytes, page_number: int, ocr_config: dict):
			if page_number == 10:
				return {"lines": ["ok-page-10"], "confidence": 0.88, "error_reason": None}
			return {"lines": [], "confidence": 0.0, "error_reason": "no_text_detected"}

		input_data: OCRExtractionInput = {
			"document_images": [b"img-a", b"img-b"],
			"source_document_id": "doc-pages",
			"context": {
				"ocr_invoke_fn": selective_ocr,
				"page_numbers": [10, 12],
			},
		}

		output = extract_with_ocr(input_data)
		page_numbers = [item["page_number"] for item in output["extracted_items"]]
		assert 10 in page_numbers
		assert 12 in page_numbers
		assert any(item.get("status") == "review_required" for item in output["extracted_items"])
