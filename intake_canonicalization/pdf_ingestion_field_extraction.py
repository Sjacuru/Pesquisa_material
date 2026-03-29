# FILE: intake_canonicalization/pdf_ingestion_field_extraction.py
# MODULE: MODULE-001-01 — PDF Ingestion & Field Extraction
# EPIC: EPIC-001 — Data Extraction & Validation
# RESPONSIBILITY: Ingest uploaded PDFs and expose extracted item candidates for downstream validation.
# EXPORTS: Extraction service stub.
# DEPENDS_ON: platform/storage.py, platform/observability.py.
# ACCEPTANCE_CRITERIA:
#   - Uploaded PDF inputs are accepted only through the defined intake boundary.
#   - Extracted item candidates are emitted through a deterministic module interface.
# HUMAN_REVIEW: Yes — mixed-document parsing correctness requires expert review.

from __future__ import annotations

import io
import re
import numpy as np

import pdfplumber
import pypdfium2 as pdfium

from intake_canonicalization.directive_reconciliation_resolver import (
	reconcile_directive_outputs,
)
from intake_canonicalization.directive_deterministic_parser import (
	apply_deterministic_directive_parser,
)
from intake_canonicalization.directive_runtime_config import (
	parse_directive_runtime_config,
)
from intake_canonicalization.llm_fallback_gateway import invoke_llm_fallback

# Optional OCR import (graceful degradation if unavailable)
try:
	from easyocr import Reader
	_OCR_AVAILABLE = True
except ImportError:
	_OCR_AVAILABLE = False


def _clamp_confidence(value: float) -> float:
	if value < 0.0:
		return 0.0
	if value > 1.0:
		return 1.0
	return round(value, 2)


def _normalize_space(value: str) -> str:
	return " ".join((value or "").strip().split())


_BOOKISH_CATEGORIES = {"book", "dictionary", "apostila"}
_BOOK_CORE_SEGMENT_KEYWORDS = (
	"student",
	"livre",
	"cahier",
	"dictionary",
	"dicionário",
	"niveau",
	"reader",
	"workbook",
)
_BOOK_SUBJECT_SEGMENTS = {
	"ciências",
	"história",
	"geografia",
	"matemática",
	"língua portuguesa",
	"língua inglesa",
	"língua francesa",
	"ensino religioso",
	"educação musical",
}
_OBSERVATION_PREFIXES = (
	"de uso",
	"será ",
	"já ",
	"pode ",
	"ver ",
	"para ",
	"não ",
	"uso ",
)
_OBSERVATION_KEYWORDS = (
	"artes visuais",
	"educação musical",
	"língua portuguesa",
	"língua inglesa",
	"língua francesa",
	"ensino religioso",
	"geografia",
	"história",
	"ciências",
	"matemática",
	"reprografia",
	"csb",
	"tinta azul",
	"tinta vermelha",
	"edição",
	"edição catequética",
)


def _clean_note_text(value: str) -> str:
	text = _normalize_space(value)
	text = text.strip("-–:;,. ")
	return _normalize_space(text)


def _looks_like_observation_segment(segment: str, category: str) -> bool:
	lower = segment.lower().strip()
	if not lower:
		return False
	if any(lower.startswith(prefix) for prefix in _OBSERVATION_PREFIXES):
		return True
	if any(keyword in lower for keyword in _OBSERVATION_KEYWORDS):
		return True
	if category not in _BOOKISH_CATEGORIES and lower.startswith("para "):
		return True
	if category not in _BOOKISH_CATEGORIES and any(color in lower for color in ("azul", "vermelha", "vermelho", "preta", "preto")):
		return True
	if len(lower) <= 5 and lower.upper() == lower and any(ch.isalpha() for ch in lower):
		return True
	return False


def _extract_parenthetical_notes(name: str) -> tuple[str, list[str]]:
	notes = [_clean_note_text(match.group(1)) for match in re.finditer(r"\(([^)]+)\)", name)]
	clean_name = re.sub(r"\s*\(([^)]+)\)", "", name)
	return _normalize_space(clean_name), [note for note in notes if note]


def _extract_trailing_author_note(name: str) -> tuple[str, str]:
	match = re.match(
		r"^(?P<title>.+)\s+(?P<author>[A-ZÀ-ÖØ-Ý][\wÀ-ÖØ-öø-ÿ'’.-]+(?:\s+[A-ZÀ-ÖØ-Ý][\wÀ-ÖØ-öø-ÿ'’.-]+){1,4})$",
		name,
	)
	if not match:
		return name, ""
	title = _normalize_space(match.group("title"))
	author = _normalize_space(match.group("author"))
	if len(title.split()) < 2:
		return name, ""
	if any(char.isdigit() for char in author):
		return name, ""
	if any(keyword in author.lower() for keyword in ("língua", "portuguesa", "francesa", "inglesa", "ciências", "história", "matemática")):
		return name, ""
	return title, author


def _looks_like_book_note_segment(segment: str) -> bool:
	lower = segment.lower().strip()
	if not lower:
		return False
	if re.fullmatch(r"niveau\s+[a-z]?\d+", lower):
		return False
	if _looks_like_observation_segment(segment, "book"):
		return True
	if lower in _BOOK_SUBJECT_SEGMENTS:
		return True
	if re.search(r"\b\d{4}\b", lower):
		return True
	if re.search(r"\b\d+ª?\s*(?:ano|ed)\b", lower):
		return True
	if lower in {"csb"}:
		return True
	return False


def _split_name_and_notes(name: str, category: str) -> tuple[str, str]:
	base_name = _normalize_space(name)
	notes: list[str] = []

	base_name, paren_notes = _extract_parenthetical_notes(base_name)
	notes.extend(paren_notes)

	if category in _BOOKISH_CATEGORIES:
		segments = [_normalize_space(segment) for segment in re.split(r"\s+[–-]\s+", base_name) if _normalize_space(segment)]
		if len(segments) > 1:
			name_segments = [segments[0]]
			for segment in segments[1:]:
				lower = segment.lower()
				if len(name_segments) == 1 and not _looks_like_book_note_segment(segment):
					name_segments.append(segment)
				elif len(name_segments) == 1 and any(keyword in lower for keyword in _BOOK_CORE_SEGMENT_KEYWORDS):
					name_segments.append(segment)
				else:
					notes.append(segment)
			base_name = " - ".join(name_segments)

		base_name, author_note = _extract_trailing_author_note(base_name)
		if author_note:
			notes.append(author_note)
	else:
		segments = [_normalize_space(segment) for segment in re.split(r"\s+[–-]\s+", base_name) if _normalize_space(segment)]
		if len(segments) > 1:
			base_name = segments[0]
			for segment in segments[1:]:
				if _looks_like_observation_segment(segment, category):
					notes.append(segment)
				else:
					base_name = _normalize_space(f"{base_name} {segment}")

		para_match = re.match(r"^(?P<name>.+?)\s+(?P<obs>para\s+.+)$", base_name, flags=re.IGNORECASE)
		if para_match:
			base_name = _normalize_space(para_match.group("name"))
			notes.append(_clean_note_text(para_match.group("obs")))

	base_name = _normalize_space(base_name).strip("-–:;,. ")
	clean_notes = [_clean_note_text(note) for note in notes if _clean_note_text(note)]
	clean_notes = list(dict.fromkeys(clean_notes))
	return base_name, " | ".join(clean_notes)


_BOOK_SECTION_HEADINGS = {
	"língua portuguesa": "book",
	"matemática": "book",
	"geografia": "apostila",
	"história": "book",
	"ciências": "book",
	"educação musical": "book",
	"ensino religioso": "book",
	"língua inglesa": "book",
	"língua francesa": "book",
	"paradidático:": "book",
	"material opcional:": "dictionary",
	"dicionário:": "dictionary",
}

_IGNORED_PAGE_HEADINGS = (
	"livraria e papelaria",
	"observações",
	"uniformes",
	"endereços para compra",
	"anotações",
)


def _normalize_pdf_lines(text: str) -> list[str]:
	return [_normalize_space(line) for line in str(text or "").splitlines() if _normalize_space(line)]


def _page_heading(lines: list[str]) -> str:
	for line in lines[:3]:
		if line.isdigit():
			continue
		return line.lower()
	return ""


def _looks_like_author_line(line: str) -> bool:
	if any(char.isdigit() for char in line):
		return False
	if line.startswith(("Editora", "ISBN", "(")):
		return False
	lower = line.lower()
	if " – " in lower and "tradução" in lower:
		return True
	if "," not in line and " e " not in lower and " and " not in lower:
		return False
	words = [word for word in re.split(r"\s+", line) if word]
	if len(words) < 2 or len(words) > 12:
		return False
	capitalized = 0
	for word in words:
		clean = word.strip(",.;:()[]-'\"")
		if not clean:
			continue
		if clean[0].isupper():
			capitalized += 1
	return capitalized >= max(2, len(words) - 1)


def _looks_like_metadata_line(line: str) -> bool:
	lower = line.lower()
	if lower.startswith("isbn"):
		return True
	if lower.startswith("editora"):
		return True
	if lower.startswith("autor:") or lower.startswith("autores:"):
		return True
	if lower.startswith("edição") or lower.startswith("ed.") or re.search(r"\b\d+ª?\s*ed\.", lower):
		return True
	if line.startswith("("):
		return True
	if _looks_like_author_line(line):
		return True
	if lower in {"moderna", "cle international", "collection découverte bd"}:
		return True
	return False


def _looks_like_fragment_line(line: str) -> bool:
	lower = line.lower().strip()
	if not lower:
		return True
	if lower in {"único"}:
		return True
	if lower.startswith("os alunos que não estudavam"):
		return True
	if lower.startswith("reprografia em fevereiro"):
		return True
	if line[:1].islower():
		return True
	if len(line.split()) <= 2 and len(line) <= 24:
		return True
	return False


def _finalize_book_candidate(current: dict | None, entries: list[dict]) -> None:
	if not current:
		return
	title = _normalize_space(" ".join(current.get("title_lines") or []))
	if not title:
		return
	title, notes = _split_name_and_notes(title, current.get("category") or "book")
	if not title:
		return
	entries.append(
		{
			"name": title,
			"notes": notes,
			"category": current.get("category") or "book",
			"quantity": "1 un",
			"isbn": current.get("isbn") or "",
		}
	)


def _parse_book_column_text(column_text: str) -> list[dict]:
	lines = _normalize_pdf_lines(column_text)
	entries: list[dict] = []
	current: dict | None = None
	current_category = "book"

	for line in lines:
		lower = line.lower()
		if lower == "livros" or line.isdigit():
			continue
		if lower.startswith("os alunos que não estudavam"):
			continue
		if lower in _BOOK_SECTION_HEADINGS:
			_finalize_book_candidate(current, entries)
			current = None
			current_category = _BOOK_SECTION_HEADINGS[lower]
			continue

		isbn_value, _ = _extract_isbn_field(line)
		if isbn_value:
			if current is None:
				current = {"title_lines": [line], "category": current_category, "isbn": isbn_value}
			else:
				current["isbn"] = isbn_value
			continue

		if current is None:
			current = {"title_lines": [line], "category": current_category, "isbn": ""}
			continue

		if _looks_like_metadata_line(line) or lower.startswith("os alunos que não estudavam"):
			current.setdefault("metadata", []).append(line)
			continue

		if _looks_like_fragment_line(line):
			if current.get("metadata"):
				current.setdefault("metadata", []).append(line)
			else:
				current.setdefault("title_lines", []).append(line)
			continue

		if current.get("metadata") or current.get("isbn"):
			_finalize_book_candidate(current, entries)
			current = {"title_lines": [line], "category": current_category, "isbn": ""}
		else:
			current.setdefault("title_lines", []).append(line)

	_finalize_book_candidate(current, entries)
	return entries


def _parse_supply_page_text(page_text: str) -> list[dict]:
	raw_lines: list[str] = []
	for raw_line in str(page_text or "").splitlines():
		split_line = re.sub(r"\s{2,}(?=\d+\s+[A-Za-zÀ-ÖØ-öø-ÿ])", "\n", raw_line)
		raw_lines.extend(split_line.splitlines())

	lines = [_normalize_space(line) for line in raw_lines if _normalize_space(line)]
	entries: list[dict] = []
	current: str | None = None

	for line in lines:
		lower = line.lower()
		if lower in {"material escolar", "material e", "escolar"} or line.isdigit():
			continue
		if re.match(r"^\d+\s+", line):
			if current:
				entries.append(current)
			current = line
		elif current:
			current = _normalize_space(f"{current} {line}")

	if current:
		entries.append(current)

	parsed_entries: list[dict] = []
	for entry in entries:
		quantity_value, _ = _extract_quantity_field(entry)
		name = re.sub(r"^\d+(?:[.,]\d+)?\s*(?:un|unidade|unidades)?\s*", "", entry, count=1, flags=re.IGNORECASE).strip()
		if not name:
			continue
		category = "general supplies" if "caderno" not in name.lower() else "notebook"
		clean_name, clean_notes = _split_name_and_notes(name, category)
		parsed_entries.append(
			{
				"name": clean_name,
				"notes": clean_notes,
				"category": category,
				"quantity": quantity_value or "1 un",
				"isbn": "",
			}
		)
	return parsed_entries


def _extract_page_columns(page) -> list[str]:
	midpoint = page.width / 2
	left_text = page.crop((0, 0, midpoint, page.height)).extract_text() or ""
	right_text = page.crop((midpoint, 0, page.width, page.height)).extract_text() or ""
	if len(left_text.strip()) >= 80 and len(right_text.strip()) >= 80:
		return [left_text, right_text]
	full_text = page.extract_text() or ""
	return [full_text] if full_text.strip() else []


def _extract_structured_candidates_from_pdf(pdf_bytes: bytes) -> list[dict]:
	entries: list[dict] = []
	try:
		with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
			for page in pdf.pages:
				full_text = page.extract_text() or ""
				lines = _normalize_pdf_lines(full_text)
				heading = _page_heading(lines)
				if not heading:
					continue
				if any(marker in heading for marker in _IGNORED_PAGE_HEADINGS):
					continue
				if "livros" in heading:
					for column_text in _extract_page_columns(page):
						entries.extend(_parse_book_column_text(column_text))
				elif "material" in heading:
					entries.extend(_parse_supply_page_text(full_text))
	except Exception:
		return []
	return entries


def _decode_pdf_text(uploaded_pdf_document: dict) -> str:
	content_type = str(uploaded_pdf_document.get("content_type") or "").lower()
	if content_type != "application/pdf":
		raise ValueError("uploaded_pdf_document must declare content_type='application/pdf'")

	if isinstance(uploaded_pdf_document.get("text"), str):
		return uploaded_pdf_document["text"]

	if isinstance(uploaded_pdf_document.get("content_bytes"), (bytes, bytearray)):
		return uploaded_pdf_document["content_bytes"].decode("utf-8", errors="ignore")

	raise ValueError("uploaded_pdf_document must contain either 'text' or 'content_bytes'")


def _line_category(line_text: str, category_matrix_reference: dict[str, dict[str, str]]) -> tuple[str, float]:
	lower = line_text.lower()

	if "isbn" in lower or "livro" in lower:
		if "book" in category_matrix_reference:
			return "book", 0.96

	if "dictionary" in lower or "dicionario" in lower:
		if "dictionary" in category_matrix_reference:
			return "dictionary", 0.96

	if "apostila" in lower:
		if "apostila" in category_matrix_reference:
			return "apostila", 0.95

	if "caderno" in lower:
		if "notebook" in category_matrix_reference:
			return "notebook", 0.9

	if "lapis" in lower or "lápis" in lower or "borracha" in lower:
		if "general supplies" in category_matrix_reference:
			return "general supplies", 0.88

	if category_matrix_reference:
		first_category = next(iter(category_matrix_reference.keys()))
		return first_category, 0.75

	return "unknown", 0.7


def _extract_quantity_field(line_text: str) -> tuple[str, float]:
	match = re.search(r"\b(\d+(?:[.,]\d+)?)\s*(un|unidade|unidades|g|kg|ml|l|cm|mm|pacote|caixa)?\b", line_text, re.IGNORECASE)
	if not match:
		return "", 0.0
	value = _normalize_space(match.group(0))
	return value, 0.87


def _extract_isbn_field(line_text: str) -> tuple[str, float]:
	match = re.search(r"(?:isbn\s*[:\-]?\s*)?([0-9Xx\-\s]{10,20})", line_text)
	if not match:
		return "", 0.0
	raw_value = _normalize_space(match.group(1))
	digits_only = re.sub(r"[^0-9Xx]", "", raw_value)
	if len(digits_only) not in (10, 13):
		return "", 0.0
	return raw_value, 0.93


def _split_seller_list(raw_value: str) -> list[str]:
	parts = re.split(r"[,;]", raw_value)
	return [_normalize_space(part) for part in parts if _normalize_space(part)]


def _extract_pdf_native_text(pdf_bytes: bytes) -> tuple[str, float]:
	"""
	Extract text from PDF using native text streams (for PDFs with embedded text).
	
	Returns: (extracted_text, coverage_ratio)
	- coverage_ratio: 0.0–1.0 indicating quality of extraction
	"""
	try:
		with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
			all_text = ""
			non_empty_pages = 0
			for page in pdf.pages:
				page_text = page.extract_text() or ""
				if page_text.strip():
					non_empty_pages += 1
				all_text += page_text + "\n"
			
			page_count = max(1, len(pdf.pages))
			expected_length = page_count * 700
			char_score = min(1.0, len(all_text.strip()) / max(expected_length, 100))
			page_score = non_empty_pages / page_count
			coverage = round(min(1.0, (char_score * 0.8) + (page_score * 0.2)), 2)
			
			return all_text.strip(), coverage
	except Exception as e:
		return "", 0.0


def _extract_pdf_with_ocr(pdf_bytes: bytes, ocr_instance=None) -> tuple[str, float]:
	"""
	Extract text from PDF using OCR by converting pages to images using EasyOCR.
	
	Returns: (extracted_text, coverage_ratio)
	- coverage_ratio: 1.0 if extraction successful, 0.0 if failed or OCR unavailable
	"""
	if not _OCR_AVAILABLE or ocr_instance is None:
		return "", 0.0
	
	try:
		# Render PDF pages to images without external Poppler dependency
		document = pdfium.PdfDocument(pdf_bytes)
		images = []
		for page_index in range(len(document)):
			page = document.get_page(page_index)
			bitmap = page.render(scale=2.5)
			images.append(bitmap.to_pil())
			page.close()
		document.close()
		all_text = ""
		
		for image in images:
			# EasyOCR readtext returns list of [[bbox], text, confidence] tuples
			result = ocr_instance.readtext(np.array(image), detail=1)
			
			# Extract text from all detections, sorted by vertical position
			page_lines = []
			if result:
				for line_result in result:
					if line_result:
						text, confidence = line_result[1], line_result[2]
						if confidence > 0.3:  # Filter low-confidence detections
							page_lines.append(text)
			
			page_text = "\n".join(page_lines)
			all_text += page_text + "\n"
		
		# Coverage for OCR: if we extracted reasonable amount of text, mark as success
		coverage = 1.0 if len(all_text.strip()) > 100 else 0.0
		return all_text.strip(), coverage
	
	except Exception as e:
		return "", 0.0


def _detect_layout_flags(text: str) -> dict[str, bool]:
	"""
	Detect layout characteristics from extracted text.
	
	Returns: {"two_column": bool, "table_heavy": bool, "uncertain": bool}
	"""
	lines = text.split('\n')
	
	# Two-column detection: look for columns pattern in first 50 lines
	two_column = False
	column_pattern = 0
	for line in lines[:50]:
		# Pattern: multiple separated segments per line might indicate columns
		if len(line.split('  ')) >= 2:  # Multiple spaces
			column_pattern += 1
	if column_pattern >= 10:
		two_column = True
	
	# Table-heavy detection: look for alignment patterns and numbers
	table_heavy = False
	numeric_lines = sum(1 for line in lines if any(c.isdigit() for c in line))
	if len(lines) > 0 and numeric_lines / len(lines) > 0.6:
		table_heavy = True
	
	# Uncertain: low text density or high symbol density
	uncertain = False
	if len(text) < 500:  # Very short extraction
		uncertain = True
	
	return {
		"two_column": two_column,
		"table_heavy": table_heavy,
		"uncertain": uncertain,
	}


def _extract_pdf_text_with_fallback(
	pdf_bytes: bytes,
	coverage_threshold: float = 0.70,
	ocr_instance=None
) -> dict:
	"""
	Extract text from PDF with native-first, OCR-fallback strategy.
	
	Returns: {
		"text": str,
		"coverage_ratio": float,
		"extraction_mode": "native" | "ocr_fallback" | "failed",
		"layout_flags": dict,
		"errors": list[str]
	}
	"""
	native_text, native_coverage = _extract_pdf_native_text(pdf_bytes)
	errors = []

	# Compatibility path for legacy tests/mocks that pass plain text bytes
	if not pdf_bytes.startswith(b"%PDF"):
		decoded_text = pdf_bytes.decode("utf-8", errors="ignore").strip()
		if decoded_text:
			return {
				"text": decoded_text,
				"coverage_ratio": 1.0,
				"extraction_mode": "legacy_bytes",
				"layout_flags": _detect_layout_flags(decoded_text),
				"errors": [],
			}
	
	# Use native if coverage is acceptable
	if native_coverage >= coverage_threshold:
		return {
			"text": native_text,
			"coverage_ratio": native_coverage,
			"extraction_mode": "native",
			"layout_flags": _detect_layout_flags(native_text),
			"errors": [],
		}
	
	# Fall back to OCR if native coverage is low
	if _OCR_AVAILABLE and ocr_instance is not None:
		ocr_text, ocr_coverage = _extract_pdf_with_ocr(pdf_bytes, ocr_instance)
		if ocr_coverage > 0:
			return {
				"text": ocr_text,
				"coverage_ratio": ocr_coverage,
				"extraction_mode": "ocr_fallback",
				"layout_flags": _detect_layout_flags(ocr_text),
				"errors": [],
			}
		else:
			errors.append("OCR extraction produced no text")
	else:
		errors.append("OCR not available (paddleocr not installed)")
	
	# Complete failure
	return {
		"text": native_text if native_text else "",  # Return partial native if available
		"coverage_ratio": native_coverage,
		"extraction_mode": "failed",
		"layout_flags": _detect_layout_flags(native_text),
		"errors": errors,
	}


def _build_document_notation_rules(lines: list[str]) -> dict[str, str]:
	rules: dict[str, str] = {}
	pattern = re.compile(
		r"^\s*(\*|\[[^\]]+\]|[A-Za-z])\s*=\s*(?:exclusive|exclusivo|somente|only)\s*(?:at|from|em|na|no|de)?\s*[:\-]?\s*(.+)$",
		re.IGNORECASE,
	)
	for line in lines:
		match = pattern.search(line)
		if not match:
			continue
		marker = _normalize_space(match.group(1))
		seller = _normalize_space(match.group(2))
		if marker and seller:
			rules[marker] = seller
	return rules


def _extract_exclusivity_fields(line_text: str, notation_rules: dict[str, str]) -> tuple[bool, list[str], list[str], str | None, float, float, float, float]:
	required_sellers: list[str] = []
	preferred_sellers: list[str] = []
	source: str | None = None

	line = _normalize_space(line_text)

	preferred_match = re.search(
		r"(?:preferencial|preferred)\s*[:\-]\s*([A-Za-z0-9À-ÖØ-öø-ÿ .,&\-]+(?:\s*[,;]\s*[A-Za-z0-9À-ÖØ-öø-ÿ .,&\-]+)*)",
		line,
		re.IGNORECASE,
	)
	if preferred_match:
		preferred_sellers = _split_seller_list(preferred_match.group(1))

	exclusive_inline_match = re.search(
		r"(?:somente|only|exclusivo(?:\s*em)?|exclusive(?:\s*at|\s*from)?)\s*[:\-]?\s*([A-Za-z0-9À-ÖØ-öø-ÿ .,&\-]+)",
		line,
		re.IGNORECASE,
	)
	if exclusive_inline_match:
		raw_required = exclusive_inline_match.group(1)
		raw_required = re.split(r"\b(?:preferencial|preferred)\b", raw_required, maxsplit=1, flags=re.IGNORECASE)[0]
		required_sellers = _split_seller_list(raw_required)
		source = "document_notation"

	for marker, seller in notation_rules.items():
		if marker and marker in line:
			required_sellers = [seller]
			source = "document_notation"
			break

	school_exclusive = len(required_sellers) > 0

	school_conf = 0.9 if school_exclusive else 0.7
	required_conf = 0.88 if required_sellers else 0.0
	preferred_conf = 0.82 if preferred_sellers else 0.0
	source_conf = 0.8 if source else 0.0

	return (
		school_exclusive,
		required_sellers,
		preferred_sellers,
		source,
		school_conf,
		required_conf,
		preferred_conf,
		source_conf,
	)


def extract_item_candidates(
	uploaded_pdf_document: dict | bytes = None,
	category_matrix_reference: dict[str, dict[str, str]] = None,
	directive_runtime_config: dict | None = None,
	llm_invoke_fn=None,
	audit_log: list[dict] | None = None,
	llm_call_log: list[dict] | None = None,
	pdf_bytes: bytes | None = None,
	ocr_instance=None,
	coverage_threshold: float = 0.70,
	return_metadata: bool = False,
) -> dict | list[dict]:
	"""
	Deterministic extraction boundary for PDF input with quality-first extraction.
	
	Accepts either:
	- Legacy dict format: uploaded_pdf_document (for backward compatibility)
	- New bytes format: pdf_bytes parameter
	
	Returns: {
		"extracted_items": list[dict],  # Item candidates with confidence scores
		"raw_text": str,                # Full extracted text
		"coverage_ratio": float,        # 0.0–1.0 extraction quality
		"extraction_mode": str,         # "native", "ocr_fallback", or "failed"
		"layout_flags": dict,           # Layout characteristics detected
		"errors": list[str],            # Extraction or processing errors
		"confidence_bands": dict,       # Count of items by confidence level
	}
	"""
	
	# Handle input format conversion
	if pdf_bytes is None:
		if isinstance(uploaded_pdf_document, bytes):
			pdf_bytes = uploaded_pdf_document
		elif isinstance(uploaded_pdf_document, dict):
			content_type = str(uploaded_pdf_document.get("content_type") or "").lower()
			if content_type != "application/pdf":
				raise ValueError("uploaded_pdf_document must declare content_type='application/pdf'")
			if "content_bytes" in uploaded_pdf_document:
				pdf_bytes = uploaded_pdf_document["content_bytes"]
			elif "text" in uploaded_pdf_document:
				# Legacy: already-decoded text
				pdf_text = uploaded_pdf_document["text"]
				extraction_result = {
					"text": pdf_text,
					"coverage_ratio": 1.0,
					"extraction_mode": "legacy",
					"layout_flags": {},
					"errors": [],
				}
			else:
				raise ValueError("uploaded_pdf_document must contain 'text' or 'content_bytes'")
		else:
			raise ValueError("Input must be bytes or dict with 'content_bytes' or 'text'")
	
	# Extract text from PDF if not already done
	if pdf_bytes is not None:
		# Initialize OCR if available and not provided
		if ocr_instance is None and _OCR_AVAILABLE:
			try:
				ocr_instance = Reader(['pt', 'en'], gpu=False)
			except Exception:
				ocr_instance = None
		
		extraction_result = _extract_pdf_text_with_fallback(
			pdf_bytes,
			coverage_threshold=coverage_threshold,
			ocr_instance=ocr_instance
		)
	
	pdf_text = extraction_result["text"]

	structured_candidates: list[dict] = []
	if pdf_bytes is not None and isinstance(pdf_bytes, (bytes, bytearray)) and bytes(pdf_bytes).startswith(b"%PDF"):
		structured_candidates = _extract_structured_candidates_from_pdf(bytes(pdf_bytes))

	# Parse extracted text into lines
	lines = [_normalize_space(line) for line in pdf_text.splitlines() if _normalize_space(line)]
	notation_rules = _build_document_notation_rules(lines)
	runtime = parse_directive_runtime_config(directive_runtime_config)

	stage_b_enabled = runtime["stage_b_enabled"]
	stage_c_enabled = runtime["stage_c_enabled"]
	llm_trigger_threshold = runtime.get("llm_trigger_threshold")
	llm_accept_threshold = runtime.get("llm_accept_threshold")
	persistence_mode = runtime["llm_persistence_mode"]

	extracted_items: list[dict] = []
	confidence_bands = {"accept": 0, "review": 0, "reject": 0}

	candidate_rows: list[dict] = []
	if structured_candidates:
		for candidate in structured_candidates:
			candidate_rows.append(
				{
					"line_text": str(candidate.get("name") or ""),
					"notes_value": str(candidate.get("notes") or ""),
					"category_value": str(candidate.get("category") or "unknown"),
					"quantity_value": str(candidate.get("quantity") or "1 un"),
					"isbn_value": str(candidate.get("isbn") or ""),
				}
			)
	else:
		for line_text in lines:
			category_value, _ = _line_category(line_text, category_matrix_reference)
			quantity_value, _ = _extract_quantity_field(line_text)
			isbn_value, _ = _extract_isbn_field(line_text)
			candidate_rows.append(
				{
					"line_text": line_text,
					"notes_value": "",
					"category_value": category_value,
					"quantity_value": quantity_value,
					"isbn_value": isbn_value,
				}
			)

	for line_index, candidate_row in enumerate(candidate_rows):
		line_text = candidate_row["line_text"]
		notes_value = candidate_row.get("notes_value") or ""
		category_value = candidate_row["category_value"]
		quantity_value = candidate_row["quantity_value"]
		isbn_value = candidate_row["isbn_value"]
		_, category_conf = _line_category(line_text, category_matrix_reference)
		_, quantity_conf = _extract_quantity_field(quantity_value or line_text)
		_, isbn_conf = _extract_isbn_field(isbn_value or line_text)
		(
			school_exclusive,
			required_sellers,
			preferred_sellers,
			exclusive_source,
			school_conf,
			required_conf,
			preferred_conf,
			source_conf,
		) = _extract_exclusivity_fields(line_text, notation_rules)
		name_value = line_text
		name_conf = 0.85

		fields = {
			"name": {
				"value": name_value,
				"confidence": _clamp_confidence(name_conf),
			},
			"notes": {
				"value": notes_value,
				"confidence": _clamp_confidence(0.88 if notes_value else 0.0),
			},
			"category": {
				"value": category_value,
				"confidence": _clamp_confidence(category_conf),
			},
			"quantity": {
				"value": quantity_value,
				"confidence": _clamp_confidence(quantity_conf),
			},
			"isbn": {
				"value": isbn_value,
				"confidence": _clamp_confidence(isbn_conf),
			},
			"school_exclusive": {
				"value": school_exclusive,
				"confidence": _clamp_confidence(school_conf),
			},
			"required_sellers": {
				"value": required_sellers,
				"confidence": _clamp_confidence(required_conf),
			},
			"preferred_sellers": {
				"value": preferred_sellers,
				"confidence": _clamp_confidence(preferred_conf),
			},
			"exclusive_source": {
				"value": exclusive_source,
				"confidence": _clamp_confidence(source_conf),
			},
		}

		stage_a_item = apply_deterministic_directive_parser(
			extracted_item={
				"line_index": line_index,
				"line_text": line_text,
				"document_notation_rules": dict(notation_rules),
				"fields": fields,
			},
			document_notation_rules=notation_rules,
			llm_trigger_threshold=float(llm_trigger_threshold) if llm_trigger_threshold is not None else None,
		)

		llm_result: dict | None = None
		error_payload: dict | None = None

		# Stage B: LLM fallback for unresolved directives
		if stage_b_enabled and stage_a_item.get("directive_resolved") is False:
			llm_config = {
				"provider": runtime.get("llm_provider"),
				"model_id": runtime.get("llm_model_id"),
				"max_latency_ms": runtime.get("llm_max_latency_ms"),
				"max_retries": runtime.get("llm_max_retries", 0),
				"shadow_mode": runtime["shadow_mode"],
			}
			llm_outcome = invoke_llm_fallback(
				item=stage_a_item,
				llm_config=llm_config,
				llm_invoke_fn=llm_invoke_fn,
				audit_log=audit_log,
			)
			llm_result = llm_outcome.get("llm_result")
			error_payload = llm_outcome.get("error_payload")

		final_item = stage_a_item
		
		# Stage C: Reconcile deterministic + LLM outputs
		if stage_c_enabled:
			reconciliation = reconcile_directive_outputs(
				deterministic_output=stage_a_item,
				llm_result=llm_result,
				error_payload=error_payload,
				llm_trigger_threshold=float(llm_trigger_threshold),
				llm_accept_threshold=float(llm_accept_threshold),
				audit_log=audit_log,
				persistence_mode=persistence_mode,
				directive_audit_ledger=audit_log,
				llm_call_log_ledger=llm_call_log,
			)
			final_item = reconciliation["resolved_item"]

		extracted_items.append(final_item)
		
		# Track confidence bands for band statistics
		item_confidence = final_item.get("overall_confidence", 0.75)
		if item_confidence >= 0.90:
			confidence_bands["accept"] += 1
		elif item_confidence >= 0.70:
			confidence_bands["review"] += 1
		else:
			confidence_bands["reject"] += 1

	result_payload = {
		"extracted_items": extracted_items,
		"raw_text": pdf_text,
		"coverage_ratio": extraction_result["coverage_ratio"],
		"extraction_mode": extraction_result["extraction_mode"],
		"layout_flags": extraction_result["layout_flags"],
		"errors": extraction_result["errors"],
		"confidence_bands": confidence_bands,
	}

	if return_metadata:
		return result_payload

	return extracted_items
