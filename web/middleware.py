# FILE: web/middleware.py
# MODULE: Web Middleware
# RESPONSIBILITY: Initialize background services safely on first request
from django.conf import settings
from job_runner import get_default_job_runner


_JOB_RUNNER_STARTED = False


class JobRunnerMiddleware:
    """Start the background job runner on first request (safe after migrations)."""

    def __init__(self, get_response):
        self.get_response = get_response
        global _JOB_RUNNER_STARTED

        # Try to start now (may fail if migrations haven't run)
        if not _JOB_RUNNER_STARTED and settings.ASYNC_SEARCH_ENABLED:
            try:
                job_runner = get_default_job_runner()
                job_runner.start()
                _JOB_RUNNER_STARTED = True
            except Exception:
                pass  # Will retry on next request

    def __call__(self, request):
        global _JOB_RUNNER_STARTED

        # Retry on each request until successful
        if not _JOB_RUNNER_STARTED and settings.ASYNC_SEARCH_ENABLED:
            try:
                job_runner = get_default_job_runner()
                if not job_runner._running:
                    job_runner.start()
                _JOB_RUNNER_STARTED = True
            except Exception:
                pass

        return self.get_response(request)
