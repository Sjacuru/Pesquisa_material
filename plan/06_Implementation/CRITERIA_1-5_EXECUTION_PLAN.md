# Deployment Readiness Execution Plan: Criteria 1-5
## School Material Price Finder (Brazil MVP) — Week 1-2 Roadmap

**Date**: March 27, 2026
**Scope**: Map the 5 deployment readiness criteria to PROMPT-8 (Week 1) and PROMPT-9 (Week 2)
**Reference**: `plan/06_Implementation/DEPLOYMENT_READINESS_DOR.md`

---

## Executive Summary

| Criterion | Focus | Week | Stories | Status |
|---|---|---|---|---|
| #1 **Staging Validation** | Critical flow integration (upload→search→export) | 1-2 | T7-001, T7-005 | ⚠️ Week 1 foundation; Week 2 integration |
| #2 **Async Queue** | Non-blocking batch execution | 2 | T7-007 | 🔴 Week 2 (job_runner.py implementation) |
| #3 **Adapter Resilience** | Graceful failure, auto-suspension | 1-2 | T7-003, T7-006 | ⚠️ Week 1 tests; Week 2 failure injection |
| #4 **CSV Export** | User-validated export artifact | 1-2 | Export formatter build + validation | ⚠️ Week 1 foundation; Week 2 full impl |
| #5 **CI Pipeline Gates** | Test + migration enforcement | 1 | T7-004 | ✅ Week 1 (gate definition) |

---

## Week 1 Foundation (PROMPT-8)

### Stories Executed
- **T7-001**: Ingestion unit coverage (edge cases for canonicalization)
- **T7-002**: Search/ranking determinism
- **T7-003**: Adapter contract tests (all 5 adapters, 3 fixtures each)
- **T7-004**: CI quality gate definition (pytest blocking merge)

### Criteria Progress After Week 1
| Criterion | Criterion Description | Week 1 Completion |
|---|---|---|
| #1 Staging Validation | Critical flows pass | 🟡 **40%** — Upload + extract tested; search orchestration not yet tested; export not yet tested |
| #2 Async Queue | Non-blocking search | 🔴 **0%** — job_runner.py not yet touched |
| #3 Adapter Resilience | Graceful failure | 🟡 **50%** — Adapters tested; failure injection not yet tested; suspension not yet validated |
| #4 CSV Export | CSV validation | 🟡 **30%** — Export formatter scaffolds exist; CSV writing not yet implemented |
| #5 CI Gates | Enforce tests + migrations | 🟢 **100%** — Gate criteria defined, pytest blocking merge configured |

---

## Week 2 Integration & Resilience (PROMPT-9)

### Stories to Execute
- **T7-005**: End-to-End Workflow Integration (upload → search → edit → export)
- **T7-006**: Failure Injection and Fallbacks (timeout/error handling, source suspension)
- **T7-007**: Concurrency and Job Runner Reliability (async dispatch, idempotent retries, SQLite concurrency)

### Criteria Progress After Week 2
| Criterion | Criterion Description | Week 2 Completion | Implementation Artifacts |
|---|---|---|---|
| #1 Staging Validation | Critical flows pass in staging | 🟢 **100%** | Integration test suite validates upload→search→export; staging env config (`.env.staging`); staging DB seed |
| #2 Async Queue | Non-blocking queue under expected volume | 🟢 **100%** | `platform/job_runner.py` fully implemented (async dispatch, status polling, retry logic); load test validates ~100 items/batch throughput |
| #3 Adapter Resilience | Adapter failure doesn't halt batch | 🟢 **100%** | Failure injection tests; auto-suspension validated; partial-result handling confirmed |
| #4 CSV Export | CSV validated by business users | 🟢 **100%** | `workflow_export/export_formatter_delivery.py` CSV writing complete; export template with headers + rows; sample export validated |
| #5 CI Gates | Enforce tests + migrations | 🟢 **100%** | All unit + integration tests passing; migration check gating enforced |

---

## Detailed Mapping: Criteria → Stories → Code

### Criterion #1: Staging Validation (Upload → Search → Export)

**Week 1 Work (PROMPT-8 T7-001)**:
- ✅ Unit tests for ingestion canonicalization (edge cases)
- Unit tests for search/ranking determinism
- Adapter contract tests

**Week 2 Work (PROMPT-9 T7-005)**:
- 🔨 End-to-end integration test: `tests/integration/test_upload_to_search_readiness.py` extended to include:
  - Upload PDF/DOCX → Stage A ingestion → Canonical items created
  - Trigger search on high-confidence items
  - Simulate source results
  - Persist offers to DB
  - Load offers in edit workflow
  - User edits item (price, quantity)
  - Version history logged
  - Export as CSV with version metadata
- 🔨 Staging environment config:
  - `.env.staging` template with DJANGO_DEBUG=false, DATABASE_URL pointing to staging SQLite
  - Staging DB seed script (populate SourceSite trust states, categories)
- 🔨 Validation: Integration test passes end-to-end; export CSV is valid (headers + rows match expected schema)

**Code Files to Create/Modify**:
- `tests/integration/test_upload_to_search_export_flow.py` (new)
- `.env.staging` (new)
- `scripts/seed_staging_db.py` (new)

---

### Criterion #2: Async Queue (Non-Blocking Batch Execution)

**Week 1 Work (PROMPT-8)**:
- ❌ None (scaffolds only)

**Week 2 Work (PROMPT-9 T7-007)**:
- 🔨 Implement `platform/job_runner.py`:
  - Job queue (in-memory or SQLite-backed; decision: **SQLite JobQueue table**)
  - Async dispatch: POST upload → create batch + enqueue search jobs → return immediately
  - Background worker (synchronous loop, runs in separate thread or subprocess)
  - Job status polling endpoint: GET `/jobs/<job_id>/status` → `{"status": "running|complete|failed", "progress": {...}}`
  - Retry logic: 3 attempts with exponential backoff (2s, 4s, 8s)
  - Timeout: [THRESHOLD NEEDED — target: 10 seconds per adapter × 5 adapters = 50s max per item search]

- 🔨 Integrate job runner into upload workflow:
  - `web/views.py` upload_workflow: after Stage A → create SearchJob records (one per high-confidence item) → enqueue in job runner
  - Update model `SearchJob` to add `job_runner_id` (foreign key to job queue entry)

- 🔨 Add concurrency + idempotency tests:
  - Test concurrent batch execution (2+ batches simultaneously)
  - Test retry on timeout (adapter returns timeout error → job retries 3x)
  - Test idempotent search (same item searched 2x → only 1 set of offers persisted)

- 🔨 Performance validation:
  - Load test: upload 100-item batch → measure time to return to user (target: <2 seconds)
  - Measure background worker throughput (target: 10-20 items/minute for 5-adapter search)

**Code Files to Create/Modify**:
- `platform/job_runner.py` (implement fully from scaffold)
- `persistence/models.py` (add JobQueueEntry model)
- `persistence/repositories.py` (add JobQueueRepository)
- `web/views.py` (update upload_workflow to use async job dispatch)
- `tests/integration/test_job_runner_reliability.py` (new)

---

### Criterion #3: Adapter Resilience (Graceful Failure)

**Week 1 Work (PROMPT-8 T7-003)**:
- ✅ Adapter contract tests (valid, missing price, empty response fixtures)
- Adapter timeout handling confirmed (timeout_seconds parameter exists)

**Week 2 Work (PROMPT-9 T7-006)**:
- 🔨 Failure injection tests:
  - Simulate timeout (httpx.TimeoutException) → confirm adapter returns `status="timeout"`, not raises
  - Simulate HTTP error (500 gateway error) → confirm adapter returns `status="error"`, not raises
  - Simulate rate limit (429) → confirm adapter backs off gracefully
  - Simulate bot detection (captcha page) → confirm adapter returns empty results, not crashes

- 🔨 Source suspension validation:
  - Trigger 5 consecutive failures on one source
  - Confirm source transitions to `is_suspended=True` in SourceSite model
  - Confirm suspended source is filtered from next search execution
  - Populate revalidation event → confirm source unhooks suspension

- 🔨 Partial result handling:
  - Execute search on batch with 1 adapter failing (status="timeout") and 4 succeeding
  - Confirm batch search completes (doesn't halt on single adapter failure)
  - Confirm results aggregated from 4 successful adapters
  - Confirm SearchJob status=`"partial"` (not "failed")

**Code Files to Create/Modify**:
- `tests/unit/source_governance/test_site_failure_monitor_auto_suspension.py` (extend with re-validation)
- `tests/integration/test_failure_injection_and_fallbacks.py` (new)
- `tests/integration/test_source_governance_to_query_execution.py` (extend partial-result scenario)

---

### Criterion #4: CSV Export (Validated by Business Users)

**Week 1 Work (PROMPT-8)**:
- ❌ None (export formatter scaffold only)

**Week 2 Work (PROMPT-9 T7-005)**:
- 🔨 Implement CSV generation in `workflow_export/export_formatter_delivery.py`:
  - Accept curated set (edited items with latest values)
  - Generate CSV with headers: `Item | Category | Quantity | Unit | Price | Source | URL | Version | Last Edited`
  - Each row: material record with latest field values + version metadata
  - Validation: CSV is valid (no unescaped quotes, proper encoding UTF-8)

- 🔨 PDF generation (optional, scope TBD):
  - Use WeasyPrint to render HTML template → PDF
  - Include branding, summary (total price, item count)

- 🔨 User validation:
  - Generate sample CSV with 5 items (mix of prices, sources, versions)
  - Manual review: columns correct, data matches in-app display
  - Confirm file download works (Content-Disposition header set)

- 🔨 Integration test:
  - Create items → edit some → export as CSV → parse CSV → assert row count matches items
  - Verify version metadata in CSV matches VersionEvent records

**Code Files to Create/Modify**:
- `workflow_export/export_formatter_delivery.py` (implement CSV + PDF generation)
- `workflow_export/csv_formatter.py` (new — CSV template helper)
- `workflow_export/pdf_formatter.py` (new — PDF template helper, optional)
- `tests/integration/test_edit_history_to_export_flow.py` (extend with CSV validation)
- `web/templates/export_template.html` (new — PDF rendering template, optional)

---

### Criterion #5: CI Pipeline Gates (Enforce Tests & Migrations)

**Week 1 Work (PROMPT-8 T7-004)**:
- ✅ Gate conditions defined:
  - `pytest tests/unit/` must pass
  - `pytest tests/integration/` must pass
  - `python manage.py migrate --check` must pass
  - Import tests pass (all modules importable)
- ✅ `pytest.ini` configured with testpaths
- ✅ Merge gate enforcement agreed upon

**Week 2 Work (PROMPT-9)**:
- ✅ All new tests from T7-005, T7-006, T7-007 added to test suite
- ✅ All existing tests still passing (no regression)
- ✅ Gate enforcement automatic (CI/CD pipeline): any PR that doesn't pass all tests is blocked from merge

**Code Files (No Changes Needed)**:
- Gate already defined; just ensure new tests added in Week 2 comply with gate

---

## Execution Sequence (Week 2)

```
Monday (Day 1-2):
  ├─ Implement T7-007: job_runner.py (platform/job_runner.py)
  │  └─ Create JobQueueEntry model + repository
  │  └─ Implement async dispatch + background worker
  │  └─ Add job status polling endpoint
  │  └─ Write concurrency + idempotency tests
  │
  ├─ Implement T7-005 Part A: E2E test framework
  │  └─ Create test_upload_to_search_export_flow.py
  │  └─ Mock search results, populate offers
  │  └─ Stage integration test (upload → search → edit → export)
  │
  └─ Seed staging environment config
     └─ Create .env.staging
     └─ Create seed_staging_db.py script

Tuesday-Wednesday (Day 3-4):
  ├─ Implement T7-006: Failure injection + adapter resilience
  │  └─ Write timeout/error/rate-limit fixtures
  │  └─ Extend site_failure_monitor tests (re-validation)
  │  └─ Write test_failure_injection_and_fallbacks.py
  │  └─ Validate partial-result handling
  │
  ├─ Implement T7-005 Part B: CSV + PDF export
  │  └─ Implement CSV generation (export_formatter_delivery.py)
  │  └─ Add PDF generation (WeasyPrint, optional)
  │  └─ Extend export test with CSV parsing + validation
  │
  └─ Run end-to-end integration tests
     └─ Full upload → search → edit → export flow
     └─ Validate CSV output, version metadata

Thursday-Friday (Day 5):
  ├─ Run full test suite (unit + integration)
  │  └─ pytest tests/unit/ —> must pass
  │  └─ pytest tests/integration/ —> must pass
  │  └─ python manage.py migrate --check —> must pass
  │
  ├─ Run load test (job runner throughput validation)
  │  └─ Simulate 100-item batch upload
  │  └─ Measure upload response time (<2s)
  │  └─ Measure background worker latency (target: 10-20 items/min)
  │
  └─ Manual validation
     └─ User downloads sample CSV, validates format
     └─ Spot-check prices, categories, version data in CSV
     └─ Confirm file download works in browser

Friday Afternoon (Sign-Off):
  └─ Week 2 sign-off gate:
     ├─ All tests passing (green CI)
     ├─ All 5 criteria at 100% (or documented reason for deferral)
     ├─ Performance baselines captured
     └─ Ready for Week 3 (staging readiness + security + rollback)
```

---

## Definition of Completeness (Week 2)

A criterion is **100% complete** when:

| Criterion | Sign-Off Condition |
|---|---|
| #1 Staging Validation | E2E integration test passes; `.env.staging` + seed script work; export CSV valid and matches app display |
| #2 Async Queue | job_runner.py fully implemented; upload returns <2s; search executes in background; job status polling works; concurrent batches handled; retry logic validated |
| #3 Adapter Resilience | Failure injection tests pass; suspension transitions validated; partial-result handling confirmed; no adapter failure stops entire batch |
| #4 CSV Export | CSV generated with correct headers + data; version metadata included; file download works; user validates sample CSV manually |
| #5 CI Gates | All unit + integration tests pass; migrate --check passes; CI blocks non-compliant PRs |

---

## References

- `plan/06_Implementation/PROMPT-7_DEPLOYMENT_EXECUTION_BACKLOG.md` — parent backlog (T7-001 through T7-010)
- `plan/06_Implementation/PROMPT-8_WEEK1_TEST_HARDENING_EXECUTION.md` — Week 1 execution guide
- `plan/06_Implementation/WEEK1_EXECUTION_CHECKLIST.md` — Week 1 binary checklist
- `plan/06_Implementation/PROMPT-9_WEEK2_INTEGRATION_RESILIENCE_EXECUTION.md` — Week 2 detailed guide (to be created)
- `plan/06_Implementation/WEEK2_EXECUTION_CHECKLIST.md` — Week 2 binary checklist (to be created)
