# FILE: search_ranking/search_executor.py
# MODULE: Real Search Executor
# RESPONSIBILITY: Run real adapter searches for a CanonicalItem, persist Offer rows,
#                 log SearchExecution records, and update SearchJob state.
# DEPENDS_ON: source_adapters/, persistence/repositories.py, search_ranking/query_orchestrator.py
from __future__ import annotations

import time
from decimal import Decimal

from persistence.models import CanonicalItem, SearchJob, SourceSite
from persistence.repositories import (
    OfferRepository,
    SearchExecutionRepository,
    SearchJobRepository,
    WorkflowStateRepository,
)
from source_adapters.base import AdapterResult
from source_adapters.category_router import build_query, get_adapters_for_category


def execute_search_for_item(
    canonical_item: CanonicalItem,
    timeout_seconds: float = 10.0,
) -> dict:
    """
    Run real adapter searches for a single CanonicalItem.

    1. Creates a SearchJob record.
    2. Determines adapters from item category.
    3. Calls each adapter, captures AdapterResult.
    4. Persists each Offer; logs each SearchExecution.
    5. Updates SearchJob status to complete/partial/failed.
    6. Transitions WorkflowState to DRAFT (search done, awaiting review).

    Returns a summary dict:
    {
        "search_job_id": int,
        "status": str,
        "offers_found": int,
        "adapters_queried": list[str],
        "errors": list[str],
    }
    """
    job_repo = SearchJobRepository()
    offer_repo = OfferRepository()
    exec_repo = SearchExecutionRepository()
    wf_repo = WorkflowStateRepository()

    job: SearchJob = job_repo.create(canonical_item=canonical_item)
    job_repo.update_status(job, SearchJob.Status.RUNNING)

    item_dict = {
        "isbn_normalized": canonical_item.isbn_normalized,
        "name": canonical_item.name,
        "category": canonical_item.category,
        "quantity": str(canonical_item.quantity),
        "unit": canonical_item.unit,
    }
    query_text = build_query(item_dict)
    adapters = get_adapters_for_category(canonical_item.category)

    offers_found = 0
    errors: list[str] = []
    adapters_queried: list[str] = []
    timeout_count = 0

    for adapter in adapters:
        source_site = _get_source_site(adapter.site_id)
        if source_site is not None:
            if source_site.trust_status in (SourceSite.TrustStatus.BLOCKED, SourceSite.TrustStatus.SUSPENDED):
                continue
            if not source_site.is_search_eligible:
                continue

        start = time.monotonic()
        try:
            result: AdapterResult = adapter.search(query_text, timeout_seconds=timeout_seconds)
        except TimeoutError as exc:
            result = AdapterResult(
                source_site_id=adapter.site_id,
                query_text=query_text,
                status="timeout",
                offers=[],
                error_message=str(exc),
            )
        except Exception as exc:
            result = AdapterResult(
                source_site_id=adapter.site_id,
                query_text=query_text,
                status="error",
                offers=[],
                error_message=str(exc),
            )
        response_ms = int((time.monotonic() - start) * 1000)

        adapters_queried.append(adapter.site_id)

        exec_repo.create(
            search_job=job,
            source_site=source_site,
            query_text=query_text,
            status=result.status,
            results_count=len(result.offers),
            error_message=result.error_message,
            response_ms=response_ms,
        )

        if result.status == "timeout":
            timeout_count += 1
            errors.append(f"{adapter.site_id}: {result.error_message or result.status}")
            continue

        if result.status == "error":
            errors.append(f"{adapter.site_id}: {result.error_message or result.status}")
            continue

        for offer_data in result.offers:
            try:
                offer_repo.create(
                    canonical_item=canonical_item,
                    source_site=source_site,
                    search_job=job,
                    product_title=offer_data.product_title,
                    seller_name=offer_data.seller_name,
                    item_price=offer_data.item_price,
                    shipping_cost=offer_data.shipping_cost,
                    total_price=offer_data.total_price,
                    currency=offer_data.currency,
                    product_url=offer_data.product_url,
                    condition=offer_data.condition,
                    confidence=offer_data.confidence,
                )
                offers_found += 1
            except Exception as exc:
                errors.append(f"{adapter.site_id} offer persist error: {exc}")

    # Determine final job status
    if offers_found > 0 and not errors:
        final_status = SearchJob.Status.COMPLETE
    elif offers_found > 0 and errors:
        final_status = SearchJob.Status.PARTIAL
    elif errors and offers_found == 0:
        final_status = SearchJob.Status.FAILED
    else:
        # No offers, no errors = no results found
        final_status = SearchJob.Status.COMPLETE

    job.queried_sources_count = len(adapters_queried)
    job.error_count = len(errors)
    job.timeout_count = timeout_count
    job.save(update_fields=["queried_sources_count", "error_count", "timeout_count"])
    job_repo.update_status(job, final_status)

    # Transition WorkflowState: brand approval needed if <3 offers
    if offers_found == 0:
        wf_repo.transition(
            canonical_item,
            "brand_approval",
            state_data={"reason": "no_offers_found", "query": query_text},
        )
    else:
        wf_repo.transition(
            canonical_item,
            "draft",
            state_data={"offers_found": offers_found, "query": query_text},
        )

    return {
        "search_job_id": job.pk,
        "status": final_status,
        "offers_found": offers_found,
        "adapters_queried": adapters_queried,
        "errors": errors,
        "query": query_text,
    }


def execute_search_for_batch(
    canonical_items: list[CanonicalItem],
    timeout_seconds: float = 10.0,
) -> list[dict]:
    """Run execute_search_for_item for each item in a batch. Returns list of summaries."""
    return [
        execute_search_for_item(item, timeout_seconds=timeout_seconds)
        for item in canonical_items
        if item.search_ready
    ]


def _get_source_site(site_id: str) -> SourceSite | None:
    """Look up a SourceSite by site_id; returns None if not found (non-fatal)."""
    try:
        return SourceSite.objects.get(site_id=site_id)
    except SourceSite.DoesNotExist:
        return None
