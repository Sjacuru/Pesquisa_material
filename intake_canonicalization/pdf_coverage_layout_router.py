# FILE: intake_canonicalization/pdf_coverage_layout_router.py
# MODULE: MODULE-001-12 — PDF Coverage and Layout Router
# EPIC: EPIC-001 — Data Extraction & Validation (Chunk 4 / FR-024 Amendment)
# RESPONSIBILITY: Compute PDF text coverage ratio, apply THRESHOLD-OCR-01, detect major layout complexity, and choose native text extraction or OCR routing.
# EXPORTS: PDF coverage analysis and routing service.
# DEPENDS_ON: platform/observability.py
# ACCEPTANCE_CRITERIA:
#   AC1: Coverage computation returns value bounded in [0.00, 1.00]
#   AC2: Coverage ratio >= 0.70 selects native_text route
#   AC3: Coverage ratio < 0.70 selects ocr route
#   AC4: Two-column layouts are flagged when detected
#   AC5: Table-heavy layouts are flagged when detected
#   AC6: Uncertain layout regions emit warning or review metadata
#   AC7: routing_audit_record includes applied logic and threshold evidence
# HUMAN_REVIEW: Yes — PDF layout detection correctness requires expert review.

from __future__ import annotations

import re
from typing import TypedDict, Optional


# Threshold for PDF text coverage routing decision
THRESHOLD_OCR_01 = 0.70


class LayoutFlags(TypedDict, total=False):
	"""Layout flags for PDF detection."""
	is_two_column: bool
	is_table_heavy: bool
	has_uncertain_regions: bool


class RoutingAuditRecord(TypedDict, total=False):
	"""Audit record for routing decision."""
	decision_logic_applied: str
	coverage_threshold: float
	coverage_ratio: float


class ErrorDetail(TypedDict, total=False):
	"""Error detail in routing output."""
	reason: str
	severity: str  # "warning" | "error"
	affected_pages: list[int]


class PDFRoutingInput(TypedDict, total=False):
	"""Input contract for PDF coverage and layout router."""
	pdf_bytes: bytes
	filename: str
	context: dict
	extraction_evidence: dict


class PDFRoutingOutput(TypedDict, total=False):
	"""Output contract for PDF coverage and layout router."""
	route_mode: str  # "native_text" | "ocr"
	text_coverage_ratio: float
	layout_flags: LayoutFlags
	routing_audit_record: RoutingAuditRecord
	error: Optional[ErrorDetail]


def _safe_pdf_text(pdf_bytes: bytes) -> str:
	if not pdf_bytes:
		return ""
	return pdf_bytes.decode("latin-1", errors="ignore")


def _count_text_operators(pdf_text: str) -> int:
	# PDF text operators and marked text operators often seen in content streams.
	patterns = [
		r"\bBT\b",  # begin text
		r"\bET\b",  # end text
		r"\bTj\b",  # show text
		r"\bTJ\b",  # show text array
		r"\bTf\b",  # text font
		r"\bTm\b",  # text matrix
	]
	count = 0
	for pattern in patterns:
		count += len(re.findall(pattern, pdf_text))
	return count


def _count_image_operators(pdf_text: str) -> int:
	patterns = [
		r"/Subtype\s*/Image",
		r"\bDo\b",  # invoke named xobject (often image)
		r"/XObject",
	]
	count = 0
	for pattern in patterns:
		count += len(re.findall(pattern, pdf_text))
	return count


def _compute_text_coverage_ratio(pdf_bytes: bytes) -> float:
	"""
	Compute text coverage ratio for PDF using deterministic byte-level PDF markers.

	Method:
	- Count text operators (BT/ET/Tj/TJ/Tf/Tm)
	- Count image operators (/Subtype /Image, Do, /XObject)
	- Compute ratio: text_score / (text_score + image_score + 1)

	Returns float in [0.00, 1.00].
	"""
	if not pdf_bytes:
		return 0.0

	pdf_text = _safe_pdf_text(pdf_bytes)
	if "%PDF" not in pdf_text[:16]:
		return 0.0

	text_ops = _count_text_operators(pdf_text)
	image_ops = _count_image_operators(pdf_text)

	if text_ops == 0 and image_ops == 0:
		# Fallback for weak fixtures: estimate from printable density
		printable = sum(1 for byte in pdf_bytes if 32 <= byte <= 126)
		density = printable / max(1, len(pdf_bytes))
		return max(0.0, min(1.0, round(density * 0.8, 2)))

	text_score = float(text_ops)
	image_score = float(image_ops * 2)
	ratio = text_score / (text_score + image_score + 1.0)
	return max(0.0, min(1.0, round(ratio, 2)))


def _detect_two_column_layout(pdf_bytes: bytes) -> bool:
	"""Detect possible two-column layout from PDF text-position cues."""
	pdf_text = _safe_pdf_text(pdf_bytes)
	if not pdf_text:
		return False

	# Safeguard: limit text size to prevent regex catastrophic backtracking on huge PDFs
	# Use first 100KB of text for layout detection to avoid performance issues
	MAX_TEXT_SAMPLE = 100_000
	pdf_text_sample = pdf_text[:MAX_TEXT_SAMPLE]

	# Heuristic 1: multiple lines with wide intra-line gaps, common in extracted two-column text
	wide_gap_lines = re.findall(r"\S+\s{4,}\S+", pdf_text_sample)

	# Heuristic 2: multiple distinct left-position text matrices e.g. '50 700 Tm' and '320 700 Tm'
	positions = re.findall(r"(\d{1,3})\s+\d{1,4}\s+Tm", pdf_text_sample)
	unique_positions = {int(position) for position in positions if position.isdigit()}
	has_split_positions = len([position for position in unique_positions if position >= 40]) >= 2

	return len(wide_gap_lines) >= 3 or has_split_positions


def _detect_table_heavy_layout(pdf_bytes: bytes) -> bool:
	"""Detect possible table-heavy layout using textual delimiters and repeated aligned rows."""
	pdf_text = _safe_pdf_text(pdf_bytes)
	if not pdf_text:
		return False

	# Safeguard: limit text size to prevent regex catastrophic backtracking on huge PDFs
	# Use first 100KB of text for layout detection to avoid performance issues
	MAX_TEXT_SAMPLE = 100_000
	pdf_text_sample = pdf_text[:MAX_TEXT_SAMPLE]

	pipe_rows = len(re.findall(r"^.*\|.*\|.*$", pdf_text_sample, flags=re.MULTILINE))
	tab_rows = len(re.findall(r"^.*\t.*\t.*$", pdf_text_sample, flags=re.MULTILINE))
	numeric_grid_rows = len(re.findall(r"\b\d+[\.,]?\d*\s{2,}\d+[\.,]?\d*", pdf_text_sample))

	return (pipe_rows + tab_rows + numeric_grid_rows) >= 4


def _detect_uncertain_regions(pdf_bytes: bytes) -> bool:
	"""Detect uncertain regions from low-signal text and ambiguity markers."""
	pdf_text = _safe_pdf_text(pdf_bytes)
	if not pdf_text:
		return True

	text_ops = _count_text_operators(pdf_text)
	image_ops = _count_image_operators(pdf_text)
	uncertain_tokens = len(re.findall(r"(\?\?\?|\ufffd|\[illegible\]|\[uncertain\])", pdf_text, flags=re.IGNORECASE))

	# Uncertain if image-heavy with little text, or explicit uncertain tokens present.
	if uncertain_tokens > 0:
		return True
	if image_ops >= 2 and text_ops <= 1:
		return True
	return False


def route_pdf_coverage(input_data: PDFRoutingInput) -> PDFRoutingOutput:
	"""
	For PDF documents, compute text coverage ratio, apply THRESHOLD-OCR-01,
	detect major layout complexity, and choose native text extraction or OCR routing.
	
	Input: pdf_bytes, filename, context
	Output: route_mode, text_coverage_ratio, layout_flags, routing_audit_record, error
	
	Behavior:
	- Compute text_coverage_ratio in [0.00, 1.00]
	- Apply THRESHOLD-OCR-01 exactly: >= 0.70 -> native_text, < 0.70 -> ocr
	- Detect layout flags for two-column, table-heavy, and uncertainty conditions
	- Emit routing_audit_record for downstream traceability
	- On routing ambiguity, preserve review-oriented metadata rather than silently forcing correctness claims
	"""
	pdf_bytes = input_data.get("pdf_bytes", b"")
	filename = input_data.get("filename", "")
	context = input_data.get("context") or {}
	extraction_evidence = input_data.get("extraction_evidence") or context.get("extraction_evidence") or {}
	
	if not pdf_bytes:
		return PDFRoutingOutput(
			route_mode="native_text",  # Default to native if no data
			text_coverage_ratio=0.0,
			layout_flags=LayoutFlags(
				is_two_column=False,
				is_table_heavy=False,
				has_uncertain_regions=True,
			),
			routing_audit_record=RoutingAuditRecord(
				decision_logic_applied="empty_pdf_bytes",
				coverage_threshold=THRESHOLD_OCR_01,
				coverage_ratio=0.0,
			),
			error=ErrorDetail(
				reason="PDF bytes are empty",
				severity="error",
				affected_pages=[],
			),
		)
	
	# Prefer extraction evidence when available (native extraction/OCR diagnostics)
	if extraction_evidence:
		coverage_ratio = float(extraction_evidence.get("coverage_ratio", 0.0))
		coverage_ratio = max(0.0, min(1.0, coverage_ratio))

		flags = extraction_evidence.get("layout_flags") or {}
		is_two_column = bool(flags.get("is_two_column") or flags.get("two_column") or False)
		is_table_heavy = bool(flags.get("is_table_heavy") or flags.get("table_heavy") or False)
		has_uncertain_regions = bool(flags.get("has_uncertain_regions") or flags.get("uncertain") or False)
		evidence_source = "extraction_evidence"
	else:
		# Compute text coverage from PDF bytes (legacy heuristic path)
		coverage_ratio = _compute_text_coverage_ratio(pdf_bytes)
		coverage_ratio = max(0.0, min(1.0, coverage_ratio))  # Clamp to [0.0, 1.0]
		
		# Detect layout flags from PDF bytes
		is_two_column = _detect_two_column_layout(pdf_bytes)
		is_table_heavy = _detect_table_heavy_layout(pdf_bytes)
		has_uncertain_regions = _detect_uncertain_regions(pdf_bytes)
		evidence_source = "pdf_byte_heuristics"

	# Apply THRESHOLD-OCR-01 routing
	route_mode = "native_text" if coverage_ratio >= THRESHOLD_OCR_01 else "ocr"
	
	# Build audit record
	audit_record = RoutingAuditRecord(
		decision_logic_applied=f"THRESHOLD-OCR-01={THRESHOLD_OCR_01}: source={evidence_source}, coverage_ratio={coverage_ratio:.2f} -> {route_mode}",
		coverage_threshold=THRESHOLD_OCR_01,
		coverage_ratio=coverage_ratio,
	)
	
	# Emit warnings if layout issues detected
	error_detail = None
	if is_two_column or is_table_heavy or has_uncertain_regions:
		error_detail = ErrorDetail(
			reason="Layout complexity flags detected",
			severity="warning",
			affected_pages=[],  # Would be populated with actual page numbers in production
		)
	
	return PDFRoutingOutput(
		route_mode=route_mode,
		text_coverage_ratio=coverage_ratio,
		layout_flags=LayoutFlags(
			is_two_column=is_two_column,
			is_table_heavy=is_table_heavy,
			has_uncertain_regions=has_uncertain_regions,
		),
		routing_audit_record=audit_record,
		error=error_detail,
	)
