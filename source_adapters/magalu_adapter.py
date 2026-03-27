# FILE: source_adapters/magalu_adapter.py
# MODULE: Magazine Luiza (Magalu) Adapter
# INTEGRATION: HTML scraping — magazineluiza.com.br search results page
# SEARCH URL: https://www.magazineluiza.com.br/busca/{query}/
# CATEGORIES: notebook, general supplies, book
# STRATEGY: JSON-LD structured data first → CSS product-card fallback
# NOTE: Magalu is heavily JS-rendered; structured data is the most reliable
#       extraction path. CSS fallback targets data-testid attributes which
#       are more stable than class names in their component library.
from __future__ import annotations

import json
import re
import time
from decimal import Decimal, InvalidOperation
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from source_adapters.base import AdapterResult, BaseSourceAdapter, OfferResult

_SEARCH_URL = "https://www.magazineluiza.com.br/busca/{query}/"
_BASE_URL = "https://www.magazineluiza.com.br"
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
_MAX_RESULTS = 10


def _parse_brl(raw: str) -> Decimal | None:
    cleaned = re.sub(r"[^\d,.]", "", raw or "")
    if not cleaned:
        return None
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _offer_from_jsonld(obj: dict, site_id: str) -> OfferResult | None:
    """Extract an OfferResult from a JSON-LD Product or ItemList entry."""
    if not isinstance(obj, dict):
        return None

    # Unwrap ItemList → ListItem → item
    if obj.get("@type") == "ItemList":
        for el in obj.get("itemListElement") or []:
            result = _offer_from_jsonld(el.get("item") or el, site_id)
            if result:
                return result
        return None

    if obj.get("@type") not in ("Product", "ListItem"):
        # May be nested
        item_obj = obj.get("item") or obj.get("product")
        if item_obj:
            return _offer_from_jsonld(item_obj, site_id)
        return None

    name = str(obj.get("name") or "").strip()
    if not name:
        return None

    url = str(obj.get("url") or obj.get("@id") or "").strip()
    if not url:
        return None
    if url.startswith("/"):
        url = _BASE_URL + url

    # Offers block
    offers_block = obj.get("offers") or {}
    if isinstance(offers_block, list):
        offers_block = offers_block[0] if offers_block else {}

    price_raw = str(offers_block.get("price") or "")
    item_price = _parse_brl(price_raw)
    if item_price is None or item_price <= 0:
        return None

    seller_name = str((offers_block.get("seller") or {}).get("name") or "Magalu").strip()

    return OfferResult(
        source_site_id=site_id,
        product_title=name,
        seller_name=seller_name,
        item_price=item_price,
        shipping_cost=None,
        total_price=item_price,
        currency="BRL",
        product_url=url,
        condition="new",
        confidence=0.9,
        raw_data=obj,
    )


class MagaluAdapter(BaseSourceAdapter):
    site_id = "magalu_br"
    label = "Magazine Luiza"
    categories = ["notebook", "general supplies", "book"]

    def search(self, query: str, timeout_seconds: float = 10.0) -> AdapterResult:
        start = time.monotonic()
        url = _SEARCH_URL.format(query=quote(query))

        try:
            response = httpx.get(
                url,
                timeout=timeout_seconds,
                headers={
                    "User-Agent": _USER_AGENT,
                    "Accept-Language": "pt-BR,pt;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
                follow_redirects=True,
            )
            if response.status_code != 200:
                return AdapterResult(
                    source_site_id=self.site_id,
                    query_text=query,
                    status="error",
                    error_message=f"HTTP {response.status_code}",
                    response_ms=self._elapsed_ms(start),
                )
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

        # Strategy 1: JSON-LD structured data
        for script_tag in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(script_tag.string or "")
                items = data if isinstance(data, list) else [data]
                for obj in items:
                    offer = _offer_from_jsonld(obj, self.site_id)
                    if offer:
                        offers.append(offer)
                    if len(offers) >= _MAX_RESULTS:
                        return offers
            except (json.JSONDecodeError, AttributeError):
                continue

        if offers:
            return offers

        # Strategy 2: CSS product card fallback
        cards = (
            soup.select('[data-testid="product-card-container"]')
            or soup.select('[data-testid="product-card"]')
            or soup.select('li[data-testid]')
            or soup.select('.productCard')
        )

        for card in cards[:_MAX_RESULTS]:
            try:
                title_el = (
                    card.select_one('[data-testid="product-title"]')
                    or card.select_one('h2')
                    or card.select_one('h3')
                    or card.select_one('[title]')
                )
                title = ""
                if title_el:
                    title = title_el.get("title") or title_el.get_text(strip=True)
                if not title:
                    continue

                # Price may be in a data attribute or text element
                price_el = (
                    card.select_one('[data-testid="price-value"]')
                    or card.select_one('.price')
                    or card.select_one('[class*="price"]')
                    or card.select_one('span[class*="Price"]')
                )
                price_raw = (price_el.get("data-price") or price_el.get_text(strip=True)) if price_el else ""
                item_price = _parse_brl(price_raw)
                if item_price is None or item_price <= 0:
                    continue

                link_el = card.select_one("a[href]")
                href = (link_el.get("href") or "") if link_el else ""
                if not href:
                    continue
                if href.startswith("/"):
                    product_url = _BASE_URL + href
                else:
                    product_url = href

                offers.append(OfferResult(
                    source_site_id=self.site_id,
                    product_title=title,
                    seller_name="Magazine Luiza",
                    item_price=item_price,
                    shipping_cost=None,
                    total_price=item_price,
                    currency="BRL",
                    product_url=product_url,
                    condition="new",
                    confidence=0.75,
                    raw_data={},
                ))
            except Exception:
                continue

        return offers
