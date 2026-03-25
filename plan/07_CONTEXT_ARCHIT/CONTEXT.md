# CONTEXT.md
## Pipeline Traveling Context — Controlled Handoff Document

**Written by:** PRD Phase  
**Updated by:** MDAP Phase  
**Read by:** EPIC · MDAP · Architecture · Folder/File Structure  
**Date:** March 25, 2026  
**Project:** School Material Price Finder (Brazil MVP)

---

## TRAVELING_CONTEXT

### Scope Ceiling (Canonical)
```
School Material Price Finder is a Brazil-focused tool for parents, school 
administrators, and budget-conscious shoppers who need to buy complete school 
lists from mixed document formats while controlling total spend.
```

### Canonical ID Ranges (Locked — No Renumbering Downstream)
- **Functional Requirements:** FR-001 through FR-021 (21 total)
- **Non-Functional Requirements:** NFR-001 through NFR-005 (5 total)
- **User Personas:** PERSONA-001 (1 total — see assumptions)
- **Success Metrics:** SM-001 through SM-011+ (post-launch validation)
- **Open Questions:** OQ-001 through OQ-012+ (unresolved items)

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
**Current:** MDAP (complete)  
**Next:** System Architecture  
**Full sequence:** PRD → EPIC → MDAP → System Architecture → Folder/File Structure

---

## PRD_HANDOFF_BLOCK

This block is the structured data payload for EPIC consumption. Extract and reference during Epic decomposition.

### FR_IN_SCOPE (21 Functional Requirements)

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

### NFR_MUST_SHOULD (5 Non-Functional Requirements)

| ID | Priority | Requirement |
|---|---|---|
| NFR-001 | MUST | Complete list processing within 10 minutes (SLA) |
| NFR-002 | SHOULD | Keep structured decision audit logs |
| NFR-003 | SHOULD | Preserve versioned change history records |
| NFR-004 | SHOULD | Track website health and suspensions |
| NFR-005 | COULD | Expose configurable log-retention and query filters for diagnostics |

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

- [ ] Verify no new FRs introduced. FR count remains 21. ✓
- [ ] Verify no new out-of-scope items added without justification. ✓
- [ ] Verify CONTEXT.md matches PRD Phase 1 output exactly. ✓

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
- Ensure all FR IDs (FR-001 to FR-021) remain locked and immutable

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

## Governance References

- **Constraint Rules:** GC-1 through GC-9 enforced in PRD Phase (see PRD Blueprint v2.0)
- **ID Permanence Rule:** GC-8 — FR/NFR IDs are immutable across all pipeline phases
- **Citation Format:** All requirements source to PRD sections or [ASSUMPTION] tags
- **Sign-Off Protocol:** THRESHOLD_ASSUMPTION_RESOLUTION_GATE above is the formal blocker

---

**CONTEXT.md Status:** ✅ UPDATED THROUGH MDAP  
**Last Updated:** March 25, 2026  
**Next Handoff:** MDAP → System Architecture

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