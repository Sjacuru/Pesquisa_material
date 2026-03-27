# FILE: source_adapters/kalunga_adapter.py
# MODULE: Kalunga Adapter
# INTEGRATION: HTML scraping + JSON-LD structured data
# SEARCH URL: https://www.kalunga.com.br/busca/{query}
# CATEGORIES: notebook, general supplies, apostila
# NOTE: JSON-LD is preferred; CSS selectors are fallback. Shipping not available in search results.
from __future__ import annotations

import json
import re
import time
from decimal import Decimal, InvalidOperation
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from source_adapters.base import AdapterResult, BaseSourceAdapter, OfferResult

_BASE_SEARCH_URL = "https://www.kalunga.com.br/busca/{query}"
_USER_AGENT = "PesquisaMaterial/1.0 (school-list-price-finder)"
_MAX_RESULTS = 10


def _parse_price(raw: str) -> Decimal | None:
	cleaned = re.sub(r"[^\d,.]", "", raw or "")
	if "," in cleaned and "." not in cleaned:
		cleaned = cleaned.replace(",", ".")
	elif "," in cleaned and "." in cleaned:
		cleaned = cleaned.replace(".", "").replace(",", ".")
	try:
		return Decimal(cleaned)
	except InvalidOperation:
		return None


class KalungaAdapter(BaseSourceAdapter):
	site_id = "kalunga_br"
	label = "Kalunga"
	categories = ["notebook", "general supplies", "apostila"]

	def search(self, query: str, timeout_seconds: float = 10.0) -> AdapterResult:
		start = time.monotonic()
		url = _BASE_SEARCH_URL.format(query=quote(query))

		try:
			response = httpx.get(
				url,
				timeout=timeout_seconds,
				headers={
					"User-Agent": _USER_AGENT,
					"Accept-Language": "pt-BR,pt;q=0.9",
				},
				follow_redirects=True,
			)
			response.raise_for_status()
			html = response.text
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
		offers = self._parse_results(html)

		return AdapterResult(
			source_site_id=self.site_id,
			query_text=query,
			status="ok" if offers else "empty",
			offers=offers,
			response_ms=response_ms,
		)

	def _parse_results(self, html: str) -> list[OfferResult]:
		soup = BeautifulSoup(html, "html.parser")
		offers: list[OfferResult] = []

		# Strategy 1: JSON-LD structured data (most reliable when present)
		for script_tag in soup.select('script[type="application/ld+json"]'):
			try:
				data = json.loads(script_tag.string or "")
				# May be a list or a single object
				items = data if isinstance(data, list) else [data]
				for obj in items:
					offer = self._offer_from_jsonld(obj)
					if offer:
						offers.append(offer)
					if len(offers) >= _MAX_RESULTS:
						return offers
			except (json.JSONDecodeError, AttributeError):
				continue

		if offers:
			return offers

		# Strategy 2: CSS selectors fallback
		cards = (
			soup.select(".product-item")
			or soup.select(".product-card")
			or soup.select(".shelf-item")
			or soup.select("[data-product-id]")
		)
		for card in cards[:_MAX_RESULTS]:
			try:
				title = self._extract_text(card, [
					".product-name", ".name", "h2", "h3", ".title", "[itemprop='name']"
				])
				price_raw = self._extract_text(card, [
					".preco-por", ".best-price", ".price", "[itemprop='price']",
					".product-price", ".valor", "[data-price]"
				]) or card.get("data-price") or ""

				link_tag = card.select_one("a[href]")
				product_url = ""
				if link_tag:
					href = link_tag.get("href", "")
					product_url = href if href.startswith("http") else f"https://www.kalunga.com.br{href}"

				item_price = _parse_price(price_raw)
				if item_price is None or item_price <= 0:
					continue

				offers.append(OfferResult(
					source_site_id=self.site_id,
					product_title=title,
					seller_name="Kalunga",
					item_price=item_price,
					shipping_cost=None,
					total_price=item_price,
					currency="BRL",
					product_url=product_url,
					condition="new",
					confidence=0.85,
				))
			except Exception:
				continue

		return offers

	def _offer_from_jsonld(self, obj: dict) -> OfferResult | None:
		"""Extract an OfferResult from a JSON-LD Product or ItemList object."""
		type_val = obj.get("@type", "")
		if type_val == "ItemList":
			# Not a direct product — skip (handled by iterating items)
			return None
		if type_val not in ("Product", "offer", "Offer"):
			return None

		name = obj.get("name") or obj.get("description") or ""
		url = obj.get("url") or obj.get("@id") or ""

		# Offers can be nested under "offers" key
		offer_data = obj.get("offers") or obj
		if isinstance(offer_data, list):
			offer_data = offer_data[0] if offer_data else {}

		price_raw = str(offer_data.get("price") or offer_data.get("lowPrice") or "")
		currency = str(offer_data.get("priceCurrency") or "BRL")
		offer_url = str(offer_data.get("url") or url)

		item_price = _parse_price(price_raw)
		if not item_price or item_price <= 0:
			return None

		return OfferResult(
			source_site_id=self.site_id,
			product_title=name,
			seller_name="Kalunga",
			item_price=item_price,
			shipping_cost=None,
			total_price=item_price,
			currency=currency,
			product_url=offer_url,
			condition="new",
			confidence=0.95,  # JSON-LD is more reliable
		)

	def _extract_text(self, tag, selectors: list[str]) -> str:
		for selector in selectors:
			el = tag.select_one(selector)
			if el:
				return el.get_text(strip=True)
		return ""
