# PRD Addendum: Foundation Pipeline Expansion (OCR + Persistence + Real Source Adapters)

**Status**: DRAFT — PENDING STAKEHOLDER SIGN-OFF  
**Date**: March 26, 2026  
**References**: PRD.md (FR-001..FR-021) [BASELINE — NOT MODIFIED]; PRD_ADDENDUM_FR022.md [NOT MODIFIED]; PRD_ADDENDUM_FR023_AI_DIRECTIVE_EXTRACTION.md [NOT MODIFIED]  

---

## 1. Executive Summary

Current system flow is functionally structured but still relies on mock search execution and limited ingestion strategy. This addendum defines the minimum production foundation needed to move from demonstration flow to real data flow.

This amendment introduces three new requirements, each mapped to one execution chunk:
- **Chunk 4 → FR-024**: Conservative OCR-first ingestion strategy for mixed file types
- **Chunk 5 → FR-025**: End-to-end persistent pipeline state in SQLite via Django models/services
- **Chunk 6 → FR-026**: Real website data acquisition adapters with controlled execution and SQL persistence

**Important implementation policy**: these three chunks SHALL be implemented and approved sequentially, not as one combined implementation.

**In Scope**:
- File-type aware ingestion (PDF, DOCX, XLSX)
- PDF text-vs-image routing using fixed threshold
- Persisted state for materials, extracted fields, search runs, and offers
- Real source adapters replacing mock search execution
- Runtime storage in SQLite for MVP

**Out of Scope**:
- Full anti-bot bypass and stealth scraping (no proxy chains, no adversarial bypass)
- Handwritten-specialized OCR model training (generic OCR only in MVP)
- Image restoration pipelines (deskew/denoise/contrast optimization beyond minimal preprocessing)
- Real-time extraction progress UI (batch status only for MVP)
- Multi-language OCR beyond Portuguese-BR and English fallback
- Distributed extraction cluster orchestration (single-node execution for MVP)
- New ranking formula redesign
- New report UX redesign
- Non-MVP document formats beyond PDF/DOCX/XLSX

---

## 2. Decision Record: Sequential Execution Strategy

### Concern Addressed
Implementing Chunks 4, 5, and 6 in one pass creates high integration risk (large surface area, difficult debugging, and higher hallucination/assumption risk).

### Decision
**Selected strategy: Sequential gated execution (one approved chunk at a time).**

### Rationale
- Keeps each chunk testable with clear acceptance gates
- Reduces integration ambiguity and cross-module regressions
- Allows stakeholder approval checkpoint between chunks
- Improves traceability from requirement to implementation and test evidence

### Mandatory Gating Rule
No implementation of Chunk N+1 may start until Chunk N is approved with:
1. requirement acceptance criteria evidence,
2. test results,
3. data contract sign-off.

---

## 3. New Functional Requirements

### FR-024 [MUST]: The system shall apply a conservative multi-format ingestion strategy with PDF text-versus-image routing, using a fixed text coverage threshold of 70%.

**Acceptance Criteria**:

| ID | Given | When | Then |
|----|-------|------|------|
| AC1 | Uploaded file is PDF, DOCX, or XLSX | Ingestion starts | System shall detect format and route to corresponding extractor |
| AC2 | Uploaded file is PDF | Pre-check runs | System shall compute text coverage ratio for direct text extraction viability |
| AC3 | PDF text coverage ratio is >= 0.70 | Extraction routing executes | System shall use direct text extraction path (non-OCR) |
| AC4 | PDF text coverage ratio is < 0.70 | Extraction routing executes | System shall use OCR extraction path for image-based content |
| AC5a | PDF has detected two-column layout | Column detection executes | Each column shall be extracted separately and merged in reading order |
| AC5b | Column merge produces conflicting order | Merge logic runs | Conflict shall be logged with source references and item routed to review when unresolved |
| AC5c | Table-heavy PDF is detected | Table extraction runs | Table cells shall be extracted as structured rows with extraction_metadata |
| AC5d | Layout uncertainty remains after parsing | Extraction completes | Uncertain items shall carry lower confidence and route via FR-002 rules |
| AC6 | Any extractor fails for a page/section | Processing completes | Failure shall be logged and affected items routed to review_required (no silent drop) |
| AC7 | Output fields are generated | Persistence handoff occurs | Each extracted field shall carry extraction_source and confidence metadata |

**Source**: FR-001 extraction intent + stakeholder directive in this conversation fixing OCR threshold.

**Depends On**: FR-001, FR-002

**Priority**: [MUST] — reason: ingestion quality determines all downstream correctness.

---

### FR-025 [MUST]: The system shall persist end-to-end pipeline state in SQLite across materials, extracted fields, search runs, offer snapshots, and report rows.

**Acceptance Criteria**:

| ID | Given | When | Then |
|----|-------|------|------|
| AC1 | Material extraction completes | Persist step runs | Material record shall be created/updated with status, confidence, and directive state |
| AC2 | Field extraction completes | Persist step runs | Extracted field rows shall be stored with source and confidence |
| AC3 | Query orchestration starts for an item | Search run created | SearchRun shall record query payload, target sources, and execution status |
| AC4 | Source returns offers | Snapshot persistence runs | Offer snapshots shall be stored with source site, URL, price, timestamp, and parser status |
| AC5 | Final report assembly runs | Row persistence runs | Report row records shall be stored with item, chosen offers, confidence summary, and provenance |
| AC6 | Partial failures occur | Pipeline finishes | Persisted state shall capture per-step failure reason without discarding successful steps |
| AC7 | Audit inspection occurs | Query history requested | System shall reconstruct full lineage: material -> extraction -> search runs -> offers -> report row |

**Source**: End-to-end state traceability required for production operation.

**Depends On**: FR-024

**Priority**: [MUST] — reason: no production-grade workflow exists without durable state.

---

### FR-026 [MUST]: The system shall use real source adapters for website data acquisition, persist retrieved offers, and enforce controlled runtime behavior.

**Acceptance Criteria**:

| ID | Given | When | Then |
|----|-------|------|------|
| AC1 | Item is search-eligible | Query executes | System shall call active real adapters (not mock executor) |
| AC2 | Adapter request succeeds | Parsing completes | Offers shall be normalized and persisted with price, URL, availability, and extraction metadata |
| AC3 | Adapter request fails transiently | Retry policy runs | System shall retry per configured max attempts and backoff |
| AC4 | Adapter repeatedly fails | Health guard runs | Source shall be marked degraded/suspended according to failure policy |
| AC5 | Source has no results | Execution completes | Search run shall persist no-result outcome explicitly (not error) |
| AC6 | Mixed source outcomes occur | Aggregation completes | Pipeline shall return partial status with per-source diagnostics |
| AC7 | Offer data is persisted | Downstream ranking/report executes | Ranking and report layers shall consume persisted offer snapshots, not transient-only memory data |

**Source**: FR-015 multi-source search objective + production requirement for real internet collection.

**Depends On**: FR-025

**Priority**: [MUST] — reason: real offer acquisition is core product value.

---

### 3.5 Technology Stack (Approved for MVP)

| Component | Library / Tool | Justification |
|-----------|----------------|---------------|
| Primary OCR | Tesseract 5.x via pytesseract | Open source, low cost, mature Python integration |
| PDF Text Extraction | PyPDF2 (primary), PyMuPDF (fallback) | Baseline compatibility with optional performance fallback |
| DOCX Extraction | python-docx | Standard Python option for .docx parsing |
| XLSX Extraction | openpyxl | Standard Python option for .xlsx parsing |
| File Type Detection | python-magic (+ extension validation) | MIME + extension cross-check to reduce misrouting |
| Persistence | Django ORM on SQLite | Aligns with current MVP architecture |
| Async Queue | Deferred choice: Celery or RQ | Needed for long-running OCR/search jobs in later phase |

**Policy Note**: THRESHOLD-OCR-01 (0.70) applies only to PDF text-vs-image routing.

---

## 4. Non-Functional Requirements

### NFR-006 [SHOULD]: Multi-library extraction resilience with >=95% completion and zero silent loss.

**Acceptance Criteria**:
- Given 100 mixed-format school lists, when pipeline runs, then at least 95 complete extraction without silent loss.
- Given extraction chain fails for an item/page, when fallbacks are exhausted, then item routes to review_required and failure is logged.
- Given one extraction library is unavailable, when fallback chain executes, then pipeline continues with available extractor path.

### NFR-007 [COULD]: OCR/extraction observability and library swappability.

**Acceptance Criteria**:
- Given extraction is running, when metrics are emitted, then per-library success rate, latency, and confidence distribution are recorded.
- Given OCR quality degradation threshold is breached, when monitoring evaluates metrics, then operations notification is generated.
- Given a compatible OCR adapter is introduced, when plugged into the extraction interface, then pipeline executes without contract changes.

---

## 5. Threshold Registry and Status

This addendum includes one fixed threshold and additional unresolved thresholds that block later stages until sign-off.

| Threshold ID | Description | Scope | Status | Resolution Phase |
|-------------|-------------|-------|--------|------------------|
| THRESHOLD-OCR-01 | PDF text coverage ratio for direct extraction path | FR-024 | **FIXED: 0.70** | Approved |
| THRESHOLD-OCR-02 | File retention duration (days) | FR-025 | [THRESHOLD NEEDED] | PRD sign-off |
| THRESHOLD-OCR-03 | Max extraction retry count per item/page | FR-024 | [THRESHOLD NEEDED] | PRD sign-off |
| THRESHOLD-SEARCH-01 | Rate limit per source (req/sec) | FR-026 | [THRESHOLD NEEDED] | Architecture |
| THRESHOLD-SEARCH-02 | Initial source list and priority | FR-026 | [THRESHOLD NEEDED] | Stakeholder + Architecture |
| THRESHOLD-OPS-01 | Retry/backoff/circuit numerics | FR-026 | [THRESHOLD NEEDED] | Architecture |

**Policy Note**: THRESHOLD-OCR-01 is fixed by stakeholder decision in this thread and shall not be altered in implementation without explicit amendment.

---

## 6. Data Contract Additions

FR-024/025/026 require persisted entities that support full lineage.

### Required Entity Families
- **Material**: canonical item identity + ingestion status
- **ExtractedField**: field-level value + source + confidence
- **SearchRun**: one execution attempt per item/query cycle
- **OfferSnapshot**: normalized source offer records
- **ReportRow**: final consolidated output rows with provenance references

### Minimum Provenance Fields
All persisted entities SHALL include:
- timestamp(s),
- source identifier,
- confidence and/or quality flags,
- reference link to predecessor entity (lineage chain).

### 6.1 Minimum Attribute Contract (MVP)

**Material**: id, upload_batch_id, filename, file_type, ingestion_status, extraction_confidence, extraction_source, item_count, directive_confidence, created_at, updated_at.

**ExtractedField**: id, material_id, field_name, field_value, normalized_value, extraction_source, field_confidence, requires_review, created_at.

**SearchRun**: id, material_id, query_payload, target_sources, execution_status, started_at, finished_at, failure_reason.

**OfferSnapshot**: id, search_run_id, source_site_id, source_url, title, price_value, currency, availability_status, parser_status, extracted_at.

**ReportRow**: id, material_id, selected_offer_ids, confidence_summary, provenance_summary, generated_at.

---

## 7. Impact on Existing Requirements

| Existing FR | Impact | Type |
|---|---|---|
| FR-001 | Extended with file-type router and OCR decision path | Extension |
| FR-002 | Confidence routing now receives extraction_source metadata from OCR/text path | Extension |
| FR-015 | Moves from conceptual multi-source querying to real adapter execution | Extension |
| FR-019 | Audit trail can include extraction/search/report lineage events from persisted state | Integration |
| FR-020 | Export consumes persisted report rows and provenance metadata | Integration |
| FR-022 / FR-023 | No behavioral change; consume improved upstream extraction/persistence quality | No direct change |

---

## 8. Governance Compliance

- ✅ GC-2 (Binary acceptance criteria): criteria are testable pass/fail.
- ✅ GC-5 (No invented thresholds): only THRESHOLD-OCR-01 is fixed; others explicitly unresolved.
- ✅ GC-8 (ID immutability): FR-024, FR-025, FR-026 are canonical and unchanged.
- ✅ Dependency clarity: explicit sequencing Chunk 4 -> Chunk 5 -> Chunk 6.
- ✅ Scope control: format and runtime boundaries explicitly declared.

---

## 9. Cross-Document Alignment

| Document | Element | Alignment | Notes |
|----------|---------|-----------|-------|
| PRD.md | FR baseline | ✅ | FR-024..FR-026 extend FR-001..FR-023 only |
| PRD_ADDENDUM_FR022.md | Exclusivity fields | ✅ | Upstream data quality improvement only |
| PRD_ADDENDUM_FR023_AI_DIRECTIVE_EXTRACTION.md | Directive confidence flow | ✅ | No contract break; improved ingestion and persistence |
| EPIC baseline | Extraction flow | ⚠️ Update needed | Add OCR router and persistence entities |
| MODULE-004-02 audit/versioning | Audit lineage | ✅ | FR-025 lineage integrates with existing audit intent |
| FR-015 search behavior | Real source execution | ✅ | FR-026 replaces mock execution path |

---

## 10. Risk Register

### High Risk

| Component | Risk | Impact | Mitigation |
|-----------|------|--------|------------|
| OCR quality | Poor scan quality causes extraction errors | Wrong items/prices downstream | FR-002 confidence gating + review routing + fallback chain |
| Multi-library integration | Version/runtime conflicts among extraction libraries | Pipeline instability | Version pinning, adapter interfaces, per-library tests |
| Source adapter reliability | Website structure and availability changes | Offer retrieval degradation | Retry/backoff, health status, partial completion handling |

### Medium Risk

| Component | Risk | Impact | Mitigation |
|-----------|------|--------|------------|
| DOCX/XLSX complexity | Advanced formatting not fully parsed | Incomplete extraction | Route uncertain outputs to review + warning logs |
| Performance vs SLA | OCR and multi-source calls may exceed SLA | Slow user outcomes | Async execution path and bounded timeout policies |

---

## 11. Success Metrics

| Metric ID | Description | Baseline | Target |
|-----------|-------------|----------|--------|
| SM-014 | Extraction success rate | [ESTABLISH AT LAUNCH] | >=95% |
| SM-015 | Multi-format coverage (PDF/DOCX/XLSX) | 0/3 | 3/3 |
| SM-016 | OCR accuracy on scanned PDFs | [ESTABLISH AT LAUNCH] | >=90% |
| SM-017 | File/record retention safety | [ESTABLISH AT LAUNCH] | 100% no silent loss |
| SM-018 | Search adapter activation rate | [ESTABLISH AT LAUNCH] | >=80% sources returning results |
| SM-019 | Offer persistence completeness | [ESTABLISH AT LAUNCH] | 100% stored offers |

---

## 12. Assumptions (Require Acknowledgment)

| ID | Assumption | Resolution |
|----|------------|------------|
| ASSUMPTION-005 | Input language is Portuguese-BR, with English fallback only | Stakeholder acknowledgment required |
| ASSUMPTION-006 | MVP usage is primarily one list per session; high-volume batch is deferred | Stakeholder acknowledgment required |
| ASSUMPTION-007 | File upload size cap is [THRESHOLD NEEDED] MB | PRD sign-off required |

---

## 13. Implementation Sequence (Approval-First)

### Stage A — Chunk 4 (FR-024)
Deliverable:
- Multi-format ingestion router
- PDF text coverage measurement
- OCR fallback at fixed threshold 0.70

Gate to proceed:
- FR-024 acceptance criteria evidence
- unit + integration tests for mixed file samples
- stakeholder approval for Stage A close
- THRESHOLD-OCR-01 confirmed locked at 0.70

### Stage B — Chunk 5 (FR-025)
Deliverable:
- SQLite model wiring + service layer persistence
- lineage reconstruction queries

Gate to proceed:
- FR-025 acceptance criteria evidence
- migration + persistence integration tests
- stakeholder approval for Stage B close
- THRESHOLD-OCR-02 decided

### Stage C — Chunk 6 (FR-026)
Deliverable:
- Real adapters replacing mock executor
- persisted offer snapshots
- controlled runtime behavior (retry + health states)

Gate to proceed:
- FR-026 acceptance criteria evidence
- adapter integration tests (mocked HTTP + bounded live smoke checks)
- stakeholder approval for Stage C close
- THRESHOLD-SEARCH-01 and THRESHOLD-SEARCH-02 decided

### Gate Checklist Detail

**Stage A Gate (FR-024 -> FR-025)**
- [ ] Mixed-format sample validation evidence attached
- [ ] OCR routing tests pass (>=0.70 direct text, <0.70 OCR)
- [ ] Failure-to-review routing verified (no silent drop)

**Stage B Gate (FR-025 -> FR-026)**
- [ ] Material/ExtractedField/SearchRun/OfferSnapshot/ReportRow migrations applied
- [ ] Lineage reconstruction query verified end-to-end
- [ ] Partial-failure persistence behavior verified

**Stage C Gate (FR-026 -> Production Readiness)**
- [ ] Mock executor fully removed from production flow
- [ ] Retry/backoff and health-state transitions tested
- [ ] Persisted offer snapshots consumed by ranking/report flow

---

## 14. Open Questions (For Architecture Follow-Up)

**OQ-FR024-01**: Secondary OCR fallback priority and activation policy if primary Tesseract path underperforms.

**OQ-FR024-02**: Conflict policy when native text extraction and OCR disagree for the same field.

**OQ-FR025-01**: Retention window for offer snapshots and report rows in SQLite before archival.

**OQ-FR026-01**: Initial source list and compliance constraints (robots/terms) per website.

**OQ-FR026-02**: Numeric values for retry/backoff/circuit suspension policy (THRESHOLD-OPS-01).

**OQ-FR026-03**: File upload size cap and timeout budgets for ingestion and search stages.

---

## 15. Approvals and Sign-Off Gate

This addendum cannot move to implementation until approvals are complete.

- [ ] Product Owner approval (scope and sequencing)
- [ ] Architecture Lead approval (technical feasibility and dependency order)
- [ ] Data Lead approval (schema and lineage integrity)
- [ ] Operations Lead approval (adapter runtime policy)

**Sign-Off Fields**  
- Product Owner: _________________ Date: _________
- Architecture Lead: _________________ Date: _________
- Data Lead: _________________ Date: _________
- Operations Lead: _________________ Date: _________

---

## HANDOFF NOTE

This document defines only requirement-level scope for Chunks 4, 5, and 6. Implementation SHALL start with Chunk 4 only after explicit approval of this addendum and SHALL remain sequential by stage gate.
