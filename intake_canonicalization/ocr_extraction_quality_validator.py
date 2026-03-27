# FILE: intake_canonicalization/ocr_extraction_quality_validator.py
# MODULE: MODULE-001-14 — OCR Extraction Quality Validator
# EPIC: EPIC-001 — Data Extraction & Validation (Step 9: OCR Post-Native Validation Hardening)
# RESPONSIBILITY: Validate OCR extraction quality, enforce confidence thresholds, and route low-quality extractions.
# EXPORTS: OCR quality validation service with routing decisions.
# ACCEPTANCE_CRITERIA:
#   AC1: OCR extractions below confidence threshold are routed to review_required
#   AC2: Empty or low-signal OCR results trigger review_required status
#   AC3: OCR extraction source is tracked and propagated through validation
#   AC4: Confidence scores from OCR are properly clamped to [0.0, 1.0]
#   AC5: Validation failures emit audit events for debugging and compliance
# HUMAN_REVIEW: Yes — OCR quality thresholds directly impact user experience and data correctness.

from __future__ import annotations

from typing import TypedDict


class OCRQualityInput(TypedDict, total=False):
	"""Contract for OCR quality validation."""
	extracted_items: list[dict]
	confidence_scores: list[float]
	extraction_source: str
	minimum_quality_threshold: float  # Default: 0.70 per FR-002
	minimum_items_required: int  # Default: 1


class OCRQualityOutput(TypedDict, total=False):
	"""Contract for OCR quality validation output."""
	validated_items: list[dict]
	quality_assessment: dict
	route_decision: str  # "auto_accept" | "review_required" | "reject"
	audit_events: list[dict]


# OCR Quality Validation Thresholds (per FR-002)
OCR_AUTO_ACCEPT_THRESHOLD = 0.90
OCR_REVIEW_THRESHOLD = 0.70
OCR_REJECT_THRESHOLD = 0.70
OCR_MINIMUM_ITEMS = 1
OCR_MINIMUM_ACCEPTABLE_SIGNAL = 0.5


def _clamp_confidence(confidence: float) -> float:
	"""Clamp confidence score to valid range [0.0, 1.0]."""
	if confidence < 0.0:
		return 0.0
	if confidence > 1.0:
		return 1.0
	return round(confidence, 2)


def _assess_text_quality(text: str) -> dict:
	"""
	Assess quality of OCR text output.
	
	Returns: {
		"has_content": bool,
		"character_count": int,
		"alphanumeric_ratio": float,
		"line_count": int,
		"has_common_ocr_artifacts": bool,
	}
	"""
	if not text:
		return {
			"has_content": False,
			"character_count": 0,
			"alphanumeric_ratio": 0.0,
			"line_count": 0,
			"has_common_ocr_artifacts": False,
		}
	
	# Count characters
	char_count = len(text)
	
	# Count alphanumeric characters
	alnum_count = sum(1 for c in text if c.isalnum() or c in "áéíóúàâãäèêëìîïòôõöùûüçñ .-_/")
	alnum_ratio = alnum_count / max(1, char_count)
	
	# Count lines
	line_count = len([l for l in text.split('\n') if l.strip()])
	
	# Detect common OCR artifacts (repeated non-ASCII or control characters)
	suspicious_patterns = (
		text.count('|') > 5,  # Excessive pipes often indicate OCR failure
		text.count('~') > 3,  # Tildes often indicate OCR misread
		text.count('£') > 2,  # £ symbol common in OCR errors
		bool(len([c for c in text if ord(c) < 32 and c not in '\n\t\r']) > 5),  # Control chars
	)
	has_artifacts = any(suspicious_patterns)
	
	return {
		"has_content": True,
		"character_count": char_count,
		"alphanumeric_ratio": round(alnum_ratio, 2),
		"line_count": line_count,
		"has_common_ocr_artifacts": has_artifacts,
	}


def _validate_extraction_source(extraction_source: str) -> tuple[bool, str]:
	"""Validate that extraction source is properly declared."""
	valid_sources = {"ocr", "native_text", "hybrid"}
	if extraction_source not in valid_sources:
		return False, f"invalid_extraction_source: {extraction_source}"
	return True, ""


def _assess_ocr_quality(extracted_items: list[dict], confidence_scores: list[float]) -> dict:
	"""
	Assess overall quality of OCR extraction batch.
	
	Returns: {
		"total_items": int,
		"items_with_content": int,
		"average_confidence": float,
		"min_confidence": float,
		"max_confidence": float,
		"items_above_review_threshold": int,
		"items_below_review_threshold": int,
		"text_quality_assessments": list[dict],
	}
	"""
	if not extracted_items or not confidence_scores:
		return {
			"total_items": 0,
			"items_with_content": 0,
			"average_confidence": 0.0,
			"min_confidence": 0.0,
			"max_confidence": 0.0,
			"items_above_review_threshold": 0,
			"items_below_review_threshold": 0,
			"text_quality_assessments": [],
		}
	
	total_items = len(extracted_items)
	clamped_scores = [_clamp_confidence(s) for s in confidence_scores]
	
	# Filter items with content
	items_with_content = sum(
		1 for item in extracted_items
		if item.get("text") or item.get("line_text") or item.get("name")
	)
	
	# Calculate confidence bands
	avg_confidence = sum(clamped_scores) / len(clamped_scores) if clamped_scores else 0.0
	min_confidence = min(clamped_scores) if clamped_scores else 0.0
	max_confidence = max(clamped_scores) if clamped_scores else 0.0
	
	# Count items by confidence band
	above_review = sum(1 for s in clamped_scores if s >= OCR_REVIEW_THRESHOLD)
	below_review = sum(1 for s in clamped_scores if s < OCR_REVIEW_THRESHOLD)
	
	# Assess text quality for each item
	text_assessments = []
	for item in extracted_items:
		text = item.get("text") or item.get("line_text") or ""
		assessment = _assess_text_quality(text)
		text_assessments.append(assessment)
	
	return {
		"total_items": total_items,
		"items_with_content": items_with_content,
		"average_confidence": round(avg_confidence, 2),
		"min_confidence": round(min_confidence, 2),
		"max_confidence": round(max_confidence, 2),
		"items_above_review_threshold": above_review,
		"items_below_review_threshold": below_review,
		"text_quality_assessments": text_assessments,
	}


def _route_quality_decision(
	quality_assessment: dict,
	extracted_items: list[dict],
) -> tuple[str, str]:
	"""
	Make routing decision based on quality assessment.
	
	Returns: (route_decision, reason)
	- "auto_accept": Quality is high and meets all thresholds
	- "review_required": Quality is acceptable but needs human review
	- "reject": Quality is too low for processing
	"""
	total = quality_assessment["total_items"]
	has_content = quality_assessment["items_with_content"]
	avg_confidence = quality_assessment["average_confidence"]
	below_threshold = quality_assessment["items_below_review_threshold"]
	
	# No items extracted
	if total == 0 or has_content == 0:
		return "reject", "no_content_extracted"
	
	# Critical failure: more than half below threshold
	if below_threshold > total * 0.5:
		return "reject", "majority_below_confidence_threshold"
	
	# High quality: most items above auto-accept threshold and none with artifacts
	has_artifacts = any(q.get("has_common_ocr_artifacts") for q in quality_assessment["text_quality_assessments"])
	
	if avg_confidence >= OCR_AUTO_ACCEPT_THRESHOLD and not has_artifacts:
		return "auto_accept", "high_quality_extraction"
	
	# Medium quality: acceptable but needs review
	if avg_confidence >= OCR_REVIEW_THRESHOLD:
		if has_artifacts:
			return "review_required", "possible_ocr_artifacts_detected"
		if below_threshold > 0:
			return "review_required", "some_items_below_confidence_threshold"
		return "review_required", "medium_quality_requires_review"
	
	# Low quality: below review threshold
	return "reject", "average_confidence_below_review_threshold"


def validate_ocr_extraction_quality(input_data: OCRQualityInput) -> OCRQualityOutput:
	"""
	Validate OCR extraction quality and make routing decisions.
	
	Input contract:
	- extracted_items: list of extracted item dicts
	- confidence_scores: parallel list of confidence values
	- extraction_source: source of extraction (e.g., "ocr")
	- minimum_quality_threshold: confidence threshold for acceptance (default: 0.70)
	- minimum_items_required: minimum items needed (default: 1)
	
	Output:
	- validated_items: input items with validation metadata
	- quality_assessment: comprehensive quality metrics
	- route_decision: "auto_accept" | "review_required" | "reject"
	- audit_events: list of validation events for debugging
	
	Behavior:
	- Validate extraction source declaration
	- Assess text quality for OCR artifacts
	- Route by confidence band and quality metric
	- Emit audit events for all decisions
	- Preserve original items with validation metadata
	"""
	extracted_items = input_data.get("extracted_items") or []
	confidence_scores = input_data.get("confidence_scores") or []
	extraction_source = input_data.get("extraction_source") or "ocr"
	minimum_quality_threshold = input_data.get("minimum_quality_threshold", OCR_REVIEW_THRESHOLD)
	minimum_items_required = input_data.get("minimum_items_required", OCR_MINIMUM_ITEMS)
	
	audit_events: list[dict] = []
	
	# Validate extraction source
	source_valid, source_error = _validate_extraction_source(extraction_source)
	if not source_valid:
		audit_events.append({
			"event_type": "validation_failure",
			"category": "extraction_source",
			"reason": source_error,
			"severity": "error",
		})
	
	# Assess quality
	quality_assessment = _assess_ocr_quality(extracted_items, confidence_scores)
	
	audit_events.append({
		"event_type": "quality_assessment",
		"category": "ocr_quality",
		"total_items": quality_assessment["total_items"],
		"average_confidence": quality_assessment["average_confidence"],
		"items_below_threshold": quality_assessment["items_below_review_threshold"],
	})
	
	# Make routing decision
	route_decision, route_reason = _route_quality_decision(quality_assessment, extracted_items)
	
	audit_events.append({
		"event_type": "routing_decision",
		"category": "extraction_routing",
		"route": route_decision,
		"reason": route_reason,
	})
	
	# Validate item count
	if quality_assessment["total_items"] < minimum_items_required:
		route_decision = "reject"
		audit_events.append({
			"event_type": "validation_failure",
			"category": "item_count",
			"reason": f"insufficient_items: {quality_assessment['total_items']} < {minimum_items_required}",
			"severity": "error",
		})
	
	# Enrich items with validation metadata
	validated_items = []
	for i, item in enumerate(extracted_items):
		enriched = dict(item)
		enriched["validation_source"] = extraction_source
		enriched["validated_at_step"] = "ocr_quality_validation"
		
		# Add confidence if missing
		if "confidence" not in enriched and i < len(confidence_scores):
			enriched["confidence"] = _clamp_confidence(confidence_scores[i])
		
		# Add quality assessment reference
		if i < len(quality_assessment["text_quality_assessments"]):
			enriched["text_quality"] = quality_assessment["text_quality_assessments"][i]
		
		# Set review flag if route decision is review_required or reject
		if route_decision in ("review_required", "reject"):
			enriched["requires_human_review"] = True
			enriched["gate_route"] = "review"
			enriched["gate_reason"] = route_reason
		
		validated_items.append(enriched)
	
	return OCRQualityOutput(
		validated_items=validated_items,
		quality_assessment=quality_assessment,
		route_decision=route_decision,
		audit_events=audit_events,
	)
