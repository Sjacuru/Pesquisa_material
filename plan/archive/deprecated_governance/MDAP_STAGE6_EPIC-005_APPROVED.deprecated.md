# DEPRECATED ARCHIVE

This document is archived for historical traceability only.
Canonical deployment readiness governance is maintained in:

- `plan/06_Implementation/DEPLOYMENT_READINESS_DOR.md`
- `plan/06_Implementation/PROMPT-7_DEPLOYMENT_EXECUTION_BACKLOG.md`

Do not treat this file as an active MDAP artifact.

# MDAP STAGE 6 — EPIC-005 APPROVED

Date: March 27, 2026  
Epic: EPIC-005 Deployment Readiness  
Status: Approved for implementation handoff

## Module Decomposition

### MODULE-005-01: Web Flow Integration Test Harness
Responsibility:
- Provide deterministic integration coverage of the user-critical path.

Interfaces:
- Input: Django TestClient requests to web routes.
- Output: Asserted HTTP status, persisted model state, rendered route transitions.

Dependencies:
- web/views.py, web/urls.py, persistence/models.py

Acceptance Contract:
- Tests assert upload->search->edit->export path and key error paths.

---

### MODULE-005-02: Adapter Fixture Parsing Validation
Responsibility:
- Validate parser stability of all source adapters offline.

Interfaces:
- Input: static fixture payloads (HTML/JSON) per source.
- Output: normalized OfferResult assertions.

Dependencies:
- source_adapters/*.py

Acceptance Contract:
- Each adapter has at least one positive and one negative parsing fixture test.

---

### MODULE-005-03: Async Batch Search Orchestration
Responsibility:
- Move search execution off the request-response path.

Interfaces:
- Input: upload completion event + batch id.
- Output: queued jobs, item-level execution status updates.

Dependencies:
- platform/job_runner.py, search_ranking/search_executor.py, persistence/models.py

Acceptance Contract:
- Upload request returns before long-running search; status progresses asynchronously.

---

### MODULE-005-04: Progress Status API/Delivery Contract
Responsibility:
- Expose progress state for UI polling and completion handling.

Interfaces:
- Input: batch_id / item_id.
- Output: aggregate counts and per-item status from SearchJob/WorkflowState.

Dependencies:
- web/views.py, persistence/repositories.py

Acceptance Contract:
- Clients can query progress until completed/failed without DB introspection.

---

### MODULE-005-05: Source Failure Governance Automation
Responsibility:
- Isolate per-source failures and auto-suspend unhealthy sources.

Interfaces:
- Input: SearchExecution failure stream.
- Output: source eligibility/trust transitions with audit record.

Dependencies:
- source_governance/site_failure_monitor_auto_suspension.py, persistence/models.py

Acceptance Contract:
- Repeated source failures trigger suspension; healthy sources continue processing.

---

### MODULE-005-06: Observability and Runtime Metrics
Responsibility:
- Emit operational logs and metrics for source health and pipeline reliability.

Interfaces:
- Input: search lifecycle events.
- Output: structured logs + metric counters/timers.

Dependencies:
- platform/observability.py, search_ranking/search_executor.py

Acceptance Contract:
- Operators can inspect per-source latency, error rates, and empty-result rates.

---

### MODULE-005-07: Deployment Pipeline and Rollback Controls
Responsibility:
- Enforce CI/CD gates and rollback preparedness.

Interfaces:
- Input: PR merges / release trigger.
- Output: gated deployment artifacts, smoke-test verdict, rollback path.

Dependencies:
- CI config (repository), manage.py migrations, environment settings

Acceptance Contract:
- Production deploy only occurs after all gates pass; rollback tested in staging.

## Traceability Map
- US-005-01 -> MODULE-005-01, MODULE-005-02
- US-005-02 -> MODULE-005-03, MODULE-005-04
- US-005-03 -> MODULE-005-05, MODULE-005-06
- US-005-04 -> MODULE-005-07

## Sequencing Constraint
Execution order:
1. MODULE-005-01, MODULE-005-02
2. MODULE-005-03, MODULE-005-04
3. MODULE-005-05, MODULE-005-06
4. MODULE-005-07
