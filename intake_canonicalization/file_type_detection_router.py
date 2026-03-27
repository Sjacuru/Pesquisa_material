# FILE: intake_canonicalization/file_type_detection_router.py
# MODULE: MODULE-001-11 — File Type Detection Router
# EPIC: EPIC-001 — Data Extraction & Validation (Chunk 4 / FR-024 Amendment)
# RESPONSIBILITY: Detect uploaded file type using MIME plus extension cross-check and route the document into the compatible extraction path.
# EXPORTS: File type detection and routing service.
# DEPENDS_ON: platform/observability.py
# ACCEPTANCE_CRITERIA:
#   AC1: PDF input with consistent signature routes as detected_type=pdf
#   AC2: DOCX input with consistent signature routes as detected_type=docx
#   AC3: XLSX input with consistent signature routes as detected_type=xlsx
#   AC4: Unknown or inconsistent file signatures emit warning or unknown type state
#   AC5: route_target is consistent with detected_type output
#   AC6: Detection failure yields explicit error_reason and no silent drop
# HUMAN_REVIEW: Yes — file-type detection correctness requires expert review.

from __future__ import annotations

import mimetypes
from typing import TypedDict, Optional


class FileTypeRoutingInput(TypedDict, total=False):
	"""Input contract for file type detection router."""
	file_bytes: bytes
	filename: str
	content_type: Optional[str]
	context: dict


class FileTypeRoutingOutput(TypedDict, total=False):
	"""Output contract for file type detection router."""
	detected_type: str  # "pdf", "docx", "xlsx", or "unknown"
	route_target: str
	detection_confidence: float
	warning_flags: list[str]
	error_reason: Optional[str]


# File-type MIME mappings
_MIME_SIGNATURES = {
	"pdf": {
		"mimes": ["application/pdf"],
		"extensions": [".pdf"],
		"magic_bytes": [b"%PDF"],
	},
	"docx": {
		"mimes": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
		"extensions": [".docx"],
		"magic_bytes": [b"PK\x03\x04"],  # ZIP header
	},
	"xlsx": {
		"mimes": ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
		"extensions": [".xlsx"],
		"magic_bytes": [b"PK\x03\x04"],  # ZIP header
	},
}


def _extract_extension(filename: str) -> str:
	"""Extract file extension from filename, normalized."""
	if not filename:
		return ""
	import os
	_, ext = os.path.splitext(filename.lower())
	return ext


def _detect_by_magic_bytes(file_bytes: bytes) -> Optional[str]:
	"""Detect file type from magic bytes (binary signature)."""
	if not file_bytes or len(file_bytes) < 4:
		return None
	
	# PDF has unique magic bytes
	if file_bytes.startswith(b"%PDF"):
		return "pdf"
	
	# ZIP header is shared by DOCX and XLSX; cannot distinguish by magic bytes alone
	# Return None for ZIP-based formats; let MIME type or extension decide
	if file_bytes.startswith(b"PK\x03\x04"):
		return None
	
	return None


def _detect_by_mime_type(content_type: Optional[str]) -> Optional[str]:
	"""Detect file type from MIME type string."""
	if not content_type:
		return None
	
	content_type = content_type.lower().strip()
	
	for file_type, signatures in _MIME_SIGNATURES.items():
		if content_type in signatures["mimes"]:
			return file_type
	
	return None


def _detect_by_extension(filename: str) -> Optional[str]:
	"""Detect file type from file extension."""
	ext = _extract_extension(filename)
	if not ext:
		return None
	
	for file_type, signatures in _MIME_SIGNATURES.items():
		if ext in signatures["extensions"]:
			return file_type
	
	return None


def _cross_check_consistency(
	mime_type: Optional[str],
	extension: Optional[str],
	magic_bytes: Optional[str],
) -> tuple[bool, list[str]]:
	"""Cross-check consistency between MIME, extension, and magic bytes. Returns (is_consistent, warnings)."""
	warnings = []
	detected_types = set()
	
	if mime_type:
		detected_types.add(mime_type)
	if extension:
		detected_types.add(extension)
	if magic_bytes:
		detected_types.add(magic_bytes)
	
	if len(detected_types) > 1:
		warnings.append(f"Type mismatch detected: MIME={mime_type}, Extension={extension}, Magic={magic_bytes}")
		return False, warnings
	
	return True, warnings


def detect_file_type(input_data: FileTypeRoutingInput) -> FileTypeRoutingOutput:
	"""
	Detect uploaded file type using MIME plus extension cross-check.
	
	Input: file_bytes, filename, optional content_type, context
	Output: detected_type, route_target, detection_confidence, warning_flags, error_reason
	
	Behavior:
	- Cross-check MIME and filename extension
	- Emit detected_type and route_target
	- Emit warning or explicit error_reason when type is inconsistent or unknown
	- Preserve no-silent-drop behavior by routing uncertainty to review path
	
	Detection priority:
	1. MIME type (most reliable for ambiguous formats like DOCX/XLSX)
	2. Magic bytes (PDF is unambiguous)
	3. File extension (fallback)
	"""
	file_bytes = input_data.get("file_bytes", b"")
	filename = input_data.get("filename", "")
	content_type = input_data.get("content_type")
	
	warnings: list[str] = []
	
	if not file_bytes:
		return FileTypeRoutingOutput(
			detected_type="unknown",
			route_target="review_required",
			detection_confidence=0.0,
			warning_flags=["empty_file_bytes"],
			error_reason="File bytes are empty; cannot detect type",
		)
	
	if not filename:
		warnings.append("filename_missing")
	
	# Detect by each method
	mime_detected = _detect_by_mime_type(content_type)
	magic_detected = _detect_by_magic_bytes(file_bytes)
	ext_detected = _detect_by_extension(filename)
	
	# Determine final detected type with priority:
	# 1. MIME type (most reliable for ambiguous formats)
	# 2. Magic bytes (unambiguous PDF detection)
	# 3. Extension (fallback)
	detected_type = mime_detected or magic_detected or ext_detected
	
	if not detected_type:
		return FileTypeRoutingOutput(
			detected_type="unknown",
			route_target="review_required",
			detection_confidence=0.0,
			warning_flags=warnings,
			error_reason="Could not determine file type from MIME, magic bytes, or extension",
		)
	
	# Cross-check consistency between detected type and other metadata
	is_consistent = True

	# Harden PDF path: direct PDF routing requires PDF magic bytes.
	# This prevents spoofed MIME/extension-only PDFs from bypassing review.
	if detected_type == "pdf" and magic_detected != "pdf":
		warnings.append("pdf_magic_bytes_missing")
		is_consistent = False

	if mime_detected and magic_detected and mime_detected != magic_detected:
		# MIME and magic bytes disagree; trust MIME for ambiguous formats
		if detected_type == mime_detected:
			warnings.append(f"magic_bytes_inconsistent_with_mime")
			is_consistent = False
	
	if ext_detected and detected_type != ext_detected:
		warnings.append(f"extension_inconsistent_with_detected_type")
		is_consistent = False
	
	# Set confidence based on consistency
	if is_consistent and all([mime_detected, magic_detected or ext_detected]):
		confidence = 0.95  # Consistent across multiple sources
	elif mime_detected:
		confidence = 0.90  # MIME type is reliable
	elif magic_detected:
		confidence = 0.85  # Magic bytes are reliable
	else:
		confidence = 0.70  # Extension-only detection is less reliable
	
	# Route target: consistent types get direct routing; inconsistent route to review
	route_target = detected_type if is_consistent else "review_required"
	
	return FileTypeRoutingOutput(
		detected_type=detected_type,
		route_target=route_target,
		detection_confidence=confidence,
		warning_flags=warnings,
		error_reason=None,
	)
