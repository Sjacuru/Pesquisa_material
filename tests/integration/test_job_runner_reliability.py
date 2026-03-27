from __future__ import annotations

from django.test import TestCase

from job_runner import JobRunner
from persistence.models import CanonicalItem, JobQueueEntry, UploadBatch


class JobRunnerReliabilityTests(TestCase):
    def setUp(self) -> None:
        self.batch = UploadBatch.objects.create(source_filename="queue.pdf", status=UploadBatch.Status.EXTRACTED)
        self.item = CanonicalItem.objects.create(
            upload_batch=self.batch,
            item_code="queue-1",
            name="Caderno universitario",
            category="notebook",
            quantity="1",
            unit="un",
            search_ready=True,
        )

    def test_job_runner_processes_pending_job(self) -> None:
        def _worker(item: CanonicalItem, timeout_seconds: float) -> dict:
            return {"status": "complete", "offers_found": 2, "item": item.pk, "timeout": timeout_seconds}

        runner = JobRunner(search_worker=_worker, poll_interval_seconds=0.1)
        job_id = runner.submit_search_job(self.item.pk)

        processed = runner.process_pending_once()

        self.assertEqual(processed, 1)
        status = runner.get_job_status(job_id)
        self.assertEqual(status["status"], JobQueueEntry.Status.COMPLETED)
        self.assertEqual(status["result"]["offers_found"], 2)

    def test_job_runner_retries_and_marks_failed(self) -> None:
        def _always_fail(_item: CanonicalItem, _timeout_seconds: float) -> dict:
            raise RuntimeError("adapter_failed")

        runner = JobRunner(search_worker=_always_fail, poll_interval_seconds=0.1)
        job_id = runner.submit_search_job(self.item.pk, max_retries=2)

        # first attempt -> retrying
        runner.process_pending_once()
        status_1 = runner.get_job_status(job_id)
        self.assertEqual(status_1["status"], JobQueueEntry.Status.RETRYING)

        # force due retry and run second attempt
        job = JobQueueEntry.objects.get(job_id=job_id)
        job.next_retry_at = job.created_at
        job.save(update_fields=["next_retry_at"])
        runner.process_pending_once()

        status_2 = runner.get_job_status(job_id)
        self.assertEqual(status_2["status"], JobQueueEntry.Status.FAILED)
        self.assertIn("adapter_failed", status_2["error"])
