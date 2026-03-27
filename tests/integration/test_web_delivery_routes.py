from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from django.urls import resolve, reverse

from web.views import exclusivity_demo, exclusivity_review, health, upload_workflow


class TestWebDeliveryRoutes(SimpleTestCase):
	def test_named_routes_map_to_intended_handlers(self) -> None:
		assert resolve(reverse("health")).func is health
		assert resolve(reverse("upload-workflow")).func is upload_workflow
		assert resolve(reverse("exclusivity-demo")).func is exclusivity_demo
		assert resolve(reverse("exclusivity-review")).func is exclusivity_review

	def test_delivery_endpoints_respond_successfully(self) -> None:
		health_response = self.client.get(reverse("health"))
		upload_response = self.client.get(reverse("upload-workflow"))
		demo_response = self.client.get(reverse("exclusivity-demo"))
		review_response = self.client.get(reverse("exclusivity-review"))

		assert health_response.status_code == 200
		assert upload_response.status_code == 200
		assert demo_response.status_code == 200
		assert review_response.status_code == 200

	@patch("web.views.process_stage_a_ingestion")
	def test_upload_workflow_post_processes_uploaded_file(self, process_stage_a_ingestion_mock) -> None:
		process_stage_a_ingestion_mock.return_value = {
			"route_mode": "native_text",
			"detected_type": "pdf",
			"extracted_items": [
				{
					"line_index": 0,
					"fields": {
						"name": {"value": "Caderno"},
						"category": {"value": "notebook"},
						"isbn": {"value": ""},
					},
					"requires_human_review": False,
				}
			],
			"persistence": {
				"upload_batch_id": 123,
				"status": "extracted",
				"canonical_item_count": 1,
			},
		}

		upload = SimpleUploadedFile(
			"lista.pdf",
			b"%PDF-1.4 test",
			content_type="application/pdf",
		)
		response = self.client.post(reverse("upload-workflow"), {"source_file": upload})

		assert response.status_code == 200
		assert process_stage_a_ingestion_mock.call_count == 1
		kwargs = process_stage_a_ingestion_mock.call_args.kwargs
		assert kwargs["persist_to_db"] is True
		assert kwargs["include_downstream_validation"] is True
		assert kwargs["uploaded_document"]["filename"] == "lista.pdf"
		assert kwargs["uploaded_document"]["file_bytes"].startswith(b"%PDF")
		assert b"Batch ID:" in response.content