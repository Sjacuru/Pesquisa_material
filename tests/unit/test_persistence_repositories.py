"""
Unit tests for persistence.repositories

Covers:
  - happy-path create/query for each repository
  - one failure-path per repository (not found / invalid state / constraint violation)
"""

from datetime import datetime, timezone as tz

from django.db import IntegrityError
from django.test import TestCase

from persistence.models import SearchJob, SourceSite, UploadBatch
from persistence.repositories import (
    CanonicalItemRepository,
    SearchJobRepository,
    SourceSiteRepository,
    UploadBatchRepository,
    VersionEventRepository,
    persist_stage_a_result,
)


# ---------------------------------------------------------------------------
# UploadBatchRepository
# ---------------------------------------------------------------------------

class UploadBatchRepositoryTests(TestCase):

    def setUp(self):
        self.repo = UploadBatchRepository()

    # happy path
    def test_create_returns_upload_batch(self):
        batch = self.repo.create("lista_2026.pdf")
        self.assertIsInstance(batch, UploadBatch)
        self.assertEqual(batch.source_filename, "lista_2026.pdf")
        self.assertIsNotNone(batch.public_id)

    def test_get_by_public_id_returns_correct_batch(self):
        batch = self.repo.create("lista.pdf")
        found = self.repo.get_by_public_id(batch.public_id)
        self.assertEqual(found.pk, batch.pk)

    # failure path
    def test_get_by_public_id_returns_none_when_not_found(self):
        import uuid
        result = self.repo.get_by_public_id(uuid.uuid4())
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# CanonicalItemRepository
# ---------------------------------------------------------------------------

class CanonicalItemRepositoryTests(TestCase):

    def setUp(self):
        self.repo = CanonicalItemRepository()
        self.batch = UploadBatchRepository().create("lista.pdf")

    # happy path
    def test_create_item(self):
        item = self.repo.create(
            upload_batch=self.batch,
            item_code="LIV-001",
            name="Caderno 10 matérias",
            category="Escolar",
            quantity=2,
            unit="un",
        )
        self.assertEqual(item.item_code, "LIV-001")
        self.assertFalse(item.search_ready)

    def test_list_by_batch_returns_only_batch_items(self):
        self.repo.create(self.batch, "A", "Item A", "Cat", 1, "un")
        self.repo.create(self.batch, "B", "Item B", "Cat", 1, "un")
        other_batch = UploadBatchRepository().create("other.pdf")
        self.repo.create(other_batch, "C", "Item C", "Cat", 1, "un")

        items = list(self.repo.list_by_batch(self.batch))
        self.assertEqual(len(items), 2)
        codes = {i.item_code for i in items}
        self.assertIn("A", codes)
        self.assertIn("B", codes)

    # failure path
    def test_duplicate_item_code_in_same_batch_raises(self):
        self.repo.create(self.batch, "DUP", "Item", "Cat", 1, "un")
        with self.assertRaises(IntegrityError):
            self.repo.create(self.batch, "DUP", "Item copy", "Cat", 1, "un")


# ---------------------------------------------------------------------------
# SourceSiteRepository
# ---------------------------------------------------------------------------

class SourceSiteRepositoryTests(TestCase):

    def setUp(self):
        self.repo = SourceSiteRepository()

    # happy path – create then upsert
    def test_upsert_creates_new_site(self):
        site = self.repo.upsert(
            site_id="livraria.com",
            label="Livraria XP",
            trust_status=SourceSite.TrustStatus.ALLOWED,
            is_search_eligible=True,
        )
        self.assertEqual(site.site_id, "livraria.com")
        self.assertTrue(site.is_search_eligible)

    def test_upsert_updates_existing_site(self):
        self.repo.upsert("livraria.com", "Old Label", SourceSite.TrustStatus.ALLOWED, True)
        updated = self.repo.upsert("livraria.com", "New Label", SourceSite.TrustStatus.ALLOWED, True)
        self.assertEqual(updated.label, "New Label")
        self.assertEqual(SourceSite.objects.filter(site_id="livraria.com").count(), 1)

    def test_list_eligible_excludes_blocked(self):
        self.repo.upsert("ok.com", "OK", SourceSite.TrustStatus.ALLOWED, True)
        self.repo.upsert("blocked.com", "Blocked", SourceSite.TrustStatus.BLOCKED, True)
        self.repo.upsert("ineligible.com", "Ineligible", SourceSite.TrustStatus.ALLOWED, False)

        eligible = list(self.repo.list_eligible())
        ids = {s.site_id for s in eligible}
        self.assertIn("ok.com", ids)
        self.assertNotIn("blocked.com", ids)
        self.assertNotIn("ineligible.com", ids)

    # failure path
    def test_list_eligible_empty_when_no_eligible_sites(self):
        # Mark all sites as ineligible/blocked — safer than delete under TestCase savepoints
        SourceSite.objects.update(is_search_eligible=False)
        self.assertEqual(list(self.repo.list_eligible()), [])


# ---------------------------------------------------------------------------
# SearchJobRepository
# ---------------------------------------------------------------------------

class SearchJobRepositoryTests(TestCase):

    def setUp(self):
        self.repo = SearchJobRepository()

    # happy path
    def test_create_job_without_item(self):
        job = self.repo.create()
        self.assertEqual(job.status, SearchJob.Status.PENDING)
        self.assertIsNone(job.canonical_item)

    def test_update_status(self):
        job = self.repo.create()
        updated = self.repo.update_status(job, SearchJob.Status.RUNNING)
        updated.refresh_from_db()
        self.assertEqual(updated.status, SearchJob.Status.RUNNING)

    def test_update_status_with_rejection_reason(self):
        job = self.repo.create()
        updated = self.repo.update_status(job, SearchJob.Status.FAILED, rejection_reason="timeout")
        updated.refresh_from_db()
        self.assertEqual(updated.rejection_reason, "timeout")

    # failure path
    def test_update_status_with_invalid_choice_does_not_raise_at_db_level(self):
        # Django does not enforce TextChoices at DB level; the value is stored as-is.
        # This test documents that behaviour explicitly.
        job = self.repo.create()
        updated = self.repo.update_status(job, "not_a_real_status")
        updated.refresh_from_db()
        self.assertEqual(updated.status, "not_a_real_status")


# ---------------------------------------------------------------------------
# VersionEventRepository
# ---------------------------------------------------------------------------

class VersionEventRepositoryTests(TestCase):

    def setUp(self):
        self.repo = VersionEventRepository()
        self.ts = datetime(2026, 3, 1, tzinfo=tz.utc)

    # happy path
    def test_append_event(self):
        event = self.repo.append(
            material_id="MAT-001",
            version_number=1,
            field_name="price",
            old_value=None,
            new_value={"amount": 12.5},
            timestamp=self.ts,
            actor_id="user-1",
        )
        self.assertEqual(event.material_id, "MAT-001")
        self.assertEqual(event.new_value, {"amount": 12.5})

    def test_list_material_history_ordered(self):
        self.repo.append("MAT-002", 2, "price", None, {"amount": 2.0}, self.ts)
        self.repo.append("MAT-002", 1, "price", None, {"amount": 1.0}, self.ts)
        history = list(self.repo.list_material_history("MAT-002"))
        self.assertEqual(history[0].version_number, 1)
        self.assertEqual(history[1].version_number, 2)

    def test_list_material_history_empty_for_unknown_material(self):
        result = list(self.repo.list_material_history("UNKNOWN"))
        self.assertEqual(result, [])

    # failure path
    def test_duplicate_material_version_raises(self):
        kwargs = dict(
            material_id="MAT-003",
            version_number=1,
            field_name="price",
            old_value=None,
            new_value={"amount": 5.0},
            timestamp=self.ts,
        )
        self.repo.append(**kwargs)
        with self.assertRaises(IntegrityError):
            self.repo.append(**kwargs)


# ---------------------------------------------------------------------------
# Stage A Persistence Flow
# ---------------------------------------------------------------------------

class StageAResultPersistenceTests(TestCase):

    def test_persist_stage_a_native_result_creates_batch_and_items(self):
        stage_a_result = {
            "route_mode": "native_text",
            "detected_type": "pdf",
            "extracted_items": [
                {
                    "line_index": 0,
                    "requires_human_review": False,
                    "fields": {
                        "name": {"value": "Livro de Matemática"},
                        "category": {"value": "book"},
                        "quantity": {"value": "2 un"},
                        "isbn": {"value": "978-0-306-40615-7"},
                    },
                }
            ],
        }

        result = persist_stage_a_result(
            stage_a_result=stage_a_result,
            source_filename="lista_2026.pdf",
        )

        batch = result["upload_batch"]
        items = result["canonical_items"]

        self.assertEqual(batch.source_filename, "lista_2026.pdf")
        self.assertEqual(batch.status, UploadBatch.Status.EXTRACTED)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].name, "Livro de Matemática")
        self.assertTrue(items[0].search_ready)
        self.assertEqual(items[0].isbn_normalized, "9780306406157")

    def test_persist_stage_a_review_required_sets_batch_status(self):
        stage_a_result = {
            "route_mode": "review_required",
            "detected_type": "unknown",
            "extracted_items": [
                {
                    "line_index": -1,
                    "line_text": "",
                    "requires_human_review": True,
                    "gate_reason": "file_type_uncertain",
                }
            ],
        }

        result = persist_stage_a_result(
            stage_a_result=stage_a_result,
            source_filename="arquivo.bin",
        )

        batch = result["upload_batch"]
        items = result["canonical_items"]

        self.assertEqual(batch.status, UploadBatch.Status.REVIEW_REQUIRED)
        self.assertEqual(len(items), 1)
        self.assertFalse(items[0].search_ready)
