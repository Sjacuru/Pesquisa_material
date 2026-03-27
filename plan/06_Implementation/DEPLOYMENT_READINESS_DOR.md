# Definition of Ready: Deployment Readiness Checklist
## School Material Price Finder (Brazil MVP) - Implementation Playbook

**Status**: Implementation Planning (NOT a functional EPIC)  
**Date**: March 27, 2026  
**Scope**: Operationalization of EPIC-001-004 (no new functional requirements)  
**Duration**: 3-week sprint execution

### Governance Classification
- **Type**: Implementation Readiness Checklist / Definition of Ready (DOR)
- **Applies To**: EPIC-001, EPIC-002, EPIC-003, EPIC-004 (completion and production hardening)
- **Does NOT introduce**: New FRs, new NFRs, new modules, new personas
- **References**: PRD (FR-001-FR-026), EPIC Output (4 EPICs), CONTEXT.md (approved scope)

### Key Distinction
This document is **NOT a new Epic**. It is a playbook for implementing and hardening existing functional scope.
It belongs in the Implementation layer, not the EPIC decomposition layer.

---

## 2. Objective
Convert the current functional MVP into a deployable, resilient service with:
- non-blocking batch execution,
- test-gated release confidence,
- adapter resilience and observability,
- secure environment configuration,
- repeatable CI/CD deployment.

## 3. Execution Stories (Operational Readiness, Not Functional FRs)

The following stories are **operational/implementation concerns**, not new user-facing requirements.
They operationalize existing EPIC-001-004 scope for production readiness.

### Story Mapping Note
- US-005-01, US-005-03, US-005-04: Operator/SRE concerns (not PERSONA-001 value)
- US-005-02: User-facing operational quality (supports FR-018/FR-020 usability)

Stories are grouped by sprint phase (Week 1-3), not by canonical EPIC structure.

---

### US-005-01: Release Confidence Through Tests [Week 1]
**Classification**: Quality assurance story (operationalizes EPIC-001-004 correctness)  
**Supports**: All FRs (ensures no regression on deployment)  
**Owner**: Backend/QA team

As an operator, I want regression-proof flows so releases do not break core user journeys.

Acceptance Criteria:
- [ ] Integration tests cover upload, automatic search, item edit, re-search, and CSV export (EPIC-001->004 happy path).
- [ ] Fail-path tests exist for timeout, empty results, and validation errors (EPIC-001->004 edge cases).
- [ ] CI fails on test regression (no deployment without coverage).

---

### US-005-02: Non-Blocking Batch Execution [Week 2]
**Classification**: User-facing operational quality  
**Supports**: FR-018 (item edits), FR-020 (export) - improves responsiveness  
**Owner**: Backend team + `platform/job_runner.py`

As a user, I want uploads to return quickly even for large lists.

Acceptance Criteria:
- [ ] Upload endpoint returns within [THRESHOLD NEEDED: seconds] even for 100-item batches.
- [ ] Search workload executes in background queue/job runner (non-blocking).
- [ ] User can inspect progress via status endpoint (enables FR-020 polling UX).

---

### US-005-03: Resilient Source Governance [Week 2]
**Classification**: Operational resilience story (operationalizes FR-014, FR-026)  
**Supports**: FR-026 (Search Adapters), FR-014 (Site Suspension)  
**Owner**: Backend team + source governance module owners (MODULE-002-05)

As an operator, I want one failing source to degrade gracefully without stopping the system.

Acceptance Criteria:
- [ ] Adapter timeout/retry policy is standardized (inherited from MODULE-002-05 implementation).
- [ ] Failure bursts trigger temporary source suspension (MODULE-002-05 auto-suspension behavior).
- [ ] SearchExecution captures source-level outcomes for diagnostics (enables observability of FR-026 query results).

---

### US-005-04: Safe Deployment and Rollback [Week 3]
**Classification**: Operational/release management story  
**Supports**: NFR-002 (audit logs), all FRs (ensures repeatable delivery)  
**Owner**: DevOps/delivery team

As a delivery team, I want predictable deployment and rapid recovery.

Acceptance Criteria:
- [ ] Staging and production environment configs are explicit and versioned (enables GC-1 traceability).
- [ ] CI/CD deploy sequence includes smoke tests (validates EPIC-001-004 integration on production).
- [ ] Rollback process is tested and documented (recovery time <15 minutes).

---

## 4. Dependencies and Scope Boundaries

### Upstream Dependencies (What This Playbook Operationalizes)
- EPIC-001 Completion: Extraction, canonicalization, validation gating (FR-001-FR-009)
- EPIC-002 Completion: Source trust and brand governance (FR-010-FR-014)
- EPIC-003 Completion: Search, ranking, Apostila routing (FR-015-FR-017, FR-021)
- EPIC-004 Completion: User edits, versioning, export (FR-018-FR-020)

### Adapter Inventory (Maps to FR-026: Search Adapters)
Current production adapters (map to EPIC-003 MODULE-003-01 Query Orchestrator):
- `amazon_br` (Amazon Brazil)
- `magalu_br` (Magalu Brazil)
- `ev_br` (Estante Virtual Brazil)
- `kalunga_br` (Kalunga Brazil)
- `ml_br` (Mercado Livre Brazil)

**Governance Note**: These adapters are implementation artifacts of FR-026 (Search Adapters).
See Section 7 (Adapter Inventory Mapping) for detailed traceability.

### Async Work Foundation Requirement
- `platform/job_runner.py` contract must be stable (background job execution)
- **Status**: Confirmed as architectural boundary in Folder/File Structure phase

### No New External Dependencies
- This playbook does NOT introduce new external systems, languages, or infrastructure beyond approved tech stack
- No new personas or user types are approved
- No new FRs or NFRs are introduced

## 5. Risks and Controls
- Risk: selector drift in scraping sources.
  - Control: fixture parser tests + source failure monitoring + suspension.
- Risk: request timeout under synchronous batch execution.
  - Control: async job orchestration and status polling.
- Risk: hidden migration/environment drift in deployment.
  - Control: CI migration checks and clean-environment staging bootstrap.

## 6. Governance Traceability and No New Scope

### Canonical ID Preservation
- **Functional Requirements**: FR-001 through FR-026 (unchanged; no renumbering)
- **Non-Functional Requirements**: NFR-001 through NFR-007 (unchanged; no new NFRs)
- **Epics**: EPIC-001 through EPIC-004 (canonical; no additional functional epic is active)
- **Personas**: PERSONA-001 (School List User - canonical; no new personas approved)

### What This Playbook Does NOT Do
- Introduce new functional requirements (FRs)
- Introduce new non-functional requirements (NFRs)
- Introduce new modules (all modules belong to EPIC-001-004)
- Introduce new personas or user roles
- Extend the scope ceiling (Brazil MVP, school material price comparison)
- Violate governance rules GC-1 through GC-9

### Governance Compliance (This Playbook)
| Rule | Status | Evidence |
|---|---|---|
| GC-1 (Traceability) | PASS | Each week 1-3 ticket maps to existing FR/NFR/EPIC/module |
| GC-2 (Binary ACs) | PARTIAL | Execution tasks are checklist-style; not FR-level ACs |
| GC-5 (No Invented Thresholds) | PASS | No invented thresholds; [THRESHOLD NEEDED] noted where applicable |
| GC-8 (ID Immutability) | PASS | No FR/NFR IDs renumbered or modified |
| Scope Ceiling Respect | PASS | No features outside school material comparison scope |

### Key Distinction: This Is NOT a Functional EPIC
**Functional EPICs** (EPIC-001-004): Decompose user-facing FRs into modules -> MDAP design -> implementation.  
**This Playbook**: Operationalizes existing EPIC-001-004 for production (testing, async, hardening, deployment).

Playbooks belong in **Implementation layer**, not EPIC decomposition layer.

## 7. Adapter Inventory Mapping to FR-026

### Governance Anchor
All adapters below implement **FR-026 [MUST]: Search adapters for configured retail sources**.

Adapters are query execution points for MODULE-003-01 (Query Orchestrator).

### Current Production Adapters (Week 3 Scope)

| Adapter | Target Site | Status | FR-026 Context | Test Fixture Path |
|---|---|---|---|---|
| `amazon_br` | Amazon.com.br | Implemented | Query executor for e-commerce books/supplies | `tests/fixtures/adapters/amazon_br_samples/` |
| `magalu_br` | Magalu.com.br | Implemented | Query executor for department store supplies | `tests/fixtures/adapters/magalu_br_samples/` |
| `ev_br` | EstanteVirtual.com.br | Implemented | Query executor for used books | `tests/fixtures/adapters/estante_virtual_samples/` |
| `kalunga_br` | Kalunga.com.br | Implemented | Query executor for school supplies retailer | `tests/fixtures/adapters/kalunga_br_samples/` |
| `ml_br` | MercadoLivre.com.br | Implemented | Query executor for marketplace (books + supplies) | `tests/fixtures/adapters/mercadolivre_samples/` |

### Adapter Resilience Governance
All adapters implement FR-026 runtime resilience expectations:
- Timeout: [THRESHOLD NEEDED: seconds per source]
- Retry: 3 attempts with exponential backoff (operational target)
- Health tracking: MODULE-002-05 (Site Failure Monitor and Auto-Suspension)
- Suspension trigger: [THRESHOLD NEEDED: consecutive failures in time window]

### Week 2-3 Adapter Testing
Each adapter shall have:
- Fixture-based parser tests (HTML/JSON snapshots; no network calls)
- Retry logic tests (simulate timeout, verify backoff)
- Integration test with full search flow (upload -> query -> offer persistence)

See week 2 ticket: Adapter failure policy and week 3 ticket: smoke tests and rollback drill.

## 8. Sprint Execution Plan (Week 1-3)

Week 1:
- DEP-001, DEP-002, DEP-003

Week 2:
- DEP-004, DEP-005, DEP-006, DEP-007

Week 3:
- DEP-008, DEP-009, DEP-010

## 9. References and Deprecation Notice

### Deprecation Notice
The original deprecated EPIC amendment file (in `plan/archive/deprecated_governance/`) is archived and superseded by this document.
It is archived for historical reference and not treated as a canonical EPIC.

### Related Documents (Canonical)
- `PRD.md`: Functional requirements (FR-001-FR-026), acceptance criteria
- `plan/07_CONTEXT_ARCHIT/CONTEXT.md`: traveling context, threshold inventory, assumptions
- `plan/02_EPIC/EPIC_OUTPUT.md`: canonical functional EPICs (EPIC-001-EPIC-004)
- `plan/06_Implementation/PROMPT-7_DEPLOYMENT_EXECUTION_BACKLOG.md`: detailed backlog and ticket breakdown

### Document Relationships
PRD (FRs)  
-> EPIC Output (decomposition)  
-> MDAP Stage 1-5 (module design)  
-> Architecture Definition (system design)  
-> Implementation prompts  
-> This DOR (readiness checklist)  
-> PROMPT-7 (execution backlog)  
-> Production deployment

## 10. Sign-Off Gate

This Definition of Ready is approved for execution once:
- [ ] Product Owner: Confirms no new functional scope, week 1-3 timeline acceptable
- [ ] Architecture Lead: Confirms `job_runner.py` contract is stable; no new infrastructure needed
- [ ] Backend Lead: Confirms team bandwidth for week 1-3 concurrent execution
- [ ] DevOps Lead: Confirms CI/CD pipeline can enforce gates by week 3

**Sign-Off Fields**:
Product Owner: _________________ Date: _________  
Architecture Lead: _________________ Date: _________  
Backend Lead: _________________ Date: _________  
DevOps Lead: _________________ Date: _________