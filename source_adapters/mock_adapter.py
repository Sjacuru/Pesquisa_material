# FILE: source_adapters/mock_adapter.py
# MODULE: Mock Adapter for Testing
# RESPONSIBILITY: Provide fake search results for testing without accessing real websites
from __future__ import annotations

from decimal import Decimal
from source_adapters.base import AdapterResult, BaseSourceAdapter, OfferResult


class MockAdapter(BaseSourceAdapter):
	"""Mock adapter that returns fake results for testing."""
	site_id = "mock_test"
	label = "Mock Test (Development)"
	categories = ["book", "dictionary", "apostila", "notebook", "general supplies"]

	def search(self, query: str, timeout_seconds: float = 10.0) -> AdapterResult:
		"""Return fake results based on query."""
		# Simulate finding some results
		offers = [
			OfferResult(
				source_site_id=self.site_id,
				product_title=f"{query} - Capa Dura",
				seller_name="Livraria Virtual Mock",
				item_price=Decimal("45.90"),
				shipping_cost=Decimal("0"),
				total_price=Decimal("45.90"),
				currency="BRL",
				product_url="https://example.com/product1",
				condition="new",
				confidence=0.95,
			),
			OfferResult(
				source_site_id=self.site_id,
				product_title=f"{query} - Edição Econômica",
				seller_name="Vendedor Mock 2",
				item_price=Decimal("38.50"),
				shipping_cost=Decimal("5.00"),
				total_price=Decimal("43.50"),
				currency="BRL",
				product_url="https://example.com/product2",
				condition="new",
				confidence=0.88,
			),
		]

		return AdapterResult(
			source_site_id=self.site_id,
			query_text=query,
			status="ok",
			offers=offers,
			response_ms=150,
		)
