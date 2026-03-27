# DEPRECATED ARCHIVE

This document is archived for historical traceability only.
Canonical deployment readiness governance is maintained in:

- `plan/06_Implementation/DEPLOYMENT_READINESS_DOR.md`
- `plan/06_Implementation/PROMPT-7_DEPLOYMENT_EXECUTION_BACKLOG.md`

Do not treat this file as an active EPIC artifact.

# EPIC AMENDMENT 005 — Deployment Readiness and Production Hardening

Date: March 27, 2026  
Status: Approved for execution  
Scope: Production-readiness completion of School Material Price Finder (Brazil MVP)

## 1. Objective
Convert the current functional MVP into a deployable, resilient service with:
- non-blocking batch execution,
- test-gated release confidence,
- adapter resilience and observability,
- secure environment configuration,
- repeatable CI/CD deployment.

## 2. New Epic Definition

### EPIC-005: Deployment Readiness
Derived from: FR-018..FR-021 operationalization, NFR-001..NFR-005 runtime enforcement

Strategic Goal:
Enable safe production rollout by enforcing release quality gates, operational controls, and rollback capability.

### Epic Definition of Done
- [ ] End-to-end upload->search->edit->export flow covered by integration tests.
- [ ] Adapter parsing behavior covered by fixture-based tests with no external network dependency.
- [ ] Batch search runs asynchronously via job runner (no long blocking request).
- [ ] Search progress/status is queryable from web layer.
- [ ] Per-source failures are isolated; repeated failure triggers source suspension policy.
- [ ] Structured logs and key runtime metrics are emitted (latency, failure rate, empty rate per source).
- [ ] Security baseline configured for production (DEBUG off, secrets via env, secure cookies, allowed hosts).
- [ ] CI/CD pipeline enforces lint/test/migration checks prior to deployment.
- [ ] Staging smoke tests and rollback drill documented and executed successfully.

## 3. User Stories and Acceptance

### US-005-01: Release Confidence Through Tests
As an operator, I want regression-proof flows so releases do not break core user journeys.

Acceptance Criteria:
- [ ] Integration tests cover upload, automatic search, item edit, re-search, and CSV export.
- [ ] Fail-path tests exist for timeout, empty results, and validation errors.
- [ ] CI fails on test regression.

### US-005-02: Non-Blocking Batch Execution
As a user, I want uploads to return quickly even for large lists.

Acceptance Criteria:
- [ ] Upload endpoint returns before full batch search completion.
- [ ] Search workload executes in background queue/job runner.
- [ ] User can inspect progress until completion.

### US-005-03: Resilient Source Governance
As an operator, I want one failing source to degrade gracefully without stopping the system.

Acceptance Criteria:
- [ ] Adapter timeout/retry policy is standardized.
- [ ] Failure bursts trigger temporary source suspension.
- [ ] SearchExecution captures source-level outcomes for diagnostics.

### US-005-04: Safe Deployment and Rollback
As a delivery team, I want predictable deployment and rapid recovery.

Acceptance Criteria:
- [ ] Staging and production environment configs are explicit and versioned.
- [ ] CI/CD deploy sequence includes smoke tests.
- [ ] Rollback process is tested and documented.

## 4. Dependency Chain
- Depends on EPIC-001..EPIC-004 completion in current branch.
- Requires adapters currently implemented: ml_br, ev_br, kalunga_br, amazon_br, magalu_br.
- Async work depends on `platform/job_runner.py` contract stabilization.

## 5. Risks and Controls
- Risk: selector drift in scraping sources.
  - Control: fixture parser tests + source failure monitoring + suspension.
- Risk: request timeout under synchronous batch execution.
  - Control: async job orchestration and status polling.
- Risk: hidden migration/environment drift in deployment.
  - Control: CI migration checks and clean-environment staging bootstrap.
