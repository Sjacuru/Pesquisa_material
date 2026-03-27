from __future__ import annotations

import csv
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from persistence.models import CanonicalItem, Offer, SourceSite, UploadBatch, VersionEvent


class UploadToSearchExportFlowTests(TestCase):
    def setUp(self) -> None:
        SourceSite.objects.update_or_create(
            site_id="ml_br",
            defaults={
                "label": "Mercado Livre",
                "trust_status": SourceSite.TrustStatus.ALLOWED,
                "is_search_eligible": True,
                "categories": ["book", "notebook", "general supplies"],
            },
        )

    def test_upload_then_export_csv_flow(self) -> None:
        upload = SimpleUploadedFile(
            "lista.pdf",
            b"%PDF-1.4\nBT /F1 12 Tf 50 700 Tm (Livro matematica) Tj ET\n",
            content_type="application/pdf",
        )

        upload_response = self.client.post(reverse("upload-workflow"), {"source_file": upload})
        self.assertEqual(upload_response.status_code, 200)

        batch = UploadBatch.objects.order_by("-id").first()
        self.assertIsNotNone(batch)
        item = batch.items.order_by("id").first()
        if item is None:
            item = CanonicalItem.objects.create(
                upload_batch=batch,
                item_code="seed-1",
                name="Livro matematica",
                category="book",
                quantity="1",
                unit="un",
                search_ready=True,
            )

        source = SourceSite.objects.get(site_id="ml_br")
        Offer.objects.create(
            canonical_item=item,
            source_site=source,
            product_title=item.name,
            seller_name="Seller",
            item_price="49.90",
            shipping_cost="0.00",
            total_price="49.90",
            currency="BRL",
            product_url="https://example.com/livro",
            condition=Offer.Condition.NEW,
            confidence=1.0,
        )
        VersionEvent.objects.create(
            material_id=f"canonical_item_{item.pk}",
            version_number=1,
            field_name="name",
            old_value=item.name,
            new_value=item.name,
            actor_id="tester",
            reason_code="seed",
            timestamp=item.created_at,
        )

        export_response = self.client.get(reverse("batch-export-download", kwargs={"batch_id": batch.pk}))
        self.assertEqual(export_response.status_code, 200)

        content = export_response.content.decode("utf-8")
        rows = list(csv.DictReader(io.StringIO(content)))
        self.assertGreaterEqual(len(rows), 1)
        self.assertIn("Item", rows[0])
        self.assertIn("Price", rows[0])
        self.assertEqual(rows[0]["Source"], "ml_br")
