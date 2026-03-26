"""
Unit tests for persistence.models

Covers:
  - required-field / blank constraints
  - uniqueness constraints (UniqueConstraint on CanonicalItem and VersionEvent)
  - default values
"""

from datetime import timezone as tz, datetime

from django.db import IntegrityError
from django.test import TestCase

from persistence.models import (
    CanonicalItem,
    SearchJob,
    SourceSite,
    UploadBatch,
    VersionEvent,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _batch(**kwargs):
    defaults = {"source_filename": "lista.pdf"}
    defaults.update(kwargs)
    return UploadBatch.objects.create(**defaults)


def _item(batch, item_code="IT-001", **kwargs):
    defaults = {"name": "Caneta azul", "category": "Escolar", "quantity": 1, "unit": "un"}
    defaults.update(kwargs)
    return CanonicalItem.objects.create(upload_batch=batch, item_code=item_code, **defaults)


# ---------------------------------------------------------------------------
# UploadBatch
# ---------------------------------------------------------------------------

class UploadBatchModelTests(TestCase):

    def test_create_with_required_fields(self):
        batch = _batch()
        self.assertIsNotNone(batch.pk)
        self.assertIsNotNone(batch.public_id)

    def test_default_status_is_uploaded(self):
        batch = _batch()
        self.assertEqual(batch.status, UploadBatch.Status.UPLOADED)

    def test_source_filename_is_required(self):
        with self.assertRaises(IntegrityError):
            UploadBatch.objects.create(source_filename=None)

    def test_public_id_is_unique(self):
        batch1 = _batch()
        with self.assertRaises(IntegrityError):
            UploadBatch.objects.create(
                source_filename="other.pdf",
                public_id=batch1.public_id,
            )


# ---------------------------------------------------------------------------
# CanonicalItem
# ---------------------------------------------------------------------------

class CanonicalItemModelTests(TestCase):

    def setUp(self):
        self.batch = _batch()

    def test_create_canonical_item(self):
        item = _item(self.batch)
        self.assertIsNotNone(item.pk)

    def test_uniqueness_batch_item_code(self):
        _item(self.batch, item_code="DUP-001")
        with self.assertRaises(IntegrityError):
            _item(self.batch, item_code="DUP-001")

    def test_same_item_code_in_different_batches_is_allowed(self):
        other_batch = _batch(source_filename="another.pdf")
        item1 = _item(self.batch, item_code="SHARED")
        item2 = _item(other_batch, item_code="SHARED")
        self.assertNotEqual(item1.pk, item2.pk)

    def test_default_search_ready_is_false(self):
        item = _item(self.batch)
        self.assertFalse(item.search_ready)

    def test_cascade_delete_removes_items(self):
        _item(self.batch)
        self.batch.delete()
        self.assertEqual(CanonicalItem.objects.count(), 0)


# ---------------------------------------------------------------------------
# SourceSite
# ---------------------------------------------------------------------------

class SourceSiteModelTests(TestCase):

    def test_create_source_site(self):
        site = SourceSite.objects.create(site_id="amazon.com.br", label="Amazon BR")
        self.assertIsNotNone(site.pk)

    def test_site_id_uniqueness(self):
        SourceSite.objects.create(site_id="amazon.com.br", label="Amazon BR")
        with self.assertRaises(IntegrityError):
            SourceSite.objects.create(site_id="amazon.com.br", label="Duplicate")

    def test_default_trust_status_is_review_required(self):
        site = SourceSite.objects.create(site_id="new-site.com", label="New")
        self.assertEqual(site.trust_status, SourceSite.TrustStatus.REVIEW_REQUIRED)

    def test_default_is_not_search_eligible(self):
        site = SourceSite.objects.create(site_id="new-site.com", label="New")
        self.assertFalse(site.is_search_eligible)


# ---------------------------------------------------------------------------
# SearchJob
# ---------------------------------------------------------------------------

class SearchJobModelTests(TestCase):

    def test_create_without_canonical_item(self):
        job = SearchJob.objects.create()
        self.assertIsNone(job.canonical_item)
        self.assertEqual(job.status, SearchJob.Status.PENDING)

    def test_create_with_canonical_item(self):
        batch = _batch()
        item = _item(batch)
        job = SearchJob.objects.create(canonical_item=item)
        self.assertEqual(job.canonical_item_id, item.pk)

    def test_deleting_item_sets_job_canonical_item_null(self):
        batch = _batch()
        item = _item(batch)
        job = SearchJob.objects.create(canonical_item=item)
        item.delete()
        job.refresh_from_db()
        self.assertIsNone(job.canonical_item)


# ---------------------------------------------------------------------------
# VersionEvent
# ---------------------------------------------------------------------------

class VersionEventModelTests(TestCase):

    def _ts(self):
        return datetime(2026, 1, 1, tzinfo=tz.utc)

    def test_create_version_event(self):
        event = VersionEvent.objects.create(
            material_id="MAT-001",
            version_number=1,
            field_name="price",
            old_value=None,
            new_value={"amount": 9.99},
            timestamp=self._ts(),
        )
        self.assertIsNotNone(event.pk)

    def test_uniqueness_material_id_version_number(self):
        kwargs = dict(
            material_id="MAT-002",
            version_number=1,
            field_name="price",
            old_value=None,
            new_value={"amount": 5.0},
            timestamp=self._ts(),
        )
        VersionEvent.objects.create(**kwargs)
        with self.assertRaises(IntegrityError):
            VersionEvent.objects.create(**kwargs)

    def test_different_versions_same_material_allowed(self):
        common = dict(material_id="MAT-003", field_name="price", old_value=None, timestamp=self._ts())
        VersionEvent.objects.create(**common, version_number=1, new_value={"amount": 1.0})
        VersionEvent.objects.create(**common, version_number=2, new_value={"amount": 2.0})
        self.assertEqual(VersionEvent.objects.filter(material_id="MAT-003").count(), 2)
