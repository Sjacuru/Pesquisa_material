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
import os
import re
import shutil
import sys
import time
from decimal import Decimal, InvalidOperation
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from source_adapters.base import AdapterResult, BaseSourceAdapter, OfferResult

_SEARCH_URL = "https://www.magazineluiza.com.br/busca/{query}/"
_BASE_URL = "https://www.magazineluiza.com.br"
_HOME_URL = "https://www.magazineluiza.com.br/"
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


def _challenge_markers_found(html: str, final_url: str = "") -> list[str]:
    lowered = str(html or "").lower()
    url_lower = str(final_url or "").lower()
    markers = [
        "radware bot manager captcha",
        "validate.perfdrive.com",
        "window.ssjsinternal",
        "shieldsquare",
        "cdn.perfdrive.com",
        "aperture.js",
    ]
    return [m for m in markers if m in lowered or m in url_lower]


def _looks_like_access_challenge(html: str, final_url: str = "") -> bool:
    lowered = str(html or "").lower()
    url_lower = str(final_url or "").lower()

    strong_markers = [
        "radware bot manager captcha",
        "validate.perfdrive.com",
        "window.ssjsinternal",
    ]
    if any(m in lowered or m in url_lower for m in strong_markers):
        return True

    weak_markers = ["shieldsquare", "cdn.perfdrive.com", "aperture.js"]
    has_weak = any(m in lowered for m in weak_markers)
    has_results = any(
        token in lowered
        for token in [
            'data-testid="product-card-container"',
            'data-testid="product-card"',
            'data-component-type="s-search-result"',
            '"@type":"product"',
        ]
    )
    return bool(has_weak and not has_results)


def _selenium_fallback_enabled() -> bool:
    return os.getenv("MAGALU_ENABLE_SELENIUM_FALLBACK", "1").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _http_fallback_after_selenium_enabled() -> bool:
    return os.getenv("MAGALU_HTTP_FALLBACK_AFTER_SELENIUM", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _use_system_chrome_profile() -> bool:
    return os.getenv("MAGALU_USE_SYSTEM_CHROME_PROFILE", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _manual_login_assist_enabled() -> bool:
    return os.getenv("MAGALU_MANUAL_LOGIN_ASSIST", "1").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _looks_like_magalu_login_screen(final_url: str, html: str = "") -> bool:
    url_lower = str(final_url or "").lower()
    html_lower = str(html or "").lower()
    return (
        "cliente/login" in url_lower
        or "sacola.magazineluiza.com.br" in url_lower
        or "fazer login" in html_lower
    )


def _clone_system_chrome_profile_enabled() -> bool:
    return os.getenv("MAGALU_CLONE_SYSTEM_CHROME_PROFILE", "1").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _safe_copy_tree(src: str, dst: str) -> None:
    ignored_names = {
        "SingletonCookie",
        "SingletonLock",
        "SingletonSocket",
        "LOCK",
        "lockfile",
        "DevToolsActivePort",
        "Current Session",
        "Current Tabs",
        "Last Session",
        "Last Tabs",
    }

    if not os.path.isdir(src):
        return

    for root, dirs, files in os.walk(src):
        rel_root = os.path.relpath(root, src)
        dest_root = dst if rel_root == "." else os.path.join(dst, rel_root)
        os.makedirs(dest_root, exist_ok=True)
        dirs[:] = [d for d in dirs if d not in ignored_names]
        for file_name in files:
            if file_name in ignored_names:
                continue
            src_file = os.path.join(root, file_name)
            dst_file = os.path.join(dest_root, file_name)
            try:
                shutil.copy2(src_file, dst_file)
            except Exception:
                continue


def _prepare_magalu_profile(system_user_data_dir: str, system_profile_dir: str) -> tuple[str, str]:
    clone_root = os.getenv(
        "MAGALU_CLONED_PROFILE_ROOT",
        os.path.join("var", "browser_profiles", "magalu_system_clone"),
    )
    clone_root = os.path.abspath(clone_root)
    clone_profile_dir = system_profile_dir or "Default"

    if os.path.isdir(clone_root):
        shutil.rmtree(clone_root, ignore_errors=True)
    os.makedirs(clone_root, exist_ok=True)

    local_state = os.path.join(system_user_data_dir, "Local State")
    if os.path.isfile(local_state):
        try:
            shutil.copy2(local_state, os.path.join(clone_root, "Local State"))
        except Exception:
            pass

    _safe_copy_tree(
        os.path.join(system_user_data_dir, clone_profile_dir),
        os.path.join(clone_root, clone_profile_dir),
    )
    return clone_root, clone_profile_dir


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

        # Selenium-first policy: avoid early HTTP fingerprinting on Magalu.
        if _selenium_fallback_enabled():
            selenium_result = self._search_selenium_fallback(query=query, timeout_seconds=timeout_seconds)
            if selenium_result.status in ("ok", "empty", "timeout"):
                return selenium_result
            if not _http_fallback_after_selenium_enabled():
                return selenium_result

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
            final_url = str(response.url)
            if _looks_like_access_challenge(html, final_url):
                return AdapterResult(
                    source_site_id=self.site_id,
                    query_text=query,
                    status="error",
                    error_message=(
                        f"access_challenge_detected markers={','.join(_challenge_markers_found(html, final_url))} "
                        f"final_url={final_url}"
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
        offers = self._parse_results(html)

        return AdapterResult(
            source_site_id=self.site_id,
            query_text=query,
            status="ok" if offers else "empty",
            offers=offers,
            response_ms=response_ms,
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
            from selenium.webdriver.common.keys import Keys  # type: ignore[import-not-found]
            from selenium.webdriver.support import expected_conditions as EC  # type: ignore[import-not-found]
            from selenium.webdriver.support.ui import WebDriverWait  # type: ignore[import-not-found]
        except Exception:
            return AdapterResult(
                source_site_id=self.site_id,
                query_text=query,
                status="error",
                error_message="selenium_not_available",
                response_ms=self._elapsed_ms(start),
            )

        headless = os.getenv("MAGALU_SELENIUM_HEADLESS", "1").strip().lower() in {"1", "true", "yes", "on"}
        anti_detection = os.getenv("MAGALU_SELENIUM_ANTI_DETECTION", "1").strip().lower() in {"1", "true", "yes", "on"}
        login_email = os.getenv("MAGALU_GOOGLE_LOGIN_EMAIL", "").strip().lower()
        manual_login_assist = _manual_login_assist_enabled()
        manual_login_wait_seconds = max(30, int(os.getenv("MAGALU_MANUAL_LOGIN_WAIT_SECONDS", "300")))
        system_user_data_dir = os.getenv(
            "MAGALU_CHROME_USER_DATA_DIR",
            os.path.join(os.getenv("LOCALAPPDATA", ""), "Google", "Chrome", "User Data"),
        )
        system_profile_dir = os.getenv("MAGALU_CHROME_PROFILE_DIRECTORY", "Default").strip()
        if _use_system_chrome_profile() and system_user_data_dir and os.path.isdir(system_user_data_dir):
            if _clone_system_chrome_profile_enabled():
                profile_dir, chrome_profile_directory = _prepare_magalu_profile(
                    system_user_data_dir=system_user_data_dir,
                    system_profile_dir=system_profile_dir or "Default",
                )
            else:
                profile_dir = system_user_data_dir
                chrome_profile_directory = system_profile_dir or "Default"
        else:
            profile_dir = os.getenv(
                "MAGALU_SELENIUM_PROFILE_DIR",
                os.path.join("var", "browser_profiles", "magalu_selenium"),
            )
            chrome_profile_directory = os.getenv("MAGALU_SELENIUM_PROFILE_DIRECTORY", "").strip()
        max_attempts = max(1, int(os.getenv("MAGALU_SELENIUM_MAX_ATTEMPTS", "2")))
        os.makedirs(profile_dir, exist_ok=True)
        search_url = _SEARCH_URL.format(query=quote(query))

        for attempt in range(1, max_attempts + 1):
            driver = None
            try:
                options = Options()
                if headless:
                    options.add_argument("--headless=new")
                    options.add_argument("--window-size=1400,900")
                else:
                    options.add_argument("--start-maximized")
                options.add_argument(f"--user-data-dir={os.path.abspath(profile_dir)}")
                if chrome_profile_directory:
                    options.add_argument(f"--profile-directory={chrome_profile_directory}")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_argument("--lang=pt-BR")
                options.add_argument(f"--user-agent={_USER_AGENT}")
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option("useAutomationExtension", False)
                options.add_experimental_option(
                    "prefs",
                    {
                        "intl.accept_languages": "pt-BR,pt,en-US,en",
                        "credentials_enable_service": False,
                        "profile.password_manager_enabled": False,
                        "profile.default_content_setting_values.notifications": 2,
                    },
                )

                driver = webdriver.Chrome(options=options)
                driver.set_page_load_timeout(max(5, int(timeout_seconds)))

                if anti_detection:
                    try:
                        driver.execute_cdp_cmd(
                            "Page.addScriptToEvaluateOnNewDocument",
                            {
                                "source": """
                                    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                                    Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR', 'pt', 'en-US', 'en'] });
                                    Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
                                """,
                            },
                        )
                    except Exception:
                        pass

                try:
                    driver.get(_HOME_URL)
                except Exception:
                    pass

                def submit_home_search() -> None:
                    search_input = WebDriverWait(driver, min(12, max(3, int(timeout_seconds)))).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="header-search-input"]'))
                    )
                    search_input.clear()
                    search_input.send_keys(query)
                    search_input.send_keys(Keys.ENTER)

                def wait_for_manual_login(message: str) -> None:
                    print(message)
                    is_interactive = False
                    try:
                        is_interactive = bool(sys.stdin and sys.stdin.isatty())
                    except Exception:
                        is_interactive = False

                    if is_interactive:
                        try:
                            input()
                            print("[magalu] Confirmation received. Resuming automation...")
                            return
                        except Exception:
                            is_interactive = False

                    print(
                        f"[magalu] Non-interactive session detected. Waiting up to {manual_login_wait_seconds}s for login completion..."
                    )
                    deadline = time.monotonic() + float(manual_login_wait_seconds)
                    while time.monotonic() < deadline:
                        try:
                            current_url = driver.current_url or ""
                            current_html = driver.page_source or ""
                        except Exception:
                            time.sleep(2.0)
                            continue
                        if not _looks_like_magalu_login_screen(current_url, current_html):
                            print("[magalu] Login appears completed. Resuming automation...")
                            return
                        time.sleep(2.0)

                    print("[magalu] Login wait timeout reached. Attempting to continue...")

                # Preferred flow: search from homepage to avoid immediate anti-bot escalation.
                try:
                    submit_home_search()
                except Exception:
                    driver.get(search_url)

                # Optional login flow that may appear after search submit.
                try:
                    login_span = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//span[normalize-space()='Fazer login']"))
                    )
                    driver.execute_script("arguments[0].click();", login_span)
                except Exception:
                    pass

                try:
                    if login_email:
                        account_xpath = f"//div[@data-email='{login_email}' or normalize-space()='{login_email}']"
                    else:
                        account_xpath = "//div[@data-email]"
                    account_el = WebDriverWait(driver, 6).until(
                        EC.element_to_be_clickable((By.XPATH, account_xpath))
                    )
                    driver.execute_script("arguments[0].click();", account_el)
                except Exception:
                    pass

                # If login page intercepted the search flow, redo the search after login/profile selection.
                try:
                    if "cliente/login" in (driver.current_url or "") or "sacola" in (driver.current_url or ""):
                        if manual_login_assist:
                            wait_for_manual_login(
                                "[magalu] Login required. Complete login in the opened browser, then press ENTER here to continue..."
                            )
                        driver.get(_HOME_URL)
                        submit_home_search()
                except Exception:
                    pass

                # After optional login, try one more homepage search if results still did not render.
                try:
                    WebDriverWait(driver, 8).until(
                        lambda d: len(d.find_elements(By.CSS_SELECTOR, '[data-testid="product-title"], [data-testid="product-card-container"], [data-testid="product-card"]')) > 0
                    )
                except Exception:
                    try:
                        if manual_login_assist and _looks_like_magalu_login_screen(driver.current_url or "", driver.page_source or ""):
                            wait_for_manual_login(
                                "[magalu] Login screen detected. Complete login in the browser, then press ENTER here to continue..."
                            )
                        driver.get(_HOME_URL)
                        submit_home_search()
                    except Exception:
                        pass

                try:
                    WebDriverWait(driver, min(12, max(3, int(timeout_seconds)))).until(
                        lambda d: len(d.find_elements(By.CSS_SELECTOR, '[data-testid="product-title"], [data-testid="product-card-container"], [data-testid="product-card"]')) > 0
                    )
                except SeleniumTimeoutException:
                    pass

                time.sleep(1.5)
                html = driver.page_source or ""
                final_url = driver.current_url or ""

                # One more manual assist checkpoint after the final navigation.
                if manual_login_assist and _looks_like_magalu_login_screen(final_url, html):
                    wait_for_manual_login(
                        "[magalu] Login is still required. Complete login in the browser, then press ENTER here to continue..."
                    )
                    driver.get(_HOME_URL)
                    submit_home_search()
                    try:
                        WebDriverWait(driver, min(12, max(3, int(timeout_seconds)))).until(
                            lambda d: len(d.find_elements(By.CSS_SELECTOR, '[data-testid="product-title"], [data-testid="product-card-container"], [data-testid="product-card"]')) > 0
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
                lower_err = str(exc).lower()
                recoverable = "invalid session id" in lower_err or "not connected to devtools" in lower_err
                if recoverable and attempt < max_attempts:
                    time.sleep(1.0 * attempt)
                    continue
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

            if _looks_like_access_challenge(html, final_url):
                return AdapterResult(
                    source_site_id=self.site_id,
                    query_text=query,
                    status="error",
                    error_message=(
                        f"selenium_fallback_challenge_detected markers={','.join(_challenge_markers_found(html, final_url))} "
                        f"final_url={final_url}"
                    ),
                    response_ms=self._elapsed_ms(start),
                )

            offers = self._parse_results(html)
            return AdapterResult(
                source_site_id=self.site_id,
                query_text=query,
                status="ok" if offers else "empty",
                offers=offers,
                response_ms=self._elapsed_ms(start),
            )

        return AdapterResult(
            source_site_id=self.site_id,
            query_text=query,
            status="error",
            offers=[],
            error_message="selenium_fallback_no_attempt_result",
            response_ms=self._elapsed_ms(start),
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

                title_link = title_el.find_parent("a", href=True) if title_el else None
                image_el = card.select_one('[data-testid="image"]')
                image_link = image_el.find_parent("a", href=True) if image_el else None
                link_el = title_link or image_link or card.select_one("a[href]")
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
