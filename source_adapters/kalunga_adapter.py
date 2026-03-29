# FILE: source_adapters/kalunga_adapter.py
# MODULE: Kalunga Adapter
# INTEGRATION: HTML scraping + JSON-LD structured data
# SEARCH URL: https://www.kalunga.com.br/busca/{query}
# CATEGORIES: notebook, general supplies, apostila
# NOTE: JSON-LD is preferred; CSS selectors are fallback. Shipping not available in search results.
from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path
from decimal import Decimal, InvalidOperation
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from source_adapters.base import AdapterResult, BaseSourceAdapter, OfferResult

_BASE_SEARCH_URL = "https://www.kalunga.com.br/busca/{query}"
_USER_AGENT = "PesquisaMaterial/1.0 (school-list-price-finder)"
_MAX_RESULTS = 10
_DEBUG_ENV = "KALUNGA_DEBUG"
_DEBUG_DUMP_DIR_ENV = "KALUNGA_DEBUG_DUMP_DIR"

logger = logging.getLogger(__name__)


def _debug_enabled() -> bool:
	return os.getenv(_DEBUG_ENV, "0").strip().lower() in {"1", "true", "yes", "on"}


def _safe_html_excerpt(html: str, limit: int = 240) -> str:
	compact = re.sub(r"\s+", " ", html or "").strip()
	if len(compact) <= limit:
		return compact
	return f"{compact[:limit]}..."


def _dump_html_snapshot(query: str, html: str) -> str | None:
	dump_dir_value = os.getenv(_DEBUG_DUMP_DIR_ENV, "").strip()
	if not dump_dir_value:
		return None

	safe_query = re.sub(r"[^a-zA-Z0-9_-]+", "_", query or "").strip("_") or "empty_query"
	timestamp_ms = int(time.time() * 1000)
	dump_dir = Path(dump_dir_value)
	dump_dir.mkdir(parents=True, exist_ok=True)
	dump_path = dump_dir / f"kalunga_{safe_query}_{timestamp_ms}.html"
	dump_path.write_text(html, encoding="utf-8")
	return str(dump_path)


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
		trace_enabled = _debug_enabled()

		if trace_enabled:
			logger.info(
				"[kalunga] request start | query=%r | url=%s | timeout=%.2fs",
				query,
				url,
				timeout_seconds,
			)

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
			if trace_enabled:
				history_codes = [str(h.status_code) for h in response.history]
				logger.info(
					"[kalunga] request ok | status=%s | final_url=%s | redirects=%s | bytes=%d",
					response.status_code,
					str(response.url),
					"->".join(history_codes) if history_codes else "none",
					len(html.encode("utf-8", errors="ignore")),
				)
		except httpx.TimeoutException:
			if trace_enabled:
				logger.warning("[kalunga] timeout | query=%r | url=%s", query, url)
			return AdapterResult(
				source_site_id=self.site_id,
				query_text=query,
				status="timeout",
				error_message="Request timed out",
				response_ms=self._elapsed_ms(start),
			)
		except Exception as exc:
			if trace_enabled:
				logger.warning("[kalunga] request error | query=%r | url=%s | error=%s", query, url, str(exc))
			return AdapterResult(
				source_site_id=self.site_id,
				query_text=query,
				status="error",
				error_message=str(exc),
				response_ms=self._elapsed_ms(start),
			)

		response_ms = self._elapsed_ms(start)
		dump_path = None
		if trace_enabled:
			dump_path = _dump_html_snapshot(query=query, html=html)
			if dump_path:
				logger.info("[kalunga] html snapshot saved | path=%s", dump_path)
		offers = self._parse_results(html)

		if trace_enabled:
			soup = BeautifulSoup(html, "html.parser")
			jsonld_count = len(soup.select('script[type="application/ld+json"]'))
			title_nodes_count = len(soup.select("h2.blocoproduto__title"))
			css_fallback_cards = len(
				soup.select(".product-item")
				or soup.select(".product-card")
				or soup.select(".shelf-item")
				or soup.select("[data-product-id]")
			)
			logger.info(
				"[kalunga] parse summary | offers=%d | jsonld_scripts=%d | title_nodes=%d | css_cards=%d",
				len(offers),
				jsonld_count,
				title_nodes_count,
				css_fallback_cards,
			)
			if not offers:
				logger.info("[kalunga] empty parse excerpt | %s", _safe_html_excerpt(html))

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

		# Strategy 2: Kalunga current card layout.
		seen_urls: set[str] = set()
		title_nodes = soup.select("h2.blocoproduto__title")
		for title_node in title_nodes:
			try:
				title = title_node.get_text(strip=True)
				if not title:
					continue

				info_container = title_node.find_parent(
					"div",
					class_=lambda value: isinstance(value, str) and "justify-content-between" in value,
				)
				if info_container is None:
					info_container = title_node.parent

				link_tag = title_node.find_parent("a", href=True) or info_container.select_one("a[href*='/prod/']")
				if not link_tag:
					continue

				href = link_tag.get("href", "")
				product_url = href if href.startswith("http") else f"https://www.kalunga.com.br{href}"
				if not product_url or product_url in seen_urls:
					continue

				price_el = info_container.select_one(".blocoproduto__price")
				price_raw = price_el.get_text(strip=True) if price_el else ""
				item_price = _parse_price(price_raw)
				if item_price is None or item_price <= 0:
					continue

				seen_urls.add(product_url)
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
					confidence=0.9,
				))
				if len(offers) >= _MAX_RESULTS:
					return offers
			except Exception:
				continue

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
