# Week 2 Execution Checklist
## School Material Price Finder — Deployment Readiness Sprint

**Date**: March 27, 2026
**Sprint Week**: Week 2 of 3
**Parent Backlog**: `plan/06_Implementation/PROMPT-7_DEPLOYMENT_EXECUTION_BACKLOG.md`
**Execution Guide**: `plan/06_Implementation/PROMPT-9_WEEK2_INTEGRATION_RESILIENCE_EXECUTION.md`
**DOR**: `plan/06_Implementation/DEPLOYMENT_READINESS_DOR.md`

### Gate Rule
No item may be marked complete unless all associated tests pass (pytest exit 0) with zero failures or errors.

---

## T7-005: End-to-End Workflow Integration

**FR Mapping**: FR-018, FR-020, all EPIC-001-004
**Test Directory**: `tests/integration/`
**Criteria Progress**: Staging Validation (#1), CSV Export (#4)

### Database Seeding
- [ ] `persistence/models.py` has SourceSite.objects.create() calls ready for 5 adapters
- [ ] `scripts/seed_staging_db.py` created and runs without error
- [ ] Running seed script populates SourceSite table with exactly 5 sources (amazon_br, magalu_br, ev_br, kalunga_br, ml_br)
- [ ] Each source has `trust_status="allowed"` and `is_search_eligible=true`

### Environment Configuration
- [ ] `.env.staging` created with vars: DJANGO_DEBUG, DJANGO_SECRET_KEY, ALLOWED_HOSTS, DATABASE_URL
- [ ] `.env.staging` DATABASE_URL points to `var/staging.sqlite3` (not dev.sqlite3)
- [ ] `.env.staging` loaded by Django settings (test: `echo $DATABASE_URL` in shell confirms value)

### CSV Export Generation
- [ ] `workflow_export/csv_formatter.py` module created with `format_as_csv(records, version_context)` function
- [ ] CSV headers present: Item | Category | Quantity | Unit | Price | Source | URL | Version | Last Edited By | Notes
- [ ] CSV rows generate correctly:
  - [ ] Item name matches `latestValues["name"]`
  - [ ] Price formatted as "R$ X.XX" (Brazilian format, not plain decimal)
  - [ ] Version number from version_context["byMaterial"][material_id]["latestVersion"]
  - [ ] Last Edited By from version_meta["entries"][-1]["actor_id"]
  - [ ] Empty prices rendered as "N/A" (not blank, not "None")
  - [ ] Row ordering alphabetical by item name

### CSV Delimiter & Encoding
- [ ] CSV uses comma (,) as delimiter, not semicolon
- [ ] Line terminator is CRLF (\r\n), not LF
- [ ] Encoding is UTF-8 (supports Brazilian characters: ã, é, ç, etc.)

### Export Formatter Integration
- [ ] `workflow_export/export_formatter_delivery.py` calls `format_as_csv()` when format="csv"
- [ ] Export delivery returns dict: `{"deliveryResult": {"status": "success", "artifact": "<csv_content>"}}`
- [ ] Artifact can be parsed by `csv.DictReader()` without error

### Integration Test Suite
- [ ] `tests/integration/test_upload_to_search_export_flow.py` created (new file)
- [ ] Test case: `test_upload_to_export_flow_happy_path()` covers full flow:
  - [ ] Upload PDF/DOCX → create UploadBatch
  - [ ] Stage A ingestion → extract items → CanonicalItem records created
  - [ ] Trigger search → mock adapter results → Offer records created
  - [ ] User edits item (name, price, quantity)
  - [ ] VersionEvent recorded (field_name, old_value, new_value, actor_id)
  - [ ] Export as CSV
  - [ ] CSV parsed, row count matches items, column values match edited data
- [ ] Test case: `test_upload_to_export_with_multiple_sources()` verifies:
  - [ ] Multiple offers from 5 adapters aggregated correctly
  - [ ] CSV shows best price offer's Source + URL
  - [ ] All offers queryable via model (Offer.objects.filter(...))
- [ ] All tests in `test_upload_to_search_export_flow.py` pass (`pytest tests/integration/test_upload_to_search_export_flow.py -v` → exit 0)

### Manual Validation
- [ ] Sample upload via web form (upload 3-item file)
- [ ] System processes upload, returns status
- [ ] Search triggers and completes
- [ ] User downloads CSV export
- [ ] CSV opens in Excel/Sheets without corruption
- [ ] Columns visible: Item, Category, Quantity, Unit, Price, Source, URL, Version, Last Edited By, Notes
- [ ] Data in CSV matches what's shown in app (prices, item names, categories)

### Execution Sign-Off — T7-005
- [ ] All happy-path integration tests pass (exit 0)
- [ ] CSV format validated (headers, rows, encoding, delimiter)
- [ ] Manual CSV download + visual inspection passed
- [ ] `.env.staging` + seed script working

---

## T7-007: Concurrency and Job Runner Reliability

**FR Mapping**: FR-026, FR-018, FR-020
**File**: `platform/job_runner.py`
**Criteria Progress**: Async Queue (#2)

### Data Model — JobQueueEntry
- [ ] `persistence/models.py` has JobQueueEntry model:
  - [ ] Fields: job_id (unique), job_type, status, canonical_item (FK), upload_batch (FK), attempt_count, max_retries, next_retry_at, payload, result, error_message, created_at, started_at, completed_at
  - [ ] Status choices: PENDING, RUNNING, COMPLETED, FAILED, RETRYING
  - [ ] Ordering: by created_at
  - [ ] Indexes: (status, created_at), (job_id)

### Data Model — JobExecutionLog
- [ ] `persistence/models.py` has JobExecutionLog model:
  - [ ] Fields: job (FK), attempt_number, status, duration_ms, error_message, created_at
  - [ ] Each job execution creates one log entry

### Database Migration
- [ ] `python manage.py makemigrations` creates migration for JobQueueEntry + JobExecutionLog
- [ ] `python manage.py migrate` applies migration without error
- [ ] Tables `persistence_jobqueueentry` + `persistence_jobexecutionlog` exist in SQLite

### Job Runner Implementation
- [ ] `platform/job_runner.py` implements `JobRunner` class:
  - [ ] `__init__(max_workers, poll_interval_seconds)` initializes runner
  - [ ] `submit_search_job(canonical_item_id, context)` → creates JobQueueEntry, returns job_id (UUID)
  - [ ] `get_job_status(job_id)` → returns dict with job_id, status, progress (attempt count), result, error
  - [ ] `start_background_worker()` → starts daemon thread running background worker loop
  - [ ] `_worker_loop()` → continuously polls for pending/retrying jobs
  - [ ] `_process_pending_jobs()` → executes up to max_workers pending jobs
  - [ ] `_process_retrying_jobs()` → executes retrying jobs that are due (next_retry_at <= now)
  - [ ] `_execute_job(job)` → orchestrates search, persists offers, updates job status

### Retry Logic
- [ ] Retry attempts: **3 maximum** per job
- [ ] Retry condition: if job fails AND attempt_count < max_retries, set status=RETRYING
- [ ] Backoff timing:
  - [ ] Attempt 1 fails → backoff 2 seconds (2^1)
  - [ ] Attempt 2 fails → backoff 4 seconds (2^2)
  - [ ] Attempt 3 fails → backoff 8 seconds (2^3)
  - [ ] Attempt 4 would fail → no more retries, status=FAILED
- [ ] `next_retry_at` set to `now + timedelta(seconds=backoff_seconds)`

### Job Execution
- [ ] `_execute_job()` does the following for each job:
  - [ ] Fetch canonical_item, category, query_text
  - [ ] Get eligible SourceSite records (is_search_eligible=true, categories match)
  - [ ] Call `orchestrate_query()` with eligible sources
  - [ ] For each offer in results, create `Offer` record in DB
  - [ ] Set job.status=COMPLETED, save result dict
  - [ ] Create JobExecutionLog entry with status="success", duration_ms, no error_message
- [ ] On exception during execution:
  - [ ] Set job.error_message = str(exception)
  - [ ] If retries remain: job.status=RETRYING, set next_retry_at
  - [ ] If no retries: job.status=FAILED, set completed_at
  - [ ] Create JobExecutionLog entry with status="error", duration_ms, error_message

### SQLite Concurrency Configuration
- [ ] `config/settings.py` DATABASES["default"]:
  - [ ] CONNECTION OPTIONS: `{"timeout": 10, "check_same_thread": False}`
  - [ ] WAL mode enabled via `@receiver(connection_created)` signal
  - [ ] CONN_MAX_AGE = 0 (disable connection pooling)
- [ ] WAL mode confirmed: run `sqlite3 var/dev.sqlite3 "PRAGMA journal_mode;"` → returns "wal"

### Web View Integration
- [ ] `web/views.py` upload_workflow modified:
  - [ ] After Stage A processing, get search_ready items
  - [ ] For each item, call `runner.submit_search_job(item.id)`
  - [ ] Collect job_ids
  - [ ] Start background worker (`runner.start_background_worker()`)
  - [ ] Return response immediately (don't wait for search to complete)
  - [ ] Upload response includes job_ids for polling

### Concurrency Tests
- [ ] `tests/integration/test_job_runner_reliability.py` created (new file)
- [ ] Test: `test_concurrent_job_execution()` — Execute 5 jobs simultaneously:
  - [ ] Create batch with 5 items
  - [ ] Start runner with max_workers=3
  - [ ] Submit all 5 jobs (non-blocking)
  - [ ] Wait for all jobs to complete (poll status every 0.5s, timeout 30s)
  - [ ] Assert all 5 jobs have status="completed"
  - [ ] Assert no corruption (no partial results, offers persisted correctly)
- [ ] Test: `test_retry_on_timeout()` — Simulate adapter timeout:
  - [ ] Create item
  - [ ] Mock orchestrate_query to raise exception
  - [ ] Submit job
  - [ ] Wait 10 seconds (should attempt 3x with backoff)
  - [ ] Assert job.status="failed" after retries exhausted
  - [ ] Assert job.attempt_count=3
  - [ ] Assert JobExecutionLog has 3 entries (attempts 1, 2, 3)
- [ ] Test: `test_idempotent_search()` — Same item searched twice:
  - [ ] Create item
  - [ ] Submit job twice (rapid succession)
  - [ ] Wait for completion
  - [ ] Assert no duplicate (offer, source, url) pairs in Offer table
  - [ ] Assert total offer count reasonable (not doubled)

### Performance Validation
- [ ] Load test: Upload 100-item batch → measure response time:
  - [ ] Target: **< 2 seconds** to return upload response
  - [ ] Run test 3x, capture times, average
  - [ ] Document baseline in test output
- [ ] Throughput test: Background worker processing:
  - [ ] 100 items in DB, 5 adapters per search, mock adapter response
  - [ ] Measure items completed per minute
  - [ ] Target: **10-20 items/minute** (allowing for mock delays)
  - [ ] Document baseline

### Execution Sign-Off — T7-007
- [ ] JobQueueEntry + JobExecutionLog models migrated successfully
- [ ] JobRunner fully implemented with all methods
- [ ] SQLite WAL configured + verified
- [ ] Web view integration: upload returns immediately with job_ids
- [ ] All concurrency tests pass (exit 0):
  - [ ] Concurrent execution passes (5 jobs, no corruption)
  - [ ] Retry logic passes (3 attempts, exponential backoff)
  - [ ] Idempotency passes (no duplicates)
- [ ] Performance baselines captured:
  - [ ] Upload response time: ____ seconds (target < 2s)
  - [ ] Worker throughput: ____ items/minute (target 10-20)

---

## T7-006: Failure Injection and Fallbacks

**FR Mapping**: FR-026, FR-021
**Test Directory**: `tests/integration/`, `tests/unit/source_governance/`
**Criteria Progress**: Adapter Resilience (#3)

### Failure Scenario 1: Adapter Timeout

- [ ] Test: `test_adapter_timeout_does_not_stop_batch()`
  - [ ] Mock Amazon adapter to raise `httpx.TimeoutException`
  - [ ] Execute search on item via job_runner or orchestrate_query
  - [ ] Assert SearchJob.status in ["partial", "complete"] (not "failed")
  - [ ] Assert SearchJob.timeout_count=1
  - [ ] Assert offers from other 4 adapters persisted (count >= 4)
  - [ ] Test passes without raising exception

### Failure Scenario 2: HTTP Error (5xx)

- [ ] Test: `test_adapter_http_error_does_not_stop_batch()`
  - [ ] Mock Magalu adapter to return AdapterResult(status="error", error_message="HTTP 500...")
  - [ ] Execute search
  - [ ] Assert SearchJob.error_count=1
  - [ ] Assert SearchJob.success_count=4 (other adapters)
  - [ ] Assert status in ["partial", "complete"]
  - [ ] Test passes

### Failure Scenario 3: Rate Limiting (429)

- [ ] Test: `test_adapter_rate_limit_retry()`
  - [ ] Mock Kalunga adapter: first call returns 429, second call succeeds
  - [ ] Execute search with retry logic enabled (max_retries=3)
  - [ ] Assert adapter called twice (first failed, second succeeded)
  - [ ] Assert offers from Kalunga persisted (second attempt succeeded)
  - [ ] Test passes

### Failure Scenario 4: Bot Detection (Captcha)

- [ ] Test: `test_adapter_bot_detection()`
  - [ ] Mock httpx.get to return HTML with captcha page
  - [ ] Call Estante Virtual adapter.search()
  - [ ] Assert adapter.result.status="error"
  - [ ] Assert adapter.result.offers=[] (no false results)
  - [ ] Assert no exception raised
  - [ ] Test passes

### Partial Result Handling

- [ ] Test: `test_search_with_one_adapter_failing()` (extends T7-005 flow)
  - [ ] 5-item batch search, mock Amazon to fail
  - [ ] Execute batch search via job_runner
  - [ ] Assert 4 adapters queried successfully
  - [ ] Assert results from 4 adapters persisted
  - [ ] Assert batch SearchJob.status="partial" (not "failed")
  - [ ] Test passes

### Source Suspension — Failure Streak

- [ ] Test: `test_source_suspension_on_failure_streak()` (unit test, source_governance)
  - [ ] Call `update_site_suspension_state()` 5x with retry_outcomes=[False, False, False]
  - [ ] Assert state["failure_streak"] increments from 0→1→2→3→4→5
  - [ ] Assert after 5th call: state["is_suspended"]=True
  - [ ] Test passes

### Source Suspension — Filtering from Search

- [ ] Test: `test_suspended_source_filtered_from_search()`
  - [ ] Create SourceSite(site_id="amazon_br", trust_status="suspended", is_search_eligible=false)
  - [ ] Execute search on item
  - [ ] Assert "amazon_br" NOT in query_result["queried_sources"]
  - [ ] Assert queried_sources == ["magalu_br", "ev_br", "kalunga_br", "ml_br"]
  - [ ] Test passes

### Source Revalidation — Suspension Reset

- [ ] Test: `test_revalidation_resets_suspension()` (unit test, source_governance)
  - [ ] Setup: state["amazon_br"]["is_suspended"]=True, failure_streak=5
  - [ ] Call `update_site_suspension_state()` with revalidation_event=True
  - [ ] Assert state["is_suspended"]=False
  - [ ] Assert state["failure_streak"]=0
  - [ ] Test passes

### Failure Injection Test Suite

- [ ] `tests/integration/test_failure_injection_and_fallbacks.py` created (new file)
- [ ] All 8 test cases above present and passing
- [ ] `pytest tests/integration/test_failure_injection_and_fallbacks.py -v` → exit 0

### Source Governance Test Extensions

- [ ] `tests/unit/source_governance/test_site_failure_monitor_auto_suspension.py` extended with:
  - [ ] `test_source_suspension_on_failure_streak()` added
  - [ ] `test_revalidation_resets_suspension()` added
  - [ ] `pytest tests/unit/source_governance/test_site_failure_monitor_auto_suspension.py -v` → exit 0

### No Adapter Failures Propagate

- [ ] Assertion across all failure tests: **No test calls raise or propagate exceptions**
  - [ ] Adapters return safe AdapterResult objects
  - [ ] Job runner catches exceptions and logs (status="error")
  - [ ] Query orchestrator continues with other sources
  - [ ] User-facing code never receives unhandled adapter exceptions

### Execution Sign-Off — T7-006
- [ ] All 8 failure injection tests pass (exit 0)
- [ ] Partial result handling validated (batch continues on single-adapter failure)
- [ ] Source suspension logic tested (5-streak threshold, revalidation)
- [ ] Suspended sources are filtered from queries
- [ ] No adapter failures break batch execution (all tests assert status in ["partial", "complete"])

---

## Combined Criteria Progress — End of Week 2

| Criterion | Status After Week 2 | Sign-Off Condition |
|---|---|---|
| #1 **Staging Validation** | 🟢 100% | E2E test passes; CSV valid; staging env config works |
| #2 **Async Queue** | 🟢 100% | job_runner.py implemented; upload returns <2s; background worker completes searches |
| #3 **Adapter Resilience** | 🟢 100% | Failure injection tests pass; partial results validated; suspension logic tested |
| #4 **CSV Export** | 🟢 100% | CSV formatter generates correct headers/rows; export test validates output |
| #5 **CI Gates** | 🟢 100% | All new tests pass; CI blocks failing PRs; migrations pass |

---

## Week 2 Final Sign-Off

Complete this block when all three stories are done:

| Story | All Checkboxes Done | Tests Pass (Exit 0) | Criteria Contributions |
|---|---|---|---|
| T7-005 End-to-End | [ ] | [ ] | Criteria #1 (Staging), #4 (CSV Export) |
| T7-006 Failure Injection | [ ] | [ ] | Criteria #3 (Adapter Resilience) |
| T7-007 Job Runner | [ ] | [ ] | Criteria #2 (Async Queue) |

**All 5 Criteria at ≥90%** (Backend Lead sign-off):
Name: _________________ Date: _________

**Performance Baselines Documented**:
- Upload response time: ___ seconds (target: <2s)
- Worker throughput: ___ items/minute (target: 10-20)
- Job retry success rate: ___ % (target: >95%)

Name: _________________ Date: _________

---

## References

- `plan/06_Implementation/PROMPT-9_WEEK2_INTEGRATION_RESILIENCE_EXECUTION.md` — detailed execution guide
- `plan/06_Implementation/PROMPT-7_DEPLOYMENT_EXECUTION_BACKLOG.md` — parent backlog (T7-001..T7-010)
- `plan/06_Implementation/DEPLOYMENT_READINESS_DOR.md` — DOR and sprint structure
- `plan/06_Implementation/CRITERIA_1-5_EXECUTION_PLAN.md` — criteria-to-work mapping
- `plan/07_CONTEXT_ARCHIT/CONTEXT.md` — canonical IDs and governance rules
