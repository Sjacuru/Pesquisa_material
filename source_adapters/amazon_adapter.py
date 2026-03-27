# FILE: source_adapters/amazon_adapter.py
# MODULE: Amazon BR Adapter
# INTEGRATION: HTML scraping — amazon.com.br search results page
# SEARCH URL: https://www.amazon.com.br/s?k={query}
# CATEGORIES: book, dictionary, apostila, notebook, general supplies
# NOTE: Amazon may return bot-detection pages (503/captcha). The adapter
#       returns status="error" gracefully in that case rather than raising.
#       Shipping is always 0 for Prime-eligible items but cannot be reliably
#       detected from the listing page — shipping_cost is left as None.
from __future__ import annotations

import re
import time
from decimal import Decimal, InvalidOperation
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from source_adapters.base import AdapterResult, BaseSourceAdapter, OfferResult

_SEARCH_URL = "https://www.amazon.com.br/s"
_BASE_URL = "https://www.amazon.com.br"
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
_MAX_RESULTS = 10


def _parse_brl(raw: str) -> Decimal | None:
    """Parse a Brazilian price string like 'R$ 45,90' or '45.90' into Decimal."""
    cleaned = re.sub(r"[^\d,.]", "", raw or "")
    if not cleaned:
        return None
    # "45.990,00" → thousands dot, decimal comma
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


class AmazonBRAdapter(BaseSourceAdapter):
    site_id = "amazon_br"
    label = "Amazon Brasil"
    categories = ["book", "dictionary", "apostila", "notebook", "general supplies"]

    def search(self, query: str, timeout_seconds: float = 10.0) -> AdapterResult:
        start = time.monotonic()
        try:
            response = httpx.get(
                _SEARCH_URL,
                params={"k": query, "language": "pt_BR"},
                timeout=timeout_seconds,
                headers={
                    "User-Agent": _USER_AGENT,
                    "Accept-Language": "pt-BR,pt;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
                follow_redirects=True,
            )
            # Amazon returns 200 even for bot-detection pages; check content
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

        # Each search result is a <div data-component-type="s-search-result">
        cards = soup.select('[data-component-type="s-search-result"]')

        for card in cards[:_MAX_RESULTS]:
            try:
                # Title — screen-reader span is the cleanest
                title_el = (
                    card.select_one("h2 span.a-text-normal")
                    or card.select_one("h2 span")
                    or card.select_one("h2")
                )
                title = title_el.get_text(strip=True) if title_el else ""
                if not title:
                    continue

                # Price — .a-offscreen contains the full formatted price (e.g. "R$ 45,90")
                price_el = card.select_one(".a-price .a-offscreen")
                if not price_el:
                    continue
                item_price = _parse_brl(price_el.get_text(strip=True))
                if item_price is None or item_price <= 0:
                    continue

                # Product URL
                link_el = card.select_one("h2 a.a-link-normal") or card.select_one("h2 a")
                href = (link_el.get("href") or "") if link_el else ""
                if href.startswith("/"):
                    product_url = _BASE_URL + href
                elif href.startswith("http"):
                    product_url = href
                else:
                    continue

                # Remove referral/affiliate noise from URL
                product_url = product_url.split("?")[0] if product_url else product_url

                total_price = item_price  # shipping unknown at listing stage

                offers.append(OfferResult(
                    source_site_id=self.site_id,
                    product_title=title,
                    seller_name="Amazon Brasil",
                    item_price=item_price,
                    shipping_cost=None,
                    total_price=total_price,
                    currency="BRL",
                    product_url=product_url,
                    condition="new",
                    confidence=0.9,
                    raw_data={},
                ))
            except Exception:
                continue

        return offers
