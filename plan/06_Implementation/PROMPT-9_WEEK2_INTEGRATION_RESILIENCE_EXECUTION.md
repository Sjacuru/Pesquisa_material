# PROMPT 9 - Week 2 Execution: Integration, Resilience, and Async Foundation
## School Material Price Finder (Brazil MVP) - Implementation Layer

**Date**: March 27, 2026
**Sprint Week**: Week 2 of 3
**Scope**: End-to-end integration, adapter resilience, and async job runner implementation
**Reference**: `plan/06_Implementation/PROMPT-7_DEPLOYMENT_EXECUTION_BACKLOG.md`
**Parent Context**: `plan/06_Implementation/DEPLOYMENT_READINESS_DOR.md`, `plan/06_Implementation/PROMPT-8_WEEK1_TEST_HARDENING_EXECUTION.md`
**Criteria Mapping**: `plan/06_Implementation/CRITERIA_1-5_EXECUTION_PLAN.md`

### Governance Classification
- **Type**: Week 2 Execution Prompt (Implementation Layer)
- **Operationalizes**: T7-005, T7-006, T7-007 (from PROMPT-7 backlog)
- **FR Traceability**: FR-018 (edits), FR-020 (export), FR-024 (OCR), FR-025 (ranking), FR-026 (adapters)
- **Does NOT introduce**: New FRs, NFRs, modules, personas, or scope changes
- **Governance rules in effect**: GC-1 through GC-9 (unchanged)

### Criteria Progress Target
- Criterion #1 (Staging Validation): 40% → **100%**
- Criterion #2 (Async Queue): 0% → **100%**
- Criterion #3 (Adapter Resilience): 50% → **100%**
- Criterion #4 (CSV Export): 30% → **100%**
- Criterion #5 (CI Gates): 100% → **100%** (maintained)

---

## 1. Objective

Execute Week 2 stories from the deployment readiness backlog. The goal is to:

1. Validate critical flows end-to-end (upload → search → edit → export)
2. Implement async job execution (non-blocking batch search)
3. Validate adapter resilience under failure conditions
4. Implement CSV export artifact generation

**Week 2 Stories:**
- T7-005: End-to-End Workflow Integration
- T7-006: Failure Injection and Fallbacks
- T7-007: Concurrency and Job Runner Reliability

**Exit Condition**: All three stories meet their Definition of Done, and all 5 criteria are ≥90% complete before Week 3 begins.

---

## 2. Story T7-005 — End-to-End Workflow Integration

**FR Mapping**: FR-018 (User Edits), FR-020 (Export), all EPIC-001-004 integration
**Modules Under Test**: All 4 domain components integrated (intake + governance + search + workflow)

### 2.1 The Critical Flow (Happy Path)

```
User uploads file (PDF/DOCX/XLSX)
    ↓
[Intake & Canonicalization] Extracts items, normalizes data
    ↓
[Source Governance] Evaluates source trust, applies eligibility filters
    ↓
[Search & Ranking] Executes async search on eligible sources, ranks results
    ↓
[User Workflow] User edits item details (price, quantity, notes)
    ↓
[Version History] Records edit as VersionEvent
    ↓
[Export] Generates CSV/PDF with latest values + version metadata
    ↓
User downloads file (CSV or PDF artifact)
```

### 2.2 Integration Test Scope

**Test File**: `tests/integration/test_upload_to_search_export_flow.py` (new)

**Preconditions**:
- SQLite database initialized (`pytest-django` fixtures handle this via Django test database)
- SourceSite records seeded (5 adapters with `is_search_eligible=true`)
- CanonicalItem table empty at start

**Flow Test Case 1: Happy Path (Upload → Search → Edit → Export CSV)**

```python
def test_upload_to_export_flow_happy_path():
    # SETUP: Create batch, upload with 3 items
    batch = upload_batch_fixture(items=[
        {"name": "Math Book 2026", "category": "book", "quantity": 1},
        {"name": "Notebook A3", "category": "notebook", "quantity": 2},
        {"name": "Pencil Set", "category": "general supplies", "quantity": 10},
    ])

    # ACT: Stage A ingestion (extract + canonicalize)
    stage_a_result = process_stage_a_ingestion(
        uploaded_document=...,
        category_matrix_reference=...,
        persist_to_db=True,
    )
    
    # ASSERT: Items persisted to CanonicalItem, batch status = "extracted"
    assert batch.items.count() == 3
    assert all(item.search_ready is True for item in batch.items.all())

    # ACT: Trigger search (mock async execution here — real async in T7-007)
    for item in batch.items.all():
        mock_adapter_results = {
            "amazon_br": [{"title": "Math Book", "price": Decimal("50.00")}],
            "magalu_br": [{"title": "Math Book Official", "price": Decimal("48.00")}],
        }
        persist_offers(item, mock_adapter_results)  # Offers created in Offer model

    # ASSERT: Offers persisted, SearchJob status = "complete"
    offers_count = Offer.objects.filter(canonical_item__upload_batch=batch).count()
    assert offers_count >= 2  # At least 2 sources returned results

    # ACT: User edits one item
    item = batch.items.first()
    old_name = item.name
    item.name = old_name + " [EDITED]"
    item.save()

    # ASSERT: VersionEvent recorded
    version_event = VersionEvent.objects.get(
        material_id=item.item_code,
        field_name="name",
    )
    assert version_event.old_value == old_name
    assert version_event.new_value == old_name + " [EDITED]"

    # ACT: Export as CSV
    curated_set = {
        "records": [
            {
                "materialId": item.item_code,
                "latestValues": {"name": item.name},
            }
        ]
    }
    export_result = export_formatter_delivery(
        curated_set=curated_set,
        version_context={...},  # version history
        export_request={"format": "csv"},
        user_context={"userId": "test-user"},
    )

    # ASSERT: CSV generated, parseable, matches data
    assert export_result["deliveryResult"]["status"] == "success"
    csv_content = export_result["deliveryResult"]["artifact"]
    csv_rows = list(csv.DictReader(io.StringIO(csv_content)))
    assert len(csv_rows) == 1
    assert csv_rows[0]["Item"] == old_name + " [EDITED]"
    assert csv_rows[0]["Version"] == "1"  # One edit applied
```

### 2.3 CSV Export Specification

**File**: `workflow_export/csv_formatter.py` (new)

**CSV Schema**:
```
Headers: Item | Category | Quantity | Unit | Price | Source | URL | Version | Last Edited By | Notes
Row Format:
  - Item: canonical item name (latest value after edits)
  - Category: category_id
  - Quantity: decimal (e.g., 2.50)
  - Unit: unit_code (e.g., "un", "kg", "pç")
  - Price: lowest price from all search results (if available)
  - Source: source_site_id (e.g., "amazon_br")
  - URL: product URL from best-price offer
  - Version: latest version number from VersionEvent records
  - Last Edited By: actor_id from most recent VersionEvent (or "system" if never edited)
  - Notes: free-text notes from workflow_state or item.notes field

Encoding: UTF-8
Delimiter: comma (,)
Quote char: double-quote (")
Line terminator: CRLF (\r\n)

Row Ordering: By item.name (alphabetical)

Special Handling:
  - Prices with Decimal type: rendered as "R$ 123.45" (Brazilian format)
  - Empty prices: rendered as "N/A"
  - Empty notes: rendered as empty string (not "None")
  - Multiple sources per item: consolidate to one row with "Source" = primary source (lowest price)
```

**Export Implementation**:
```python
# File: workflow_export/csv_formatter.py

def format_as_csv(records: list[dict], version_context: dict) -> str:
    """
    Convert curated records to CSV string.
    
    Args:
        records: list of material records with latestValues
        version_context: {byMaterial: {material_id: {latestVersion, entries}}}
    
    Returns:
        CSV string (UTF-8, comma-delimited)
    """
    import csv, io
    from datetime import datetime
    
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "Item", "Category", "Quantity", "Unit", 
            "Price", "Source", "URL", "Version", "Last Edited By", "Notes"
        ],
        lineterminator="\r\n",
    )
    
    writer.writeheader()
    for record in sorted(records, key=lambda r: r.get("name", "")):
        latest_values = record.get("latestValues", {})
        version_meta = version_context.get("byMaterial", {}).get(record.get("materialId"), {})
        
        # Find latest editor from version_meta["entries"]
        last_editor = "system"
        if version_meta.get("entries"):
            last_actor = version_meta["entries"][-1].get("actor_id")
            if last_actor:
                last_editor = last_actor
        
        writer.writerow({
            "Item": latest_values.get("name", ""),
            "Category": latest_values.get("category", ""),
            "Quantity": latest_values.get("quantity", ""),
            "Unit": latest_values.get("unit", "un"),
            "Price": format_price(latest_values.get("price")),  # Format as R$ X.XX
            "Source": record.get("preferred_source", ""),
            "URL": record.get("preferred_url", ""),
            "Version": version_meta.get("latestVersion", 0),
            "Last Edited By": last_editor,
            "Notes": record.get("notes", ""),
        })
    
    return output.getvalue()
```

### 2.4 Staging Environment Configuration

**Files to Create**:

**File 1**: `.env.staging` (new)
```
# Staging Environment Configuration
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=staging-secret-change-in-production
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,staging.local
DATABASE_URL=sqlite:///var/staging.sqlite3
SCHOOL_EXCLUSIVE_ENABLED=false
WEBSEARCH_ENABLED=true
```

**File 2**: `scripts/seed_staging_db.py` (new)
```python
"""
Seed staging database with base data:
- 5 SourceSite records (Amazon, Magalu, Estante Virtual, Kalunga, Mercado Livre)
- Trust status: ALLOWED
- Search eligibility: true
- Categories: book, dictionary, apostila, notebook, general supplies
"""

def seed_sources():
    SourceSite.objects.bulk_create([
        SourceSite(
            site_id="amazon_br",
            label="Amazon Brasil",
            trust_status=SourceSite.TrustStatus.ALLOWED,
            is_search_eligible=True,
            integration_type=SourceSite.IntegrationType.SCRAPING,
            categories=["book", "dictionary", "apostila", "notebook", "general supplies"],
        ),
        # ... (repeat for magalu_br, ev_br, kalunga_br, ml_br)
    ])

if __name__ == "__main__":
    import django
    django.setup()
    seed_sources()
    print("Staging database seeded.")
```

### 2.5 Definition of Done — T7-005

- [ ] Integration test `test_upload_to_search_export_flow.py` covering happy path (upload → edit → export) passes
- [ ] CSV formatter (`csv_formatter.py`) generates valid CSV with correct headers, data types, and Brazilian price formatting
- [ ] Export integration test parses generated CSV and validates row count + column values match in-app state
- [ ] `.env.staging` created with correct variable names (DJANGO_DEBUG, DATABASE_URL, etc.)
- [ ] `scripts/seed_staging_db.py` runs without error and populates SourceSite table with 5 sources
- [ ] Manual validation: Sample CSV downloaded from app, opened in Excel/Sheets, columns and data visually correct

---

## 3. Story T7-007 — Concurrency and Job Runner Reliability

**FR Mapping**: FR-026 (all adapters must work under async conditions), FR-018, FR-020
**Modules Under Test**: `platform/job_runner.py`, `search_ranking/query_orchestrator.py`, `persistence/models.py`

### 3.1 Job Runner Architecture

The job runner is the async execution foundation. It must:

1. **Accept job submissions** → Create JobQueueEntry record
2. **Dispatch jobs** → Background worker picks up entries
3. **Execute in background** → Does not block upload request
4. **Track status** → User can poll progress
5. **Retry on failure** → Up to 3 attempts with exponential backoff
6. **Handle concurrency** → Multiple jobs in parallel (SQLite WAL mode enables this)
7. **Persist results** → Offers stored in database

### 3.2 Data Model Extension

**File**: `persistence/models.py` (extend)

```python
class JobQueueEntry(models.Model):
    """Represents a single job (search for one item, or batch processing job)."""
    
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        RETRYING = "retrying", "Retrying"
    
    job_id = models.CharField(max_length=64, unique=True)  # UUID
    job_type = models.CharField(max_length=32)  # "search_item", "batch_process"
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    canonical_item = models.ForeignKey(CanonicalItem, on_delete=models.CASCADE, null=True, blank=True)
    upload_batch = models.ForeignKey(UploadBatch, on_delete=models.CASCADE, null=True, blank=True)
    
    # Retry tracking
    attempt_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    payload = models.JSONField(default=dict, blank=True)  # Job input (query, context)
    result = models.JSONField(default=dict, blank=True)   # Job output (offers, errors)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["job_id"]),
        ]

class JobExecutionLog(models.Model):
    """Audit trail for job execution (attempt #1, #2, #3, etc.)."""
    
    job = models.ForeignKey(JobQueueEntry, on_delete=models.CASCADE, related_name="execution_log")
    attempt_number = models.PositiveIntegerField()
    status = models.CharField(max_length=32)  # "success", "timeout", "error"
    duration_ms = models.PositiveIntegerField()
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
```

### 3.3 Job Runner Implementation

**File**: `platform/job_runner.py` (implement from scaffold)

```python
"""
Background job execution and retry orchestration.

Responsibilities:
- Accept job submissions (create JobQueueEntry)
- Dispatch jobs to background worker
- Execute search queries asynchronously
- Track job status and allow polling
- Retry failed jobs with exponential backoff
- Persist results to database

Concurrency model:
- SQLite with WAL mode enabled (allows concurrent reads/writes)
- Background worker runs in separate thread/process
- Job status is atomic (read/write via Django ORM)
"""

import time
import threading
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from django.utils import timezone as django_tz
from persistence.models import JobQueueEntry, JobExecutionLog, CanonicalItem, Offer, SourceSite
from persistence.repositories import JobRepository
from search_ranking.query_orchestrator import orchestrate_query
from source_adapters.category_router import get_adapters_for_category


class JobRunner:
    """Manages job queue and background execution."""
    
    def __init__(self, max_workers: int = 2, poll_interval_seconds: float = 1.0):
        self.max_workers = max_workers
        self.poll_interval = poll_interval_seconds
        self.running = False
    
    def submit_search_job(self, canonical_item_id: int, context: dict = None) -> str:
        """
        Submit a search job for a canonical item.
        Returns job_id immediately (non-blocking).
        """
        item = CanonicalItem.objects.get(id=canonical_item_id)
        job_id = str(uuid.uuid4())
        
        JobQueueEntry.objects.create(
            job_id=job_id,
            job_type="search_item",
            status=JobQueueEntry.Status.PENDING,
            canonical_item=item,
            upload_batch=item.upload_batch,
            payload=context or {},
            max_retries=3,
        )
        return job_id
    
    def get_job_status(self, job_id: str) -> dict:
        """Get current status of a job."""
        try:
            job = JobQueueEntry.objects.get(job_id=job_id)
            return {
                "job_id": job_id,
                "status": job.status,
                "progress": {
                    "attempt": job.attempt_count,
                    "max_retries": job.max_retries,
                },
                "result": job.result or None,
                "error": job.error_message or None,
            }
        except JobQueueEntry.DoesNotExist:
            return {"error": "Job not found"}
    
    def start_background_worker(self):
        """Start background worker thread (runs continuously)."""
        if self.running:
            return
        self.running = True
        worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        worker_thread.start()
    
    def _worker_loop(self):
        """Background worker: continuously poll for pending/retrying jobs."""
        while self.running:
            try:
                self._process_pending_jobs()
                self._process_retrying_jobs()
            except Exception as e:
                print(f"Worker error: {e}")
            
            time.sleep(self.poll_interval)
    
    def _process_pending_jobs(self):
        """Find pending jobs and execute them."""
        pending_jobs = JobQueueEntry.objects.filter(
            status=JobQueueEntry.Status.PENDING
        ).order_by("created_at")[:self.max_workers]
        
        for job in pending_jobs:
            self._execute_job(job)
    
    def _process_retrying_jobs(self):
        """Find jobs due for retry and execute them."""
        now = django_tz.now()
        retrying_jobs = JobQueueEntry.objects.filter(
            status=JobQueueEntry.Status.RETRYING,
            next_retry_at__lte=now,
        ).order_by("next_retry_at")[:self.max_workers]
        
        for job in retrying_jobs:
            self._execute_job(job)
    
    def _execute_job(self, job: JobQueueEntry):
        """Execute a single job (search for canonical item)."""
        start = time.monotonic()
        job.status = JobQueueEntry.Status.RUNNING
        job.started_at = django_tz.now()
        job.attempt_count += 1
        job.save(update_fields=["status", "started_at", "attempt_count"])
        
        try:
            item = job.canonical_item
            category = item.category
            query_text = item.name
            
            # Get eligible sources
            eligible_sources = SourceSite.objects.filter(
                is_search_eligible=True,
                categories__contains=[category],
            ).exclude(trust_status=SourceSite.TrustStatus.BLOCKED)
            
            # Execute search (orchestrate_query)
            query_result = orchestrate_query(
                query={"text": query_text, "categoryID": category},
                validation_result={"is_valid": True, "dependency_chain_validated": True},
                eligible_sources=[{"site_id": s.site_id, "label": s.label} for s in eligible_sources],
                source_query_executor=self._source_executor,
                exclusivity_context={},  # TODO: integrate brand exclusivity
            )
            
            # Persist offers
            offers_created = 0
            for offer_dict in query_result.get("offers", []):
                Offer.objects.create(
                    canonical_item=item,
                    source_site_id=offer_dict.get("source"),
                    title=offer_dict.get("title"),
                    price=Decimal(str(offer_dict.get("price", 0))),
                    url=offer_dict.get("url"),
                    raw_data=offer_dict,
                )
                offers_created += 1
            
            # Mark complete
            duration_ms = int((time.monotonic() - start) * 1000)
            job.status = JobQueueEntry.Status.COMPLETED
            job.completed_at = django_tz.now()
            job.result = {"offers_created": offers_created, "duration_ms": duration_ms}
            job.save()
            
            # Log execution
            JobExecutionLog.objects.create(
                job=job,
                attempt_number=job.attempt_count,
                status="success",
                duration_ms=duration_ms,
            )
            
        except Exception as e:
            duration_ms = int((time.monotonic() - start) * 1000)
            job.error_message = str(e)
            
            if job.attempt_count < job.max_retries:
                # Schedule retry (exponential backoff: 2s, 4s, 8s)
                backoff_seconds = 2 ** job.attempt_count
                job.status = JobQueueEntry.Status.RETRYING
                job.next_retry_at = django_tz.now() + timedelta(seconds=backoff_seconds)
            else:
                # All retries exhausted
                job.status = JobQueueEntry.Status.FAILED
                job.completed_at = django_tz.now()
            
            job.save()
            
            # Log execution
            JobExecutionLog.objects.create(
                job=job,
                attempt_number=job.attempt_count,
                status="error",
                duration_ms=duration_ms,
                error_message=str(e),
            )
    
    def _source_executor(self, source: dict, query: dict, timeout_seconds: float = 10.0) -> dict:
        """Execute search on a single source."""
        from source_adapters.category_router import get_adapters_for_category
        adapters = get_adapters_for_category(query.get("categoryID", ""))
        
        for adapter in adapters:
            if adapter.site_id == source.get("site_id"):
                result = adapter.search(query.get("text", ""), timeout_seconds=timeout_seconds)
                return {
                    "results": [
                        {
                            "title": offer.product_title,
                            "price": float(offer.item_price),
                            "source": source.get("site_id"),
                            "url": offer.product_url,
                        }
                        for offer in result.offers
                    ]
                }
        
        return {"results": []}
```

### 3.4 Integration into Upload Workflow

**File**: `web/views.py` (modify upload_workflow)

```python
def upload_workflow(request: HttpRequest):
    """Handle file upload with async search execution."""
    # ... existing Stage A processing ...
    
    stage_a_result = process_stage_a_ingestion(...)
    
    if stage_a_result.get("persistence"):
        batch_id = stage_a_result["persistence"]["upload_batch_id"]
        batch = UploadBatch.objects.get(id=batch_id)
        
        # Get high-confidence items ready for search
        search_ready_items = batch.items.filter(search_ready=True)
        
        # Submit async jobs (non-blocking)
        job_ids = []
        for item in search_ready_items:
            job_runner = JobRunner()
            job_runner.start_background_worker()  # Start if not running
            job_id = job_runner.submit_search_job(item.id)
            job_ids.append(job_id)
        
        # Return immediately (upload response includes job_ids for polling)
        return render(request, "upload_complete.html", {
            "batch_id": batch.public_id,
            "job_ids": job_ids,
            "item_count": search_ready_items.count(),
        })
```

### 3.5 Concurrency and Idempotency Tests

**File**: `tests/integration/test_job_runner_reliability.py` (new)

```python
def test_concurrent_job_execution():
    """Execute 5 search jobs concurrently, verify no conflicts."""
    batch = create_upload_batch_with_items(count=5)
    runner = JobRunner(max_workers=3)
    runner.start_background_worker()
    
    # Submit 5 jobs
    job_ids = []
    for item in batch.items.all():
        job_id = runner.submit_search_job(item.id)
        job_ids.append(job_id)
    
    # Wait for completion (with timeout)
    timeout = time.time() + 30
    while time.time() < timeout:
        all_done = all(
            runner.get_job_status(jid)["status"] == "completed"
            for jid in job_ids
        )
        if all_done:
            break
        time.sleep(0.5)
    
    # Verify all jobs completed
    for job_id in job_ids:
        status = runner.get_job_status(job_id)
        assert status["status"] == "completed", f"Job {job_id} not completed"

def test_retry_on_timeout():
    """Simulate adapter timeout, verify job retries 3x, then fails."""
    item = create_canonical_item_with_search_ready()
    runner = JobRunner()
    runner.start_background_worker()
    
    job_id = runner.submit_search_job(item.id)
    # Mock adapter to always timeout
    # ... (use patch to mock orchestrate_query)
    
    # Wait for retries to exhaust
    time.sleep(10)  # Should attempt 3x with exponential backoff
    
    status = runner.get_job_status(job_id)
    assert status["status"] == "failed"
    assert status["progress"]["attempt"] == 3

def test_idempotent_search():
    """Search for same item twice, verify offers only created once (or correctly merged)."""
    item = create_canonical_item_with_search_ready()
    runner = JobRunner()
    runner.start_background_worker()
    
    # Submit same job twice (rapid succession)
    job_id_1 = runner.submit_search_job(item.id)
    job_id_2 = runner.submit_search_job(item.id)
    
    time.sleep(10)
    
    # Verify: offers created, no duplicates
    offers = Offer.objects.filter(canonical_item=item)
    # Should have offers from 5 adapters (if all succeeded)
    # Check no duplicate URL/source pairs
    offer_keys = [(o.source_site_id, o.url) for o in offers]
    assert len(offer_keys) == len(set(offer_keys)), "Duplicate offers detected"
```

### 3.6 Database Configuration (SQLite Concurrency)

**File**: `config/settings.py` (modify DATABASES)

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "var" / "dev.sqlite3",
        "CONN_MAX_AGE": 0,  # Disable connection pooling (SQLite)
        "OPTIONS": {
            "timeout": 10,  # Wait up to 10s for database lock
            "check_same_thread": False,  # Allow multi-threaded access
        },
    }
}

# Enable WAL mode for better concurrency
from django.db.backends.signals import connection_created
from django.dispatch import receiver

@receiver(connection_created)
def setup_sqlite_wal(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        with connection.cursor() as cursor:
            cursor.execute('PRAGMA journal_mode = WAL;')
```

### 3.7 Definition of Done — T7-007

- [ ] `JobQueueEntry` and `JobExecutionLog` models created and migrated
- [ ] `JobRepository` class created with methods for create, get_by_id, update_status, list_pending, list_retrying
- [ ] `platform/job_runner.py` fully implemented with:
  - [ ] JobRunner class with submit_search_job, get_job_status, start_background_worker
  - [ ] Background worker loop (_worker_loop, _process_pending_jobs, _process_retrying_jobs, _execute_job)
  - [ ] Exponential backoff retry logic (2s, 4s, 8s)
  - [ ] Job execution logging (JobExecutionLog entries created per attempt)
- [ ] Web view integration: upload_workflow triggers async search job submission, returns immediately
- [ ] SQLite WAL mode enabled in config/settings.py
- [ ] Integration test: `test_job_runner_reliability.py` with concurrent, retry, and idempotency cases all passing
- [ ] Manual validation: Upload file, confirm response returns immediately, poll job_ids endpoint, verify jobs complete in background

---

## 4. Story T7-006 — Failure Injection and Fallbacks

**FR Mapping**: FR-026 (adapter resilience), FR-021 (source governance)
**Modules Under Test**: `source_adapters/`, `source_governance/`, `search_ranking/query_orchestrator.py`

### 4.1 Failure Scenarios

Each failure scenario must be tested with both the real adapter code and a mocked failure. The goal is to verify that single-adapter failure does not halt the entire search batch.

### 4.2 Failure Case 1: Adapter Timeout

**Scenario**: Search request to Amazon takes 15 seconds, timeout is 10 seconds.

**Expected Behavior**:
- Adapter returns `AdapterResult(status="timeout", error_message="...")`
- Query orchestrator continues with remaining 4 adapters
- SearchJob records outcome: `timeout_count=1, error_count=0`
- Offers from other 4 adapters are persisted

**Test File**: `tests/integration/test_failure_injection_and_fallbacks.py` (new)

```python
def test_adapter_timeout_does_not_stop_batch():
    """Mock Amazon adapter to timeout; verify batch continues with other 4 adapters."""
    item = create_canonical_item_with_search_ready()
    
    with patch("source_adapters.amazon_adapter.AmazonBRAdapter.search") as mock_amazon:
        mock_amazon.side_effect = httpx.TimeoutException("Timeout")
        
        # Execute search
        job_result = execute_search_for_item(item, timeout_seconds=10.0, max_adapters=5)
        
        # Verify
        assert job_result["status"] in ["partial", "complete"]  # Not "failed"
        assert job_result["timeout_count"] == 1
        assert job_result["success_count"] == 4  # Other adapters succeeded
        
        # Persist offers from 4 successful adapters
        offers = Offer.objects.filter(canonical_item=item)
        assert offers.count() >= 4

def test_adapter_http_error_does_not_stop_batch():
    """Mock Magalu adapter to return HTTP 500; verify batch continues."""
    item = create_canonical_item_with_search_ready()
    
    with patch("source_adapters.magalu_adapter.MagaluBRAdapter.search") as mock_magalu:
        mock_magalu.return_value = AdapterResult(
            source_site_id="magalu_br",
            query_text=item.name,
            status="error",
            error_message="HTTP 500 Internal Server Error",
            response_ms=100,
        )
        
        job_result = execute_search_for_item(item, timeout_seconds=10.0, max_adapters=5)
        
        assert job_result["status"] in ["partial", "complete"]
        assert job_result["error_count"] == 1
        assert job_result["success_count"] == 4
```

### 4.3 Failure Case 2: Rate Limiting (429 Too Many Requests)

**Scenario**: Kalunga returns 429; adapter should back off gracefully.

**Expected Behavior**:
- Adapter detects 429 and returns `status="error"`
- Retry logic waits (configurable backoff: 2s base)
- Next attempt succeeds
- SearchJob records: `error_count=1` but successful on retry

**Test File**: (same as above)

```python
def test_adapter_rate_limit_retry():
    """Adapter returns 429, waits, retries, succeeds."""
    item = create_canonical_item_with_search_ready()
    
    call_count = 0
    def mock_search_with_rate_limit(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return AdapterResult(
                source_site_id="kalunga_br",
                query_text="",
                status="error",
                error_message="HTTP 429 Too Many Requests",
                response_ms=100,
            )
        else:  # Second attempt
            return AdapterResult(
                source_site_id="kalunga_br",
                query_text="",
                status="ok",
                offers=[OfferResult(...)],  # Success
                response_ms=150,
            )
    
    with patch("source_adapters.kalunga_adapter.KalungaBRAdapter.search", side_effect=mock_search_with_rate_limit):
        job_result = execute_search_for_item(item, timeout_seconds=10.0, max_retries=3)
        
        # Verify retried and succeeded
        assert call_count == 2
        assert job_result["offers"][...] # Offers from Kalunga present
```

### 4.4 Failure Case 3: Bot Detection (Captcha Page)

**Scenario**: Estante Virtual returns HTML with captcha instead of search results.

**Expected Behavior**:
- Adapter detects non-catalog responses
- Returns `status="error"` with empty offers list
- Search continues with remaining adapters

**Test File**: (same)

```python
def test_adapter_bot_detection():
    """Adapter receives captcha page, returns error, batch continues."""
    item = create_canonical_item_with_search_ready()
    
    # Mock response with captcha HTML
    captcha_html = """
    <html>
        <form action="/verify" method="POST">
            <h1>Verificação de Segurança</h1>
            <p>Você pode parecer um bot...</p>
        </form>
    </html>
    """
    
    with patch("httpx.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = captcha_html
        mock_get.return_value = mock_response
        
        # Call Estante Virtual adapter
        adapter = EvanteVirtualAdapter()
        result = adapter.search(item.name, timeout_seconds=10.0)
        
        # Verify graceful failure
        assert result.status == "error"
        assert result.offers == []
```

### 4.5 Failure Case 4: Source Suspension (Auto-Suspension on Streaks)

**Scenario**: Amazon fails 5 consecutive searches; auto-suspension triggers.

**Expected Behavior**:
- 5 consecutive failures → `failure_streak=5`
- SourceSite.is_suspended transitions to `True`
- Next search skips suspended source
- Revalidation event can reset suspension

**Test File**: `tests/unit/source_governance/test_site_failure_monitor_auto_suspension.py` (extend)

```python
def test_source_suspension_on_failure_streak():
    """5 consecutive failures trigger suspension; revalidation resets."""
    from source_governance.site_failure_monitor_auto_suspension import update_site_suspension_state
    
    current_state = {}
    suspension_threshold = {"failure_streak_threshold": 5}
    
    # Simulate 5 consecutive failures
    for i in range(5):
        retry_outcomes = [False, False, False]  # First 3 of batch retries all fail
        status, state = update_site_suspension_state(
            site_id="amazon_br",
            retry_outcomes=retry_outcomes,
            current_state=current_state,
            suspension_threshold_config=suspension_threshold,
        )
        current_state["amazon_br"] = state
    
    # After 5 failures, should be suspended
    assert current_state["amazon_br"]["is_suspended"] is True
    
    # Revalidation event resets suspension
    status, state = update_site_suspension_state(
        site_id="amazon_br",
        retry_outcomes=[],
        current_state=current_state,
        suspension_threshold_config=suspension_threshold,
        revalidation_event=True,
    )
    
    assert state["is_suspended"] is False
    assert state["failure_streak"] == 0

def test_suspended_source_filtered_from_search():
    """Suspended source is excluded from query orchestration."""
    # Setup: Amazon suspended
    amazon = SourceSite.objects.create(
        site_id="amazon_br",
        label="Amazon Brasil",
        trust_status=SourceSite.TrustStatus.SUSPENDED,  # <-- Suspended
        is_search_eligible=False,
    )
    
    item = create_canonical_item_with_search_ready()
    
    # Execute search
    job_result = execute_search_for_item(item)
    
    # Verify Amazon was not queried
    assert "amazon_br" not in job_result["queried_sources"]
    assert job_result["queried_sources"] == ["magalu_br", "ev_br", "kalunga_br", "ml_br"]
```

### 4.6 Definition of Done — T7-006

- [ ] Test file `test_failure_injection_and_fallbacks.py` created with 4+ failure scenarios (timeout, HTTP error, rate limit, captcha)
- [ ] All failure injection tests pass:
  - [ ] Timeout does not halt batch
  - [ ] HTTP 500 does not halt batch
  - [ ] 429 rate limit retried successfully
  - [ ] Captcha page handled gracefully
- [ ] `test_site_failure_monitor_auto_suspension.py` extended with:
  - [ ] Suspension triggers on streak=5
  - [ ] Revalidation event resets suspension
  - [ ] Suspended source filtered from search
- [ ] SearchJob model records timeout_count and error_count accurately
- [ ] No adapter failure propagates to user (always returns partial or complete, never failed batch)

---

## 5. Dependencies and Sequence

```
T7-005 (E2E Integration)  ──┐
T7-006 (Failure Injection) ──┤──→ All 5 criteria at 100% ──→ Week 3 Start
T7-007 (Job Runner)       ──┘
```

T7-005, T7-006, and T7-007 may be executed in parallel, but T7-007 (job runner implementation) should prioritize because T7-005 integration tests depend on it.

**Recommended order**:
1. **Day 1-2**: T7-007 (Job Runner implementation + concurrency tests)
2. **Day 3**: T7-006 (Failure injection tests — can be mocked, doesn't need runner)
3. **Day 4**: T7-005 (E2E integration — uses runner from Day 1-2)
4. **Day 5**: Final validation + sign-off

---

## 6. Governance Compliance

| Rule | Status | Evidence |
|---|---|---|
| GC-1 (Traceability) | PASS | All tasks map to FR-018, FR-020, FR-024, FR-025, FR-026 |
| GC-5 (No Invented Thresholds) | PASS | Retry thresholds (3x) + backoff (2s, 4s, 8s) documented; suspension threshold uses config |
| GC-8 (ID Immutability) | PASS | No FR/NFR IDs altered |
| Scope Ceiling | PASS | No features beyond school material comparison scope |
| No New FRs | PASS | All work operationalizes existing approved FRs (FR-018, FR-020, FR-024, FR-025, FR-026) |

---

## 7. References

- `plan/06_Implementation/PROMPT-7_DEPLOYMENT_EXECUTION_BACKLOG.md` — parent backlog (T7-001 through T7-010)
- `plan/06_Implementation/DEPLOYMENT_READINESS_DOR.md` — canonical DOR
- `plan/06_Implementation/PROMPT-8_WEEK1_TEST_HARDENING_EXECUTION.md` — Week 1 execution guide (predecessor)
- `plan/06_Implementation/CRITERIA_1-5_EXECUTION_PLAN.md` — detailed criteria mapping
- `plan/06_Implementation/WEEK2_EXECUTION_CHECKLIST.md` — tactical checkbox tracker for Week 2
