# FILE: tests/fixtures/pdf_fixtures.py
# MODULE: Test Fixtures for PDF Integration Tests
# PURPOSE: Generate realistic PDF fixtures for testing Stage A ingestion paths
# EXPORTS: PDF factory functions returning bytes payloads suitable for upload workflow testing

"""
PDF Fixture Generation

This module provides factory functions that generate minimal but realistic PDF
payloads for testing different extraction paths and scenarios.

Each fixture is designed to trigger specific routing or confidence decisions:
- text_heavy_pdf: >= 70% text coverage (routes to native_text)
- image_heavy_pdf: < 70% text coverage (routes to ocr)
- two_column_pdf: Layout flag triggers
- table_heavy_pdf: Special layout processing
- mixed_quality_pdf: Multi-page with varied success/failure
"""

from typing import Dict, Any


def _minimal_pdf_header() -> bytes:
	"""Minimal valid PDF header."""
	return (
		b"%PDF-1.4\n"
		b"1 0 obj\n"
		b"<< /Type /Catalog /Pages 2 0 R >>\n"
		b"endobj\n"
		b"2 0 obj\n"
		b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>\n"
		b"endobj\n"
		b"3 0 obj\n"
		b"<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >>\n"
		b"endobj\n"
	)


def text_heavy_pdf(lines: int = 40) -> bytes:
	"""
	Generate PDF with high text coverage (>= 70%).
	
	Args:
		lines: approximate number of text lines to include
	
	Returns:
		PDF bytes payload suitable for native text extraction
	"""
	header = _minimal_pdf_header()
	
	# Build text content stream
	text_lines = [
		"Notebook 200 pages lined",
		"Math Book ISBN 9780306406157",
		"Blue school uniform",
		"Personal hygiene kit",
		"Color pencils 24 colors",
		"Pencil case",
		"School backpack",
		"Black shoes",
		"White socks (3 pairs)",
		"Classroom eraser",
	] * (lines // 10)

	
	text_content = "BT /F1 12 Tf 50 700 Tm\n"
	for i, line in enumerate(text_lines):
		if i > 0:
			text_content += "(\\n) Tj\n"
		text_content += f"({line}) Tj\n"
	text_content += "ET\n"
	
	# Minimal PDF structure for text extraction
	content_stream = (
		b"5 0 obj\n"
		b"<< /Length " + str(len(text_content)).encode() + b" >>\n"
		b"stream\n" +
		text_content.encode() +
		b"\nendstream\n"
		b"endobj\n"
		b"xref\n"
		b"0 6\n"
		b"0000000000 65535 f\n"
		b"0000000009 00000 n\n"
		b"0000000058 00000 n\n"
		b"0000000115 00000 n\n"
		b"0000000280 00000 n\n"
		b"0000000330 00000 n\n"
		b"trailer\n"
		b"<< /Size 6 /Root 1 0 R >>\n"
		b"startxref\n"
		b"450\n"
		b"%%EOF\n"
	)
	
	return header + content_stream


def image_heavy_pdf(image_count: int = 8) -> bytes:
	"""
	Generate PDF with low text coverage (< 70%).
	Simulates scanned document or image-based layout.
	
	Args:
		image_count: approximate number of images to simulate
	
	Returns:
		PDF bytes payload suitable for OCR routing
	"""
	header = b"%PDF-1.4\n"
	
	# Simulate image-based PDF structure
	xobject_refs = "\n".join([f"/Im{i} {i+4} 0 R" for i in range(image_count)])
	
	content = (
		b"1 0 obj\n"
		b"<< /Type /Catalog /Pages 2 0 R >>\n"
		b"endobj\n"
		b"2 0 obj\n"
		b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>\n"
		b"endobj\n"
		b"3 0 obj\n"
		b"<< /Type /Page /Parent 2 0 R /Resources << /XObject << " +
		xobject_refs.encode() +
		b" >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >>\n"
		b"endobj\n"
		b"5 0 obj\n"
		b"<< /Length 100 >>\n"
		b"stream\n"
		b"q 100 0 0 100 50 650 cm /Im0 Do Q\n"
		b"q 100 0 0 100 350 650 cm /Im1 Do Q\n"
		b"endstream\n"
		b"endobj\n"
	)
	
	# Add image object stubs
	for i in range(image_count):
		content += (
			f"{i+4} 0 obj\n".encode() +
			b"<< /Type /XObject /Subtype /Image /Width 100 /Height 100 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Length 50 >>\n" +
			b"stream\n" +
			b"fake_image_data_" + str(i).encode() + b"\n" +
			b"endstream\n" +
			b"endobj\n"
		)
	
	xref = (
		b"xref\n"
		b"0 " + str(image_count + 4).encode() + b"\n" +
		b"0000000000 65535 f\n" +
		b"0000000010 00000 n\n" +
		b"0000000060 00000 n\n" +
		b"0000000120 00000 n\n"
	)
	
	return header + content + xref + b"trailer\n<< /Size " + str(image_count + 4).encode() + b" /Root 1 0 R >>\nstartxref\n1000\n%%EOF\n"


def two_column_pdf() -> bytes:
	"""
	Generate PDF with two-column layout.
	Tests layout detection flags.
	
	Returns:
		PDF bytes with text positioned in two distinct columns
	"""
	header = _minimal_pdf_header()
	
	# Text positioned in left and right columns
	text_content = (
		"BT /F1 12 Tf\n"
		"50 700 Tm (Left Column) Tj\n"
		"50 680 Tm (Line 2 Left) Tj\n"
		"50 660 Tm (Line 3 Left) Tj\n"
		"320 700 Tm (Right Column) Tj\n"
		"320 680 Tm (Line 2 Right) Tj\n"
		"320 660 Tm (Line 3 Right) Tj\n"
		"ET\n"
	)
	
	content_stream = (
		b"5 0 obj\n"
		b"<< /Length " + str(len(text_content)).encode() + b" >>\n"
		b"stream\n" +
		text_content.encode() +
		b"\nendstream\n"
		b"endobj\n"
		b"xref\n"
		b"0 6\n"
		b"0000000000 65535 f\n"
		b"0000000009 00000 n\n"
		b"0000000058 00000 n\n"
		b"0000000115 00000 n\n"
		b"0000000280 00000 n\n"
		b"0000000330 00000 n\n"
		b"trailer\n"
		b"<< /Size 6 /Root 1 0 R >>\n"
		b"startxref\n"
		b"450\n"
		b"%%EOF\n"
	)
	
	return header + content_stream


def table_heavy_pdf() -> bytes:
	"""
	Generate PDF with table-heavy content.
	Tests table detection heuristics.
	
	Returns:
		PDF bytes with tabular data structure
	"""
	header = _minimal_pdf_header()
	
	# Table-like structure with alignment indicators
	text_content = (
		"BT /F1 10 Tf\n"
		"50 700 Tm (Item       Qty         Value) Tj\n"
		"50 680 Tm (Book|      2           R$ 59.90) Tj\n"
		"50 660 Tm (Notebook|  5           R$ 12.00) Tj\n"
		"50 640 Tm (Pencil|    10          R$ 1.50) Tj\n"
		"50 620 Tm (Eraser|    4           R$ 2.30) Tj\n"
		"ET\n"
	)
	
	content_stream = (
		b"5 0 obj\n"
		b"<< /Length " + str(len(text_content)).encode() + b" >>\n"
		b"stream\n" +
		text_content.encode() +
		b"\nendstream\n"
		b"endobj\n"
		b"xref\n"
		b"0 6\n"
		b"0000000000 65535 f\n"
		b"0000000009 00000 n\n"
		b"0000000058 00000 n\n"
		b"0000000115 00000 n\n"
		b"0000000280 00000 n\n"
		b"0000000330 00000 n\n"
		b"trailer\n"
		b"<< /Size 6 /Root 1 0 R >>\n"
		b"startxref\n"
		b"450\n"
		b"%%EOF\n"
	)
	
	return header + content_stream


def mixed_quality_pdf(text_pages: int = 2, image_pages: int = 1) -> bytes:
	"""
	Generate multi-page PDF with mixed text and image pages.
	Tests partial success handling and multi-page routing.
	
	Args:
		text_pages: number of text content pages
		image_pages: number of image-based pages
	
	Returns:
		PDF bytes with mixed content types across pages
	"""
	header = b"%PDF-1.4\n"
	
	# Simplified multi-page structure
	# For testing purposes, we'll include text and image references
	content = (
		b"1 0 obj\n"
		b"<< /Type /Catalog /Pages 2 0 R >>\n"
		b"endobj\n"
		b"2 0 obj\n"
		b"<< /Type /Pages /Kids [3 0 R 4 0 R 5 0 R] /Count 3 >>\n"
		b"endobj\n"
		b"3 0 obj\n"
		b"<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 6 0 R >> >> /MediaBox [0 0 612 792] /Contents 7 0 R >>\n"
		b"endobj\n"
		b"4 0 obj\n"
		b"<< /Type /Page /Parent 2 0 R /Resources << /XObject << /Im0 8 0 R >> >> /MediaBox [0 0 612 792] /Contents 9 0 R >>\n"
		b"endobj\n"
		b"5 0 obj\n"
		b"<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 6 0 R >> >> /MediaBox [0 0 612 792] /Contents 10 0 R >>\n"
		b"endobj\n"
		b"6 0 obj\n"
		b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\n"
		b"endobj\n"
		b"7 0 obj\n"
		b"<< /Length 50 >>\n"
		b"stream\n"
		b"BT /F1 12 Tf 50 700 Tm (Page 1 - Text) Tj ET\n"

		b"endstream\n"
		b"endobj\n"
		b"8 0 obj\n"
		b"<< /Type /XObject /Subtype /Image /Width 100 /Height 100 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Length 50 >>\n"
		b"stream\n"
		b"fake_image_data\n"
		b"endstream\n"
		b"endobj\n"
		b"9 0 obj\n"
		b"<< /Length 30 >>\n"
		b"stream\n"
		b"q 100 0 0 100 50 650 cm /Im0 Do Q\n"
		b"endstream\n"
		b"endobj\n"
		b"10 0 obj\n"
		b"<< /Length 50 >>\n"
		b"stream\n"
		b"BT /F1 12 Tf 50 700 Tm (Page 3 - Text) Tj ET\n"

		b"endstream\n"
		b"endobj\n"
		b"xref\n"
		b"0 11\n"
		b"0000000000 65535 f\n"
		b"0000000010 00000 n\n"
		b"0000000060 00000 n\n"
		b"0000000130 00000 n\n"
		b"0000000280 00000 n\n"
		b"0000000430 00000 n\n"
		b"0000000580 00000 n\n"
		b"0000000660 00000 n\n"
		b"0000000750 00000 n\n"
		b"0000000880 00000 n\n"
		b"0000000950 00000 n\n"
		b"trailer\n"
		b"<< /Size 11 /Root 1 0 R >>\n"
		b"startxref\n"
		b"1050\n"
		b"%%EOF\n"
	)
	
	return header + content


def fixture_library() -> Dict[str, Dict[str, Any]]:
	"""
	Return a library of pre-built fixtures for integration testing.
	
	Returns:
		Dictionary mapping fixture names to metadata + callable factories
	"""
	return {
		"text_heavy": {
			"description": "High text coverage PDF (>= 70%), should route to native_text",
			"expected_route": "native_text",
			"factory": text_heavy_pdf,
			"tags": ["text", "native", "high_coverage"],
		},
		"image_heavy": {
			"description": "Low text coverage PDF (< 70%), should route to ocr",
			"expected_route": "ocr",
			"factory": image_heavy_pdf,
			"tags": ["image", "ocr", "low_coverage"],
		},
		"two_column": {
			"description": "Two-column layout PDF, should flag layout detection",
			"expected_route": "native_text",
			"expected_layout_flags": ["is_two_column"],
			"factory": two_column_pdf,
			"tags": ["layout", "two_column"],
		},
		"table_heavy": {
			"description": "Table-heavy PDF, should flag layout detection",
			"expected_route": "native_text",
			"expected_layout_flags": ["is_table_heavy"],
			"factory": table_heavy_pdf,
			"tags": ["layout", "table"],
		},
		"mixed_quality": {
			"description": "Multi-page PDF with mixed text/image content, tests partial success",
			"expected_route": "mixed",
			"factory": mixed_quality_pdf,
			"tags": ["multi_page", "partial_success"],
		},
	}
