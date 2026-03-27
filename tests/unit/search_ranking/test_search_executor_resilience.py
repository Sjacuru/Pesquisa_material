from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from persistence.models import CanonicalItem, Offer, SearchExecution, SearchJob, SourceSite, UploadBatch
from search_ranking.search_executor import execute_search_for_item
from source_adapters.base import AdapterResult, OfferResult


class SearchExecutorResilienceTests(TestCase):
    def setUp(self) -> None:
        self.batch = UploadBatch.objects.create(source_filename="resilience.pdf", status=UploadBatch.Status.EXTRACTED)
        self.item = CanonicalItem.objects.create(
            upload_batch=self.batch,
            item_code="item-1",
            name="Livro matematica",
            category="book",
            quantity="1",
            unit="un",
            search_ready=True,
        )
        SourceSite.objects.create(
            site_id="ok_br",
            label="OK Site",
            trust_status=SourceSite.TrustStatus.ALLOWED,
            is_search_eligible=True,
            categories=["book"],
        )
        SourceSite.objects.create(
            site_id="fail_br",
            label="Fail Site",
            trust_status=SourceSite.TrustStatus.ALLOWED,
            is_search_eligible=True,
            categories=["book"],
        )

    def test_single_adapter_failure_does_not_fail_batch(self) -> None:
        class OkAdapter:
            site_id = "ok_br"

            def search(self, query: str, timeout_seconds: float = 10.0) -> AdapterResult:
                return AdapterResult(
                    source_site_id="ok_br",
                    query_text=query,
                    status="ok",
                    offers=[
                        OfferResult(
                            source_site_id="ok_br",
                            product_title="Livro matematica",
                            seller_name="Seller",
                            item_price=Decimal("35.00"),
                            shipping_cost=Decimal("0.00"),
                            total_price=Decimal("35.00"),
                            currency="BRL",
                            product_url="https://example.com/item",
                            condition="new",
                        )
                    ],
                )

        class FailingAdapter:
            site_id = "fail_br"

            def search(self, _query: str, timeout_seconds: float = 10.0) -> AdapterResult:
                raise TimeoutError("timeout")

        with patch("search_ranking.search_executor.get_adapters_for_category", return_value=[OkAdapter(), FailingAdapter()]):
            summary = execute_search_for_item(self.item, timeout_seconds=0.01)

        self.assertEqual(summary["status"], SearchJob.Status.PARTIAL)
        self.assertEqual(summary["offers_found"], 1)
        self.assertEqual(SearchExecution.objects.count(), 2)
        self.assertEqual(Offer.objects.count(), 1)

        search_job = SearchJob.objects.get(pk=summary["search_job_id"])
        self.assertEqual(search_job.timeout_count, 1)
        self.assertGreaterEqual(search_job.error_count, 1)
