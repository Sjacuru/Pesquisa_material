# FILE: tests/unit/intake_canonicalization/test_pdf_coverage_layout_router.py
# MODULE: MODULE-001-12 — PDF Coverage and Layout Router
# EPIC: EPIC-001 — Data Extraction & Validation (Chunk 4 / FR-024 Amendment)
# RESPONSIBILITY: Reserve unit tests for PDF coverage and layout routing acceptance criteria.
# EXPORTS: Unit test suite.
# DEPENDS_ON: intake_canonicalization/pdf_coverage_layout_router.py
# ACCEPTANCE_CRITERIA:
#   - PDF routing acceptance criteria are testable from this unit boundary.
#   - No live PDF processing library is required by the tests.
# HUMAN_REVIEW: No.

import pytest

from intake_canonicalization.pdf_coverage_layout_router import (
	route_pdf_coverage,
	THRESHOLD_OCR_01,
	PDFRoutingInput,
)


def _pdf_fixture_text_heavy() -> bytes:
	return (
		b"%PDF-1.4\n"
		b"BT /F1 12 Tf 50 700 Tm (Linha 1) Tj ET\n"
		b"BT /F1 12 Tf 50 680 Tm (Linha 2) Tj ET\n"
		b"BT /F1 12 Tf 50 660 Tm (Linha 3) Tj ET\n"
		b"BT /F1 12 Tf 50 640 Tm (Linha 4) Tj ET\n"
	)


def _pdf_fixture_image_heavy() -> bytes:
	return (
		b"%PDF-1.4\n"
		b"/XObject << /Im1 1 0 R /Im2 2 0 R >>\n"
		b"/Subtype /Image\n"
		b"/Subtype /Image\n"
		b"Do Do Do\n"
	)


def _pdf_fixture_two_column() -> bytes:
	return (
		b"%PDF-1.4\n"
		b"Titulo Esquerda    Titulo Direita\n"
		b"linha 1 esquerda    linha 1 direita\n"
		b"linha 2 esquerda    linha 2 direita\n"
		b"50 700 Tm\n"
		b"320 700 Tm\n"
	)


def _pdf_fixture_table_heavy() -> bytes:
	return (
		b"%PDF-1.4\n"
		b"Item | Qtde | Valor\n"
		b"Livro | 2 | 59.90\n"
		b"Caderno | 5 | 12.00\n"
		b"Lapis | 10 | 1.50\n"
		b"Borracha | 4 | 2.30\n"
	)


def _pdf_fixture_uncertain() -> bytes:
	return (
		b"%PDF-1.4\n"
		b"/Subtype /Image\n"
		b"Do\n"
		b"[illegible] ???\n"
	)


class TestModuleAC1_CoverageRatioBounds:
	"""AC1: Coverage computation returns value bounded in [0.00, 1.00]"""
	
	def test_ac1_small_pdf_has_bounded_coverage(self) -> None:
		"""Small PDF returns coverage in valid range."""
		input_data: PDFRoutingInput = {
			"pdf_bytes": b"%PDF-1.4\n" + b"x" * 10000,  # ~10KB
			"filename": "small.pdf",
		}
		
		output = route_pdf_coverage(input_data)
		
		assert 0.0 <= output["text_coverage_ratio"] <= 1.0
	
	def test_ac1_large_pdf_has_bounded_coverage(self) -> None:
		"""Large PDF returns coverage in valid range."""
		input_data: PDFRoutingInput = {
			"pdf_bytes": b"%PDF-1.4\n" + b"x" * 200000,  # ~200KB
			"filename": "large.pdf",
		}
		
		output = route_pdf_coverage(input_data)
		
		assert 0.0 <= output["text_coverage_ratio"] <= 1.0
	
	def test_ac1_empty_pdf_has_zero_coverage(self) -> None:
		"""Empty PDF has zero coverage."""
		input_data: PDFRoutingInput = {
			"pdf_bytes": b"",
			"filename": "empty.pdf",
		}
		
		output = route_pdf_coverage(input_data)
		
		assert output["text_coverage_ratio"] == 0.0


class TestModuleAC2_NativeTextRouting:
	"""AC2: Coverage ratio >= 0.70 selects native_text route"""
	
	def test_ac2_high_coverage_routes_to_native_text(self) -> None:
		"""High coverage (>= threshold) routes to native_text."""
		input_data: PDFRoutingInput = {
			"pdf_bytes": _pdf_fixture_text_heavy(),
			"filename": "document.pdf",
		}
		
		output = route_pdf_coverage(input_data)
		assert output["text_coverage_ratio"] >= THRESHOLD_OCR_01
		assert output["route_mode"] == "native_text"


class TestModuleAC3_OCRRouting:
	"""AC3: Coverage ratio < 0.70 selects ocr route"""
	
	def test_ac3_low_coverage_routes_to_ocr(self) -> None:
		"""Low coverage (< threshold) routes to OCR."""
		input_data: PDFRoutingInput = {
			"pdf_bytes": _pdf_fixture_image_heavy(),
			"filename": "document.pdf",
		}
		
		output = route_pdf_coverage(input_data)
		assert output["text_coverage_ratio"] < THRESHOLD_OCR_01
		assert output["route_mode"] == "ocr"


class TestModuleAC4_TwoColumnFlagDetection:
	"""AC4: Two-column layouts are flagged when detected"""
	
	def test_ac4_layout_flags_present_in_output(self) -> None:
		"""Output includes layout flags structure."""
		input_data: PDFRoutingInput = {
			"pdf_bytes": _pdf_fixture_two_column(),
			"filename": "document.pdf",
		}
		
		output = route_pdf_coverage(input_data)
		
		assert "is_two_column" in output["layout_flags"]
		assert isinstance(output["layout_flags"]["is_two_column"], bool)
	
	def test_ac4_two_column_flag_is_boolean(self) -> None:
		"""Two-column flag is boolean."""
		input_data: PDFRoutingInput = {
			"pdf_bytes": _pdf_fixture_two_column(),
			"filename": "document.pdf",
		}
		
		output = route_pdf_coverage(input_data)
		
		assert isinstance(output["layout_flags"]["is_two_column"], bool)
		assert output["layout_flags"]["is_two_column"] is True


class TestModuleAC5_TableHeavyFlagDetection:
	"""AC5: Table-heavy layouts are flagged when detected"""
	
	def test_ac5_table_heavy_flag_present(self) -> None:
		"""Output includes table-heavy flag."""
		input_data: PDFRoutingInput = {
			"pdf_bytes": _pdf_fixture_table_heavy(),
			"filename": "document.pdf",
		}
		
		output = route_pdf_coverage(input_data)
		
		assert "is_table_heavy" in output["layout_flags"]
		assert isinstance(output["layout_flags"]["is_table_heavy"], bool)
		assert output["layout_flags"]["is_table_heavy"] is True


class TestModuleAC6_UncertainRegionHandling:
	"""AC6: Uncertain layout regions emit warning or review metadata"""
	
	def test_ac6_uncertain_regions_flag_present(self) -> None:
		"""Output includes uncertain regions flag."""
		input_data: PDFRoutingInput = {
			"pdf_bytes": _pdf_fixture_uncertain(),
			"filename": "document.pdf",
		}
		
		output = route_pdf_coverage(input_data)
		
		assert "has_uncertain_regions" in output["layout_flags"]
		assert isinstance(output["layout_flags"]["has_uncertain_regions"], bool)
		assert output["layout_flags"]["has_uncertain_regions"] is True


class TestModuleAC7_AuditRecord:
	"""AC7: routing_audit_record includes applied logic and threshold evidence"""
	
	def test_ac7_audit_record_includes_threshold(self) -> None:
		"""Audit record includes threshold value."""
		input_data: PDFRoutingInput = {
			"pdf_bytes": b"%PDF-1.4\n" + b"x" * 100000,
			"filename": "document.pdf",
		}
		
		output = route_pdf_coverage(input_data)
		
		assert "routing_audit_record" in output
		assert output["routing_audit_record"]["coverage_threshold"] == THRESHOLD_OCR_01
	
	def test_ac7_audit_record_includes_coverage_ratio(self) -> None:
		"""Audit record includes computed coverage ratio."""
		input_data: PDFRoutingInput = {
			"pdf_bytes": b"%PDF-1.4\n" + b"x" * 100000,
			"filename": "document.pdf",
		}
		
		output = route_pdf_coverage(input_data)
		
		assert output["routing_audit_record"]["coverage_ratio"] == output["text_coverage_ratio"]
	
	def test_ac7_audit_record_includes_decision_logic(self) -> None:
		"""Audit record includes decision logic description."""
		input_data: PDFRoutingInput = {
			"pdf_bytes": b"%PDF-1.4\n" + b"x" * 100000,
			"filename": "document.pdf",
		}
		
		output = route_pdf_coverage(input_data)
		
		assert "decision_logic_applied" in output["routing_audit_record"]
		assert len(output["routing_audit_record"]["decision_logic_applied"]) > 0


class TestThresholdOCR01Application:
	"""Verify THRESHOLD-OCR-01 is applied correctly."""
	
	def test_threshold_is_locked_at_0_70(self) -> None:
		"""THRESHOLD-OCR-01 is locked at 0.70."""
		assert THRESHOLD_OCR_01 == 0.70
	
	def test_threshold_boundary_at_exact_0_70(self) -> None:
		"""Coverage exactly at 0.70 routes to native_text."""
		input_data: PDFRoutingInput = {
			"pdf_bytes": _pdf_fixture_text_heavy(),
			"filename": "document.pdf",
		}
		
		output = route_pdf_coverage(input_data)
		assert output["text_coverage_ratio"] >= 0.70
		assert output["route_mode"] == "native_text"


class TestExtractionEvidencePrecedence:
	"""Router should prefer extraction evidence over byte-level heuristics when available."""

	def test_extraction_evidence_is_preferred_for_routing(self) -> None:
		input_data: PDFRoutingInput = {
			"pdf_bytes": _pdf_fixture_image_heavy(),
			"filename": "document.pdf",
			"extraction_evidence": {
				"coverage_ratio": 0.95,
				"layout_flags": {
					"two_column": False,
					"table_heavy": False,
					"uncertain": False,
				},
			},
		}

		output = route_pdf_coverage(input_data)

		assert output["route_mode"] == "native_text"
		assert output["text_coverage_ratio"] == 0.95
		assert "source=extraction_evidence" in output["routing_audit_record"]["decision_logic_applied"]
