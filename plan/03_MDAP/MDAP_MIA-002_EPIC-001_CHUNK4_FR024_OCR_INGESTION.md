# MDAP Module Impact Assessment — MIA-002
## EPIC-001: Addition of MODULE-001-11, MODULE-001-12, MODULE-001-13
## Chunk 4 / FR-024 Conservative OCR Ingestion

**Status**: APPROVED  
**Date**: March 26, 2026  
**Change Type**: Module Addition (3 new modules; visible scope extension to approved EPIC-001)  
**Impact Level**: HIGH (critical-path extension; routing correctness; OCR fallback reliability)  
**References**:
- EPIC_OUTPUT.md (approved EPIC-001 baseline)
- MDAP_STAGE1_EPIC-001_APPROVED.md through MDAP_STAGE5_EPIC-001_APPROVED.md (baseline approved)
- PRD_ADDENDUM_FR024_FR026_FOUNDATION_PIPELINE.md (APPROVED)
- EPIC_AMENDMENT_004_CHUNK4_FR024_OCR_INGESTION.md (APPROVED)
- CONTEXT.md (updated amendment-aware traveling context)

---

## 1. Baseline Reference

**Approved EPIC-001 Baseline Artifacts**:
- MDAP_STAGE1_EPIC-001_APPROVED.md (7 modules identified)
- MDAP_STAGE2_EPIC-001_APPROVED.md (dependency map)
- MDAP_STAGE3_EPIC-001_APPROVED.md (module details and acceptance criteria)
- MDAP_STAGE4_EPIC-001_APPROVED.md (scope and risk review)
- MDAP_STAGE5_EPIC-001_APPROVED.md (advancement sign-off)
- All approved and advanced in the baseline architecture flow

**Change**:
- Add 3 modules: MODULE-001-11, MODULE-001-12, MODULE-001-13
- Extend baseline intake flow before confidence gating
- Preserve existing MODULE-001-01 through MODULE-001-07 semantics unless explicitly amended here

**Boundary Check**:
- No scope-ceiling violation detected
- No new persona introduced
- No FR renumbering or baseline FR mutation
- Chunk 5 (FR-025) and Chunk 6 (FR-026) remain out of scope for this MIA

---

## 2. Stage 1: Module Identification

### Module: MODULE-001-11 — File Type Detection Router

**Responsibility**: Detect uploaded file type using MIME plus extension cross-check and route the document into the compatible extraction path (PDF, DOCX, XLSX, or unknown-review path).

**User Stories Covered**: US-0011-A  
**FRs Covered**: FR-024 (AC1, AC6)  
**Coverage**: ✓ 100% for file-type routing leg

---

### Module: MODULE-001-12 — PDF Coverage and Layout Router

**Responsibility**: For PDF documents, compute text coverage ratio, apply THRESHOLD-OCR-01, detect major layout complexity, and choose native text extraction or OCR routing with explicit audit metadata.

**User Stories Covered**: US-0012-A  
**FRs Covered**: FR-024 (AC2, AC3, AC4, AC5a, AC5b, AC5c, AC5d)  
**Coverage**: ✓ 100% for PDF routing and layout leg

---

### Module: MODULE-001-13 — OCR Extraction Processor

**Responsibility**: Execute OCR on routed image-heavy PDF content, emit extraction_source and confidence metadata, and preserve no-silent-drop behavior on failures or partial success.

**User Stories Covered**: US-0013-A  
**FRs Covered**: FR-024 (AC4, AC6, AC7), NFR-006  
**Coverage**: ✓ 100% for OCR execution leg

---

## 3. Stage 2: Dependency Mapping

### Intra-EPIC-001 Dependencies

```text
Upload input
    ↓
MODULE-001-11 (File Type Detection Router)
    ↓ detected_type, route_target

If detected_type == pdf:
    MODULE-001-12 (PDF Coverage and Layout Router)
        ↓ route_mode, text_coverage_ratio, layout_flags

    If route_mode == native_text:
        Existing native PDF extraction path (baseline EPIC-001)

    If route_mode == ocr:
        MODULE-001-13 (OCR Extraction Processor)
            ↓ extracted_items, extraction_source, item_confidence, failure_events

Common downstream:
    MODULE-001-02 (Confidence Gating Router)
```

### Baseline Module Extension Notes

| Baseline Module | Extension Type | Amendment Impact |
|-----------------|----------------|------------------|
| MODULE-001-01 | Scope narrowing | Responsibility narrowed from PDF extraction (text + OCR internally) to native PDF text extraction only (post-routing); file-type and PDF routing logic extracted to MODULE-001-11/12 |
| MODULE-001-02 | Input-contract extension | Must accept extraction_source plus confidence metadata originating from OCR or native path |

### Module Lifecycle Note

The original MODULE-001-01 (PDF Ingestion & Field Extraction) undergoes a **scope narrowing**, not retirement:
- **Previous Responsibility**: Handle PDF extraction with internal OCR fallback logic
- **New Responsibility**: Handle native PDF text extraction only; OCR routing decision delegated upstream
- **Architectural Change**: EPIC-001 entry point shifts from MODULE-001-01 to MODULE-001-11 (File Type Detection Router)
- **Backward Compatibility**: MODULE-001-01 still receives extraction context and confidence metadata, just with pre-determined route from MODULE-001-12
- **Rationale**: Separating routing logic from extraction logic improves testability and enables mixed-document support without redesigning 001-01

This lifecycle clarification ensures Architecture teams understand that baseline module contracts remain stable even as upstream responsibilities are factored out.

### Cross-Epic Dependencies

| Module | Upstream/Downstream | Epic | Dependency |
|--------|---------------------|------|------------|
| MODULE-001-13 | MODULE-004-02 | EPIC-004 | Optional audit/event persistence integration for failure evidence; non-blocking for module logic |
| FR-025 future work | MODULE-001-11/12/13 outputs | Future amendment | Persistence of extraction lineage is downstream and explicitly out of current scope |

**Direction Check**: ✓ All forward or same-epic linear flow; no reverse blocking introduced

### Circular Dependency Check
- ✓ NO CYCLES
- Linear conditional path only: 001-11 -> 001-12 -> 001-13 (conditional) -> 001-02

### Critical Path Impact

| | Baseline EPIC-001 | Amended Chunk 4 Path |
|---|---|---|
| Entry path | 001-01 -> 001-02 -> ... -> 001-07 | 001-11 -> 001-12 -> [001-13 when OCR] -> 001-02 -> ... -> 001-07 |
| Path length change | 7 modules | 9 baseline-visible path nodes (+2 always, +1 conditional OCR branch) |
| Conditional branch | None | OCR branch activates only when PDF text coverage < 0.70 |

---

## 4. Stage 3: Module Details and Acceptance Criteria

### MODULE-001-11: File Type Detection Router

**Domain**: File-type classification and routing  
**Type**: Domain Logic / Routing  
**Risk Level**: MEDIUM  
**Expert Domains**: [File Format Detection, Input Validation]

**Responsibility Chain**:
1. Accept raw uploaded file bytes, filename, and optional content_type metadata
2. Cross-check MIME and filename extension
3. Emit detected_type and route_target
4. Emit warning or explicit error_reason when type is inconsistent or unknown
5. Preserve no-silent-drop behavior by routing uncertainty to review path rather than implicit best guess

**Acceptance Criteria**:

| ID | Criterion | Pass/Fail |
|----|-----------|-----------|
| AC1 | PDF input with consistent signature routes as detected_type=pdf | Verifiable |
| AC2 | DOCX input with consistent signature routes as detected_type=docx | Verifiable |
| AC3 | XLSX input with consistent signature routes as detected_type=xlsx | Verifiable |
| AC4 | Unknown or inconsistent file signatures emit warning or unknown type state | Verifiable |
| AC5 | route_target is consistent with detected_type output | Verifiable |
| AC6 | Detection failure yields explicit error_reason and no silent drop | Verifiable |

**Public Interface**:
```python
FileTypeRoutingInput = {
    "file_bytes": bytes,
    "filename": str,
    "content_type": str | None,
    "context": {
        "upload_id": str,
        "user_id": str | None,
    },
}

FileTypeRoutingOutput = {
    "detected_type": "pdf" | "docx" | "xlsx" | "unknown",
    "route_target": str,
    "detection_confidence": float,
    "warning_flags": list[str],
    "error_reason": str | None,
}
```

**Constraints and Assumptions**:
- No file-size threshold is invented here; ASSUMPTION-007 remains unresolved and carried forward
- Router does not redesign DOCX/XLSX parsing; it only routes to compatible existing paths

---

### MODULE-001-12: PDF Coverage and Layout Router

**Domain**: Coverage computation, threshold routing, layout detection  
**Type**: Domain Logic / Decision Router  
**Risk Level**: HIGH  
**Expert Domains**: [PDF Analysis, Routing Logic, Layout Heuristics]

**Responsibility Chain**:
1. Accept PDF bytes and extraction context from MODULE-001-11
2. Compute text_coverage_ratio in [0.00, 1.00]
3. Apply THRESHOLD-OCR-01 exactly: >= 0.70 -> native_text, < 0.70 -> ocr
4. Detect layout flags for two-column, table-heavy, and uncertainty conditions
5. Emit routing_audit_record for downstream traceability
6. On routing ambiguity, preserve review-oriented metadata rather than silently forcing correctness claims

**Acceptance Criteria**:

| ID | Criterion | Pass/Fail |
|----|-----------|-----------|
| AC1 | Coverage computation returns value bounded in [0.00, 1.00] | Verifiable |
| AC2 | Coverage ratio >= 0.70 selects native_text route | Verifiable |
| AC3 | Coverage ratio < 0.70 selects ocr route | Verifiable |
| AC4 | Two-column layouts are flagged when detected | Verifiable |
| AC5 | Table-heavy layouts are flagged when detected | Verifiable |
| AC6 | Uncertain layout regions emit warning or review metadata | Verifiable |
| AC7 | routing_audit_record includes applied logic and threshold evidence | Verifiable |

**Public Interface**:
```python
PDFRoutingInput = {
    "pdf_bytes": bytes,
    "filename": str,
    "context": {
        "upload_id": str,
        "user_id": str | None,
        "extraction_config": {
            "ocr_enabled": bool,
            "coverage_threshold": float,
        },
    },
}

PDFRoutingOutput = {
    "route_mode": "native_text" | "ocr",
    "text_coverage_ratio": float,
    "layout_flags": {
        "is_two_column": bool,
        "is_table_heavy": bool,
        "has_uncertain_regions": bool,
    },
    "routing_audit_record": {
        "decision_logic_applied": str,
        "coverage_threshold": float,
        "coverage_ratio": float,
    },
    "error": {
        "reason": str,
        "severity": "warning" | "error",
        "affected_pages": list[int],
    } | None,
}
```

**Constraints and Assumptions**:
- THRESHOLD-OCR-01 is fixed and approved at 0.70; no alternative routing threshold permitted without amendment
- Layout detection is best-effort and does not guarantee table reconstruction quality beyond FR-024 boundaries

---

### MODULE-001-13: OCR Extraction Processor

**Domain**: OCR execution and failure-safe extraction  
**Type**: External library integration / Domain processing  
**Risk Level**: HIGH  
**Expert Domains**: [OCR Processing, Failure Recovery, Confidence Propagation]

**Responsibility Chain**:
1. Accept OCR-routed image payloads from MODULE-001-12
2. Execute OCR extraction over pages or regions
3. Emit extracted_items with extraction_source and item_confidence metadata
4. Emit failure_events for failed pages/regions
5. Preserve partial successful extraction when possible
6. Route failed or uncertain outputs into downstream review logic rather than silent discard

**Acceptance Criteria**:

| ID | Criterion | Pass/Fail |
|----|-----------|-----------|
| AC1 | OCR path returns extracted_items on successful processing | Verifiable |
| AC2 | Each extracted item includes extraction_source and confidence metadata | Verifiable |
| AC3 | OCR failures emit failure_events with explicit reason | Verifiable |
| AC4 | OCR failures route affected output to review_required rather than silent drop | Verifiable |
| AC5 | Partial OCR success preserves successful outputs while flagging failed regions | Verifiable |

**Public Interface**:
```python
OCRExtractionInput = {
    "document_images": list[bytes],
    "source_document_id": str,
    "context": {
        "upload_id": str,
        "page_numbers": list[int],
        "ocr_config": {
            "primary_engine": str,
            "fallback_enabled": bool,
        },
    },
}

OCRExtractionOutput = {
    "extracted_items": list[dict],
    "extraction_source": str,
    "item_confidence": list[float],
    "failure_events": list[dict],
}
```

**Constraints and Assumptions**:
- OCR engine selection is approved at PRD stack level as Tesseract primary; fallback activation policy remains open (OQ-FR024-01)
- No timeout values are invented in this MIA; timeout budgets remain implementation-time configuration unless separately approved

---

## 5. Stage 4: Scope and Risk Review

### Scope Boundary

**In Scope for this MIA**:
- ✓ File-type detection and route decision before extraction
- ✓ PDF text-coverage routing using THRESHOLD-OCR-01
- ✓ Layout detection flags relevant to FR-024
- ✓ OCR execution path with extraction_source and confidence metadata
- ✓ Failure-safe no-silent-drop behavior for Stage A

**Out of Scope**:
- ❌ Chunk 5 persistence models and storage schema implementation
- ❌ Chunk 6 real source adapters
- ❌ New DOCX/XLSX parser redesign beyond router compatibility
- ❌ Invented file-size caps, timeout thresholds, or retry counts
- ❌ New UI for extraction-progress visualization

**Scope Verdict**: ✓ PASS — bounded to approved Chunk 4 requirements only

### Risk Assessment

| Risk ID | Component | Risk | Likelihood | Severity | Impact | Mitigation |
|---------|-----------|------|-----------|----------|--------|----------|
| R-001 | MODULE-001-11 | Wrong file-type route | MEDIUM | HIGH | Incorrect extraction path, processing failure | MIME + extension cross-check; unknown-review path; contract tests |
| R-002 | MODULE-001-12 | Incorrect coverage ratio leads to wrong route | MEDIUM | HIGH | Native text fallback on complex PDFs, low extraction quality | Fixture-based coverage tests across known PDF patterns |
| R-003 | MODULE-001-12 | Layout ambiguity creates ordering/association errors | LOW | MEDIUM | Item association errors in complex layouts | Warning flags, review metadata, integration tests on complex PDFs |
| R-004 | MODULE-001-13 | OCR degradation on poor scans | MEDIUM | HIGH | Extraction loss or high-error propagation | Confidence propagation, partial-success handling, review routing |

### Risk Mitigation Evidence Required
- [ ] Module-level unit tests for routing logic and output contracts
- [ ] Integration tests on mixed sample set: PDF, DOCX, XLSX, two-column PDF, table-heavy PDF
- [ ] Failure-path verification showing no silent drop
- [ ] Human review of THRESHOLD-OCR-01 application and layout ambiguity policy

**Risk Verdict**: ✓ ACCEPTABLE with mitigation and human review

---

## 6. Stage 5: Advancement Sign-Off

### Implementation Staging Plan

| Stage | Deliverable | Gate Condition |
|-------|-------------|----------------|
| A1 | MODULE-001-11 implemented and contract-tested | File routing outputs stable across representative file fixtures |
| A2 | MODULE-001-12 implemented with threshold routing and layout flags | THRESHOLD-OCR-01 behavior verified on fixture set |
| A3 | MODULE-001-13 implemented with confidence and failure propagation | No-silent-drop failure handling verified |
| A4 | Stage A integration into baseline EPIC-001 intake path | Existing FR-002 confidence gating compatibility verified |

### Human Gate Checklist

- [x] EPIC Amendment 004 approved
- [x] THRESHOLD-OCR-01 confirmed as fixed at 0.70 in implementation notes
- [x] Module-level ACs reviewed for all 3 modules
- [x] Public contracts reviewed for downstream compatibility with MODULE-001-02
- [x] ASSUMPTION-007 explicitly carried forward without invented value
- [x] OQ-FR024-01 and OQ-FR024-02 carried into implementation planning
- [x] Mixed sample validation set defined for Stage A evidence

### Advancement Recommendation

**Status**: APPROVED FOR IMPLEMENTATION

**Recommendation**:
- Chunk 4 MDAP is approved to advance.
- Implementation may proceed for Stage A modules (MODULE-001-11 through MODULE-001-13).
- Chunk 5 and Chunk 6 remain blocked from implementation under this MIA.

### Human Gate Sign-Off Block

| Role | Name | Decision | Date | Notes |
|------|------|----------|------|-------|
| EPIC-001 Owner | User Directive | APPROVE | March 26, 2026 | Approved to start Stage A |
| Architecture Lead | User Directive | APPROVE | March 26, 2026 | Contracts and routing boundaries accepted |
| Intake/OCR Reviewer | User Directive | APPROVE | March 26, 2026 | High-risk review acknowledged; proceed with Stage A |

**Overall MIA-002 Status**: ☑ APPROVED | ☐ CONDITIONAL | ☐ REWORK REQUIRED

**Conditions (if CONDITIONAL)**:
- [x] Condition 1: EPIC Amendment 004 approved
- [x] Condition 2: Stage A validation sample set defined

**MIA-002 Advancement Verdict**: ☑ GATE PASSED | ☐ GATE PENDING CONDITIONS | ☐ GATE FAILED

---

## 7. Summary

**Baseline**: EPIC-001 (7 modules approved in baseline MDAP)

**Change**: Add MODULE-001-11, MODULE-001-12, MODULE-001-13 for Chunk 4 / FR-024

**Impact**:
- Extends EPIC-001 entry path with document routing and OCR branch
- Narrows MODULE-001-01 scope from PDF extraction (with OCR) to native text extraction only
- Preserves existing FR-001 through FR-009 semantics while improving intake breadth and robustness
- Keeps persistence and real-source acquisition out of current MDAP scope

**Dependencies**:
- Same-epic linear dependency chain with no reverse blocking
- Future FR-025 persistence integration intentionally deferred

**Risk Governance**: HIGH severity with MEDIUM-LOW likelihood; mitigations are testable and implementable

**Note on Success Metrics**: SM-020 through SM-024 (file detection accuracy, coverage computation accuracy, OCR confidence propagation, etc.) are deferred to implementation phase (PROMPT-6). This MDAP establishes module contracts and acceptance criteria; success metrics validation belongs in implementation planning and UAT.

**MIA Gate**: ✅ PASSED — approved for Stage A implementation
