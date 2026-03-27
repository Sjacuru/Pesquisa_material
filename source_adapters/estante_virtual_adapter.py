# FILE: source_adapters/estante_virtual_adapter.py
# MODULE: Estante Virtual Adapter
# INTEGRATION: HTML scraping — no public API available
# SEARCH URL: https://www.estantevirtual.com.br/busca/{query}
# ISBN URL:   https://www.estantevirtual.com.br/busca/{isbn}
# CATEGORIES: book, dictionary
# NOTE: HTML structure changes require periodic selector maintenance.
from __future__ import annotations

import re
import time
from decimal import Decimal, InvalidOperation
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from source_adapters.base import AdapterResult, BaseSourceAdapter, OfferResult

_BASE_SEARCH_URL = "https://www.estantevirtual.com.br/busca/{query}"
_USER_AGENT = "PesquisaMaterial/1.0 (school-list-price-finder)"
_MAX_RESULTS = 10


def _parse_price(raw: str) -> Decimal | None:
	"""Extract a BRL decimal price from strings like 'R$ 29,90' or '29.90'."""
	cleaned = re.sub(r"[^\d,.]", "", raw or "")
	# BR format: 29,90 → convert comma to dot
	if "," in cleaned and "." not in cleaned:
		cleaned = cleaned.replace(",", ".")
	elif "," in cleaned and "." in cleaned:
		# e.g. 1.299,90 → 1299.90
		cleaned = cleaned.replace(".", "").replace(",", ".")
	try:
		return Decimal(cleaned)
	except InvalidOperation:
		return None


class EstanteVirtualAdapter(BaseSourceAdapter):
	site_id = "ev_br"
	label = "Estante Virtual"
	categories = ["book", "dictionary"]

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
		offers = self._parse_results(html, query)

		return AdapterResult(
			source_site_id=self.site_id,
			query_text=query,
			status="ok" if offers else "empty",
			offers=offers,
			response_ms=response_ms,
		)

	def _parse_results(self, html: str, query: str) -> list[OfferResult]:
		soup = BeautifulSoup(html, "html.parser")
		offers: list[OfferResult] = []

		# Primary selectors — Estante Virtual product card layout (2024+)
		cards = (
			soup.select(".result-item")
			or soup.select(".livro")
			or soup.select("[data-testid='book-card']")
			or soup.select(".book-card")
		)

		for card in cards[:_MAX_RESULTS]:
			try:
				title = self._extract_text(card, [
					".book-title", ".titulo", "h2", "h3", ".title", "[itemprop='name']"
				])
				seller = self._extract_text(card, [
					".seller-name", ".livreiro", ".vendedor", "[itemprop='seller']"
				])
				price_raw = self._extract_text(card, [
					".preco", ".price", "[itemprop='price']", ".valor", "[data-price]"
				]) or card.get("data-price") or ""
				link_tag = card.select_one("a[href]")
				product_url = ""
				if link_tag:
					href = link_tag.get("href", "")
					product_url = href if href.startswith("http") else f"https://www.estantevirtual.com.br{href}"

				condition_raw = self._extract_text(card, [".condicao", ".condition", ".estado"]) or "used"
				condition = "used" if any(w in condition_raw.lower() for w in ["usado", "used", "semi"]) else "new"

				item_price = _parse_price(price_raw)
				if item_price is None or item_price <= 0:
					continue

				# Estante Virtual: shipping calculated at checkout — mark as unknown
				offers.append(OfferResult(
					source_site_id=self.site_id,
					product_title=title,
					seller_name=seller,
					item_price=item_price,
					shipping_cost=None,
					total_price=item_price,  # Conservative: exclude unknown shipping
					currency="BRL",
					product_url=product_url,
					condition=condition,
					confidence=0.85,  # Slightly lower: scraping + unknown shipping
				))
			except Exception:
				continue

		return offers

	def _extract_text(self, tag, selectors: list[str]) -> str:
		for selector in selectors:
			el = tag.select_one(selector)
			if el:
				return el.get_text(strip=True)
		return ""
