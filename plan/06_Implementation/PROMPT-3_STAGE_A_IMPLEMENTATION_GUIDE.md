# Implementation Specification — PROMPT-3
## Chunk 4 / FR-024: Conservative OCR Ingestion Pipeline
## MODULE-001-11, MODULE-001-12, MODULE-001-13 Stage A Implementation

**Date**: March 26, 2026  
**Scope**: Stage A (A1, A2, A3, A4) implementation planning for Chunk 4 modules  
**Reference**: MDAP_MIA-002_EPIC-001_CHUNK4_FR024_OCR_INGESTION.md  
**Implementation Phase**: Post-gate-approval

---

## 1. Introduction and Scope

This implementation specification provides guidance for developers implementing Stage A of Chunk 4 (FR-024 Conservative OCR Ingestion).

**Modules to Implement**:
- MODULE-001-11: File Type Detection Router
- MODULE-001-12: PDF Coverage and Layout Router
- MODULE-001-13: OCR Extraction Processor

**Implementation Artifacts Available**:
- `intake_canonicalization/file_type_detection_router.py` (scaffold)
- `intake_canonicalization/pdf_coverage_layout_router.py` (scaffold)
- `intake_canonicalization/ocr_extraction_processor.py` (scaffold)
- `tests/unit/intake_canonicalization/test_file_type_detection_router.py` (AC-based tests)
- `tests/unit/intake_canonicalization/test_pdf_coverage_layout_router.py` (AC-based tests)
- `tests/unit/intake_canonicalization/test_ocr_extraction_processor.py` (AC-based tests)

**Implementation Staging**:
- **A1**: MODULE-001-11 implementation and contract testing
- **A2**: MODULE-001-12 implementation with threshold routing
- **A3**: MODULE-001-13 implementation with failure propagation
- **A4**: Integration into baseline EPIC-001 intake path

---

## 2. Architecture Overview

### 2.1 Pipeline Entry Flow (Post-Amendment)

```
Upload Input
    ↓
MODULE-001-11 (File Type Detection Router)
    ↓ detected_type, route_target
    
If detected_type == pdf:
    MODULE-001-12 (PDF Coverage and Layout Router)
        ↓ route_mode
        
    If route_mode == native_text:
        Existing native PDF extraction (MODULE-001-01 narrowed scope)
        
    If route_mode == ocr:
        MODULE-001-13 (OCR Extraction Processor)
            ↓ extracted_items, extraction_source
            
Common downstream:
    MODULE-001-02 (Confidence Gating Router)
```

### 2.2 Module Contracts

All modules expose input/output contracts as TypedDict in their source files.

**MODULE-001-11 Contracts**:
```python
FileTypeRoutingInput = {
    "file_bytes": bytes,
    "filename": str,
    "content_type": str | None,
    "context": dict,
}

FileTypeRoutingOutput = {
    "detected_type": str,  # "pdf", "docx", "xlsx", "unknown"
    "route_target": str,
    "detection_confidence": float,
    "warning_flags": list[str],
    "error_reason": str | None,
}
```

**MODULE-001-12 Contracts**:
```python
PDFRoutingInput = {
    "pdf_bytes": bytes,
    "filename": str,
    "context": dict,
}

PDFRoutingOutput = {
    "route_mode": str,  # "native_text" | "ocr"
    "text_coverage_ratio": float,
    "layout_flags": dict,
    "routing_audit_record": dict,
    "error": dict | None,
}
```

**MODULE-001-13 Contracts**:
```python
OCRExtractionInput = {
    "document_images": list[bytes],
    "source_document_id": str,
    "context": dict,
}

OCRExtractionOutput = {
    "extracted_items": list[dict],
    "extraction_source": str,  # "ocr"
    "item_confidence": list[float],
    "failure_events": list[dict],
}
```

---

## 3. Stage A1: File Type Detection Router Implementation

### 3.1 Responsibilities

1. Accept raw uploaded file bytes, filename, and optional content_type metadata
2. Cross-check MIME and filename extension
3. Emit detected_type and route_target
4. Emit warning or explicit error_reason when type is inconsistent or unknown
5. Preserve no-silent-drop behavior by routing uncertainty to review path

### 3.2 Implementation Checklist

- [ ] Replace stub `_detect_by_magic_bytes()` with binary signature detection
  - [ ] Implement PDF magic byte detection (`%PDF`)
  - [ ] Implement DOCX/XLSX magic byte detection (ZIP header `PK\x03\x04`)
  - [ ] Add fallback for unknown signatures
  
- [ ] Enhance `_extract_extension()` to normalize and validate extensions
  - [ ] Support `.pdf`, `.docx`, `.xlsx` (case-insensitive)
  - [ ] Handle edge cases (no extension, multiple dots)
  
- [ ] Complete `_cross_check_consistency()` with detailed logging
  - [ ] Compare MIME, extension, magic bytes
  - [ ] Generate human-readable warnings for mismatches
  - [ ] Support confidence scoring based on consistency level
  
- [ ] Add unit test fixtures for file types
  - [ ] Create sample PDF, DOCX, XLSX bytes (magic bytes only, not full files)
  - [ ] Test consistency checking logic
  - [ ] Verify error handling and no-silent-drop behavior
  
- [ ] Integrate `detect_file_type()` with platform observability
  - [ ] Log detection decisions for audit
  - [ ] Track confidence metrics for validation
  
- [ ] Run full AC test suite and fix failures
  - Command: `pytest tests/unit/intake_canonicalization/test_file_type_detection_router.py -v`

### 3.3 AC Gate Conditions (A1)
- [ ] File routing outputs are stable across representative file fixtures (PDF, DOCX, XLSX, unknown)
- [ ] All 6 ACs pass
- [ ] Zero silent-drop cases

---

## 4. Stage A2: PDF Coverage and Layout Router Implementation

### 4.1 Responsibilities

1. Accept PDF bytes and extraction context
2. Compute text_coverage_ratio in [0.00, 1.00]
3. Apply THRESHOLD-OCR-01 exactly: >= 0.70 -> native_text, < 0.70 -> ocr
4. Detect layout flags for two-column, table-heavy, and uncertainty conditions
5. Emit routing_audit_record for downstream traceability

### 4.2 Implementation Checklist

- [ ] Implement `_compute_text_coverage_ratio()` with real PDF parsing
  - [ ] Use pdfplumber or PyPDF2 to extract text from PDF
  - [ ] Calculate coverage as: (char_count_text_regions) / (total_page_area_pixels)
  - [ ] Return float in [0.0, 1.0]
  - [ ] Handle corrupted/encrypted PDFs gracefully
  
- [ ] Implement `_detect_two_column_layout()`
  - [ ] Analyze text line positions (x-coordinates)
  - [ ] Detect two distinct vertical clusters (left/right columns)
  - [ ] Return boolean flag
  
- [ ] Implement `_detect_table_heavy_layout()`
  - [ ] Analyze whitespace patterns and aligned columns
  - [ ] Detect regular grid structures
  - [ ] Return boolean flag
  
- [ ] Implement `_detect_uncertain_regions()`
  - [ ] Identify low-confidence text or blurry regions
  - [ ] Track affected page numbers
  - [ ] Return boolean flag
  
- [ ] Complete `routing_audit_record` with full metadata
  - [ ] Include decision_logic_applied (human-readable)
  - [ ] Include coverage_threshold and coverage_ratio
  - [ ] Log any layout anomalies
  
- [ ] Add integration fixtures for PDF patterns
  - [ ] Create fixture: High text coverage (>= 0.70) PDF
  - [ ] Create fixture: Low text coverage (< 0.70) PDF
  - [ ] Create fixture: Two-column PDF
  - [ ] Create fixture: Table-heavy PDF
  - [ ] Create fixture: Uncertain regions PDF
  
- [ ] Run full AC test suite
  - Command: `pytest tests/unit/intake_canonicalization/test_pdf_coverage_layout_router.py -v`
  
- [ ] Verify THRESHOLD-OCR-01 = 0.70 is applied exactly (locked, no alternative permitted)

### 4.3 AC Gate Conditions (A2)
- [ ] THRESHOLD-OCR-01 behavior verified on fixture set
- [ ] All 7 ACs pass
- [ ] Coverage computation is deterministic and repeatable

---

## 5. Stage A3: OCR Extraction Processor Implementation

### 5.1 Responsibilities

1. Accept OCR-routed image payloads
2. Execute OCR extraction over pages or regions
3. Emit extracted_items with extraction_source and item_confidence metadata
4. Emit failure_events for failed pages/regions
5. Preserve partial successful extraction when possible

### 5.2 Implementation Checklist

- [ ] Implement `_run_ocr_on_image()` with real OCR engine
  - [ ] Use pytesseract (Tesseract wrapper) as primary engine
  - [ ] Configure language: Portuguese (pt-BR) + English (eng)
  - [ ] Return (extracted_lines, confidence, failure_event)
  - [ ] Implement confidence scoring based on Tesseract metadata
  
- [ ] Implement fallback behavior for OCR failures
  - [ ] Log OCR errors with page context
  - [ ] Emit failure_events with explicit reason (e.g., "image_too_blurry", "unsupported_script")
  - [ ] Preserve attempt metadata for review queue
  
- [ ] Implement partial success handling
  - [ ] Continue processing subsequent pages after single-page failure
  - [ ] Aggregate successful and failed results separately
  - [ ] Route partial-success records with review-required flags
  
- [ ] Implement no-silent-drop behavior
  - [ ] All failed pages generate failure_events
  - [ ] All failed pages generate review_required markers in extracted_items
  - [ ] Never silently discard or hide failed extraction attempts
  
- [ ] Add integration fixtures for image patterns
  - [ ] Create fixture: Clear text image
  - [ ] Create fixture: Low-contrast image
  - [ ] Create fixture: Rotated/skewed image
  - [ ] Create fixture: Blurry image (OCR failure)
  - [ ] Create fixture: Multi-page document (mixed success/failure)
  
- [ ] Run full AC test suite
  - Command: `pytest tests/unit/intake_canonicalization/test_ocr_extraction_processor.py -v`
  
- [ ] Integrate with Tesseract configuration and observability
  - [ ] Log OCR execution time and confidence metrics
  - [ ] Track failure rates per image type

### 5.3 AC Gate Conditions (A3)
- [ ] No-silent-drop failure handling verified (all failures explicitly recorded)
- [ ] All 5 ACs pass
- [ ] Partial success handling verified on mixed-failure fixtures

---

## 6. Stage A4: Integration into Baseline EPIC-001

### 6.1 Integration Points

1. **Upstream Integration**:
   - Replace direct entry call to MODULE-001-01 with entry call to MODULE-001-11
   - File type detection routes to appropriate extraction path
   - Apply routing logic _before_ confidance gating

2. **Downstream Integration**:
   - MODULE-001-02 (Confidence Gating Router) must accept both native_text and ocr extraction_source values
   - No changes to existing confidence gating logic
   - Review-required items flow through confidence gates unchanged

3. **Error Propagation**:
   - Routing errors from MODULE-001-11 route to review_required
   - Layout/OCR errors from MODULE-001-12/13 propagate as warning flags
   - No errors silently dropped

### 6.2 Integration Checklist

- [ ] Update intake entry point to invoke MODULE-001-11 first
  - [ ] Create new pipeline orchestration function (e.g., `handle_mixed_document_upload()`)
  - [ ] Route based on MODULE-001-11 detected_type
  
- [ ] Verify MODULE-001-02 (Confidence Gating) accepts mixed extraction_source
  - [ ] Add test cases for ocr extraction_source
  - [ ] Verify gate_route logic is agnostic to extraction method
  
- [ ] Integrate with MODULE-001-01 (PDF Ingestion) narrowed scope
  - [ ] MODULE-001-01 now receives pre-routed PDF with coverage decision
  - [ ] Remove internal OCR branching logic from MODULE-001-01 (or keep as fallback)
  - [ ] Verify backward compatibility
  
- [ ] Update MODULE-001-02 input contract
  - [ ] Must accept extraction_source field from both MODULE-001-01 and MODULE-001-13
  - [ ] Confidence gating remains unchanged
  
- [ ] Create integration test: end-to-end pipeline
  - [ ] Upload PDF -> MODULE-001-11 -> MODULE-001-12 -> [native or OCR] -> MODULE-001-02
  - [ ] Verify confidence gate routes correctly after OCR
  - [ ] Test review-required path with OCR failures
  
- [ ] Run baseline EPIC-001 compatibility tests
  - Command: `pytest tests/integration/test_upload_to_search_readiness.py -v -k "ocr"`
  
- [ ] Document module entry point changes in architecture

### 6.3 AC Gate Conditions (A4)
- [ ] Existing FR-002 confidence gating compatibility verified
- [ ] Integration test passes with mixed native/OCR extraction
- [ ] No regression in baseline extraction paths

---

## 7. Testing and Validation Strategy

### 7.1 Unit Test Execution

Run all AC-based tests for each module:

```bash
# Stage A1
pytest tests/unit/intake_canonicalization/test_file_type_detection_router.py -v

# Stage A2
pytest tests/unit/intake_canonicalization/test_pdf_coverage_layout_router.py -v

# Stage A3
pytest tests/unit/intake_canonicalization/test_ocr_extraction_processor.py -v
```

### 7.2 Integration Test Execution

```bash
# Full upload-to-search pipeline
pytest tests/integration/test_upload_to_search_readiness.py -v

# Specific OCR integration tests (add new)
pytest tests/integration/test_ocr_ingestion_integration.py -v
```

### 7.3 Fixture Set Validation

For each module, validate on representative fixture set:

**Module-001-11 Fixtures**:
- PDF with correct magic bytes and .pdf extension
- DOCX with correct magic bytes and .docx extension
- XLSX with correct magic bytes and .xlsx extension
- Unknown file type (should route to review_required)
- Mismatched MIME vs extension (should generate warning)

**Module-001-12 Fixtures**:
- PDF with >= 70% text coverage
- PDF with < 70% text coverage
- PDF with two-column layout
- PDF with table-heavy content
- PDF with uncertain/ambiguous regions

**Module-001-13 Fixtures**:
- Clear, high-confidence OCR image
- Low-contrast image
- Rotated/skewed image
- Blurry image (intentional OCR failure)
- Multi-page mixed success/failure

### 7.4 Success Criteria

- ✓ All unit test ACs pass (0 failures)
- ✓ All integration tests pass
- ✓ No regression in baseline EPIC-001 tests
- ✓ No silent-drop cases observed
- ✓ Confidence metrics properly logged and traceable

---

## 8. Configuration and Dependencies

### 8.1 External Dependencies

Add to `requirements.txt`:
```
pytesseract>=0.3.10  # Tesseract OCR wrapper
pdfplumber>=0.9.0    # PDF text extraction and analysis
Pillow>=9.0.0        # Image processing
```

### 8.2 System Dependencies

- **Tesseract OCR**: Install via system package manager
  - macOS: `brew install tesseract`
  - Linux (Ubuntu): `apt-get install tesseract-ocr`
  - Windows: Download from [GitHub Tesseract releases](https://github.com/UB-Mannheim/tesseract/wiki)

- **Language Data**:
  - Portuguese (pt-BR) language model for Tesseract
  - English (eng) language model for fallback

### 8.3 Configuration Parameters

Define in `config/settings.py`:

```python
# OCR Configuration
OCR_PRIMARY_ENGINE = "tesseract"
OCR_FALLBACK_ENABLED = False  # Can be enabled post-A3

# PDF Analysis Thresholds
THRESHOLD_OCR_01 = 0.70  # Locked value; no alternative permitted

# Tesseract Configuration
TESSERACT_CONFIG = {
    "lang": "pt_BR+eng",  # Portuguese + English
    "psm": 1,  # Automatic page segmentation with OSD
}
```

---

## 9. Error Handling and Observability

### 9.1 Error Handling Strategy

**No Silent Drops**:
- All errors must be explicitly recorded (failure_events, warnings, error_reason)
- All unclear cases must route to review_required
- Partial successes must be preserved with failure markers

**Error Classification**:
- MODULE-001-11: File detection errors → review_required route
- MODULE-001-12: PDF analysis errors → warning flag, no route change
- MODULE-001-13: OCR failures → review_required marker + failure_event

### 9.2 Observability and Logging

Add logging for audit and debugging:

```python
import logging

logger = logging.getLogger(__name__)

# Log routing decisions
logger.info(f"File type detection: {detected_type}, confidence={confidence}")

# Log threshold application
logger.info(f"PDF routing: coverage={coverage_ratio:.2f}, route={route_mode}")

# Log OCR execution
logger.info(f"OCR execution: pages={len(document_images)}, failures={len(failure_events)}")
```

### 9.3 Metrics to Track

- File type detection accuracy (by type)
- PDF coverage ratio distribution
- OCR success rate by image quality
- Confidence gate route distribution (accept/review/reject)
- Time-to-extract (latency by module)

---

## 10. Known Limitations and Deferred Work

### 10.1 Out of Scope (Post-A4)

- **Chunk 5 (FR-025)**: Persistence models and storage schema — explicitly deferred
- **Chunk 6 (FR-026)**: Real source adapters and acquisition — explicitly deferred
- **OCR Fallback** (OQ-FR024-01): Fallback engine selection — deferred to implementation time
- **File Size Caps** (ASSUMPTION-007): Upload size threshold — remains unresolved

### 10.2 Known Limitations of Scaffold

- `_compute_text_coverage_ratio()`: Stub uses file-size heuristics; must implement real PDF parsing
- `_detect_two_column_layout()`: Stub returns False; must implement positional analysis
- `_detect_table_heavy_layout()`: Stub returns False; must implement whitespace/grid analysis
- `_detect_uncertain_regions()`: Stub returns False; must implement confidence flagging
- `_run_ocr_on_image()`: Stub returns dummy lines; must integrate pytesseract

---

## 11. Sign-Off and Approval

### Implementation Gate Checklist

Before advancing from each stage:

**Stage A1 Completion**:
- [ ] `test_file_type_detection_router.py` passes (6 ACs)
- [ ] Integration with platform observability complete
- [ ] Code review approved by Architecture Lead

**Stage A2 Completion**:
- [ ] `test_pdf_coverage_layout_router.py` passes (7 ACs)
- [ ] THRESHOLD-OCR-01 = 0.70 locked and verified
- [ ] Code review approved by PDF domain expert

**Stage A3 Completion**:
- [ ] `test_ocr_extraction_processor.py` passes (5 ACs)
- [ ] No-silent-drop verified on multi-page fixtures
- [ ] Code review approved by OCR domain expert

**Stage A4 Completion**:
- [ ] Integration tests pass
- [ ] Baseline EPIC-001 tests pass (no regression)
- [ ] Code review approved by EPIC-001 Owner

---

## 12. References

- **MDAP**: plan/03_MDAP/MDAP_MIA-002_EPIC-001_CHUNK4_FR024_OCR_INGESTION.md
- **EPIC Amendment**: plan/02_EPIC/EPIC_AMENDMENT_004_CHUNK4_FR024_OCR_INGESTION.md
- **Architecture**: plan/04_Architecture/ARCHITECTURE_DEFINITION.md
- **Baseline EPIC-001**: plan/02_EPIC/EPIC_OUTPUT.md

---

**Implementation Status**: Ready for Stage A1 kickoff upon EPIC Amendment 004 and MDAP MIA-002 gate approval.
