# System Architecture Definition

**Project:** School Material Price Finder (Brazil MVP)  
**Phase:** Architecture  
**Date:** March 25, 2026  
**Status:** Drafted from approved MDAP handoff and locked architecture decisions

---

## 0. Gate Check and Prompt Fit

### Advancement Gate Status
- EPIC generation complete.
- MDAP complete for EPIC-001 through EPIC-004.
- CONTEXT.md contains the full 19-module registry.
- Architecture decisions already locked in ADR-0001.

### Prompt Compatibility Notes
The provided architecture prompt is broadly compatible with the project state and has been applied with the following controlled interpretations:
- Previously approved architecture decisions are treated as fixed baseline, not re-opened.
- No web research was conducted because the current handoff is sufficient and external patterns must not override PRD/MDAP traceability.
- Sample prompt examples referring to Auth Service, Profile Service, and payment handling are not adopted because they are not traceable to this product scope.
- Security sections that imply multi-user role systems are constrained by ASSUMPTION-001 and the PRD out-of-scope rule on multi-user access control.
- Ambiguities discovered during review are recorded in Section 11 rather than silently resolved.

### Architecture Input Sufficiency
- PRD handoff present in CONTEXT.md.
- MDAP module registry present in CONTEXT.md.
- Cross-Epic dependency summary present in CONTEXT.md.
- Carry-forward assumptions and thresholds present in CONTEXT.md.

Gate Verdict: PASS - sufficient input exists to define Architecture.

---

## 1. Architecture Overview

### System Style
**Chosen style:** Modular monolith.

**Justification:**
- Satisfies the approved decision to keep a single deployable application while preserving internal module boundaries.
- Matches the local-first hosting target and minimizes operational burden.
- Supports FR-001 through FR-021 without introducing distributed-system complexity not required by the PRD.
- Fits NFR-001, NFR-002, NFR-003, and NFR-004 while keeping implementation simple enough for personal use and testing.

### High-Level Component Diagram Description
The system is a single Python application composed of module-owning domain components and supporting infrastructure boundaries:
- A server-rendered web interface handles upload, review, edit, search initiation, site onboarding, source-health visibility, and export/download interactions.
- An Intake and Canonicalization component processes uploaded PDFs into validated, normalized material records.
- A Source Governance component manages source onboarding, trust classification, site eligibility, and automatic suspension state.
- A Search and Ranking component orchestrates source querying, match classification, trust-aware ranking, and Apostila routing.
- A User Workflow and Export component handles user edits, versioned audit history, and final export generation.
- Relational storage persists structured business state.
- File/object storage persists uploaded artifacts and generated exports.
- Background workers execute long-running source query waves and resilience logic outside the synchronous UI request path.

### Considered and Rejected
- **Split services / microservices:** rejected because they increase operational complexity without requirement justification.
- **Full SPA frontend:** rejected because MVP workflows are table/form/review heavy and do not justify client-state complexity.
- **Cache or search index from day one:** rejected because no current requirement forces it and unresolved thresholds must not be guessed.
- **Cloud-first deployment:** rejected because the approved target is local-only first.
- **API-only source strategy:** rejected because FR-015 requires broad source coverage and the approved integration decision allows targeted scraping where APIs do not exist.

---

## 2. Technology Stack

| Layer | Technology | Justification | Alternative | Limitation |
| --- | --- | --- | --- | --- |
| Frontend UI | Django templates + HTMX | Supports server-rendered UI with small interactive components; fits FR-018, FR-020 and the approved frontend decision | Full SPA with React | Less suitable for highly stateful client interactions if the product later grows into a rich multi-user app |
| Application Runtime | Python 3.12 + Django 5 | Aligns with the approved language/runtime and modular-monolith shape; strong fit for PDF processing, validation, and admin-like workflows | FastAPI + Jinja2 | Django is heavier than a minimal API framework |
| Domain Processing | Python service modules inside the Django app | Preserves 19 MDAP modules as internal boundaries while keeping single deployable shape | Separate services | Strong discipline is needed to keep module boundaries clean inside one codebase |
| Relational Data Store | PostgreSQL | Strong fit for structured relationships, audit/versioning, site governance, and search result persistence | SQLite for local-only MVP | PostgreSQL is more setup than SQLite, but safer for concurrency and future migration |
| File/Object Storage | Local filesystem through a storage abstraction | Fits local-first hosting and binary artifact handling for uploads/exports while preserving future S3-compatible migration path | Database BLOB storage | Local files are not ideal for multi-machine access until deployment evolves |
| Background Execution | Database-backed job runner inside the same application boundary | Supports long-running source queries without adding broker/cache infrastructure at day one; aligns with single deployable app | Celery + Redis | Lower throughput ceiling than a dedicated broker-based queue |
| Source Integration | HTTPX for APIs + Playwright/BeautifulSoup for targeted scraping adapters | Matches balanced integration decision and handles both API and non-API retailers | Selenium or Scrapy-only | Browser automation is heavier and can be brittle on dynamic sites |
| PDF Export | WeasyPrint | Supports PDF artifact generation for FR-020 within a server-rendered Python stack | ReportLab | Adds HTML-to-PDF rendering constraints and system dependencies |
| CSV Export | Python csv module | Satisfies FR-020 with minimal complexity | pandas | Less convenience for complex tabular transformations |
| JSON Export | Python json module | Satisfies FR-020 with minimal complexity and clear machine-readable output | orjson | Standard library is simpler for MVP |
| Observability | Python logging with JSON-formatted structured logs | Supports minimal-but-effective observability and local debugging without premature telemetry stack adoption | Full OpenTelemetry stack | Less rich tracing across async workflows |
| Secrets and Config | Environment variables + local .env outside source control | Simplest secure baseline for local-first deployment and external credentials | Hard-coded settings | Manual secret handling discipline is required |

**Trade-off Summary:**
- The stack favors simplicity, local operability, and traceability over elastic scale.
- PostgreSQL is selected even for local-first use to avoid a later migration from SQLite into a more concurrent architecture.
- Background execution remains inside the application boundary to avoid introducing a separate broker until evidence demands it.

---

## 3. Module-to-Component Mapping

| Component | Modules | Responsibility | Rationale |
| --- | --- | --- | --- |
| Intake and Canonicalization Component | MODULE-001-01, MODULE-001-02, MODULE-001-03, MODULE-001-04, MODULE-001-05, MODULE-001-06, MODULE-001-07 | Convert uploaded source documents into validated, normalized, search-ready material records | Consolidates the full pre-search item-preparation pipeline into one cohesive domain boundary |
| Source Governance Component | MODULE-002-01, MODULE-002-02, MODULE-002-03, MODULE-002-04, MODULE-002-05 | Manage source trust, brand-expansion governance, search eligibility, and automatic source suspension | Groups source-facing governance rules and audit-sensitive decisions together |
| Search and Ranking Component | MODULE-003-01, MODULE-003-02, MODULE-003-03, MODULE-003-04 | Query eligible sources, classify matches, rank offers, and route Apostila items correctly | Consolidates performance-sensitive search behavior and post-search decision logic |
| User Workflow and Export Component | MODULE-004-01, MODULE-004-02, MODULE-004-03 | Support user edits, version history, and final export artifact generation | Keeps mutable user workflow and final-delivery concerns together |

---

## 4. Module Consolidation Strategy

CONSOLIDATION LOGIC:

By domain ownership:
- Intake and Canonicalization Component: all EPIC-001 modules.
- Source Governance Component: all EPIC-002 modules.
- Search and Ranking Component: all EPIC-003 modules.
- User Workflow and Export Component: all EPIC-004 modules.

By technical runtime:
- Web interface layer exposes screens and actions for all four domain components.
- Background execution layer runs long-lived external-query and retry workloads, primarily for the Search and Ranking Component and source-health monitoring in the Source Governance Component.
- Persistence layer stores domain state, audit state, and files for all components.

Rationale:
- MDAP already produced cohesive domain module groups by Epic.
- No approved requirement currently justifies breaking those groups into independently deployable services.
- The resulting architecture preserves traceability from Epic and module boundaries while still making deployment and folder structure practical.
- This architecture keeps logical ownership by Epic/domain and technical ownership by runtime layer without forcing premature service extraction.

---

## 5. System Components (Detail)

### 5.1 Intake and Canonicalization Component
- **Modules:** MODULE-001-01 through MODULE-001-07
- **Responsibility:** ingest PDFs, extract fields, classify confidence, normalize units, resolve duplicates, enforce category rules, validate ISBNs, and block search until mandatory identifiers are ready.
- **Interfaces exposed:** upload intake commands, canonical material record retrieval, validation results, review queue inputs, and search-readiness status.
- **Dependencies:** file/object storage for source files; relational data for canonical records; User Workflow component for downstream editable state.
- **Failure mode and recovery:**
  - PDF parsing failure -> mark item set as extraction_failed and keep original upload available for manual retry.
  - Validation conflict -> route item to review queue rather than silently fail.
  - Duplicate merge ambiguity -> hold merge decision pending user review.
- **PRD requirements satisfied:** FR-001 through FR-009, NFR-002, NFR-003.

### 5.2 Source Governance Component
- **Modules:** MODULE-002-01 through MODULE-002-05
- **Responsibility:** manage source onboarding, trust decisions, site eligibility, brand-expansion approval, substitution logging, and auto-suspension state.
- **Interfaces exposed:** site onboarding commands, source status queries, brand-expansion decisions, audit events, and eligibility filters consumed by search.
- **Dependencies:** relational data for source state; Search and Ranking component for source utilization signals; observability/logging for failure counters.
- **Failure mode and recovery:**
  - Trust lookup failure -> site remains pending review, not automatically searchable.
  - Brand-approval path unavailable -> same-brand-only fallback is retained.
  - Auto-suspension threshold reached -> site moves to suspended state and search excludes it until recovery validation passes.
- **PRD requirements satisfied:** FR-010 through FR-014, NFR-002, NFR-004, NFR-005.

### 5.3 Search and Ranking Component
- **Modules:** MODULE-003-01 through MODULE-003-04
- **Responsibility:** execute source queries, classify candidate matches, rank valid offers by delivered cost plus trust, and enforce Apostila routing rules.
- **Interfaces exposed:** search initiation, per-source query jobs, ranked results retrieval, exception states, and Apostila-routing decisions.
- **Dependencies:** Intake and Canonicalization component for search-ready items; Source Governance component for eligible sources and source health; background execution layer for long-running fan-out workloads.
- **Failure mode and recovery:**
  - Single-source timeout -> retry with backoff; if still failing, isolate source via circuit-breaker state and continue with remaining sources.
  - Broad search degradation -> return partial results with explicit source-coverage status rather than blocking all output.
  - Match-classification uncertainty -> downgrade candidate to review-required rather than treating it as valid.
- **PRD requirements satisfied:** FR-015, FR-016, FR-017, FR-021, NFR-001, NFR-004.

### 5.4 User Workflow and Export Component
- **Modules:** MODULE-004-01 through MODULE-004-03
- **Responsibility:** allow pre-search edits, preserve version history, and generate downloadable result artifacts.
- **Interfaces exposed:** item edit actions, version history retrieval, export requests, export status, and download endpoints.
- **Dependencies:** Search and Ranking component for ranked results; Intake and Canonicalization component for editable-field and category contracts; file/object storage for generated exports.
- **Failure mode and recovery:**
  - Invalid edit request -> reject change and keep previous version intact.
  - Audit-write failure -> block export/finalization path until version history is durably recorded.
  - Export generation failure -> keep export request state as failed, expose retry action, and preserve prior successful export if available.
- **PRD requirements satisfied:** FR-018, FR-019, FR-020, NFR-002, NFR-003, NFR-005.

---

## 6. Data Architecture

### Core Entities
- UploadBatch: source upload event and file metadata.
- ExtractedItem: raw extracted rows before canonicalization.
- CanonicalItem: normalized item record used for search and export.
- ReviewDecision: manual resolution for confidence, duplicate, and validation conflicts.
- SourceSite: onboarded retailer/marketplace record with trust and lifecycle status.
- SourceHealthEvent: failures, suspensions, recoveries, and validation checkpoints.
- BrandApprovalDecision: user decision to permit brand expansion when same-brand coverage is insufficient.
- SearchJob: long-running search execution unit for one list or one query wave.
- SearchResultCandidate: raw or normalized offer candidate returned by a source adapter.
- RankedOffer: final ranked output per item.
- VersionEvent: append-only history of user edits and merge decisions.
- ExportArtifact: generated PDF/CSV/JSON artifact and associated metadata.

### Relationships
- One UploadBatch contains many ExtractedItems.
- ExtractedItems resolve into CanonicalItems through normalization and review decisions.
- CanonicalItems produce many SearchResultCandidates and one or more RankedOffers.
- SourceSite owns many SourceHealthEvents and participates in many SearchResultCandidates.
- CanonicalItems may have many VersionEvents and BrandApprovalDecisions.
- ExportArtifact references a stable snapshot of CanonicalItems, RankedOffers, and VersionEvents.

### Data Ownership per Component
- Intake and Canonicalization owns UploadBatch, ExtractedItem, CanonicalItem, and ReviewDecision.
- Source Governance owns SourceSite, SourceHealthEvent, and BrandApprovalDecision policy state.
- Search and Ranking owns SearchJob, SearchResultCandidate, and RankedOffer.
- User Workflow and Export owns VersionEvent and ExportArtifact.

### Data Flow
1. User uploads PDF into file/object storage and UploadBatch metadata into relational storage.
2. Intake and Canonicalization extracts and normalizes item data into CanonicalItems.
3. Search and Ranking reads CanonicalItems and Source Governance eligibility state, then runs search jobs.
4. RankedOffers are stored and exposed to user-edit workflows.
5. User Workflow records edits and version history, then produces ExportArtifacts.

### Data at Rest, In Transit, Retention
- **At rest:** relational data in PostgreSQL; binary uploads/exports in local file storage abstraction.
- **In transit:** all browser-to-app and app-to-external-source traffic must use HTTPS when running beyond localhost; local-only development may use loopback-only HTTP.
- **Retention:** THRESHOLD-003 remains unresolved, so retention windows are architecture-configurable and not hard-coded.

### PRD Requirements Satisfied
- FR-001 through FR-021 indirectly via data support boundaries.
- NFR-002 and NFR-003 through append-only audit/version storage.
- NFR-004 through source-health records.
- NFR-005 through configurable diagnostic data retention and filterable logs.

---

## 7. Security Architecture

### Trust Boundaries
- Boundary 1: Browser <-> local web application.
- Boundary 2: application <-> local relational database.
- Boundary 3: application <-> local file/object storage.
- Boundary 4: application <-> external retailer APIs or websites.
- Boundary 5: local secrets/configuration <-> runtime process.

### Authentication Mechanism + Justification
**Baseline decision:** local-first trusted-workstation mode with optional operator sign-in, escalating to mandatory session authentication before any non-local deployment.

**Justification:**
- Multi-user access control is explicitly out of scope.
- The approved hosting target is local-only first.
- The architecture must not invent a full multi-role auth system without PRD amendment.

### Authorization Model + Justification
**Baseline decision:** capability-gated maintenance views inside the same application boundary, not a full multi-user RBAC model.

**Justification:**
- Aligns with the earlier decision to keep operator screens in the same app.
- Avoids violating ASSUMPTION-001 by treating maintenance capabilities as deployment/operator controls rather than new product personas.
- If the product is later exposed beyond a trusted local workstation, this must be revisited with explicit stakeholder approval.

### Secrets Management
- Store external credentials and environment-specific secrets outside source control.
- Use environment variables and local secret files excluded from the repository.
- Never store source credentials or tokens in the relational database unless encrypted and justified.

### Known Attack Surfaces + Mitigations
- **Malicious PDF upload:** validate file type, size, page count, and processing sandbox boundaries.
- **Scraping adapter abuse or site-blocking risk:** rate limit outbound traffic, identify adapters per source, and respect source-specific throttle behavior.
- **Credential leakage:** keep adapter credentials outside source control and minimize credential scope.
- **Local data exposure on shared machine:** recommend OS-level account protection and encrypted disk if sensitive data is retained.
- **Tampering with audit history:** make version and audit records append-only at the application level and protect deletion paths.

### SECURITY FLAGS (Human Review Required)
- [ ] Authentication flows
- [ ] Authorization/permission management
- [x] Payment processing (not applicable; out of scope)
- [ ] Secret management
- [ ] External API credentials

Note: unchecked items above require human review before any non-local deployment or real retailer credential onboarding.

---

## 8. Integration Points

### External Systems
- Retailer APIs where available.
- Retailer websites where targeted scraping is required.
- Reputation/trust lookup sources used during onboarding.

### Expected SLA and Behavior
- External sources are treated as variable-latency dependencies and must not be assumed reliable.
- Internal NFR-001 drives bounded per-source execution and graceful degradation rather than waiting indefinitely.

### Fallback Behavior if Unavailable
- API unavailable -> use scraper adapter only if approved for that source.
- Scraper adapter unavailable -> mark source unavailable for the current wave, log the event, and continue with other eligible sources.
- Trust source unavailable during onboarding -> keep site pending review, not auto-approved.

### Data Contracts and Versioning
- Each source adapter returns a normalized candidate-offer contract before ranking.
- Adapter output versions must be explicit so parser changes do not silently change ranking semantics.
- Export adapter contract remains format-agnostic until ASSUMPTION-003 is fully resolved.

---

## 9. Scalability and Performance

### Bottlenecks Identified
- PDF extraction and normalization for mixed-quality inputs.
- Fan-out source query waves for FR-015.
- Match classification and ranking over many candidate offers.
- Export generation on large result sets.

### Scaling Approach
- **Initial approach:** vertical scaling on the local machine plus bounded concurrency in background jobs.
- **Future-ready path:** if THRESHOLD-005 is later resolved upward, separate worker processes can be increased before any service split is considered.

### Caching Strategy
- No cache or search index initially.
- Revisit only if measured bottlenecks against THRESHOLD-002 and THRESHOLD-005 justify it.

### Load Handling Approach
- Use asynchronous/background job execution for multi-source searches.
- Bound per-source concurrency and timeout budgets.
- Continue with partial coverage when some sources fail instead of failing the entire list.
- Persist intermediate search state so the UI can poll for progress rather than waiting synchronously.

---

## 10. Deployment Architecture

### Environment Strategy
- **Environment 1:** local development/testing on the user's own computer.
- **Environment 2:** future non-local deployment only after auth, secret handling, and retention policies are hardened.

### CI/CD Pipeline Overview
- Minimal repository validation pipeline: linting, unit tests, contract tests for adapters, and migration checks.
- No automatic production deployment is required for the local-only MVP baseline.

### Infrastructure as Code
**Decision:** No, not initially.

**Justification:**
- The approved target is local-only first.
- Constraint Section 2 favors the simplest architecture that satisfies requirements.
- IaC becomes justified only when a repeatable remote environment is introduced.

### Rollback Strategy
- Restore the previous tagged application version.
- Restore the latest compatible relational backup.
- Keep uploads and generated exports in versioned or timestamped storage paths where feasible.
- On failed adapter rollout, disable the affected source adapter without rolling back the entire application if domain state remains compatible.

---

## 11. Architectural Risks and Open Decisions

### Confirmed Carry-Forward Items
- ASSUMPTION-003: Export schema and formatting details unresolved.
- ASSUMPTION-004: Brand substitution reason-code taxonomy unresolved.
- THRESHOLD-002: Performance reference environment unresolved.
- THRESHOLD-003: Audit-log retention duration unresolved.
- THRESHOLD-005: Peak concurrent users without degradation unresolved.

### Architecture-Level Ambiguities Found During Prompt Review
1. **Privileged screens versus single generalized persona**
   - Earlier architecture discussion accepted operator/admin-like maintenance screens in the same app.
   - PRD and CONTEXT.md explicitly constrain the product to a single generalized persona and keep multi-user access control out of scope.
   - Architecture response: treat maintenance screens as local deployment capabilities rather than a formal multi-role product model unless PRD is amended.

### Other Risks
- Scraping adapters may become brittle as retailer sites change.
- Source latency variation can pressure the 10-minute SLA if concurrency budgets are poorly tuned.
- Audit and version storage can grow quickly once retention is formalized.
- Local filesystem storage is sufficient for the approved hosting target but will need replacement or abstraction hardening for remote multi-machine deployment.

### Conditions for Revisiting This Architecture
- THRESHOLD-005 is resolved at a materially higher concurrency target.
- The product moves beyond local-only hosting.
- PRD is amended to add real multi-user access control.
- Search throughput measurements show the database-backed worker model is insufficient.
- The product scope is revised to support a different export set than PDF/CSV/JSON.

---

## Output Verification

- [x] Every component maps to MDAP modules
- [x] Every technology choice cites PRD/NFR requirement
- [x] Failure modes defined for all major components
- [x] Trust boundaries explicitly identified
- [x] Module consolidation strategy documented
- [x] Security-critical components flagged for human review
- [x] No code or pseudocode included
- [x] Simplest architecture satisfying requirements chosen
- [x] Unresolved assumptions acknowledged
- [x] Research skipped intentionally because current handoff is sufficient

---

[CONTEXT.MD_UPDATE]
## Architecture Definition Complete

### System Style: Modular Monolith

### Components:
- Intake and Canonicalization Component: MODULE-001-01 through MODULE-001-07, pre-search extraction and validation pipeline
- Source Governance Component: MODULE-002-01 through MODULE-002-05, source trust and brand-governance controls
- Search and Ranking Component: MODULE-003-01 through MODULE-003-04, eligible-source querying and result ranking
- User Workflow and Export Component: MODULE-004-01 through MODULE-004-03, user edits, version history, and export delivery

### Technology Stack:
- Frontend: Django templates + HTMX
- Backend: Python 3.12 + Django 5 modular monolith
- Database: PostgreSQL
- File/Object Storage: local filesystem behind storage abstraction
- Background Execution: database-backed job runner inside application boundary
- Integration: HTTPX + Playwright/BeautifulSoup adapters

### Module Consolidation:
- Intake and Canonicalization Component: MODULE-001-01 through MODULE-001-07
- Source Governance Component: MODULE-002-01 through MODULE-002-05
- Search and Ranking Component: MODULE-003-01 through MODULE-003-04
- User Workflow and Export Component: MODULE-004-01 through MODULE-004-03

### High-Risk Components (Human Review):
- Search and Ranking Component: performance-critical fan-out and partial-failure handling under NFR-001
- Source Governance Component: external trust and source-lifecycle controls
- Security baseline for non-local deployment: authentication, secret handling, and outbound credentials

### Architectural Risks:
- Operator/maintenance capability must not drift into unapproved multi-user role design
- Unresolved thresholds still limit hard performance and retention commitments

### Unresolved Assumptions Affecting Architecture:
- ASSUMPTION-003
- ASSUMPTION-004
- THRESHOLD-002
- THRESHOLD-003
- THRESHOLD-005

### Research Conducted (if any):
- What was researched: none
- Key findings: none
- Impact on architecture: none

[/CONTEXT.MD_UPDATE]

---

[7A_PHASE_TRANSITION_NOTE]

### Components Ready for File Structuring:
1. Intake and Canonicalization Component: MODULE-001-01 through MODULE-001-07, pre-search extraction and validation, Risk Level High
2. Source Governance Component: MODULE-002-01 through MODULE-002-05, source trust and lifecycle governance, Risk Level High
3. Search and Ranking Component: MODULE-003-01 through MODULE-003-04, source querying and ranking, Risk Level High
4. User Workflow and Export Component: MODULE-004-01 through MODULE-004-03, edit/version/export flows, Risk Level Medium

### Module-to-File Mapping Guidance:
Each component should map to a top-level folder inside the future application structure:
- /intake_canonicalization: MODULE-001-01 through MODULE-001-07
- /source_governance: MODULE-002-01 through MODULE-002-05
- /search_ranking: MODULE-003-01 through MODULE-003-04
- /workflow_export: MODULE-004-01 through MODULE-004-03
- /web: server-rendered pages, forms, and interaction endpoints for all components
- /platform: shared infrastructure such as storage, job execution, configuration, and observability

### High-Risk Components (Implementation Review Before Coding):
- Search and Ranking Component: timeout budgets, retries, and partial-failure behavior affect NFR-001
- Source Governance Component: trust classification and suspension logic affect FR-012 through FR-014
- Export path: verify PDF rendering dependencies and artifact-template decisions before implementation

### Dependency Graph:
- Source Governance Component depends on platform persistence and outbound integration boundaries
- Search and Ranking Component depends on Intake and Canonicalization Component
- Search and Ranking Component depends on Source Governance Component
- User Workflow and Export Component depends on Search and Ranking Component
- User Workflow and Export Component depends on Intake and Canonicalization Component

[/7A_PHASE_TRANSITION_NOTE]
