# Architecture Component View

**Project:** School Material Price Finder (Brazil MVP)  
**Phase:** Architecture Refinement  
**Date:** March 25, 2026

---

## Purpose

This artifact makes the Architecture phase more concrete by showing:
- actor-to-system interactions
- component boundaries inside the modular monolith
- cross-component dependencies
- which parts are likely to become folders in the next phase

It is intentionally more explicit than the Architecture Definition document, but still remains implementation-agnostic.

---

## 1. System Context View

### Actors
- School List User: uploads lists, reviews items, edits material details, starts search, reviews results, exports outputs
- Local Maintenance Operator: manages websites, reviews source health, inspects logs and audit history on the trusted local workstation
- External Retailer APIs/Websites: provide offer data
- Trust/Reputation Sources: provide trust-validation signals during onboarding and revalidation

### Context Narrative
The product is a local-first web application that ingests school material lists from mixed source documents, converts them into a canonical item set, queries eligible retailers, ranks results by delivered price and trust, allows corrective edits, and exports the final curated output as PDF, CSV, or JSON.

---

## 2. Container View

### Runtime Containers
1. **Web Application Container**
   - server-rendered UI
   - form handling
   - orchestration entry points
   - synchronous user interactions

2. **Background Worker Container**
   - asynchronous source querying
   - retries/backoff
   - circuit-breaker state transitions
   - scheduled source-health tasks

3. **Relational Database Container**
   - canonical domain records
   - source governance state
   - search state
   - audit/version state

4. **File/Object Storage Container**
   - uploaded source documents
   - intermediate artifacts if needed
   - generated exports (PDF/CSV/JSON)

5. **External Source Container Set**
   - retailer APIs
   - retailer web pages for targeted scraping
   - trust/reputation services

### Container Interaction Summary
- Web Application writes uploads and user actions.
- Background Worker processes slow or external tasks.
- Both application containers read/write relational state.
- File/Object Storage holds binary artifacts.
- External Source Container Set is accessed only through integration adapters.

---

## 3. Component Decomposition View

### A. Intake and Canonicalization Component
**Owns:** MODULE-001-01 through MODULE-001-07

**Sub-boundaries:**
- Upload intake
- Extraction and confidence routing
- Normalization and duplicate review
- Category/ISBN enforcement
- Search-readiness gate

**Primary outputs:**
- Canonical item set
- Review tasks
- Search-ready material records

### Amendment Note for Component A
- Approved PRD amendment FR-024 introduces mixed-document routing and OCR-first PDF decisioning.
- Pending downstream approval adds Stage A modules: MODULE-001-11, MODULE-001-12, MODULE-001-13.
- DOCX and XLSX routing are in scope for the router boundary; new DOCX/XLSX parser redesign is not.

### B. Source Governance Component
**Owns:** MODULE-002-01 through MODULE-002-05

**Sub-boundaries:**
- Source onboarding
- Trust classification
- Site eligibility policy
- Failure monitoring and suspension lifecycle
- Brand-expansion approval and substitution logging

**Primary outputs:**
- Eligible-source list
- Source trust state
- Brand governance decisions

### C. Search and Ranking Component
**Owns:** MODULE-003-01 through MODULE-003-04

**Sub-boundaries:**
- Search job orchestration
- Adapter fan-out execution
- Match classification
- Ranking and Apostila routing

**Primary outputs:**
- Candidate offers
- Ranked offers
- Coverage and exception state

### D. User Workflow and Export Component
**Owns:** MODULE-004-01 through MODULE-004-03

**Sub-boundaries:**
- Editable item workflow
- Version and audit trail
- Export generation and delivery

**Primary outputs:**
- Edited item state
- Immutable version history
- PDF/CSV/JSON export artifacts

---

## 4. Dependency View

### Inter-Component Dependencies
- Source Governance Component depends on shared persistence and outbound integration boundaries, but not on Intake and Canonicalization.
- Search and Ranking Component depends on Intake and Canonicalization for search-ready items.
- Search and Ranking Component depends on Source Governance for eligible sources and source-health state.
- User Workflow and Export Component depends on Search and Ranking for ranked offers.
- User Workflow and Export Component depends on Intake and Canonicalization for category and edit-boundary rules.

### Critical Path
1. Upload and canonicalization complete
2. Eligible-source set resolved
3. Search fan-out executed
4. Ranking completed
5. User edits/versioning applied
6. Export artifact generated

### Parallel Work Potential
- Source onboarding and trust validation can evolve independently from list ingestion.
- Some source-health maintenance tasks can run independently from active list processing.
- Export delivery can be retried independently after ranking and version history are already durable.

---

## 5. Failure Surface View

### Intake and Canonicalization
- Bad upload or low extraction confidence does not kill the batch; it creates review work.
- Mixed-document routing uncertainty must default to review_required rather than silent data loss.

### Source Governance
- Trust-source outages do not auto-approve sites; they leave sites pending or unchanged.

### Search and Ranking
- Per-source failures degrade coverage, not total availability, unless all eligible sources fail.

### User Workflow and Export
- Export failure does not erase ranking or edit state; it only blocks artifact generation until retry succeeds.

---

## 6. Folder/File Structure Preview

This is the first concrete preview of what comes after Architecture.

The next phase will likely turn component boundaries into top-level application folders such as:
- /web
- /intake_canonicalization
- /source_governance
- /search_ranking
- /workflow_export
- /platform
- /tests

What changes in that next phase:
- We stop talking about architecture in abstract components.
- We start deciding where files live.
- We define which folders own views, services, models, adapters, jobs, and shared infrastructure.
- We preserve traceability so a folder or file can still be tied back to MODULE-xxx-yy and FR/NFR IDs.

---

## 7. Why This Matters Before Coding

Without this artifact, the jump from Architecture to folder structure can feel arbitrary.
With this artifact, the next phase has a clear rule:
- component boundary first
- file layout second
- code only after both are stable

---

## AMENDMENT: FOUNDATION PIPELINE EXPANSION (FR-024..FR-026)

**Status**: PRD APPROVED; downstream EPIC/MDAP propagation pending  
**Date**: March 26, 2026

### Boundary Check Result
- No scope boundary violation detected.
- The amendment extends the existing intake boundary rather than creating a new component.

### Pending Component Change (Non-Canonical Until EPIC/MDAP Approval)

```text
MODULE-001-11: File Type Detection Router
   -> routes PDF, DOCX, XLSX into compatible extraction paths

MODULE-001-12: PDF Coverage and Layout Router
   -> decides native_text vs ocr for PDFs using THRESHOLD-OCR-01 = 0.70

MODULE-001-13: OCR Extraction Processor
   -> executes OCR path and returns extraction_source + confidence metadata
```

### Architectural Effect
- Component A expands from PDF-only wording to mixed-document ingestion.
- No new top-level component is required.
- Chunk 5 and Chunk 6 remain outside this component-view amendment until their downstream approvals exist.

---

## AMENDMENT: CIR-002 / MIA-001 — AI Directive Extraction Fallback

**Status**: PENDING HUMAN GATE APPROVAL  
**Date**: March 27, 2026

### Amended Component A: Intake and Canonicalization Component

**Pending addition** (CIR-002, all PENDING sign-off):

```
MODULE-001-08: Deterministic Directive Parser
  - Feeds into: MODULE-001-10
  - Risk: MEDIUM
  - Sub-boundary: Directive notation parsing and confidence scoring

MODULE-001-09: LLM Fallback Gateway
  - Feeds into: MODULE-001-10
  - Conditional: invoked only when MODULE-001-08 directive_confidence < THRESHOLD-LLM-01
  - External dependency: configured LLM provider (architecture decision deferred)
  - Risk: HIGH
  - Sub-boundary: External LLM call lifecycle (prompt, invoke, retry, timeout, parse, shadow mode)

MODULE-001-10: Directive Reconciliation Resolver
  - Receives from: MODULE-001-08 (always) + MODULE-001-09 (when invoked)
  - Feeds into: MODULE-001-07 (with complete directive contract)
  - Risk: HIGH
  - Sub-boundary: Reconciliation precedence policy; directive contract finalization; audit trail write
```

**Updated Sub-boundaries for Component A**:
- Upload intake
- Extraction and confidence routing
- **Directive extraction: deterministic parser → [conditional LLM fallback] → reconciliation resolver** ← NEW
- Normalization and duplicate review
- Category/ISBN enforcement
- Search-readiness gate

**Updated Primary outputs for Component A**:
- Canonical item set
- Review tasks
- Search-ready material records
- **Directive contract per item: school_exclusive, required_sellers, preferred_sellers, directive_confidence, decision_source, requires_human_review** ← NEW

### Amended Component C: Search and Ranking Component

**Pending addition** (CIR-001, PENDING sign-off):

```
MODULE-003-05: School Exclusivity Resolver
  - Receives from: MODULE-001-10 (directive contract) + MODULE-002-04 (eligible sources)
  - Feeds into: MODULE-003-01 (Query Orchestrator)
  - New position: between directive contract resolution and search fan-out
  - Risk: HIGH
```

**Updated Sub-boundaries for Component C**:
- **Exclusivity resolution and conflict logging** ← NEW (MODULE-003-05)
- Search job orchestration
- Adapter fan-out execution
- Match classification
- Ranking and Apostila routing

### Updated Inter-Component Dependency

New dependency added:

```
Intake and Canonicalization Component
    ↓ directive contract (MODULE-001-10 output)
Search and Ranking Component → MODULE-003-05 (exclusivity resolver)
    ↓ resolved item with exclusivity state
MODULE-003-01 (query orchestrator)
```

### New External Integration Pattern (PENDING — requires Architecture decision)

MODULE-001-09 (LLM Fallback Gateway) introduces an **outbound LLM call** as a new external integration type. This requires:

- A-04 amendment: LLM gateway adapter added as a third integration adapter type (alongside retailer API and targeted scraping adapters)
- Provider selection and API credential management deferred to Architecture implementation decision
- A-05 amendment: shadow mode structured logs added to observability baseline

**All changes above are PENDING. Treat as non-canonical until CIR-002 / MIA-001 are approved.**
