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
The product is a local-first web application that ingests school material lists, converts them into a canonical item set, queries eligible retailers, ranks results by delivered price and trust, allows corrective edits, and exports the final curated output as PDF, CSV, or JSON.

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
   - uploaded PDFs
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
