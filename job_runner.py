from __future__ import annotations

import threading
import time
import uuid
from datetime import timedelta
from typing import Callable

from django.db import close_old_connections
from django.db.utils import OperationalError
from django.utils import timezone

from persistence.models import CanonicalItem, JobQueueEntry
from persistence.repositories import JobExecutionLogRepository, JobQueueRepository
from search_ranking.search_executor import execute_search_for_item


SearchWorker = Callable[[CanonicalItem, float], dict]


def _safe_close_old_connections() -> None:
    """Best-effort DB connection cleanup for background threads.

    Under pytest-django, background threads may hit a DB access blocker during
    teardown; this must not surface as an unhandled thread exception.
    """
    try:
        close_old_connections()
    except (OperationalError, RuntimeError):
        pass
    except Exception:
        pass


class JobRunner:
    """Background worker for search jobs with retry support."""

    def __init__(
        self,
        max_workers: int = 2,
        poll_interval_seconds: float = 1.0,
        adapter_timeout_seconds: float = 10.0,
        search_worker: SearchWorker | None = None,
    ) -> None:
        self.max_workers = max(1, int(max_workers))
        self.poll_interval_seconds = max(0.2, float(poll_interval_seconds))
        self.adapter_timeout_seconds = max(1.0, float(adapter_timeout_seconds))
        self._search_worker: SearchWorker = search_worker or execute_search_for_item
        self._queue_repo = JobQueueRepository()
        self._log_repo = JobExecutionLogRepository()
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker_loop, name="job-runner", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=max(1.0, self.poll_interval_seconds * 2))

    def submit_search_job(self, canonical_item_id: int, payload: dict | None = None, max_retries: int = 3) -> str:
        item = CanonicalItem.objects.get(pk=canonical_item_id)
        job_id = str(uuid.uuid4())
        self._queue_repo.create(
            job_id=job_id,
            canonical_item=item,
            upload_batch=item.upload_batch,
            payload=payload or {},
            max_retries=max_retries,
        )
        return job_id

    def get_job_status(self, job_id: str) -> dict:
        job = self._queue_repo.get_by_job_id(job_id)
        if job is None:
            return {"job_id": job_id, "status": "not_found", "error": "job_not_found"}

        return {
            "job_id": job.job_id,
            "status": job.status,
            "attempt_count": job.attempt_count,
            "max_retries": job.max_retries,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "result": job.result,
            "error": job.error_message,
        }

    def process_pending_once(self) -> int:
        jobs = list(self._queue_repo.list_pending(limit=self.max_workers))
        jobs.extend(list(self._queue_repo.list_retrying_due(now=timezone.now(), limit=self.max_workers)))
        processed = 0
        for job in jobs:
            self._execute_job(job)
            processed += 1
        return processed

    def _worker_loop(self) -> None:
        while self._running:
            try:
                # Ensure this thread does not reuse stale DB connections.
                _safe_close_old_connections()
                self.process_pending_once()
            except OperationalError:
                # SQLite may transiently lock under concurrent tests; retry on next loop.
                pass
            except Exception:
                # Keep background loop alive even if one iteration fails.
                pass
            finally:
                _safe_close_old_connections()
            time.sleep(self.poll_interval_seconds)

    def _execute_job(self, job: JobQueueEntry) -> None:
        start = time.monotonic()
        self._queue_repo.mark_running(job)

        if job.canonical_item is None:
            error = "missing_canonical_item"
            self._queue_repo.mark_failed(job, error)
            self._log_repo.create(job=job, attempt_number=job.attempt_count, status="error", duration_ms=0, error_message=error)
            return

        try:
            summary = self._search_worker(job.canonical_item, self.adapter_timeout_seconds)
            duration_ms = int((time.monotonic() - start) * 1000)
            self._queue_repo.mark_completed(job, result=summary)
            self._log_repo.create(job=job, attempt_number=job.attempt_count, status="success", duration_ms=duration_ms)
        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            error = str(exc)
            self._log_repo.create(job=job, attempt_number=job.attempt_count, status="error", duration_ms=duration_ms, error_message=error)

            if int(job.attempt_count) < int(job.max_retries):
                backoff_seconds = 2 ** int(job.attempt_count)
                next_retry_at = timezone.now() + timedelta(seconds=backoff_seconds)
                self._queue_repo.mark_retrying(job, error_message=error, next_retry_at=next_retry_at)
            else:
                self._queue_repo.mark_failed(job, error)


_default_runner: JobRunner | None = None


def get_default_job_runner() -> JobRunner:
    global _default_runner
    if _default_runner is None:
        _default_runner = JobRunner()
    return _default_runner
