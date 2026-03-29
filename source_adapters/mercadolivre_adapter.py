# FILE: source_adapters/mercadolivre_adapter.py
# MODULE: Mercado Livre Adapter
# INTEGRATION: Official public REST API — no auth required for product searches
# API BASE: https://api.mercadolibre.com/sites/MLB/search
# CATEGORIES: book, dictionary, apostila, notebook, general supplies
from __future__ import annotations

import re
import time
from decimal import Decimal
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from source_adapters.base import AdapterResult, BaseSourceAdapter, OfferResult

_ML_SEARCH_URL = "https://api.mercadolibre.com/sites/MLB/search"
_ML_WEB_SEARCH_URL = "https://lista.mercadolivre.com.br/{query}"
_DEFAULT_LIMIT = 10
_USER_AGENT = "PesquisaMaterial/1.0 (school-list-price-finder)"
_BROWSER_USER_AGENT = (
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
	"AppleWebKit/537.36 (KHTML, like Gecko) "
	"Chrome/124.0.0.0 Safari/537.36"
)


def _parse_decimal(raw: str) -> Decimal | None:
	cleaned = re.sub(r"[^\d,.]", "", str(raw or ""))
	if not cleaned:
		return None
	if "," in cleaned and "." in cleaned:
		cleaned = cleaned.replace(".", "").replace(",", ".")
	elif "," in cleaned:
		cleaned = cleaned.replace(",", ".")
	try:
		return Decimal(cleaned)
	except Exception:
		return None


def _slugify_query(query: str) -> str:
	return quote(str(query or "").strip().replace(" ", "-"))


class MercadoLivreAdapter(BaseSourceAdapter):
	site_id = "ml_br"
	label = "Mercado Livre"
	categories = ["book", "dictionary", "apostila", "notebook", "general supplies"]

	def search(self, query: str, timeout_seconds: float = 10.0) -> AdapterResult:
		# Prefer web search first to mimic normal browsing and avoid API-specific blocks.
		web_result = self._search_web_fallback(query=query, timeout_seconds=timeout_seconds)
		if web_result.status == "ok":
			return web_result

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
			if web_result.status in ("empty", "timeout"):
				return web_result
			return AdapterResult(
				source_site_id=self.site_id,
				query_text=query,
				status="timeout",
				error_message="Request timed out",
				response_ms=self._elapsed_ms(start),
			)
		except httpx.HTTPStatusError as exc:
			if web_result.status in ("ok", "empty", "timeout"):
				return web_result
			return AdapterResult(
				source_site_id=self.site_id,
				query_text=query,
				status="error",
				error_message=str(exc),
				response_ms=self._elapsed_ms(start),
			)
		except Exception as exc:
			if web_result.status in ("ok", "empty", "timeout"):
				return web_result
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

	def _search_web_fallback(self, query: str, timeout_seconds: float) -> AdapterResult:
		start = time.monotonic()
		url = _ML_WEB_SEARCH_URL.format(query=_slugify_query(query))
		try:
			response = httpx.get(
				url,
				timeout=timeout_seconds,
				headers={
					"User-Agent": _BROWSER_USER_AGENT,
					"Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
					"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
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
				error_message="Web fallback timed out",
				response_ms=self._elapsed_ms(start),
			)
		except Exception as exc:
			return AdapterResult(
				source_site_id=self.site_id,
				query_text=query,
				status="error",
				error_message=f"Web fallback error: {exc}",
				response_ms=self._elapsed_ms(start),
			)

		soup = BeautifulSoup(html, "html.parser")
		cards = soup.select("li.ui-search-layout__item")
		offers: list[OfferResult] = []

		for card in cards:
			if len(offers) >= _DEFAULT_LIMIT:
				break
			try:
				link = card.select_one("a.poly-component__title") or card.select_one("a[href]")
				title = link.get_text(" ", strip=True) if link else ""
				product_url = str(link.get("href") or "") if link else ""

				price_int = card.select_one(".andes-money-amount__fraction")
				price_cents = card.select_one(".andes-money-amount__cents")
				if not price_int:
					continue
				raw_price = price_int.get_text(strip=True)
				if price_cents and price_cents.get_text(strip=True):
					raw_price = f"{raw_price}.{price_cents.get_text(strip=True)}"
				item_price = _parse_decimal(raw_price)
				if item_price is None or item_price <= 0:
					continue

				offers.append(
					OfferResult(
						source_site_id=self.site_id,
						product_title=title,
						seller_name="",
						item_price=item_price,
						shipping_cost=None,
						total_price=item_price,
						currency="BRL",
						product_url=product_url,
						condition="unknown",
						confidence=0.85,
						raw_data={},
					)
				)
			except Exception:
				continue

		return AdapterResult(
			source_site_id=self.site_id,
			query_text=query,
			status="ok" if offers else "empty",
			offers=offers,
			response_ms=self._elapsed_ms(start),
		)
