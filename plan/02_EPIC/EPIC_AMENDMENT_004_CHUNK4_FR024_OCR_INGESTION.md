# EPIC-001 Amendment: Chunk 4 / FR-024 (Conservative OCR Ingestion)

**References**: EPIC_OUTPUT.md, PRD_ADDENDUM_FR024_FR026_FOUNDATION_PIPELINE.md  
**Status**: APPROVED  
**Amendment Date**: March 26, 2026

---

## 1. Change Summary

**Original EPIC-001**: Ingestion/canonicalization pipeline focused on mixed PDF extraction with confidence gating.  
**Amended Scope (This document)**: Adds **FR-024 only** to EPIC-001 via Stage A modules for multi-format detection and conservative PDF text-vs-image OCR routing.

**In Amendment Scope**:
- FR-024 (all ACs including AC5a–AC5d)
- THRESHOLD-OCR-01 fixed at 0.70 for PDF routing
- NFR-006 resilience constraints applied to Stage A behavior

**Out of Amendment Scope**:
- FR-025 persistence schema wiring (Chunk 5)
- FR-026 real source adapters (Chunk 6)
- Operational policies requiring THRESHOLD-SEARCH-* resolution

---

## 2. Epic Impact

### EPIC-001 (Ingestion, Canonicalization, and Validation Gating)

**Added Requirement Coverage**:
- FR-024 [MUST]
- NFR-006 [SHOULD] (Stage A applicability)
- NFR-007 [COULD] (observability hooks only; full implementation deferred)

**No change** to existing FR-001..FR-009 coverage or acceptance semantics.

### 2.1 Scope Clarification: DOCX/XLSX in Chunk 4

**Stage A includes**:
- MODULE-001-11 (File Type Detection Router) routing to PDF, DOCX, and XLSX paths
- MODULE-001-12 (PDF Coverage and Layout Router) for PDF-specific routing logic
- MODULE-001-13 (OCR Extraction Processor) for OCR fallback on routed PDF content

**Stage A does not include**:
- New DOCX extraction logic beyond compatibility with the router contract
- New XLSX extraction logic beyond compatibility with the router contract
- Chunk 5 persistence implementation changes

**Integration Point**:
- DOCX files are routed by MODULE-001-11 to the existing DOCX extraction path
- XLSX files are routed by MODULE-001-11 to the existing XLSX extraction path
- PDF files continue through MODULE-001-12 and, when required, MODULE-001-13

---

## 3. New Module Additions (Stage A Only)

### MODULE-001-11: File Type Detection Router

**User Story (US-0011-A)**  
As a School List User, I want uploaded files to be correctly identified by type before extraction, so that the system uses the right parsing path and avoids silent misreads.

**FR Coverage**: FR-024 (AC1, AC6)  
**Risk Level**: MEDIUM  
**Responsibility**:
1. Detect file type using MIME + extension cross-check
2. Route to PDF/DOCX/XLSX extraction pipeline
3. Emit uncertainty/failure markers when type cannot be reliably determined

**Public Interface**:
- Input: uploaded_file bytes + filename metadata
- Output: detected_type (pdf|docx|xlsx|unknown), route_target, detection_confidence, error_reason (optional)

**Module Acceptance Criteria**:

| AC ID | Criterion | Pass/Fail |
|-------|-----------|-----------|
| AC1 | PDF input is detected as pdf when MIME and filename are consistent | Verifiable |
| AC2 | DOCX input is detected as docx when MIME and filename are consistent | Verifiable |
| AC3 | XLSX input is detected as xlsx when MIME and filename are consistent | Verifiable |
| AC4 | Unknown or inconsistent file signatures produce detected_type=unknown or warning state | Verifiable |
| AC5 | Router emits route_target consistent with detected_type | Verifiable |
| AC6 | Detection failure produces explicit error_reason without silent drop | Verifiable |

**Detailed Interface Contract**:

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

**MDAP Design Output Expectations**:
- Stage 1: confirm module identity and boundaries
- Stage 2: map dependency on existing DOCX/XLSX and PDF paths
- Stage 3: derive test cases from AC1-AC6
- Stage 4: document failure handling and uncertainty routing
- Stage 5: produce sign-off evidence for router contract stability

---

### MODULE-001-12: PDF Coverage and Layout Router

**User Story (US-0012-A)**  
As a School List User, I want PDF extraction to choose text extraction or OCR based on measurable content coverage, so that image-heavy documents are processed correctly.

**FR Coverage**: FR-024 (AC2, AC3, AC4, AC5a, AC5b, AC5c, AC5d)  
**Risk Level**: HIGH  
**Responsibility**:
1. Compute PDF text coverage ratio
2. Apply fixed threshold policy: coverage >= 0.70 => direct text path; coverage < 0.70 => OCR path
3. Detect layout complexity (two-column/table-heavy)
4. Route uncertain layout outputs to review_required with confidence metadata

**Public Interface**:
- Input: PDF bytes + extraction context
- Output: route_mode (native_text|ocr), text_coverage_ratio, layout_flags, routing_audit_record

**Module Acceptance Criteria**:

| AC ID | Criterion | Pass/Fail |
|-------|-----------|-----------|
| AC1 | Coverage computation returns a bounded ratio in [0.00, 1.00] | Verifiable |
| AC2 | Coverage ratio >= 0.70 selects native_text route | Verifiable |
| AC3 | Coverage ratio < 0.70 selects ocr route | Verifiable |
| AC4 | Two-column layouts are flagged in layout_flags when detected | Verifiable |
| AC5 | Table-heavy layouts are flagged in layout_flags when detected | Verifiable |
| AC6 | Uncertain layout regions are surfaced through warning or review metadata | Verifiable |
| AC7 | Routing decisions generate routing_audit_record with decision rationale | Verifiable |

**Detailed Interface Contract**:

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

**MDAP Design Output Expectations**:
- Stage 1: confirm module scope for coverage and layout routing only
- Stage 2: map dependency on MODULE-001-11 input and MODULE-001-13 downstream OCR path
- Stage 3: derive threshold and layout test matrix from AC1-AC7
- Stage 4: document ambiguous-layout handling rules
- Stage 5: produce sign-off evidence for threshold application and routing determinism

---

### MODULE-001-13: OCR Extraction Processor

**User Story (US-0013-A)**  
As a School List User, I want image-based content extracted through OCR with confidence tracking and safe fallback behavior, so that no relevant items are silently lost.

**FR Coverage**: FR-024 (AC4, AC6, AC7) + NFR-006  
**Risk Level**: HIGH  
**Responsibility**:
1. Execute OCR extraction on routed pages/documents
2. Return extracted fields with extraction_source and confidence
3. On extractor failure, emit failure reason and route affected output to review_required

**Public Interface**:
- Input: document/page image payload + OCR config
- Output: extracted_items[], extraction_source, item_confidence[], failure_events[]

**Module Acceptance Criteria**:

| AC ID | Criterion | Pass/Fail |
|-------|-----------|-----------|
| AC1 | OCR path returns extracted_items collection when processing succeeds | Verifiable |
| AC2 | Each extracted item includes extraction_source and confidence metadata | Verifiable |
| AC3 | OCR processing failure emits failure_events with explicit reason | Verifiable |
| AC4 | OCR failures route affected output to review_required rather than silent drop | Verifiable |
| AC5 | Partial OCR success preserves successful items while flagging failed regions | Verifiable |

**Detailed Interface Contract**:

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

**MDAP Design Output Expectations**:
- Stage 1: confirm OCR processor boundary and output contract
- Stage 2: map dependency on MODULE-001-12 route_mode=ocr
- Stage 3: derive success, partial-success, and failure-path tests from AC1-AC5
- Stage 4: document fallback and review routing behavior
- Stage 5: produce sign-off evidence for no-silent-drop guarantee

---

## 4. Stage A Acceptance Criteria Mapping

| FR-024 AC | Module(s) | Test Evidence Type |
|----------|-----------|--------------------|
| AC1 | MODULE-001-11 | Unit + integration (format routing) |
| AC2 | MODULE-001-12 | Unit (coverage computation) |
| AC3 | MODULE-001-12 | Unit (>=0.70 native routing) |
| AC4 | MODULE-001-12, MODULE-001-13 | Unit + integration (<0.70 OCR routing) |
| AC5a-AC5d | MODULE-001-12 | Layout parsing integration tests |
| AC6 | MODULE-001-11, MODULE-001-13 | Failure-path tests (no silent drop) |
| AC7 | MODULE-001-13 | Contract tests for extraction_source + confidence |

---

## 5. Dependencies

### 5.1 Internal Module Dependency Chain (Stage A)

```text
MODULE-001-11 (File Type Detection Router)
	-> outputs detected_type, route_target, detection_confidence

If detected_type == pdf:
	MODULE-001-12 (PDF Coverage and Layout Router)
		-> outputs route_mode, text_coverage_ratio, layout_flags

	If route_mode == ocr:
		MODULE-001-13 (OCR Extraction Processor)
			-> outputs extracted_items, extraction_source, item_confidence, failure_events

Common downstream integration:
	Existing EPIC-001 confidence gating path (FR-002)
```

### 5.2 Internal Dependency Notes
- MODULE-001-11 feeds all file categories, not only PDF.
- MODULE-001-12 depends on MODULE-001-11 only when detected_type=pdf.
- MODULE-001-13 depends on MODULE-001-12 only when route_mode=ocr.
- Native PDF text extraction remains in the existing EPIC-001 path and is selected by MODULE-001-12.

### Hard Blocking Dependencies
- Existing EPIC-001 baseline contracts for field confidence and review routing (FR-002) must remain unchanged.
- THRESHOLD-OCR-01 is fixed at 0.70 and must be applied exactly.

### Soft Dependencies
- NFR-007 observability fields may be emitted in Stage A logs but full dashboarding can be deferred.

### External Dependencies
- OCR library runtime availability and system package installation requirements (implementation-time concern, not changing Epic scope).

---

## 6. Risks and Controls (Stage A)

| Risk ID | Component | Risk | Likelihood | Severity | Impact | Control | Closure Evidence |
|---------|-----------|------|------------|----------|--------|---------|-----------------|
| R-001 | MODULE-001-11 | Wrong file type route | Medium | High | Incorrect extraction path | MIME + extension cross-check; unknown type review route | File-routing unit and integration evidence |
| R-002 | MODULE-001-12 | Incorrect coverage ratio | Medium | High | Wrong text/OCR decision | Coverage computation tests with fixed fixtures | Threshold-routing evidence across representative PDF fixtures |
| R-003 | MODULE-001-12 | Layout merge errors | Medium | Medium | Item order/association errors | Conflict logging + review routing for unresolved merges | Two-column and table-layout integration evidence |
| R-004 | MODULE-001-13 | OCR degradation on poor scans | High | High | Low quality extraction | FR-002 confidence gating + review_required fallback | OCR failure/low-confidence routing evidence |

### 6.1 Pre-Implementation Validation (Before MDAP Begins)

**Architectural Readiness**:
- [ ] Module-level acceptance criteria defined for MODULE-001-11, MODULE-001-12, and MODULE-001-13
- [ ] Public interface contracts specified with typed field expectations
- [ ] Internal dependency graph documented and reviewed
- [ ] Integration point with existing FR-002 confidence gating confirmed

**Requirement Readiness**:
- [ ] THRESHOLD-OCR-01 locked at 0.70
- [ ] ASSUMPTION-007 tracked as unresolved implementation constraint
- [ ] OQ-FR024-01 and OQ-FR024-02 explicitly carried into MDAP

**Risk Readiness**:
- [ ] Each risk has a closure evidence type
- [ ] Mitigation strategy can be traced to a planned test or review gate

---

## 7. Success Metrics (Stage A Validation)

| Metric ID | Description | Baseline | Target |
|-----------|-------------|----------|--------|
| SM-020 | File type detection accuracy | [ESTABLISH AT LAUNCH] | >=98% |
| SM-021 | Coverage ratio computation accuracy | [ESTABLISH AT LAUNCH] | >=95% within accepted fixture variance |
| SM-022 | Two-column/table layout detection usefulness | [ESTABLISH AT LAUNCH] | >=90% correctly flagged in validation set |
| SM-023 | OCR extraction success rate | [ESTABLISH AT LAUNCH] | >=95% |
| SM-024 | Silent data loss rate | [ESTABLISH AT LAUNCH] | 0% |

---

## 8. Stage Gate (Chunk 4 Approval)

### 8.1 Stage A Sub-Sequencing

**Sub-Stage A1**
- Implement MODULE-001-11 and validate routing contract stability
- Complete unit coverage for detected_type and route_target behavior

**Sub-Stage A2**
- Implement MODULE-001-12 and MODULE-001-13
- Validate threshold routing, layout flags, OCR outputs, and failure routing

Chunk 5 (FR-025) MUST NOT start until all gates below pass:

- [x] FR-024 AC1..AC7 evidence attached
- [x] THRESHOLD-OCR-01 behavior verified: >=0.70 native, <0.70 OCR
- [x] Mixed sample test set includes PDF, DOCX, XLSX and two-column/table PDF examples
- [x] Failure-path verification: no silent drop, review_required routing confirmed
- [x] Data contract fields present: extraction_source + confidence on extracted outputs
- [x] Stakeholder sign-off recorded for Stage A close

---

## 9. Open Questions Carried Forward

- OQ-FR024-01: Secondary OCR fallback activation policy if primary OCR underperforms.
- OQ-FR024-02: Conflict resolution policy when native text and OCR disagree on same field.
- ASSUMPTION-007 linkage: upload size cap threshold remains unresolved and may affect Stage A timeout behavior.

---

## 10. Sign-Off

**Amendment Status**: Approved for Stage A implementation.

**Sign-Off Fields**  
- Product Owner: APPROVED (User Directive) Date: March 26, 2026  
- Architecture Lead: APPROVED (User Directive) Date: March 26, 2026  
- Data Lead: APPROVED (User Directive) Date: March 26, 2026

---

## HANDOFF NOTE

This amendment authorizes only Chunk 4 planning and implementation preparation. No Chunk 5/6 implementation work is permitted until Stage A gate is explicitly approved.
