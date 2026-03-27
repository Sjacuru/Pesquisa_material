# FILE: source_adapters/mercadolivre_adapter.py
# MODULE: Mercado Livre Adapter
# INTEGRATION: Official public REST API — no auth required for product searches
# API BASE: https://api.mercadolibre.com/sites/MLB/search
# CATEGORIES: book, dictionary, apostila, notebook, general supplies
from __future__ import annotations

import time
from decimal import Decimal

import httpx

from source_adapters.base import AdapterResult, BaseSourceAdapter, OfferResult

_ML_SEARCH_URL = "https://api.mercadolibre.com/sites/MLB/search"
_DEFAULT_LIMIT = 10
_USER_AGENT = "PesquisaMaterial/1.0 (school-list-price-finder)"


class MercadoLivreAdapter(BaseSourceAdapter):
	site_id = "ml_br"
	label = "Mercado Livre"
	categories = ["book", "dictionary", "apostila", "notebook", "general supplies"]

	def search(self, query: str, timeout_seconds: float = 10.0) -> AdapterResult:
		start = time.monotonic()
		try:
			response = httpx.get(
				_ML_SEARCH_URL,
				params={"q": query, "limit": _DEFAULT_LIMIT},
				timeout=timeout_seconds,
				headers={"User-Agent": _USER_AGENT},
				follow_redirects=True,
			)
			response.raise_for_status()
			data = response.json()
		except httpx.TimeoutException:
			return AdapterResult(
				source_site_id=self.site_id,
				query_text=query,
				status="timeout",
				error_message="Request timed out",
				response_ms=self._elapsed_ms(start),
			)
		except Exception as exc:
			return AdapterResult(
				source_site_id=self.site_id,
				query_text=query,
				status="error",
				error_message=str(exc),
				response_ms=self._elapsed_ms(start),
			)

		response_ms = self._elapsed_ms(start)
		results = data.get("results") or []

		if not results:
			return AdapterResult(
				source_site_id=self.site_id,
				query_text=query,
				status="empty",
				response_ms=response_ms,
			)

		offers: list[OfferResult] = []
		for item in results:
			try:
				item_price = Decimal(str(item.get("price") or 0))
				free_shipping = bool((item.get("shipping") or {}).get("free_shipping", False))
				shipping_cost = Decimal("0") if free_shipping else None
				# When shipping unknown, use item_price as total (conservative lower bound)
				total_price = item_price + (shipping_cost if shipping_cost is not None else Decimal("0"))

				offers.append(OfferResult(
					source_site_id=self.site_id,
					product_title=str(item.get("title") or ""),
					seller_name=str((item.get("seller") or {}).get("nickname") or ""),
					item_price=item_price,
					shipping_cost=shipping_cost,
					total_price=total_price,
					currency=str(item.get("currency_id") or "BRL"),
					product_url=str(item.get("permalink") or ""),
					condition=str(item.get("condition") or "unknown"),
					confidence=1.0,
					raw_data=item,
				))
			except Exception:
				# Skip malformed individual results silently
				continue

		return AdapterResult(
			source_site_id=self.site_id,
			query_text=query,
			status="ok" if offers else "empty",
			offers=offers,
			response_ms=response_ms,
		)
