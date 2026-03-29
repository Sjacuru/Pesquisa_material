# FILE: search_ranking/search_executor.py
# MODULE: Real Search Executor
# RESPONSIBILITY: Run real adapter searches for a CanonicalItem, persist Offer rows,
#                 log SearchExecution records, and update SearchJob state.
# DEPENDS_ON: source_adapters/, persistence/repositories.py, search_ranking/query_orchestrator.py
from __future__ import annotations

import logging
import os
import re
import time
import unicodedata
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


logger = logging.getLogger(__name__)


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _build_query_candidates(item_dict: dict) -> list[str]:
    name = str(item_dict.get("name") or "").strip()
    isbn = str(item_dict.get("isbn_normalized") or "").strip()
    category = str(item_dict.get("category") or "").strip().lower()

    isbn_candidates: list[str] = []
    name_candidates: list[str] = []

    def _push(buffer: list[str], candidate: str) -> None:
        value = str(candidate or "").strip()
        if value and value not in buffer:
            buffer.append(value)

    if isbn:
        _push(isbn_candidates, isbn)

    if name:
        _push(name_candidates, name)

    if category in ("book", "dictionary") and name:
        name_head = re.split(r"\s+[-|]\s+", name, maxsplit=1)[0].strip()
        _push(name_candidates, name_head)

    name_ascii = _strip_accents(name)
    if name_ascii and name_ascii != name:
        _push(name_candidates, name_ascii)

    # Explicit strategy requested by user: ISBN first, product-name second.
    candidates = isbn_candidates + name_candidates
    return candidates or [str(build_query(item_dict) or "").strip()]


def _tokenize(text: str) -> list[str]:
    normalized = _strip_accents(str(text or "").lower())
    return re.findall(r"[a-z0-9]{3,}", normalized)


def _relevance_debug_enabled() -> bool:
    return os.getenv("SEARCH_RELEVANCE_DEBUG", "0").strip().lower() in {"1", "true", "yes", "on"}


def _offer_relevance_decision(offer_title: str, query_text: str, isbn: str, item_name: str) -> tuple[bool, str, dict]:
    offer_title = str(offer_title or "")
    query_text = str(query_text or "")
    isbn = str(isbn or "")

    offer_compact = re.sub(r"\D", "", offer_title)
    isbn_compact = re.sub(r"\D", "", isbn)
    query_compact = re.sub(r"\D", "", query_text)

    offer_tokens = set(_tokenize(offer_title))
    query_tokens = set(_tokenize(query_text))
    item_tokens = set(_tokenize(item_name))
    query_overlap = len(offer_tokens & query_tokens)
    item_overlap = len(offer_tokens & item_tokens)
    long_query_tokens = {t for t in query_tokens if len(t) >= 6}
    long_overlap = len(offer_tokens & long_query_tokens)

    debug_meta = {
        "query_overlap": query_overlap,
        "item_overlap": item_overlap,
        "long_overlap": long_overlap,
        "offer_tokens": sorted(offer_tokens),
        "query_tokens": sorted(query_tokens),
        "item_tokens": sorted(item_tokens),
    }

    if isbn_compact and query_compact == isbn_compact and isbn_compact in offer_compact:
        return True, "isbn_exact_match", debug_meta

    if not offer_tokens:
        return False, "no_offer_tokens", debug_meta

    if query_tokens and query_overlap >= 2:
        return True, "query_token_overlap>=2", debug_meta
    if item_tokens and item_overlap >= 2:
        return True, "item_token_overlap>=2", debug_meta

    # Accept a single overlap only for long, specific tokens.
    if long_query_tokens and long_overlap >= 1:
        return True, "long_query_token_overlap", debug_meta

    return False, "insufficient_overlap", debug_meta


def _is_offer_relevant(offer_title: str, query_text: str, isbn: str, item_name: str) -> bool:
    is_relevant, _, _ = _offer_relevance_decision(
        offer_title=offer_title,
        query_text=query_text,
        isbn=isbn,
        item_name=item_name,
    )
    return is_relevant


def _run_adapter_with_fallback(adapter, query_candidates: list[str], timeout_seconds: float) -> tuple[AdapterResult, list[str]]:
    attempted_queries: list[str] = []
    last_result = AdapterResult(
        source_site_id=adapter.site_id,
        query_text=query_candidates[0] if query_candidates else "",
        status="empty",
        offers=[],
        error_message="",
        response_ms=0,
    )

    for query_text in query_candidates:
        attempted_queries.append(query_text)
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

        if result.response_ms is None:
            result.response_ms = int((time.monotonic() - start) * 1000)
        last_result = result

        if result.status == "ok" and result.offers:
            return result, attempted_queries
        if result.status == "timeout":
            return result, attempted_queries
        if result.status == "error":
            lower_error = str(result.error_message or "").lower()
            is_hard_block = any(marker in lower_error for marker in ["403", "503", "forbidden", "captcha", "bot"]) 
            if is_hard_block:
                return result, attempted_queries

    return last_result, attempted_queries


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
    query_candidates = _build_query_candidates(item_dict)
    primary_query = query_candidates[0]
    adapters = get_adapters_for_category(canonical_item.category)

    offers_found = 0
    errors: list[str] = []
    adapters_queried: list[str] = []
    timeout_count = 0
    debug_relevance = _relevance_debug_enabled()

    for adapter in adapters:
        source_site = _get_source_site(adapter.site_id)
        if source_site is not None:
            if source_site.trust_status in (SourceSite.TrustStatus.BLOCKED, SourceSite.TrustStatus.SUSPENDED):
                continue
            if not source_site.is_search_eligible:
                continue

        result, attempted_queries = _run_adapter_with_fallback(
            adapter=adapter,
            query_candidates=query_candidates,
            timeout_seconds=timeout_seconds,
        )

        adapters_queried.append(adapter.site_id)

        exec_repo.create(
            search_job=job,
            source_site=source_site,
            query_text=" | ".join(attempted_queries)[:512],
            status=result.status,
            results_count=len(result.offers),
            error_message=result.error_message,
            response_ms=result.response_ms,
        )

        if result.status == "timeout":
            timeout_count += 1
            errors.append(f"{adapter.site_id}: {result.error_message or result.status} (query={result.query_text})")
            continue

        if result.status == "error":
            errors.append(f"{adapter.site_id}: {result.error_message or result.status} (query={result.query_text})")
            continue

        for offer_data in result.offers:
            try:
                is_relevant, reason, debug_meta = _offer_relevance_decision(
                    offer_title=offer_data.product_title,
                    query_text=result.query_text,
                    isbn=canonical_item.isbn_normalized,
                    item_name=canonical_item.name,
                )
                if debug_relevance:
                    logger.info(
                        "[relevance] site=%s category=%s query=%r decision=%s reason=%s title=%r overlaps(q=%s,item=%s,long=%s)",
                        adapter.site_id,
                        str(canonical_item.category or ""),
                        result.query_text,
                        "accept" if is_relevant else "reject",
                        reason,
                        offer_data.product_title,
                        debug_meta["query_overlap"],
                        debug_meta["item_overlap"],
                        debug_meta["long_overlap"],
                    )
                if not is_relevant:
                    continue
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
            state_data={"reason": "no_offers_found", "query": primary_query},
        )
    else:
        wf_repo.transition(
            canonical_item,
            "draft",
            state_data={"offers_found": offers_found, "query": primary_query},
        )

    return {
        "search_job_id": job.pk,
        "status": final_status,
        "offers_found": offers_found,
        "adapters_queried": adapters_queried,
        "errors": errors,
        "query": primary_query,
        "query_candidates": query_candidates,
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
