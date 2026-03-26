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