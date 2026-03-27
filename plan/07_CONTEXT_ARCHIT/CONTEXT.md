# CONTEXT.md
## Pipeline Traveling Context — Controlled Handoff Document

**Written by:** PRD Phase  
**Updated by:** MDAP Phase, Architecture Phase  
**Amended by:** CIR-002/MIA-001 (AI Directive Extraction Fallback) — PENDING APPROVAL; PRD Addendum FR-024..FR-026 (Foundation Pipeline Expansion) — APPROVED; EPIC Amendment 004 (Chunk 4 / FR-024) — PENDING APPROVAL; Deployment Readiness Governance Reclassification (Implementation DOR) — APPLIED  
**Read by:** EPIC · MDAP · Architecture · Folder/File Structure · Implementation  
**Date (Original):** March 25, 2026  
**Date (Last Amendment):** March 26, 2026  
**Project:** School Material Price Finder (Brazil MVP)

---

## TRAVELING_CONTEXT

### Amendment Status
This document contains amendment blocks reflecting:
- PRD Addendum FR-023 (AI-assisted directive extraction fallback)
- EPIC Amendment CIR-002 (EPIC-001 extension with 3 new modules)
- MDAP MIA-001 (impact assessment pending human gate approval)
- PRD Addendum FR-024..FR-026 (Foundation Pipeline Expansion) — approved at PRD level
- EPIC Amendment 004 (Chunk 4 / FR-024 Conservative OCR Ingestion) — pending stakeholder sign-off

⚠️ CAUTION: PRD-approved FR/NFR additions are canonical requirements. Downstream module inventories and architecture/module details remain non-canonical until the related EPIC/MDAP amendment artifacts are approved.

### Scope Ceiling (Canonical)
```
School Material Price Finder is a Brazil-focused tool for parents, school 
administrators, and budget-conscious shoppers who need to buy complete school 
lists from mixed document formats while controlling total spend.
```

### Canonical ID Ranges (Locked — No Renumbering Downstream)
- **Functional Requirements:** FR-001 through FR-026 (26 total)
- **Non-Functional Requirements:** NFR-001 through NFR-007 (7 total)
- **Canonical EPIC Inventory:** EPIC-001 through EPIC-004 (4 total)
- **User Personas:** PERSONA-001 (1 total — see assumptions)
- **Success Metrics:** SM-001 through SM-024+ (post-launch validation)
- **Open Questions:** OQ-001 through OQ-012+, plus amendment-specific OQ-FR024..OQ-FR026 identifiers

### Governance Classification Note
- Deployment readiness planning is an implementation-layer artifact (`plan/06_Implementation/DEPLOYMENT_READINESS_DOR.md` and `plan/06_Implementation/PROMPT-7_DEPLOYMENT_EXECUTION_BACKLOG.md`).
- It does not constitute a functional EPIC and does not alter canonical EPIC inventory or FR/NFR counts.

### Hard Constraints (Confirmed Non-Negotiable)
- Identifier permanence (GC-8): All FR/NFR IDs are canonical across entire pipeline. Do NOT renumber, merge, split, or rename.
- Scope ceiling immutable: Any requirement not traceable to stated user need is out of scope by default.
- No sub-personas without PRD amendment: EPIC phase SHALL NOT introduce new personas (e.g., parent vs admin variants) without explicit PRD revision.
- No invented thresholds: All [THRESHOLD NEEDED] items must be resolved by stakeholder decision, not LLM inference.

### Out-of-Scope Summary
Explicitly deferred features (documented in PRD Section 7):
- Per-user geolocation shipping customization
- Price history or predictive analytics
- Real-time price notifications
- API for third-party integrations
- Multi-language support beyond Portuguese-BR
- Mobile app (web MVP only)
- Bulk list import from competitor platforms
- Payment processing or cart integration

### Pipeline Stage
**Current:** Amendment propagation (baseline MDAP complete; approved PRD amendment for FR-024..FR-026; Chunk 4 EPIC amendment pending sign-off)  
**Next:** MDAP Amendment for Chunk 4 after EPIC amendment approval  
**Full sequence:** PRD → EPIC → MDAP → System Architecture → Folder/File Structure, with approved amendment flow applied where required

---

## PRD_HANDOFF_BLOCK

This block is the structured data payload for EPIC consumption. Extract and reference during Epic decomposition.

### FR_IN_SCOPE (26 Functional Requirements)

**Data Extraction & Validation (FR-001 to FR-009):**
- FR-001: Extract mixed-PDF item fields reliably
- FR-002: Gate extraction by confidence bands
- FR-003: Normalize quantities and canonical units
- FR-004: Deduplicate items and queue merges
- FR-005: Enforce category required field rules
- FR-006: Enforce category forbidden constraints
- FR-007: Apply hard constraints before search
- FR-008: Normalize and validate ISBN formats
- FR-009: Require missing ISBN before search

**Brand Handling & Source Trust (FR-010 to FR-014):**
- FR-010: Request approval for brand fallback
- FR-011: Log cross-brand substitution reason codes
- FR-012: Onboard websites with trust validation
- FR-013: Block bad-rated sites from search
- FR-014: Auto-suspend sites after failures threshold

**Search & Ranking (FR-015 to FR-017):**
- FR-015: Query all activated eligible websites
- FR-016: Classify matches via confidence thresholds
- FR-017: Rank by delivered price plus trust

**User Workflow (FR-018 to FR-021):**
- FR-018: Allow pre-search item field edits
- FR-019: Version edits and merge decisions
- FR-020: Export results to PDF, CSV, and JSON
- FR-021: Route Apostila to external sources

**Directive and Exclusivity Expansion (FR-022 to FR-023):**
- FR-022: Resolve school-defined seller exclusivity constraints
- FR-023: Apply AI-assisted directive extraction fallback under controlled reconciliation

**Foundation Pipeline Expansion (FR-024 to FR-026):**
- FR-024: Apply conservative multi-format ingestion with PDF text-vs-image routing at 0.70 threshold
- FR-025: Persist end-to-end pipeline state in SQLite across materials, extracted fields, search runs, offers, and report rows
- FR-026: Use real source adapters for website data acquisition with controlled runtime behavior

### NFR_MUST_SHOULD (7 Non-Functional Requirements)

| ID | Priority | Requirement |
|---|---|---|
| NFR-001 | MUST | Complete list processing within 10 minutes (SLA) |
| NFR-002 | SHOULD | Keep structured decision audit logs |
| NFR-003 | SHOULD | Preserve versioned change history records |
| NFR-004 | SHOULD | Track website health and suspensions |
| NFR-005 | COULD | Expose configurable log-retention and query filters for diagnostics |
| NFR-006 | SHOULD | Multi-library extraction resilience with >=95% completion and zero silent loss |
| NFR-007 | COULD | OCR/extraction observability and library swappability |

### PERSONAS (1 User Type)

- **PERSONA-001: School List User**
  - Role: Parent, school administrator, or budget-conscious shopper
  - Primary goal: Find complete school material list at lowest delivered cost while preserving item constraints
  - Primary pain point: School material price comparison is manual, time-consuming, and error-prone across multiple sources

### UNRESOLVED_ASSUMPTIONS (4 Items — Require Stakeholder Sign-Off)

1. **ASSUMPTION-001:** Persona model is a single generalized School List User without role-specific workflow variants (parent vs admin). If sub-personas are needed, PRD must be amended before EPIC proceeds.

2. **ASSUMPTION-002:** Scope ceiling statement is sourced from Executive Summary sentence 1. No explicit one-line scope-ceiling statement appears elsewhere in PRD Phase 1 output.

3. **ASSUMPTION-003:** Export schema formatting details (column order, locale decimal separators, date/time format) remain undefined and deferred to MDAP phase.

4. **ASSUMPTION-004:** Brand substitution reason-code taxonomy remains undefined. EPIC phase must define taxonomy or defer to stakeholder decision.

### THRESHOLD_STATUS (7 Items — Resolved or Carried Forward)

| THRESHOLD-ID | Affected FR(s) | Current Status | Resolution Phase |
|---|---|---|---|
| THRESHOLD-001 | NFR-001 | Resolved: 3 to 10 visible items (expandable) | PRD sign-off |
| THRESHOLD-002 | NFR-001 | Unresolved: reference hardware/environment for performance measurement | Architecture carry-forward |
| THRESHOLD-003 | NFR-005 | Unresolved: audit-log retention duration; handled as runtime policy in MDAP | Architecture carry-forward |
| THRESHOLD-004 | FR-014, NFR-004 | Resolved: 5 consecutive failures in 1 hour | EPIC |
| THRESHOLD-005 | NFR-001, FR-015 | Unresolved: peak concurrent users without degradation | Architecture carry-forward |
| THRESHOLD-006 | FR-015, NFR-004 | Resolved: >=95% items searchable per site | EPIC |
| THRESHOLD-007 | FR-001, NFR-001 | Resolved: maximum PDF input size of 5 pages | PRD sign-off |

---

## THRESHOLD_ASSUMPTION_RESOLUTION_GATE

**This section is a formal blocker. All items below must be resolved (stakeholder sign-off or business decision) BEFORE EPIC phase begins.**

### Pre-Epic Sign-Off Checklist

#### Assumptions (Require Stakeholder Acknowledgment)

- [ ] **ASSUMPTION-001:** Single persona (School List User) without sub-roles is accepted for MVP.
  - **Chosen:** Keep single generalized persona. Impact: Workflow defaults apply uniformly.
  - ✅ CONFIRMED

- [ ] **ASSUMPTION-002:** Scope ceiling sourced from Executive Summary.
  - ✅ CONFIRMED

- [ ] **ASSUMPTION-003:** Export formatting deferred to MDAP.
  - ✅ CONFIRMED

- [ ] **ASSUMPTION-004:** Brand reason-code taxonomy deferred to EPIC or stakeholder decision.
  - ✅ CONFIRMED

#### Thresholds (Require Business/Product Decision)

- [ ] **THRESHOLD-001:** Define maximum items per list for 10-minute SLA.
  - **Assigned to:** PRD sign-off
  - **Decision:** 3 to 10  (e.g., "shows 3 imediately and alow to expand to max 10")
  - ✅ CONFIRMED

- [ ] **THRESHOLD-007:** Define maximum PDF upload size/page count.
  - **Assigned to:** PRD sign-off
  - **Decision:** 5 pages 
  - ✅ CONFIRMED

- [ ] **THRESHOLD-004:** Define consecutive failure count for auto-suspension.
  - **Assigned to:** EPIC
  - **Decision:** "5 consecutive failures in 1 hour
  - ✅ CONFIRMED

- [ ] **THRESHOLD-006:** Define per-website search completion rate target.
  - **Assigned to:** EPIC
  - **Decision:**  ≥95% items searchable per site
  - ✅ CONFIRMED

- [ ] **THRESHOLD-002, THRESHOLD-003, THRESHOLD-005:** Deferred to MDAP phase.
  - ✅ CONFIRMED

### Critical Open Question Resolution

- [ ] **OQ-001 (Persona Scope):** Resolved in ASSUMPTION-001 above.
  - ✅ CONFIRMED

### Scope Creep Validation

- [ ] Verify no unapproved FRs introduced. FR count is 26 including approved FR-024..FR-026. ✓
- [ ] Verify no new out-of-scope items added without justification. ✓
- [ ] Verify CONTEXT.md matches approved PRD baseline plus approved addenda only. ✓

### Gate Status: READY FOR EPIC?

**Proceed to EPIC only if ALL checkboxes above are marked [✓] with stakeholder signatures.**

- [ ] All 4 assumptions signed off
- [ ] All PRD sign-off thresholds (THRESHOLD-001, THRESHOLD-007) decided and recorded
- [ ] EPIC-phase thresholds (THRESHOLD-004, THRESHOLD-006) assigned owner
- [ ] MDAP-phase thresholds acknowledged (THRESHOLD-002, THRESHOLD-003, THRESHOLD-005)
- [ ] Scope ceiling confirmed immutable
- [ ] Persona decision locked
- [ ] No scope creep detected

**Gate Status:** READY FOR EPIC (all items complete)

---

## TRAVELING NOTES (For All Downstream Phases)

### For EPIC Phase
- Use [PRD_HANDOFF_BLOCK] above for FR/NFR inventory and quick reference
- Reference PRD-to-EPIC-INTEGRATION-GUIDE.md for complete dependency map
- Do NOT introduce new personas without amending PRD
- Do NOT invent thresholds for [THRESHOLD NEEDED] items
- Ensure all FR IDs (FR-001 to FR-026) remain locked and immutable

### For MDAP Phase
- Historical note: MDAP completed with 19 approved modules across 4 Epics
- THRESHOLD-002, THRESHOLD-003, and THRESHOLD-005 were not resolved in MDAP and now carry into Architecture
- Ensure all EPIC-produced artifacts maintain FR ID immutability
- Cross-reference [THRESHOLD_ASSUMPTION_RESOLUTION_GATE] for blockers

### For Architecture Phase
- Confirm all MDAP-produced specifications maintain FR/NFR/ID integrity
- Use the MDAP module registry below as the canonical module inventory for architecture design
- Preserve unresolved carry-forward items exactly as written: ASSUMPTION-003, ASSUMPTION-004, THRESHOLD-002, THRESHOLD-003, THRESHOLD-005
- Use scope ceiling as reference for architecture boundary
- Do NOT propose features outside out-of-scope list without PRD amendment
- FR-020 supported export formats are resolved for Architecture as PDF, CSV, and JSON
- Approved FR-024..FR-026 must be treated as in-scope requirements even where downstream EPIC/MDAP amendments remain pending

### For Folder/File Structure Phase
- Final artifact naming and organization should reference canonical FR/NFR IDs
- Maintain traceability from folder structure back to PR IDs

---

## MDAP_HANDOFF_BLOCK

This block is the structured handoff payload from MDAP to Architecture. It records the approved module registry and the unresolved items that remain architecture-bound.

### MDAP_PHASE_STATUS

- EPIC-001: Complete and advanced to Architecture
- EPIC-002: Complete and advanced to Architecture
- EPIC-003: Complete and advanced to Architecture
- EPIC-004: Complete and advanced to Architecture
- Total approved modules: 19

### MDAP_MODULE_REGISTRY

#### EPIC-001 Modules (7 total)
- MODULE-001-01: PDF Ingestion & Field Extraction | FRs: FR-001 | Risk: HIGH | Depends on: none
- MODULE-001-02: Confidence Gating Router | FRs: FR-002 | Risk: MEDIUM | Depends on: MODULE-001-01
- MODULE-001-03: Quantity & Unit Normalizer | FRs: FR-003 | Risk: MEDIUM | Depends on: MODULE-001-02
- MODULE-001-04: Duplicate Resolution Coordinator | FRs: FR-004 | Risk: HIGH | Depends on: MODULE-001-03
- MODULE-001-05: Category Rules & Eligibility Validator | FRs: FR-005, FR-006, FR-007 | Risk: HIGH | Depends on: MODULE-001-04
- MODULE-001-06: ISBN Normalization & Validation | FRs: FR-008 | Risk: MEDIUM | Depends on: MODULE-001-03
- MODULE-001-07: Missing-ISBN Search Gate | FRs: FR-009 | Risk: MEDIUM | Depends on: MODULE-001-05, MODULE-001-06

#### EPIC-002 Modules (5 total)
- MODULE-002-01: Brand Expansion Approval Gate | FRs: FR-010 | Risk: MEDIUM | Depends on: none
- MODULE-002-02: Brand Substitution Audit Logger | FRs: FR-011 | Risk: MEDIUM | Depends on: MODULE-002-01
- MODULE-002-03: Website Onboarding & Trust Classifier | FRs: FR-012 | Risk: HIGH | Depends on: none
- MODULE-002-04: Search Eligibility Site Filter | FRs: FR-013 | Risk: HIGH | Depends on: MODULE-002-03
- MODULE-002-05: Site Failure Monitor & Auto-Suspension | FRs: FR-014 | Risk: HIGH | Depends on: MODULE-002-03

#### EPIC-003 Modules (4 total)
- MODULE-003-01: Query Orchestrator | FRs: FR-015 | Risk: HIGH | Depends on: MODULE-001-05, MODULE-001-07, MODULE-002-04
- MODULE-003-02: Match Classifier | FRs: FR-016 | Risk: MEDIUM | Depends on: MODULE-003-01, optional MODULE-002-02 context
- MODULE-003-03: Ranking Engine | FRs: FR-017 | Risk: HIGH | Depends on: MODULE-003-02, MODULE-002-05
- MODULE-003-04: Apostila Routing Guard | FRs: FR-021 | Risk: MEDIUM | Depends on: MODULE-003-03, MODULE-001-04 provenance output

#### EPIC-004 Modules (3 total)
- MODULE-004-01: User Edit Handler | FRs: FR-018 | Risk: LOW | Depends on: EPIC-003 ranked output, MODULE-001-05 category contract
- MODULE-004-02: Versioned Audit Trail Logger | FRs: FR-019 | Risk: MEDIUM | Depends on: MODULE-004-01
- MODULE-004-03: Export Formatter & Delivery | FRs: FR-020 | Risk: MEDIUM | Depends on: MODULE-004-02

### ARCHITECTURE_CARRY_FORWARD_ITEMS

#### Unresolved Assumptions
- ASSUMPTION-003: Export schema and formatting details remain unresolved and must be handled in Architecture without changing FR IDs or module boundaries
- ASSUMPTION-004: Brand substitution reason-code taxonomy remains unresolved and must stay externally configurable

#### Unresolved Thresholds
- THRESHOLD-002: Reference hardware/environment for performance measurement
- THRESHOLD-003: Audit-log retention duration
- THRESHOLD-005: Peak concurrent users without degradation

#### Cross-Epic Dependency Summary
- EPIC-001 is the entry Epic and gates search eligibility and identifier readiness for EPIC-003
- EPIC-002 is the source-trust Epic and gates source eligibility and failure/reputation signals for EPIC-003
- EPIC-003 depends on EPIC-001 and EPIC-002 and produces ranked material output for EPIC-004
- EPIC-004 depends on EPIC-003 output plus EPIC-001 category rules and does not introduce reverse blocking

### ARCHITECTURE_ENTRY_NOTES

- Architecture should treat the 19 modules above as the approved decomposition baseline
- No new modules should be introduced unless traceably required by an approved change in scope
- Detailed implementation, storage choices, adapter design, and deployment concerns belong to Architecture, not MDAP
- All future folder/file structure work should preserve traceability from implementation artifacts back to these module IDs

---

## APPROVED_AMENDMENT_BLOCK — FR-024..FR-026 FOUNDATION PIPELINE EXPANSION

**Status:** PRD APPROVED  
**Date:** March 26, 2026

### Requirement Additions
- FR-024: Conservative multi-format ingestion with PDF text-vs-image routing
- FR-025: SQLite-backed persisted pipeline state
- FR-026: Real source adapters with controlled runtime behavior
- NFR-006: Extraction resilience
- NFR-007: OCR/extraction observability and swappability

### Boundary Notes
- These additions stay within the existing scope ceiling of mixed document formats and school-material price comparison.

### Downstream Propagation Status
- Stage A Implementation Scaffolding (Chunk 4): Complete ✅, 41/41 AC tests passing
  - MODULE-001-11 (File Type Detection): 12 tests ✅
  - MODULE-001-12 (PDF Coverage Router): 14 tests ✅
  - MODULE-001-13 (OCR Processor): 15 tests ✅
  - PROMPT-3 Implementation Guide: Complete
- EPIC Amendment 004 (Chunk 4 / FR-024): Approved ✅
- MDAP amendment for Chunk 4 (MIA-002): Approved ✅ (Gate Passed)
- Stage A implementation started ✅
  - A1/A4 kickoff: `stage_a_ingestion_pipeline.py` integrated as new entry orchestration
  - Stage A focused test suite: 45/45 passing
- Stage A2 hardening update ✅
  - MODULE-001-12 coverage computation upgraded from file-size stub to PDF marker analysis
  - Two-column, table-heavy, and uncertain-region heuristics implemented
  - Deterministic runtime assertions validated for native_text vs ocr routing and layout flags
- Stage A3 hardening update ✅
  - MODULE-001-13 upgraded with pluggable OCR invocation (`ocr_invoke_fn`) via context
  - Failure propagation hardened for engine exceptions, low-signal payloads, and explicit error reasons
  - Partial-success behavior preserved with page-aware output mapping and review_required markers
  - Runtime assertions validated injected-engine success and exception paths
- Stage A4 integration hardening update ✅
  - Added Stage A → MODULE-001-02 adapter: `to_confidence_handoff_items(...)`
  - Handoff preserves `extraction_source` (native_text/ocr/routing), confidence, and review-required semantics
  - Added integration coverage for native path, OCR path, and forced review path handoff behavior
  - Runtime assertions validated OCR-route handoff compatibility with confidence gating


## Governance References

- **Constraint Rules:** GC-1 through GC-9 enforced in PRD Phase (see PRD Blueprint v2.0)
- **ID Permanence Rule:** GC-8 — FR/NFR IDs are immutable across all pipeline phases
- **Citation Format:** All requirements source to PRD sections or [ASSUMPTION] tags
- **Sign-Off Protocol:** THRESHOLD_ASSUMPTION_RESOLUTION_GATE above is the formal blocker

---

**CONTEXT.md Status:** ✅ UPDATED THROUGH CHUNK 4 EPIC/MDAP APPROVAL | ✅ STAGE A IMPLEMENTATION STARTED  
**Last Updated:** March 26, 2026 (EPIC/MDAP approved; Stage A kickoff recorded)  
**Next Handoff:** Continue Stage A implementation (A1 -> A2 -> A3 -> A4 integration hardening)

**Modify this file only through approved phase-handoff merges. Treat it as the canonical traveling context.**

---

## ARCHITECTURE_HANDOFF_BLOCK

### ARCHITECTURE_STATUS

- Architecture definition completed from approved MDAP handoff and ADR-0001 baseline
- System style locked: Modular Monolith
- Frontend shape locked: server-rendered web app with small interactive components
- Runtime baseline locked: local-first single deployable Python application

### ARCHITECTURE_COMPONENTS

- Intake and Canonicalization Component: MODULE-001-01 through MODULE-001-07 | Responsibility: pre-search extraction, normalization, duplicate handling, search-readiness validation
- Source Governance Component: MODULE-002-01 through MODULE-002-05 | Responsibility: source trust, source eligibility, source lifecycle, and brand-governance controls
- Search and Ranking Component: MODULE-003-01 through MODULE-003-04 | Responsibility: eligible-source querying, candidate classification, ranking, and Apostila routing
- User Workflow and Export Component: MODULE-004-01 through MODULE-004-03 | Responsibility: user edits, version history, and export delivery

### ARCHITECTURE_TECHNOLOGY_BASELINE

- Frontend: Django templates + HTMX
- Backend: Python 3.12 + Django 5 modular monolith
- Database: PostgreSQL
- File/Object Storage: local filesystem behind storage abstraction
- Background Execution: database-backed job runner inside application boundary
- Source Integration: HTTPX + Playwright/BeautifulSoup adapters
- Export Formats: PDF, CSV, JSON

### ARCHITECTURE_DECISIONS_CONFIRMED

- FR-020 export format conflict resolved by stakeholder decision: PDF, CSV, and JSON are the supported export formats for Architecture and downstream phases
- Operator/maintenance screens remain inside the same application boundary as local maintenance capability; this is not a multi-user RBAC decision
- Cache/search index remains deferred unless performance evidence later justifies it

### HIGH_RISK_COMPONENTS

- Search and Ranking Component: performance-critical fan-out, timeout, retry, and partial-failure handling under NFR-001
- Source Governance Component: source trust classification and suspension lifecycle affect FR-012 through FR-014
- Security baseline for non-local deployment: authentication, authorization hardening, secret handling, and outbound credentials require human review before remote deployment

### ARCHITECTURAL_RISKS

- Scraping adapters may become brittle as retailer websites evolve
- THRESHOLD-002 and THRESHOLD-005 still limit precision of hard performance commitments
- THRESHOLD-003 still limits final retention policy design
- Local filesystem storage is appropriate for local-first deployment but will need replacement or stronger abstraction if deployment scope broadens

### NEXT_PHASE_ENTRY

- Next phase: Folder/File Structure
- Use Architecture components as the top-level decomposition basis for folders
- Preserve traceability from implementation folders back to component names and MODULE IDs

**CONTEXT.md Status:** ✅ UPDATED THROUGH ARCHITECTURE  
**Last Updated:** March 25, 2026  
**Next Handoff:** System Architecture → Folder/File Structure

---

## FOLDER_STRUCTURE_HANDOFF_BLOCK

### FILE_STRUCTURE_STATUS

- Folder/File Structure definition completed from Architecture handoff
- Scaffold tightened to the minimum Django-compatible support set for local-first implementation
- Single runtime gateway retained: ASGI

### FILE_STRUCTURE_PATTERN

- Architecture Pattern: component-aligned modular monolith with Django bootstrap
- Domain folders: `intake_canonicalization/`, `source_governance/`, `search_ranking/`, `workflow_export/`
- Delivery folder: `web/`
- Platform folder: `platform/`
- Configuration folder: `config/`
- Test folders: `tests/unit/` and `tests/integration/`

### FILE_STRUCTURE_COUNTS

- Total module-owned source files: 19
- Total unit test files: 19
- Total integration test files: 4
- Total support/config/bootstrap files in scaffold: 13
- Total scaffold files: 55

### FILE_STRUCTURE_HIGH_RISK_FILES

- `intake_canonicalization/pdf_ingestion_field_extraction.py`
- `intake_canonicalization/duplicate_resolution_coordinator.py`
- `intake_canonicalization/category_rules_eligibility_validator.py`
- `source_governance/website_onboarding_trust_classifier.py`
- `source_governance/site_failure_monitor_auto_suspension.py`
- `search_ranking/query_orchestrator.py`
- `search_ranking/ranking_engine.py`
- `workflow_export/versioned_audit_trail_logger.py`
- `workflow_export/export_formatter_delivery.py`
- `web/views.py`
- `platform/database.py`
- `platform/storage.py`
- `platform/job_runner.py`
- `config/settings.py`

### FILE_STRUCTURE_ENTRY_POINTS

- `manage.py`: local command/bootstrap entry point
- `config/asgi.py`: runtime gateway

### NEXT_PHASE_ENTRY

- Next phase: Implementation
- Implementation begins from stub files only; no business logic was approved in Folder/File Structure
- All flagged high-risk files require human review before coding proceeds

**CONTEXT.md Status:** ✅ UPDATED THROUGH FOLDER/FILE STRUCTURE  
**Last Updated:** March 25, 2026  
**Next Handoff:** Folder/File Structure → Implementation

---

## ⚠️ AMENDMENT_BLOCK: CIR-002 / MIA-001 — AI Directive Extraction Fallback (FR-023)

**Status**: PENDING HUMAN GATE APPROVAL (Stages B–D blocked on threshold resolution; Stage A approvable independently)  
**Amendment Date**: March 27, 2026  
**References**:
- PRD_ADDENDUM_FR023_AI_DIRECTIVE_EXTRACTION.md (DRAFT — pending sign-off)
- EPIC_AMENDMENT_001_CIR002_AI_DIRECTIVE_EXTRACTION.md (PENDING MDAP MIA-001 APPROVAL)
- MDAP_MIA-001_EPIC-001_AI_DIRECTIVE_EXTRACTION.md (PENDING HUMAN GATE APPROVAL)

---

### ⛔ CRITICAL: PROPOSED, NOT CANONICAL

DO NOT use amended ID ranges, module counts, thresholds, or high-risk files from this block as current baseline.

All values below are conditional and pending approval of all three change documents:
- PRD Addendum FR-023 sign-off
- EPIC Amendment CIR-002 approval
- MDAP MIA-001 human-gate approval

During the pending period, baseline sections above remain canonical. This amendment block describes the proposed post-approval state.

### Amendment Approval Paths

**Path A — APPROVED**
- Amendment values are merged into baseline sections.
- This block is archived as historical change record.
- CONTEXT status is updated to approved amendment state.

**Path B — CONDITIONAL**
- This block is updated with explicit conditions and deadlines.
- Conditional status remains until all conditions are satisfied.

**Path C — REJECTED / REWORK REQUIRED**
- This block is marked rejected and superseded by a revised amendment submission.
- Baseline sections above remain fully canonical.

---

### PROPOSED_AMENDED_CANONICAL_ID_RANGES (PENDING APPROVAL)

The following ranges will supersede the baseline `Canonical ID Ranges` only after all amendment approvals are complete.

- **Functional Requirements**: FR-001 through FR-023 (23 total; FR-022 via PRD_ADDENDUM_FR022, FR-023 via PRD_ADDENDUM_FR023)
- **Non-Functional Requirements**: NFR-001 through NFR-005 (5 total — unchanged)
- **User Personas**: PERSONA-001 (1 total — unchanged)
- **EPICs**: EPIC-001 through EPIC-004 (4 total — unchanged; EPIC-001 and EPIC-003 amended via CIR)
- **EPIC CIRs**: CIR-001 (EPIC-003 MODULE-003-05, PENDING), CIR-002 (EPIC-001 AI Directive Extraction, PENDING)
- **MDAP Change Records**: MIA-001 (EPIC-001 AI Directive Extraction, PENDING)
- **Thresholds**: THRESHOLD-LLM-01 through THRESHOLD-LLM-05 (5 total new; all [THRESHOLD NEEDED] — pending stakeholder decisions)

---

### AMENDED_MODULE_REGISTRY

**EPIC-001 Modules (10 total — was 7; +3 via CIR-002, all PENDING)**

| Module ID | Name | FRs | Risk | Status |
|-----------|------|-----|------|--------|
| MODULE-001-01 | PDF Ingestion & Field Extraction | FR-001 | HIGH | Approved (extended: emits notation_rules dict) |
| MODULE-001-02 | Confidence Gating Router | FR-002 | MEDIUM | Approved (extended: separate directive gating lane) |
| MODULE-001-03 | Quantity & Unit Normalizer | FR-003 | MEDIUM | Approved (unchanged) |
| MODULE-001-04 | Duplicate Resolution Coordinator | FR-004 | HIGH | Approved (unchanged) |
| MODULE-001-05 | Category Rules & Eligibility Validator | FR-005, FR-006, FR-007 | HIGH | Approved (unchanged) |
| MODULE-001-06 | ISBN Normalization & Validation | FR-008 | MEDIUM | Approved (unchanged) |
| MODULE-001-07 | Missing-ISBN Search Gate | FR-009 | MEDIUM | Approved (receives enriched item with directive contract) |
| **MODULE-001-08** | **Deterministic Directive Parser** | **FR-023, FR-001 ext** | **MEDIUM** | **PENDING (CIR-002 / MIA-001)** |
| **MODULE-001-09** | **LLM Fallback Gateway** | **FR-023** | **HIGH** | **PENDING (CIR-002 / MIA-001) — STAGE B** |
| **MODULE-001-10** | **Directive Reconciliation Resolver** | **FR-023** | **HIGH** | **PENDING (CIR-002 / MIA-001) — STAGE C** |

**EPIC-002 Modules (5 total — unchanged)**  
See MDAP_MODULE_REGISTRY section above.

**EPIC-003 Modules (5 total — was 4; +1 via CIR-001, PENDING)**

| Module ID | Name | FRs | Risk | Status |
|-----------|------|-----|------|--------|
| MODULE-003-01 | Query Orchestrator | FR-015 | HIGH | Approved (extended for exclusivity) |
| MODULE-003-02 | Match Classifier | FR-016 | MEDIUM | Approved (unchanged) |
| MODULE-003-03 | Ranking Engine | FR-017 | HIGH | Approved (extended for preferred sellers) |
| MODULE-003-04 | Apostila Routing Guard | FR-021 | MEDIUM | Approved (unchanged) |
| **MODULE-003-05** | **School Exclusivity Resolver** | **FR-022** | **HIGH** | **PENDING (CIR-001)** |

**EPIC-004 Modules (3 total — unchanged)**  
See MDAP_MODULE_REGISTRY section above.

**Total approved modules (baseline)**: 19  
**Total pending modules (amendments CIR-001 + CIR-002, awaiting approval)**: +4 (MODULE-001-08, MODULE-001-09, MODULE-001-10, MODULE-003-05)  
**Total modules (approved baseline + pending amendments)**: 23

### STAGE_A_INDEPENDENCE

**Stage A Advancement (MODULE-001-08 Deterministic Directive Parser):**
- ✓ Can be implemented and integrated immediately after CIR-002/MIA-001 approval
- ✓ No threshold dependencies block Stage A
- ✓ Enables directive contract schema entry into persistence layer
- ✓ Deterministic parser only (no LLM integration)

**Stages B–D Advancement (MODULE-001-09/010 + shadow-mode promotion):**
- ⏸ MODULE-001-09 blocked on THRESHOLD-LLM-01 and THRESHOLD-LLM-03
- ⏸ MODULE-001-10 blocked on THRESHOLD-LLM-02
- ⏸ Stage D blocked on THRESHOLD-LLM-04 and THRESHOLD-LLM-05
- ⏸ OQ-FR023-02 must be resolved before MDAP detailed design for MODULE-001-09/001-10

---

### AMENDED_THRESHOLD_STATUS

The following threshold items are ADDED by FR-023 and are entirely unresolved. They MUST be decided by stakeholders before Stages B–D of FR-023 implementation can begin.

| Threshold ID | Description | Scope | Status |
|-------------|-------------|-------|--------|
| THRESHOLD-LLM-01 | Deterministic directive confidence below which LLM fallback is triggered | FR-023; MODULE-001-08, MODULE-001-09 | [THRESHOLD NEEDED] |
| THRESHOLD-LLM-02 | LLM output confidence floor for auto-acceptance of LLM result | FR-023; MODULE-001-10 | [THRESHOLD NEEDED] |
| THRESHOLD-LLM-03 | Maximum LLM call latency (ms) per item before timeout | FR-023; MODULE-001-09 | [THRESHOLD NEEDED] |
| THRESHOLD-LLM-04 | LLM precision floor required to exit shadow mode and promote to live routing | FR-023; MODULE-001-09 | [THRESHOLD NEEDED] |
| THRESHOLD-LLM-05 | Minimum shadow mode sample size (item count) before shadow-mode exit gate can open | FR-023; MODULE-001-09 | [THRESHOLD NEEDED] |

---

### AMENDED_OPEN_QUESTIONS

| ID | Question | Must Resolve By |
|---|---|---|
| OQ-FR023-01 | Should LLM fallback be disableable per-school configuration? | Before Stage B |
| OQ-FR023-02 | Is LLM rationale string stored in versioned audit trail (MODULE-004-02) or separate LLM call log? | ESCALATED: PRD sign-off before MDAP detailed design. Impact: MODULE-004-02 schema extension and audit-record structure. Coordination required with EPIC-004 team before Stage C. |
| OQ-FR023-03 | Escalation path for requires_human_review=true items unreviewed after N days? | Before Stage C |

---

### AMENDED_CROSS_EPIC_DEPENDENCY

The following new cross-epic dependency is introduced by CIR-002 (in addition to existing CIR-001 dependency):

```
MODULE-001-10 (Directive Reconciliation Resolver — EPIC-001)
    ↓ directive contract (school_exclusive, required_sellers, preferred_sellers,
                          directive_confidence, decision_source, requires_human_review)
MODULE-003-05 (School Exclusivity Resolver — EPIC-003)
```

**Direction**: Forward-blocking (valid; no reverse dependency)  
**Consumes**: Complete directive contract per FR-023 Section 4 schema

---

### AMENDED_HIGH_RISK_FILES (PENDING — TO BE CREATED DURING STAGED IMPLEMENTATION)

The following new files are flagged as high-risk and will be added to `FILE_STRUCTURE_HIGH_RISK_FILES` once implemented:

- `intake_canonicalization/deterministic_directive_parser.py` (MODULE-001-08, Stage A — MEDIUM risk: rule completeness)
- `intake_canonicalization/llm_fallback_gateway.py` (MODULE-001-09, Stage B — HIGH risk: external LLM dependency)
- `intake_canonicalization/directive_reconciliation_resolver.py` (MODULE-001-10, Stage C — HIGH risk: precedence policy correctness)
- `search_ranking/school_exclusivity_resolver.py` (MODULE-003-05, CIR-001 PENDING — HIGH risk: conflict handling)

Implementation note: Human review is required for all four files before code approval.

---

**Amendment Block Status**: PENDING — Do NOT treat amended ID ranges, module counts, or thresholds as canonical until PRD addendum is signed off and CIR-002 / MIA-001 are approved.  
**Last Updated**: March 27, 2026