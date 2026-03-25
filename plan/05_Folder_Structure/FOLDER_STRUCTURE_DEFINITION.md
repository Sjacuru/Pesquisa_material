# Folder and File Structure Definition

**Project:** School Material Price Finder (Brazil MVP)  
**Phase:** Folder/File Structure  
**Date:** March 25, 2026  
**Status:** Generated from approved MDAP and Architecture outputs

---

## 0. Prompt Fit Notes

The supplied folder-structure prompt is usable, with two controlled interpretations applied to remove internal contradictions:

- The rule "Every file maps to exactly one MDAP module" is applied to all module-owned business files and their unit tests.
- Bootstrap, framework, configuration, platform, and integration-test files are treated as explicit support files. The prompt itself permits these through its configuration, entry-point, and integration-test sections.

No example layout from the prompt was treated as authoritative. The structure below is derived from the actual 19-module MDAP output, the Architecture Definition, and the Folder Structure Phase Input.

---

## 1. Naming Convention Declaration

**Architecture Pattern:** Component-aligned modular monolith with Django bootstrap and module-owned Python files.

**Naming Rules:**
- Folders: `snake_case` for all component, platform, config, and test folders.
- Files: `snake_case.py` for Python source files.
- Module-owned source files: one primary source file per MDAP module, named from the approved module responsibility.
- Tests: mirror source structure under `tests/unit/` with `test_*.py` naming.
- Integration tests: `tests/integration/*.py`, named by cross-component flow.

**Rationale:**
- Matches the approved Python 3.12 and Django architecture.
- Keeps component boundaries visible in the repository.
- Avoids unnecessary sublayers at this stage.
- Keeps file discovery deterministic and traceable to module IDs.

---

## 2. Module-to-File Mapping

| Module ID | Module Name | Type | Component | Files Created |
| --- | --- | --- | --- | --- |
| MODULE-001-01 | PDF Ingestion & Field Extraction | Integration | Intake and Canonicalization | `intake_canonicalization/pdf_ingestion_field_extraction.py` |
| MODULE-001-02 | Confidence Gating Router | Domain Logic | Intake and Canonicalization | `intake_canonicalization/confidence_gating_router.py` |
| MODULE-001-03 | Quantity & Unit Normalizer | Domain Logic | Intake and Canonicalization | `intake_canonicalization/quantity_unit_normalizer.py` |
| MODULE-001-04 | Duplicate Resolution Coordinator | Domain Logic | Intake and Canonicalization | `intake_canonicalization/duplicate_resolution_coordinator.py` |
| MODULE-001-05 | Category Rules & Eligibility Validator | Domain Logic | Intake and Canonicalization | `intake_canonicalization/category_rules_eligibility_validator.py` |
| MODULE-001-06 | ISBN Normalization & Validation | Domain Logic | Intake and Canonicalization | `intake_canonicalization/isbn_normalization_validation.py` |
| MODULE-001-07 | Missing-ISBN Search Gate | Domain Logic | Intake and Canonicalization | `intake_canonicalization/missing_isbn_search_gate.py` |
| MODULE-002-01 | Brand Expansion Approval Gate | Domain Logic | Source Governance | `source_governance/brand_expansion_approval_gate.py` |
| MODULE-002-02 | Brand Substitution Audit Logger | Infrastructure | Source Governance | `source_governance/brand_substitution_audit_logger.py` |
| MODULE-002-03 | Website Onboarding & Trust Classifier | Integration | Source Governance | `source_governance/website_onboarding_trust_classifier.py` |
| MODULE-002-04 | Search Eligibility Site Filter | Domain Logic | Source Governance | `source_governance/search_eligibility_site_filter.py` |
| MODULE-002-05 | Site Failure Monitor & Auto-Suspension | Infrastructure | Source Governance | `source_governance/site_failure_monitor_auto_suspension.py` |
| MODULE-003-01 | Query Orchestrator | Integration | Search and Ranking | `search_ranking/query_orchestrator.py` |
| MODULE-003-02 | Match Classifier | Domain Logic | Search and Ranking | `search_ranking/match_classifier.py` |
| MODULE-003-03 | Ranking Engine | Domain Logic | Search and Ranking | `search_ranking/ranking_engine.py` |
| MODULE-003-04 | Apostila Routing Guard | Domain Logic | Search and Ranking | `search_ranking/apostila_routing_guard.py` |
| MODULE-004-01 | User Edit Handler | Interface | User Workflow and Export | `workflow_export/user_edit_handler.py` |
| MODULE-004-02 | Versioned Audit Trail Logger | Infrastructure | User Workflow and Export | `workflow_export/versioned_audit_trail_logger.py` |
| MODULE-004-03 | Export Formatter & Delivery | Integration | User Workflow and Export | `workflow_export/export_formatter_delivery.py` |

**Consolidation shown:** modules are grouped by the four approved architecture components, with one primary business file per approved MDAP module.

---

## 3. Environment and Configuration Files

| File | Purpose | Contains Secrets? | Committed? | Handled By |
| --- | --- | --- | --- | --- |
| `.env.example` | Template for local environment variables | No | Yes | Developers copy to `.env` |
| `.env` | Local secrets and machine-specific values | Yes | No | Local setup only |
| `.gitignore` | Excludes secrets, caches, local artifacts, and generated files | No | Yes | Repository |
| `pyproject.toml` | Python dependencies, tooling, and project metadata | No | Yes | Repository |
| `config/settings.py` | Django application settings and environment loading | No secrets directly | Yes | Code + environment |
| `config/urls.py` | Root URL registration | No | Yes | Code |
| `config/asgi.py` | ASGI entry point | No | Yes | Code |
| `platform/database.py` | Database connection/bootstrap helpers | No secrets directly | Yes | Code + environment |
| `platform/storage.py` | File/object storage abstraction | No secrets directly | Yes | Code + environment |
| `platform/job_runner.py` | Background job execution bootstrap | No | Yes | Code |
| `platform/observability.py` | Logging and metrics bootstrap | No | Yes | Code |

---

## 4. Full Folder and File Tree

```text
project-root/
├── .env.example
├── .gitignore
├── README.md
├── manage.py                              # Application bootstrap entry point
├── pyproject.toml
├── config/
│   ├── asgi.py
│   ├── settings.py
│   └── urls.py
├── web/
│   ├── urls.py                            # HTTP route registration
│   └── views.py                           # Server-rendered delivery layer entry points
├── intake_canonicalization/
│   ├── pdf_ingestion_field_extraction.py
│   ├── confidence_gating_router.py
│   ├── quantity_unit_normalizer.py
│   ├── duplicate_resolution_coordinator.py
│   ├── category_rules_eligibility_validator.py
│   ├── isbn_normalization_validation.py
│   └── missing_isbn_search_gate.py
├── source_governance/
│   ├── brand_expansion_approval_gate.py
│   ├── brand_substitution_audit_logger.py
│   ├── website_onboarding_trust_classifier.py
│   ├── search_eligibility_site_filter.py
│   └── site_failure_monitor_auto_suspension.py
├── search_ranking/
│   ├── query_orchestrator.py
│   ├── match_classifier.py
│   ├── ranking_engine.py
│   └── apostila_routing_guard.py
├── workflow_export/
│   ├── user_edit_handler.py
│   ├── versioned_audit_trail_logger.py
│   └── export_formatter_delivery.py
├── platform/
│   ├── database.py
│   ├── job_runner.py
│   ├── observability.py
│   └── storage.py
└── tests/
    ├── unit/
    │   ├── intake_canonicalization/
    │   │   ├── test_pdf_ingestion_field_extraction.py
    │   │   ├── test_confidence_gating_router.py
    │   │   ├── test_quantity_unit_normalizer.py
    │   │   ├── test_duplicate_resolution_coordinator.py
    │   │   ├── test_category_rules_eligibility_validator.py
    │   │   ├── test_isbn_normalization_validation.py
    │   │   └── test_missing_isbn_search_gate.py
    │   ├── source_governance/
    │   │   ├── test_brand_expansion_approval_gate.py
    │   │   ├── test_brand_substitution_audit_logger.py
    │   │   ├── test_website_onboarding_trust_classifier.py
    │   │   ├── test_search_eligibility_site_filter.py
    │   │   └── test_site_failure_monitor_auto_suspension.py
    │   ├── search_ranking/
    │   │   ├── test_query_orchestrator.py
    │   │   ├── test_match_classifier.py
    │   │   ├── test_ranking_engine.py
    │   │   └── test_apostila_routing_guard.py
    │   └── workflow_export/
    │       ├── test_user_edit_handler.py
    │       ├── test_versioned_audit_trail_logger.py
    │       └── test_export_formatter_delivery.py
    └── integration/
        ├── test_upload_to_search_readiness.py
        ├── test_source_governance_to_query_execution.py
        ├── test_search_results_to_edit_flow.py
        └── test_edit_history_to_export_flow.py
```

---

## 5. File Manifest

| File Path | Module ID | Epic ID | Responsibility | Exports | Flagged |
| --- | --- | --- | --- | --- | --- |
| intake_canonicalization/pdf_ingestion_field_extraction.py | MODULE-001-01 | EPIC-001 | Ingest uploaded PDFs and expose extracted item candidates | extraction service stub | Yes — external input parsing and extraction risk |
| intake_canonicalization/confidence_gating_router.py | MODULE-001-02 | EPIC-001 | Route extracted records by confidence band | confidence routing stub | No |
| intake_canonicalization/quantity_unit_normalizer.py | MODULE-001-03 | EPIC-001 | Normalize quantities and canonical units | normalization service stub | No |
| intake_canonicalization/duplicate_resolution_coordinator.py | MODULE-001-04 | EPIC-001 | Coordinate duplicate detection and merge review routing | duplicate coordination stub | Yes — algorithmic correctness affects canonical list |
| intake_canonicalization/category_rules_eligibility_validator.py | MODULE-001-05 | EPIC-001 | Enforce category required/forbidden rules and search eligibility | category validation stub | Yes — domain-rule correctness gate |
| intake_canonicalization/isbn_normalization_validation.py | MODULE-001-06 | EPIC-001 | Normalize and validate ISBN identifiers | ISBN validation stub | No |
| intake_canonicalization/missing_isbn_search_gate.py | MODULE-001-07 | EPIC-001 | Block search when mandatory ISBN values are missing | search gate stub | No |
| source_governance/brand_expansion_approval_gate.py | MODULE-002-01 | EPIC-002 | Record and expose brand-expansion approval decisions | approval gate stub | No |
| source_governance/brand_substitution_audit_logger.py | MODULE-002-02 | EPIC-002 | Persist substitution reason-code audit events | audit logging stub | No |
| source_governance/website_onboarding_trust_classifier.py | MODULE-002-03 | EPIC-002 | Validate and classify candidate sources by trust state | onboarding/classification stub | Yes — external integration and trust decision |
| source_governance/search_eligibility_site_filter.py | MODULE-002-04 | EPIC-002 | Determine whether a site is eligible for search | eligibility filter stub | No |
| source_governance/site_failure_monitor_auto_suspension.py | MODULE-002-05 | EPIC-002 | Track failure streaks and transition site lifecycle state | suspension monitor stub | Yes — operational control and source availability |
| search_ranking/query_orchestrator.py | MODULE-003-01 | EPIC-003 | Coordinate multi-source search execution and job state | query orchestration stub | Yes — performance-critical external fan-out |
| search_ranking/match_classifier.py | MODULE-003-02 | EPIC-003 | Classify search candidates by confidence and hard constraints | match classification stub | No |
| search_ranking/ranking_engine.py | MODULE-003-03 | EPIC-003 | Rank valid offers by delivered price and trust | ranking stub | Yes — algorithmic correctness and SLA impact |
| search_ranking/apostila_routing_guard.py | MODULE-003-04 | EPIC-003 | Enforce Apostila-specific routing restrictions | routing guard stub | No |
| workflow_export/user_edit_handler.py | MODULE-004-01 | EPIC-004 | Apply user edits inside approved field boundaries | edit workflow stub | No |
| workflow_export/versioned_audit_trail_logger.py | MODULE-004-02 | EPIC-004 | Persist append-only version history for edits and decisions | version/audit stub | Yes — traceability and data durability |
| workflow_export/export_formatter_delivery.py | MODULE-004-03 | EPIC-004 | Generate and deliver PDF/CSV/JSON export artifacts | export delivery stub | Yes — file generation and delivery risk |
| tests/unit/intake_canonicalization/test_pdf_ingestion_field_extraction.py | MODULE-001-01 | EPIC-001 | Validate extraction module acceptance criteria | unit tests | No |
| tests/unit/intake_canonicalization/test_confidence_gating_router.py | MODULE-001-02 | EPIC-001 | Validate confidence routing criteria | unit tests | No |
| tests/unit/intake_canonicalization/test_quantity_unit_normalizer.py | MODULE-001-03 | EPIC-001 | Validate quantity/unit normalization criteria | unit tests | No |
| tests/unit/intake_canonicalization/test_duplicate_resolution_coordinator.py | MODULE-001-04 | EPIC-001 | Validate duplicate coordination criteria | unit tests | No |
| tests/unit/intake_canonicalization/test_category_rules_eligibility_validator.py | MODULE-001-05 | EPIC-001 | Validate category and eligibility rules | unit tests | No |
| tests/unit/intake_canonicalization/test_isbn_normalization_validation.py | MODULE-001-06 | EPIC-001 | Validate ISBN rules | unit tests | No |
| tests/unit/intake_canonicalization/test_missing_isbn_search_gate.py | MODULE-001-07 | EPIC-001 | Validate missing-ISBN search blocking | unit tests | No |
| tests/unit/source_governance/test_brand_expansion_approval_gate.py | MODULE-002-01 | EPIC-002 | Validate brand approval gate behavior | unit tests | No |
| tests/unit/source_governance/test_brand_substitution_audit_logger.py | MODULE-002-02 | EPIC-002 | Validate substitution audit logging behavior | unit tests | No |
| tests/unit/source_governance/test_website_onboarding_trust_classifier.py | MODULE-002-03 | EPIC-002 | Validate site onboarding classification behavior | unit tests | No |
| tests/unit/source_governance/test_search_eligibility_site_filter.py | MODULE-002-04 | EPIC-002 | Validate site eligibility filtering | unit tests | No |
| tests/unit/source_governance/test_site_failure_monitor_auto_suspension.py | MODULE-002-05 | EPIC-002 | Validate site suspension transitions | unit tests | No |
| tests/unit/search_ranking/test_query_orchestrator.py | MODULE-003-01 | EPIC-003 | Validate query orchestration acceptance criteria | unit tests | No |
| tests/unit/search_ranking/test_match_classifier.py | MODULE-003-02 | EPIC-003 | Validate match classification rules | unit tests | No |
| tests/unit/search_ranking/test_ranking_engine.py | MODULE-003-03 | EPIC-003 | Validate ranking behavior | unit tests | No |
| tests/unit/search_ranking/test_apostila_routing_guard.py | MODULE-003-04 | EPIC-003 | Validate Apostila routing restrictions | unit tests | No |
| tests/unit/workflow_export/test_user_edit_handler.py | MODULE-004-01 | EPIC-004 | Validate user edit constraints | unit tests | No |
| tests/unit/workflow_export/test_versioned_audit_trail_logger.py | MODULE-004-02 | EPIC-004 | Validate append-only versioning behavior | unit tests | No |
| tests/unit/workflow_export/test_export_formatter_delivery.py | MODULE-004-03 | EPIC-004 | Validate export format and delivery behavior | unit tests | No |
| web/views.py | support | Architecture | Expose server-rendered HTTP entry points for approved workflows | request handlers | Yes — user-facing workflow entry layer |
| web/urls.py | support | Architecture | Register route patterns to web entry points | route table | No |
| platform/database.py | support | Architecture | Provide database bootstrap and connection boundaries | database bootstrap helpers | Yes — persistence and recovery boundary |
| platform/storage.py | support | Architecture | Provide storage abstraction for uploads and exports | storage abstraction | Yes — artifact durability boundary |
| platform/job_runner.py | support | Architecture | Provide background job bootstrap and execution boundary | job runner bootstrap | Yes — concurrency and retry control |
| platform/observability.py | support | Architecture | Provide structured logging and metrics bootstrap | observability bootstrap | No |
| config/settings.py | config | Architecture | Load application settings from environment and defaults | settings object | Yes — security and runtime configuration |
| config/urls.py | config | Architecture | Bind project-level URL configuration | root URL config | No |
| config/asgi.py | entry point | Architecture | Expose ASGI application entry point | ASGI app | No |
| manage.py | entry point | Architecture | Bootstrap management commands and local server execution | CLI bootstrap | No |
| tests/integration/test_upload_to_search_readiness.py | integration | EPIC-001 + EPIC-003 | Validate upload through search-ready gating flow | integration tests | No |
| tests/integration/test_source_governance_to_query_execution.py | integration | EPIC-002 + EPIC-003 | Validate eligible-source state feeding query execution | integration tests | No |
| tests/integration/test_search_results_to_edit_flow.py | integration | EPIC-003 + EPIC-004 | Validate ranked-result handoff into edit workflow | integration tests | No |
| tests/integration/test_edit_history_to_export_flow.py | integration | EPIC-004 | Validate edit history feeding export delivery | integration tests | No |

---

## 6. Entry Points

### Application Entry Point
- **File:** `manage.py`
- **Role:** bootstrap the Django application for local commands and local server execution
- **Initialization Order:**
  1. Load environment values from `.env` through settings bootstrap
  2. Load application settings from `config/settings.py`
  3. Initialize database boundary through `platform/database.py`
  4. Register routes through `config/urls.py` and `web/urls.py`
  5. Start the local application server or execute management command

### Runtime Gateways
- **File:** `config/asgi.py`
  - Role: ASGI gateway for async-capable server runtime

---

## 7. Files Flagged for Human Review

Before any implementation begins, the following files require human review and sign-off:

| File Path | Module ID | Reason | Required Expertise | Acceptance Criteria to Validate |
| --- | --- | --- | --- | --- |
| intake_canonicalization/pdf_ingestion_field_extraction.py | MODULE-001-01 | Mixed-document parsing and extraction correctness | Document processing / data extraction | Extraction boundaries, rejection paths, and review routing are explicit |
| intake_canonicalization/duplicate_resolution_coordinator.py | MODULE-001-04 | Duplicate logic affects canonical list integrity | Domain lead / data quality | Duplicate merge criteria do not collapse distinct items |
| intake_canonicalization/category_rules_eligibility_validator.py | MODULE-001-05 | Hard constraints gate downstream search | Domain lead | Category required/forbidden rules match PRD matrix |
| source_governance/website_onboarding_trust_classifier.py | MODULE-002-03 | External trust integration and policy classification | Architect / integration reviewer | Sites cannot become eligible without valid trust classification path |
| source_governance/site_failure_monitor_auto_suspension.py | MODULE-002-05 | Operational lifecycle control | Architect / operations reviewer | Failure threshold and state transitions remain explicit and testable |
| search_ranking/query_orchestrator.py | MODULE-003-01 | Performance-critical external fan-out | Architect | Timeout, retry, and partial-failure boundaries are explicit |
| search_ranking/ranking_engine.py | MODULE-003-03 | Ranking correctness affects final outcome | Domain lead / architect | Ranking rules preserve delivered-price-plus-trust ordering |
| workflow_export/versioned_audit_trail_logger.py | MODULE-004-02 | Traceability and append-only audit durability | Audit/compliance reviewer | Version history cannot be silently overwritten |
| workflow_export/export_formatter_delivery.py | MODULE-004-03 | Artifact generation and output safety | Export/integration reviewer | PDF/CSV/JSON boundaries and failure states are explicit |
| web/views.py | support | User-facing delivery surface | Architect / frontend reviewer | User flows expose only approved actions and maintain clear boundaries |
| platform/database.py | support | Persistence boundary and recovery implications | Database reviewer | Connection handling, recovery assumptions, and ownership boundaries are explicit |
| platform/storage.py | support | Upload/export artifact durability | Storage reviewer | Upload and export storage boundaries are explicit and isolated |
| platform/job_runner.py | support | Background execution and retry control | Architect | Job state, retry ownership, and failure isolation are explicit |
| config/settings.py | support | Security-sensitive runtime configuration | Security reviewer | No secrets are hard-coded; local-only defaults remain explicit |

---

## 8. Test Strategy

### Unit Tests
- Every module-owned business file has a matching unit test under `tests/unit/`.
- Unit tests mirror the component folder structure exactly.
- Unit tests validate the binary acceptance criteria defined by MDAP for each module.

### Integration Tests
- Integration tests live under `tests/integration/`.
- They verify cross-component handoffs, not internal implementation details.
- They focus on the critical program path: upload -> canonicalization -> source eligibility -> search -> edit/version -> export.

### Test Boundaries
- No UI snapshot or browser-automation files are created at this phase.
- No external-source live-call tests are created at this phase.
- Test stubs remain structure-only until implementation begins.

---

## 9. File Header Policy

Every module-owned source file and every unit test file must begin with the required project header using Python comments.

```python
# FILE: intake_canonicalization/pdf_ingestion_field_extraction.py
# MODULE: MODULE-001-01 — PDF Ingestion & Field Extraction
# EPIC: EPIC-001 — Data Extraction and Validation
# RESPONSIBILITY: Ingest uploaded PDFs and expose extracted item candidates.
# EXPORTS: Extraction service stub.
# DEPENDS_ON: platform/storage.py, platform/observability.py
# ACCEPTANCE_CRITERIA:
#   - Uploaded PDF inputs are accepted only through the defined intake boundary.
#   - Extracted item candidates are emitted through a deterministic module interface.
# HUMAN_REVIEW: Yes — mixed-document parsing correctness requires expert review.
```

Support files, configuration files, and entry points must use the same header shape, with `MODULE: support` or `MODULE: config` where no single MDAP module owns the file.

---

## 10. Output Verification

- [x] Every module-owned file traces to exactly one MDAP module
- [x] Every module-owned file traces to exactly one Epic
- [x] No file is included only as speculation
- [x] Test files exist for every testable module
- [x] Naming conventions are applied consistently
- [x] Configuration files with secrets are separated from committed files
- [x] Security-critical and high-risk files are flagged for human review
- [x] Entry points are explicitly identified
- [x] Structure matches the approved modular-monolith Architecture Definition
- [x] Structure complexity matches the 19-module MDAP baseline

---

[CONTEXT.MD_UPDATE]
## File Structure Complete

### Architecture Pattern: Component-aligned modular monolith with Django bootstrap

### Components and File Organization:
- Intake and Canonicalization Component: `intake_canonicalization/` -> 7 module-owned source files
- Source Governance Component: `source_governance/` -> 5 module-owned source files
- Search and Ranking Component: `search_ranking/` -> 4 module-owned source files
- User Workflow and Export Component: `workflow_export/` -> 3 module-owned source files
- Delivery Layer: `web/` -> route and view entry files
- Platform Layer: `platform/` -> database, storage, job-runner, and observability support files
- Tests: `tests/unit/` mirrors module source; `tests/integration/` holds cross-component flow tests

### Total Files: 55
- Source files: 25
- Test files: 23
- Configuration/bootstrap files: 7

### Files Flagged for Human Review: 14
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

### Entry Points:
- `manage.py` (main application bootstrap)
- `config/asgi.py` (ASGI gateway)

### Next Phase: Implementation
Developers use this structure to create and implement file stubs.
All flagged files must be signed off before coding proceeds.

[/CONTEXT.MD_UPDATE]

---

[8A_IMPLEMENTATION_READY]

### Structure Complete: Ready for Implementation

Total Modules: 19  
Total Files: 58  
High-Risk Files: 14

### Implementation Sequence:

PHASE 1 — High-Risk and Security-Sensitive Files
1. `config/settings.py`
2. `platform/database.py`
3. `platform/storage.py`
4. `platform/job_runner.py`
5. `intake_canonicalization/pdf_ingestion_field_extraction.py`
6. `intake_canonicalization/duplicate_resolution_coordinator.py`
7. `intake_canonicalization/category_rules_eligibility_validator.py`
8. `source_governance/website_onboarding_trust_classifier.py`
9. `source_governance/site_failure_monitor_auto_suspension.py`
10. `search_ranking/query_orchestrator.py`
11. `search_ranking/ranking_engine.py`
12. `workflow_export/versioned_audit_trail_logger.py`
13. `workflow_export/export_formatter_delivery.py`
14. `web/views.py`

PHASE 2 — Remaining Core Module Files
1. Remaining Intake and Canonicalization module files
2. Remaining Source Governance module files
3. Remaining Search and Ranking module files
4. Remaining User Workflow and Export module files

PHASE 3 — Delivery and Routing Layer Finalization
1. `web/urls.py`
2. `config/urls.py`
3. `manage.py`
4. `config/asgi.py`

PHASE 4 — Test Implementation
1. Implement unit tests for all 19 modules
2. Implement integration tests for the four cross-component flows
3. Validate human-reviewed files against acceptance criteria

### Per-File Implementation Checklist:
- [ ] Read file header (responsibility, exports, dependencies, acceptance criteria)
- [ ] Create stub structure only first
- [ ] Implement acceptance-criteria tests
- [ ] Implement module behavior without crossing file responsibility boundaries
- [ ] Self-review against acceptance criteria
- [ ] Obtain human review for flagged files before finalizing

[/8A_IMPLEMENTATION_READY]
