# FILE: tests/unit/intake_canonicalization/test_file_type_detection_router.py
# MODULE: MODULE-001-11 — File Type Detection Router
# EPIC: EPIC-001 — Data Extraction & Validation (Chunk 4 / FR-024 Amendment)
# RESPONSIBILITY: Reserve unit tests for file type detection acceptance criteria.
# EXPORTS: Unit test suite.
# DEPENDS_ON: intake_canonicalization/file_type_detection_router.py
# ACCEPTANCE_CRITERIA:
#   - File type detection acceptance criteria are testable from this unit boundary.
#   - No live external library dependency is required by the tests.
# HUMAN_REVIEW: No.

import pytest

from intake_canonicalization.file_type_detection_router import detect_file_type, FileTypeRoutingInput


class TestModuleAC1_PDFDetection:
	"""AC1: PDF input with consistent signature routes as detected_type=pdf"""
	
	def test_ac1_pdf_mime_type_detected(self) -> None:
		"""PDF detected via MIME type."""
		input_data: FileTypeRoutingInput = {
			"file_bytes": b"%PDF-1.4\n%test",
			"filename": "document.pdf",
			"content_type": "application/pdf",
		}
		
		output = detect_file_type(input_data)
		
		assert output["detected_type"] == "pdf"
		assert output["route_target"] == "pdf"
	
	def test_ac1_pdf_magic_bytes_detected(self) -> None:
		"""PDF detected via magic bytes."""
		input_data: FileTypeRoutingInput = {
			"file_bytes": b"%PDF-1.4\n" + b"x" * 1000,
			"filename": "document.pdf",
			"content_type": "application/pdf",
		}
		
		output = detect_file_type(input_data)
		
		assert output["detected_type"] == "pdf"
		assert output["error_reason"] is None


class TestModuleAC2_DOCXDetection:
	"""AC2: DOCX input with consistent signature routes as detected_type=docx"""
	
	def test_ac2_docx_mime_type_detected(self) -> None:
		"""DOCX detected via MIME type."""
		input_data: FileTypeRoutingInput = {
			"file_bytes": b"PK\x03\x04" + b"x" * 100,  # ZIP header
			"filename": "document.docx",
			"content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
		}
		
		output = detect_file_type(input_data)
		
		assert output["detected_type"] == "docx"
		assert output["route_target"] == "docx"
	
	def test_ac2_docx_extension_detected(self) -> None:
		"""DOCX detected via file extension."""
		input_data: FileTypeRoutingInput = {
			"file_bytes": b"PK\x03\x04" + b"x" * 100,
			"filename": "document.docx",
			"content_type": None,
		}
		
		output = detect_file_type(input_data)
		
		assert output["detected_type"] == "docx"


class TestModuleAC3_XLSXDetection:
	"""AC3: XLSX input with consistent signature routes as detected_type=xlsx"""
	
	def test_ac3_xlsx_detected(self) -> None:
		"""XLSX detected."""
		input_data: FileTypeRoutingInput = {
			"file_bytes": b"PK\x03\x04" + b"x" * 100,  # ZIP header
			"filename": "spreadsheet.xlsx",
			"content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
		}
		
		output = detect_file_type(input_data)
		
		assert output["detected_type"] == "xlsx"
		assert output["route_target"] == "xlsx"


class TestModuleAC4_UnknownTypeHandling:
	"""AC4: Unknown or inconsistent file signatures emit warning or unknown type state"""
	
	def test_ac4_unknown_magic_bytes(self) -> None:
		"""Unknown file type emits unknown state."""
		input_data: FileTypeRoutingInput = {
			"file_bytes": b"UNKNOWN_SIGNATURE" + b"x" * 100,
			"filename": "unknown_file.bin",
			"content_type": None,
		}
		
		output = detect_file_type(input_data)
		
		assert output["detected_type"] == "unknown"
		assert output["route_target"] == "review_required"
	
	def test_ac4_inconsistent_types_emit_warning(self) -> None:
		"""Inconsistent types between MIME and extension emit warning."""
		input_data: FileTypeRoutingInput = {
			"file_bytes": b"%PDF" + b"x" * 100,
			"filename": "document.docx",  # Mismatch: PDF content but DOCX extension
			"content_type": "application/pdf",
		}
		
		output = detect_file_type(input_data)
		
		# Should detect PDF via magic bytes but emit warnings
		assert output["detected_type"] == "pdf"
		assert len(output["warning_flags"]) > 0
		assert any("inconsistent" in w.lower() for w in output["warning_flags"])


class TestModuleAC5_RouteTargetConsistency:
	"""AC5: route_target is consistent with detected_type output"""
	
	def test_ac5_route_target_matches_detected_type(self) -> None:
		"""route_target matches detected_type for consistent inputs."""
		test_cases = [
			(b"%PDF" + b"x" * 100, "document.pdf", "application/pdf", "pdf"),
			(b"PK\x03\x04" + b"x" * 100, "document.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "docx"),
		]
		
		for file_bytes, filename, content_type, expected_type in test_cases:
			input_data: FileTypeRoutingInput = {
				"file_bytes": file_bytes,
				"filename": filename,
				"content_type": content_type,
			}
			
			output = detect_file_type(input_data)
			
			assert output["route_target"] == output["detected_type"]
			assert output["detected_type"] == expected_type


class TestModuleAC6_ErrorHandling:
	"""AC6: Detection failure yields explicit error_reason and no silent drop"""
	
	def test_ac6_empty_bytes_yields_error(self) -> None:
		"""Empty file bytes yield explicit error."""
		input_data: FileTypeRoutingInput = {
			"file_bytes": b"",
			"filename": "empty.bin",
			"content_type": None,
		}
		
		output = detect_file_type(input_data)
		
		assert output["detected_type"] == "unknown"
		assert output["error_reason"] is not None
		assert len(output["error_reason"]) > 0
		assert output["route_target"] == "review_required"
	
	def test_ac6_undetectable_type_yields_error(self) -> None:
		"""Undetectable type yields explicit error with review routing."""
		input_data: FileTypeRoutingInput = {
			"file_bytes": b"UNRECOGNIZED_MAGIC_BYTES" + b"x" * 100,
			"filename": "unknown.tmp",
			"content_type": None,
		}
		
		output = detect_file_type(input_data)
		
		assert output["detected_type"] == "unknown"
		assert output["error_reason"] is not None
		assert output["route_target"] == "review_required"


class TestModuleConfidenceMetric:
	"""Confidence scoring for detection reliability."""
	
	def test_confidence_high_for_consistent_inputs(self) -> None:
		"""High confidence for consistent MIME, extension, magic bytes."""
		input_data: FileTypeRoutingInput = {
			"file_bytes": b"%PDF" + b"x" * 100,
			"filename": "document.pdf",
			"content_type": "application/pdf",
		}
		
		output = detect_file_type(input_data)
		
		assert output["detection_confidence"] >= 0.90
	
	def test_confidence_lower_for_inconsistent_inputs(self) -> None:
		"""Lower confidence for inconsistent inputs."""
		input_data: FileTypeRoutingInput = {
			"file_bytes": b"%PDF" + b"x" * 100,
			"filename": "document.docx",  # Mismatch
			"content_type": "application/pdf",
		}
		
		output = detect_file_type(input_data)
		
		assert output["detection_confidence"] < 0.95


class TestPDFHardening:
	"""PDF direct routing requires real PDF magic bytes."""

	def test_pdf_mime_without_pdf_magic_routes_to_review(self) -> None:
		input_data: FileTypeRoutingInput = {
			"file_bytes": b"NOT_A_REAL_PDF" + b"x" * 100,
			"filename": "document.pdf",
			"content_type": "application/pdf",
		}

		output = detect_file_type(input_data)

		assert output["detected_type"] == "pdf"
		assert output["route_target"] == "review_required"
		assert "pdf_magic_bytes_missing" in output["warning_flags"]

	def test_pdf_extension_only_without_pdf_magic_routes_to_review(self) -> None:
		input_data: FileTypeRoutingInput = {
			"file_bytes": b"RANDOM_BYTES" + b"x" * 100,
			"filename": "document.pdf",
			"content_type": None,
		}

		output = detect_file_type(input_data)

		assert output["detected_type"] == "pdf"
		assert output["route_target"] == "review_required"
		assert "pdf_magic_bytes_missing" in output["warning_flags"]
