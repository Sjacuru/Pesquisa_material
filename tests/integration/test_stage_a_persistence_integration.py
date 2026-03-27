from django.test import TestCase

from intake_canonicalization.stage_a_ingestion_pipeline import process_stage_a_ingestion
from persistence.models import CanonicalItem, UploadBatch


def _category_matrix() -> dict[str, dict[str, str]]:
	return {
		"book": {"id": "book"},
		"general supplies": {"id": "general supplies"},
	}


class StageAPersistenceIntegrationTests(TestCase):
	def test_process_stage_a_can_persist_native_results(self) -> None:
		result = process_stage_a_ingestion(
			uploaded_document={
				"filename": "lista.pdf",
				"content_type": "application/pdf",
				"text": "Livro ISBN 9780306406157",
				"file_bytes": b"%PDF" + b"x" * 150000,
			},
			category_matrix_reference=_category_matrix(),
			persist_to_db=True,
		)

		self.assertIn("persistence", result)
		self.assertEqual(UploadBatch.objects.count(), 1)
		self.assertGreaterEqual(CanonicalItem.objects.count(), 1)

		batch = UploadBatch.objects.first()
		self.assertEqual(batch.source_filename, "lista.pdf")
		self.assertIn(batch.status, [UploadBatch.Status.EXTRACTED, UploadBatch.Status.REVIEW_REQUIRED])

	def test_process_stage_a_can_persist_review_required_results(self) -> None:
		result = process_stage_a_ingestion(
			uploaded_document={
				"filename": "unknown.bin",
				"content_type": "application/octet-stream",
				"file_bytes": b"NOT_A_KNOWN_TYPE",
			},
			category_matrix_reference=_category_matrix(),
			persist_to_db=True,
		)

		self.assertIn("persistence", result)
		batch = UploadBatch.objects.get(id=result["persistence"]["upload_batch_id"])
		self.assertEqual(batch.status, UploadBatch.Status.REVIEW_REQUIRED)
		self.assertEqual(batch.items.count(), 1)
