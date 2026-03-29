# FILE: source_adapters/estante_virtual_adapter.py
# MODULE: Estante Virtual Adapter
# INTEGRATION: HTML scraping — no public API available
# SEARCH URL: https://www.estantevirtual.com.br/busca/{query}
# ISBN URL:   https://www.estantevirtual.com.br/busca/{isbn}
# CATEGORIES: book, dictionary
# NOTE: HTML structure changes require periodic selector maintenance.
from __future__ import annotations

import logging
import os
import re
import time
from decimal import Decimal, InvalidOperation
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from source_adapters.base import AdapterResult, BaseSourceAdapter, OfferResult

_BASE_SEARCH_URL = "https://www.estantevirtual.com.br/busca/{query}"
_HOME_URL = "https://www.estantevirtual.com.br/"
_USER_AGENT = "PesquisaMaterial/1.0 (school-list-price-finder)"
_MAX_RESULTS = 10
_BROWSER_UA = (
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
	"AppleWebKit/537.36 (KHTML, like Gecko) "
	"Chrome/124.0.0.0 Safari/537.36"
)

logger = logging.getLogger(__name__)


def _is_isbn_query(query: str) -> bool:
	compact = re.sub(r"\D", "", str(query or ""))
	return len(compact) in (10, 13)


def _browser_fallback_isbn_only_enabled() -> bool:
	return os.getenv("EV_BROWSER_FALLBACK_ISBN_ONLY", "0").strip().lower() in {"1", "true", "yes", "on"}


def _should_use_browser_fallback(query: str) -> bool:
	if not _browser_fallback_isbn_only_enabled():
		return True
	return _is_isbn_query(query)


def _selenium_fallback_enabled() -> bool:
	return os.getenv("EV_ENABLE_SELENIUM_FALLBACK", "1").strip().lower() in {"1", "true", "yes", "on"}


def _challenge_markers_found(html: str, final_url: str = "") -> list[str]:
	lowered = str(html or "").lower()
	url_lower = str(final_url or "").lower()
	markers = [
		"radware bot manager captcha",
		"validate.perfdrive.com",
		"cdn.perfdrive.com",
		"window.ssjsinternal",
		"aperture.js",
	]
	found = [marker for marker in markers if marker in lowered or marker in url_lower]
	return found


def _looks_like_bot_challenge(html: str, final_url: str = "") -> bool:
	lowered = str(html or "").lower()
	url_lower = str(final_url or "").lower()

	strong_markers = [
		"radware bot manager captcha",
		"validate.perfdrive.com",
		"window.ssjsinternal",
	]
	if any(marker in lowered or marker in url_lower for marker in strong_markers):
		return True

	# Weak markers (perfdrive JS) can appear on normal pages. Treat as challenge
	# only if there is no evidence of actual result cards rendered.
	has_weak_marker = any(marker in lowered for marker in ["cdn.perfdrive.com", "aperture.js"])
	has_result_evidence = any(token in lowered for token in ["product-item", "product-item__link", "product-item__sale-price"])
	return bool(has_weak_marker and not has_result_evidence)


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


def _has_isbn_signal(query: str, title: str, product_url: str, card_text: str) -> bool:
	"""For ISBN queries, keep only offers with explicit ISBN evidence in card data."""
	if not _is_isbn_query(query):
		return True
	isbn = re.sub(r"\D", "", str(query or ""))
	if not isbn:
		return False
	for candidate in (title, product_url, card_text):
		compact = re.sub(r"\D", "", str(candidate or ""))
		if isbn and isbn in compact:
			return True
	return False


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
					"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
					"Accept-Language": "pt-BR,pt;q=0.9",
				},
				follow_redirects=True,
			)
			response.raise_for_status()
			html = response.text
			if _looks_like_bot_challenge(html, str(response.url)):
				if not _should_use_browser_fallback(query):
					# Return empty to allow upstream ISBN->name candidate fallback to proceed.
					return AdapterResult(
						source_site_id=self.site_id,
						query_text=query,
						status="empty",
						error_message="bot_challenge_detected_browser_fallback_disabled_for_non_isbn",
						response_ms=self._elapsed_ms(start),
					)

				browser_result = self._search_browser_fallback(query=query, timeout_seconds=timeout_seconds)
				if browser_result.status == "ok":
					return browser_result

				# Last resort fallback: Selenium (only when enabled).
				selenium_result = self._search_selenium_fallback(query=query, timeout_seconds=timeout_seconds)
				if selenium_result.status in ("ok", "empty"):
					return selenium_result

				if browser_result.status == "empty":
					return browser_result

				# Preserve upstream query-candidate fallback when browser fallback fails.
				return AdapterResult(
					source_site_id=self.site_id,
					query_text=query,
					status="empty",
					error_message=(
						"bot_challenge_detected"
						if not browser_result.error_message and not selenium_result.error_message
						else (
							f"bot_challenge_detected; browser_fallback_failed={browser_result.error_message}; "
							f"selenium_fallback_failed={selenium_result.error_message}"
						)
					),
					response_ms=self._elapsed_ms(start),
				)
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

		# Primary selectors — Estante Virtual current product list layout.
		cards = (
			soup.select(".product-list .product-item")
			or soup.select(".product-item.product-list__item")
			or soup.select(".search-result .product-item")
			or soup.select(".product-item")
			or soup.select(".result-item")
			or soup.select(".livro")
			or soup.select("[data-testid='book-card']")
			or soup.select(".book-card")
		)

		for card in cards[:_MAX_RESULTS]:
			try:
				card_text = card.get_text(" ", strip=True)
				title = self._extract_text(card, [
					".product-item__name", ".product-item__title", ".book-title", ".titulo", "h2", "h3", ".title", "[itemprop='name']"
				])
				seller = self._extract_text(card, [
					".product-item__author", ".seller-name", ".livreiro", ".vendedor", "[itemprop='seller']"
				]) or "Estante Virtual"
				price_raw = self._extract_text(card, [
					"span[data-auto='price'].product-item__sale-price",
					".product-item__sale-price",
					".preco",
					".price",
					"[itemprop='price']",
					".valor",
					"[data-price]",
				]) or card.get("data-price") or ""
				link_tag = (
					card.select_one("a.product-item__link[href]")
					or card.select_one("a.product-item__button[href]")
					or card.select_one("a[href*='/livro/']")
				)
				if link_tag and not title:
					title = str(link_tag.get("title") or "").strip()
				product_url = ""
				if link_tag:
					href = link_tag.get("href", "")
					product_url = href if href.startswith("http") else f"https://www.estantevirtual.com.br{href}"

				if not _has_isbn_signal(query, title, product_url, card_text):
					continue

				condition_raw = card_text.lower()
				if "usado" in condition_raw or "semi" in condition_raw:
					condition = "used"
				elif "novo" in condition_raw:
					condition = "new"
				else:
					condition = "unknown"

				item_price = _parse_price(price_raw)
				if item_price is None or item_price <= 0:
					continue

				offers.append(OfferResult(
					source_site_id=self.site_id,
					product_title=title,
					seller_name=seller,
					item_price=item_price,
					shipping_cost=None,
					total_price=item_price,
					currency="BRL",
					product_url=product_url,
					condition=condition,
					confidence=0.85,
				))
			except Exception:
				continue

		offers.sort(key=lambda offer: offer.total_price)
		return offers[:_MAX_RESULTS]

	def _search_browser_fallback(self, query: str, timeout_seconds: float) -> AdapterResult:
		start = time.monotonic()
		try:
			from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
			from playwright.sync_api import sync_playwright
		except Exception:
			return AdapterResult(
				source_site_id=self.site_id,
				query_text=query,
				status="error",
				error_message="playwright_not_available",
				response_ms=self._elapsed_ms(start),
			)

		search_url = _BASE_SEARCH_URL.format(query=quote(query))
		timeout_ms = int(max(timeout_seconds, 1.0) * 1000)
		headless = os.getenv("EV_PLAYWRIGHT_HEADLESS", "1").lower() not in {"0", "false", "no"}
		max_attempts = max(1, int(os.getenv("EV_BROWSER_MAX_ATTEMPTS", "2")))
		pre_nav_home = os.getenv("EV_BROWSER_PRENAV_HOME", "1").strip().lower() in {"1", "true", "yes", "on"}

		# Persistent profile directory: reused across calls so the site sees an
		# established session with cookies/history rather than a blank new browser.
		# Set EV_BROWSER_PROFILE_DIR to override the default location.
		profile_dir = os.getenv(
			"EV_BROWSER_PROFILE_DIR",
			os.path.join("var", "browser_profiles", "estante_virtual"),
		)
		os.makedirs(profile_dir, exist_ok=True)

		try:
			html = ""
			final_url = ""
			found_markers: list[str] = []
			with sync_playwright() as p:
				# launch_persistent_context keeps cookies, localStorage and
				# browsing history between calls, mimicking a real returning user.
				context = p.chromium.launch_persistent_context(
					user_data_dir=profile_dir,
					headless=headless,
					locale="pt-BR",
					user_agent=_BROWSER_UA,
					viewport={"width": 1280, "height": 800},
					args=["--disable-blink-features=AutomationControlled"],
				)
				context.set_extra_http_headers({
					"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
					"Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
				})
				page = context.new_page()
				page.add_init_script(
					"Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
				)

				for attempt in range(1, max_attempts + 1):
					if pre_nav_home:
						try:
							page.goto(_HOME_URL, wait_until="domcontentloaded", timeout=timeout_ms)
							page.wait_for_timeout(900)
						except Exception:
							pass

					page.goto(search_url, wait_until="domcontentloaded", timeout=timeout_ms)
					try:
						page.wait_for_selector(".product-item, a.product-item__link", timeout=8000)
					except PlaywrightTimeoutError:
						page.wait_for_timeout(3000)

					html = page.content()
					final_url = page.url
					found_markers = _challenge_markers_found(html, final_url)
					if not found_markers:
						break

					logger.info(
						"[ev_browser] challenge attempt=%s markers=%s final_url=%s",
						attempt,
						",".join(found_markers),
						final_url,
					)
					if attempt < max_attempts:
						page.wait_for_timeout(1200 * attempt)

				context.close()
		except PlaywrightTimeoutError:
			return AdapterResult(
				source_site_id=self.site_id,
				query_text=query,
				status="timeout",
				error_message="browser_fallback_timeout",
				response_ms=self._elapsed_ms(start),
			)
		except Exception as exc:
			return AdapterResult(
				source_site_id=self.site_id,
				query_text=query,
				status="error",
				error_message=f"browser_fallback_error: {exc}",
				response_ms=self._elapsed_ms(start),
			)

		if _looks_like_bot_challenge(html, final_url):
			markers_text = ",".join(_challenge_markers_found(html, final_url))
			return AdapterResult(
				source_site_id=self.site_id,
				query_text=query,
				status="error",
				error_message=f"browser_fallback_challenge_detected markers={markers_text} final_url={final_url}",
				response_ms=self._elapsed_ms(start),
			)

		offers = self._parse_results(html, query)
		return AdapterResult(
			source_site_id=self.site_id,
			query_text=query,
			status="ok" if offers else "empty",
			offers=offers,
			response_ms=self._elapsed_ms(start),
		)

	def _search_selenium_fallback(self, query: str, timeout_seconds: float) -> AdapterResult:
		start = time.monotonic()
		if not _selenium_fallback_enabled():
			return AdapterResult(
				source_site_id=self.site_id,
				query_text=query,
				status="error",
				error_message="selenium_fallback_disabled",
				response_ms=self._elapsed_ms(start),
			)

		try:
			from selenium import webdriver  # type: ignore[import-not-found]
			from selenium.common.exceptions import TimeoutException as SeleniumTimeoutException  # type: ignore[import-not-found]
			from selenium.webdriver.chrome.options import Options  # type: ignore[import-not-found]
			from selenium.webdriver.common.by import By  # type: ignore[import-not-found]
			from selenium.webdriver.support.ui import WebDriverWait  # type: ignore[import-not-found]
		except Exception:
			return AdapterResult(
				source_site_id=self.site_id,
				query_text=query,
				status="error",
				error_message="selenium_not_available",
				response_ms=self._elapsed_ms(start),
			)

		headless = os.getenv("EV_SELENIUM_HEADLESS", os.getenv("EV_PLAYWRIGHT_HEADLESS", "1")).strip().lower() in {"1", "true", "yes", "on"}
		pre_nav_home = os.getenv("EV_SELENIUM_PRENAV_HOME", "1").strip().lower() in {"1", "true", "yes", "on"}
		anti_detection = os.getenv("EV_SELENIUM_ANTI_DETECTION", "1").strip().lower() in {"1", "true", "yes", "on"}
		profile_dir = os.getenv(
			"EV_SELENIUM_PROFILE_DIR",
			os.path.join("var", "browser_profiles", "estante_virtual_selenium"),
		)
		os.makedirs(profile_dir, exist_ok=True)
		search_url = _BASE_SEARCH_URL.format(query=quote(query))

		driver = None
		try:
			options = Options()
			if headless:
				options.add_argument("--headless=new")
				options.add_argument("--window-size=1400,900")
			else:
				options.add_argument("--start-maximized")
			options.add_argument(f"--user-data-dir={os.path.abspath(profile_dir)}")
			options.add_argument("--no-sandbox")
			options.add_argument("--disable-dev-shm-usage")
			options.add_argument("--disable-blink-features=AutomationControlled")
			options.add_argument("--lang=pt-BR")
			options.add_argument(f"--user-agent={_BROWSER_UA}")
			prefs = {
				"intl.accept_languages": "pt-BR,pt,en-US,en",
				"credentials_enable_service": False,
				"profile.password_manager_enabled": False,
				"profile.default_content_setting_values.notifications": 2,
			}
			options.add_experimental_option("prefs", prefs)
			options.add_experimental_option("excludeSwitches", ["enable-automation"])
			options.add_experimental_option("useAutomationExtension", False)

			driver = webdriver.Chrome(options=options)
			driver.set_page_load_timeout(max(5, int(timeout_seconds)))

			if anti_detection:
				try:
					driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
						"source": """
							Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
							Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR', 'pt', 'en-US', 'en'] });
							Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
							Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
						""",
					})
				except Exception:
					pass

			if pre_nav_home:
				try:
					driver.get(_HOME_URL)
				except Exception:
					pass

			driver.get(search_url)
			try:
				WebDriverWait(driver, min(12, max(3, int(timeout_seconds)))).until(
					lambda d: len(d.find_elements(By.CSS_SELECTOR, ".product-item, a.product-item__link")) > 0
				)
			except SeleniumTimeoutException:
				pass

			time.sleep(1.5)
			html = driver.page_source or ""
			final_url = driver.current_url or ""
		except SeleniumTimeoutException:
			return AdapterResult(
				source_site_id=self.site_id,
				query_text=query,
				status="timeout",
				error_message="selenium_fallback_timeout",
				response_ms=self._elapsed_ms(start),
			)
		except Exception as exc:
			return AdapterResult(
				source_site_id=self.site_id,
				query_text=query,
				status="error",
				error_message=f"selenium_fallback_error: {exc}",
				response_ms=self._elapsed_ms(start),
			)
		finally:
			if driver is not None:
				try:
					driver.quit()
				except Exception:
					pass

		if _looks_like_bot_challenge(html, final_url):
			markers_text = ",".join(_challenge_markers_found(html, final_url))
			return AdapterResult(
				source_site_id=self.site_id,
				query_text=query,
				status="error",
				error_message=f"selenium_fallback_challenge_detected markers={markers_text} final_url={final_url}",
				response_ms=self._elapsed_ms(start),
			)

		offers = self._parse_results(html, query)
		return AdapterResult(
			source_site_id=self.site_id,
			query_text=query,
			status="ok" if offers else "empty",
			offers=offers,
			response_ms=self._elapsed_ms(start),
		)

	def _extract_text(self, tag, selectors: list[str]) -> str:
		for selector in selectors:
			el = tag.select_one(selector)
			if el:
				return el.get_text(strip=True)
		return ""
