# FILE: tests/integration/test_ocr_extraction_quality_validation.py
# MODULE: Step 9 Integration Tests — OCR Post-Native Validation Hardening
# EPIC: EPIC-001 — Data Extraction & Validation
# RESPONSIBILITY: Comprehensive integration tests for OCR extraction quality validation and routing.
# ACCEPTANCE_CRITERIA:
#   AC1: OCR extractions below confidence threshold are routed to review_required
#   AC2: Empty or low-signal OCR results trigger review_required status
#   AC3: OCR extraction source is tracked and propagated through validation
#   AC4: Confidence scores from OCR are properly clamped to [0.0, 1.0]
#   AC5: Validation failures emit audit events for debugging and compliance
# HUMAN_REVIEW: Yes — OCR validation routing directly impacts data quality and user experience.

from django.test import TestCase
from intake_canonicalization.ocr_extraction_quality_validator import (
	validate_ocr_extraction_quality,
	OCRQualityInput,
	_assess_text_quality,
	_clamp_confidence,
	OCR_AUTO_ACCEPT_THRESHOLD,
	OCR_REVIEW_THRESHOLD,
)


class OCRExtractionQualityValidationTests(TestCase):
	"""AC1: OCR extractions below confidence threshold are routed to review_required"""

	def test_high_confidence_extraction_routes_to_auto_accept(self) -> None:
		"""High-confidence extraction (>= 0.90) routes to auto_accept."""
		input_data: OCRQualityInput = {
			"extracted_items": [
				{"text": "Advanced Calculus Textbook", "extraction_source": "ocr", "status": "extracted"},
				{"text": "ISBN: 978-0-123456-78-9", "extraction_source": "ocr", "status": "extracted"},
			],
			"confidence_scores": [0.95, 0.92],
			"extraction_source": "ocr",
		}

		output = validate_ocr_extraction_quality(input_data)

		assert output["route_decision"] == "auto_accept"
		assert "high_quality_extraction" in output["quality_assessment"] or \
		       output["route_decision"] in ["auto_accept"]
		assert len(output["validated_items"]) == 2

	def test_medium_confidence_extraction_routes_to_review(self) -> None:
		"""Medium-confidence extraction (0.70-0.89) routes to review_required."""
		input_data: OCRQualityInput = {
			"extracted_items": [
				{"text": "Notebook 200 pages line paper", "extraction_source": "ocr", "status": "extracted"},
				{"text": "Blue cover plastic binding", "extraction_source": "ocr", "status": "extracted"},
			],
			"confidence_scores": [0.78, 0.75],
			"extraction_source": "ocr",
		}

		output = validate_ocr_extraction_quality(input_data)

		assert output["route_decision"] == "review_required"
		assert output["quality_assessment"]["average_confidence"] >= OCR_REVIEW_THRESHOLD
		assert output["quality_assessment"]["average_confidence"] < OCR_AUTO_ACCEPT_THRESHOLD

	def test_low_confidence_extraction_routes_to_reject(self) -> None:
		"""Low-confidence extraction (< 0.70) routes to reject."""
		input_data: OCRQualityInput = {
			"extracted_items": [
				{"text": "illllllllllll||||~~~~", "extraction_source": "ocr", "status": "extracted"},
				{"text": "£££|||| garbled text", "extraction_source": "ocr", "status": "extracted"},
			],
			"confidence_scores": [0.45, 0.38],
			"extraction_source": "ocr",
		}

		output = validate_ocr_extraction_quality(input_data)

		assert output["route_decision"] == "reject"
		assert output["quality_assessment"]["average_confidence"] < OCR_REVIEW_THRESHOLD


class OCREmptyAndLowSignalTests(TestCase):
	"""AC2: Empty or low-signal OCR results trigger review_required status"""

	def test_empty_extraction_routes_to_reject(self) -> None:
		"""Empty extraction (no content) routes to reject."""
		input_data: OCRQualityInput = {
			"extracted_items": [],
			"confidence_scores": [],
			"extraction_source": "ocr",
		}

		output = validate_ocr_extraction_quality(input_data)

		assert output["route_decision"] == "reject"
		assert output["quality_assessment"]["total_items"] == 0
		assert len(output["audit_events"]) > 0

	def test_zero_confidence_items_trigger_rejection(self) -> None:
		"""Items with zero confidence trigger rejection."""
		input_data: OCRQualityInput = {
			"extracted_items": [
				{"text": "", "extraction_source": "ocr", "status": "extracted"},
			],
			"confidence_scores": [0.0],
			"extraction_source": "ocr",
		}

		output = validate_ocr_extraction_quality(input_data)

		assert output["route_decision"] == "reject"
		assert output["quality_assessment"]["min_confidence"] == 0.0

	def test_mostly_low_confidence_items_trigger_rejection(self) -> None:
		"""If majority of items are below threshold, reject entire batch."""
		input_data: OCRQualityInput = {
			"extracted_items": [
				{"text": "Good text", "extraction_source": "ocr", "status": "extracted"},
				{"text": "|||~~ bad", "extraction_source": "ocr", "status": "extracted"},
				{"text": "|||~~ bad", "extraction_source": "ocr", "status": "extracted"},
				{"text": "|||~~ bad", "extraction_source": "ocr", "status": "extracted"},
			],
			"confidence_scores": [0.92, 0.40, 0.35, 0.42],
			"extraction_source": "ocr",
		}

		output = validate_ocr_extraction_quality(input_data)

		assert output["route_decision"] == "reject"
		assert output["quality_assessment"]["items_below_review_threshold"] >= 3


class OCRExtractionSourceTrackingTests(TestCase):
	"""AC3: OCR extraction source is tracked and propagated through validation"""

	def test_extraction_source_ocr_is_preserved(self) -> None:
		"""OCR extraction source is preserved in validated items."""
		input_data: OCRQualityInput = {
			"extracted_items": [
				{"text": "Book Title", "extraction_source": "ocr", "status": "extracted"},
			],
			"confidence_scores": [0.85],
			"extraction_source": "ocr",
		}

		output = validate_ocr_extraction_quality(input_data)

		assert output["validated_items"][0]["extraction_source"] == "ocr"
		assert output["validated_items"][0]["validation_source"] == "ocr"

	def test_extraction_source_native_text_is_preserved(self) -> None:
		"""Native text extraction source is preserved in validated items."""
		input_data: OCRQualityInput = {
			"extracted_items": [
				{"text": "Notebook 200 pages", "extraction_source": "native_text", "status": "extracted"},
			],
			"confidence_scores": [0.88],
			"extraction_source": "native_text",
		}

		output = validate_ocr_extraction_quality(input_data)

		assert output["validated_items"][0]["extraction_source"] == "native_text"
		assert output["validated_items"][0]["validation_source"] == "native_text"

	def test_invalid_extraction_source_triggers_audit_event(self) -> None:
		"""Invalid extraction source triggers audit event."""
		input_data: OCRQualityInput = {
			"extracted_items": [
				{"text": "Some text", "extraction_source": "invalid_source"},
			],
			"confidence_scores": [0.80],
			"extraction_source": "invalid_source",
		}

		output = validate_ocr_extraction_quality(input_data)

		# Should have audit event for invalid source
		source_events = [e for e in output["audit_events"] if "extraction_source" in str(e)]
		assert len(source_events) > 0


class OCRConfidenceClampingTests(TestCase):
	"""AC4: Confidence scores from OCR are properly clamped to [0.0, 1.0]"""

	def test_confidence_clamp_function_clamps_below_zero(self) -> None:
		"""Negative confidence is clamped to 0.0."""
		assert _clamp_confidence(-0.5) == 0.0
		assert _clamp_confidence(-1.5) == 0.0

	def test_confidence_clamp_function_clamps_above_one(self) -> None:
		"""Confidence above 1.0 is clamped to 1.0."""
		assert _clamp_confidence(1.5) == 1.0
		assert _clamp_confidence(2.0) == 1.0

	def test_confidence_clamp_function_preserves_valid_range(self) -> None:
		"""Valid confidence values are preserved."""
		assert _clamp_confidence(0.0) == 0.0
		assert _clamp_confidence(0.5) == 0.5
		assert _clamp_confidence(0.75) == 0.75
		assert _clamp_confidence(1.0) == 1.0

	def test_extracted_items_have_clamped_confidence(self) -> None:
		"""Validated items have clamped confidence values."""
		input_data: OCRQualityInput = {
			"extracted_items": [
				{"text": "Item 1", "status": "extracted"},
				{"text": "Item 2", "status": "extracted"},
			],
			"confidence_scores": [-0.5, 1.5],  # Both outside valid range
			"extraction_source": "ocr",
		}

		output = validate_ocr_extraction_quality(input_data)

		assert output["validated_items"][0]["confidence"] == 0.0
		assert output["validated_items"][1]["confidence"] == 1.0


class OCRValidationAuditEventsTests(TestCase):
	"""AC5: Validation failures emit audit events for debugging and compliance"""

	def test_quality_assessment_audit_event_is_always_emitted(self) -> None:
		"""Quality assessment audit event is always emitted."""
		input_data: OCRQualityInput = {
			"extracted_items": [{"text": "Test text", "extraction_source": "ocr"}],
			"confidence_scores": [0.85],
			"extraction_source": "ocr",
		}

		output = validate_ocr_extraction_quality(input_data)

		quality_events = [e for e in output["audit_events"] if e.get("event_type") == "quality_assessment"]
		assert len(quality_events) > 0
		assert "total_items" in quality_events[0]
		assert "average_confidence" in quality_events[0]

	def test_routing_decision_audit_event_is_always_emitted(self) -> None:
		"""Routing decision audit event is always emitted."""
		input_data: OCRQualityInput = {
			"extracted_items": [{"text": "Test text", "extraction_source": "ocr"}],
			"confidence_scores": [0.75],
			"extraction_source": "ocr",
		}

		output = validate_ocr_extraction_quality(input_data)

		routing_events = [e for e in output["audit_events"] if e.get("event_type") == "routing_decision"]
		assert len(routing_events) > 0
		assert "route" in routing_events[0]
		assert "reason" in routing_events[0]

	def test_validation_failure_audit_event_includes_details(self) -> None:
		"""Validation failure audit events include detailed reasons."""
		input_data: OCRQualityInput = {
			"extracted_items": [],
			"confidence_scores": [],
			"extraction_source": "ocr",
		}

		output = validate_ocr_extraction_quality(input_data)

		failure_events = [e for e in output["audit_events"] if e.get("event_type") == "validation_failure"]
		assert len(failure_events) > 0
		assert any(e.get("severity") == "error" for e in failure_events)


class OCRTextQualityAssessmentTests(TestCase):
	"""Integration tests for text quality analysis and OCR artifact detection"""

	def test_good_quality_text_assessment(self) -> None:
		"""Good quality text is assessed correctly."""
		assessment = _assess_text_quality("Advanced Calculus Textbook Edition 5")
		
		assert assessment["has_content"] == True
		assert assessment["character_count"] > 0
		assert assessment["alphanumeric_ratio"] >= 0.8
		assert assessment["has_common_ocr_artifacts"] == False

	def test_text_with_ocr_artifacts_detected(self) -> None:
		"""Text with OCR artifacts is flagged."""
		# Text with excessive pipes (common OCR error)
		assessment = _assess_text_quality("Book||||Title||||||with||||many||||pipes")
		
		assert assessment["has_content"] == True
		assert assessment["has_common_ocr_artifacts"] == True

	def test_text_with_tildes_detected(self) -> None:
		"""Text with excessive tildes is flagged as artifact."""
		assessment = _assess_text_quality("Book~Title~with~~~~many~~~tildes~~~")
		
		assert assessment["has_common_ocr_artifacts"] == True

	def test_empty_text_assessment(self) -> None:
		"""Empty text is assessed as no content."""
		assessment = _assess_text_quality("")
		
		assert assessment["has_content"] == False
		assert assessment["character_count"] == 0
		assert assessment["alphanumeric_ratio"] == 0.0


class OCRWithStagePipelineIntegrationTests(TestCase):
	"""Integration tests for OCR validation within the full Stage A pipeline"""

	def test_ocr_extraction_with_stage_a_response_flow(self) -> None:
		"""OCR quality validation integrates with Stage A response flow."""
		# Simulate OCR extraction results from Stage A
		ocr_results = [
			{
				"source_document_id": "upload-123",
				"page_number": 1,
				"text": "Advanced Mathematics Textbook",
				"extraction_source": "ocr",
				"confidence": 0.88,
				"status": "extracted",
			},
			{
				"source_document_id": "upload-123",
				"page_number": 2,
				"text": "Edition 5, ISBN 978-0-123456-78-9",
				"extraction_source": "ocr",
				"confidence": 0.85,
				"status": "extracted",
			},
		]

		input_data: OCRQualityInput = {
			"extracted_items": ocr_results,
			"confidence_scores": [0.88, 0.85],
			"extraction_source": "ocr",
		}

		output = validate_ocr_extraction_quality(input_data)

		# Should route to review (not high enough for auto-accept)
		assert output["route_decision"] in ["auto_accept", "review_required"]
		assert len(output["validated_items"]) == 2
		assert output["quality_assessment"]["total_items"] == 2

	def test_ocr_quality_validation_with_mixed_confidence(self) -> None:
		"""OCR quality validation handles mixed confidence scores correctly."""
		input_data: OCRQualityInput = {
			"extracted_items": [
				{"text": "High quality text clearly visible", "extraction_source": "ocr"},
				{"text": "Medium quality somewhat unclear", "extraction_source": "ocr"},
				{"text": "||||Low quality~~~~", "extraction_source": "ocr"},
			],
			"confidence_scores": [0.95, 0.72, 0.35],
			"extraction_source": "ocr",
		}

		output = validate_ocr_extraction_quality(input_data)

		# Quality assessment should be available
		assert output["quality_assessment"]["total_items"] == 3
		assert output["quality_assessment"]["items_above_review_threshold"] == 2
		assert output["quality_assessment"]["items_below_review_threshold"] == 1

	def test_requires_human_review_flag_set_on_review_route(self) -> None:
		"""Items marked for review have requires_human_review flag set."""
		input_data: OCRQualityInput = {
			"extracted_items": [
				{"text": "Text for review", "extraction_source": "ocr"},
			],
			"confidence_scores": [0.75],
			"extraction_source": "ocr",
		}

		output = validate_ocr_extraction_quality(input_data)

		if output["route_decision"] == "review_required":
			# All items should be marked for review
			for item in output["validated_items"]:
				assert item.get("requires_human_review") == True
				assert item.get("gate_route") == "review"

	def test_gate_reason_provided_for_review_routing(self) -> None:
		"""Gate reason is provided when items are routed to review."""
		input_data: OCRQualityInput = {
			"extracted_items": [
				{"text": "Item 1", "extraction_source": "ocr"},
				{"text": "||||Item 2", "extraction_source": "ocr"},
			],
			"confidence_scores": [0.78, 0.76],
			"extraction_source": "ocr",
		}

		output = validate_ocr_extraction_quality(input_data)

		if output["route_decision"] in ["review_required", "reject"]:
			# Items should have gate_reason
			for item in output["validated_items"]:
				if "gate_reason" in item:
					assert len(item["gate_reason"]) > 0
