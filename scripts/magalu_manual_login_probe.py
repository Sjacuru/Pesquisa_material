from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from source_adapters.magalu_adapter import MagaluAdapter


def _set_default_env(name: str, value: str) -> None:
    if not os.getenv(name):
        os.environ[name] = value


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a Magalu search with manual login assist enabled.",
    )
    parser.add_argument("query", help="Search term to send to Magalu.")
    parser.add_argument(
        "--timeout",
        type=float,
        default=90.0,
        help="Search timeout in seconds.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Selenium headless. Manual login assist usually needs a visible browser.",
    )
    args = parser.parse_args()

    _set_default_env("MAGALU_ENABLE_SELENIUM_FALLBACK", "1")
    _set_default_env("MAGALU_HTTP_FALLBACK_AFTER_SELENIUM", "0")
    _set_default_env("MAGALU_SELENIUM_ANTI_DETECTION", "1")
    _set_default_env("MAGALU_MANUAL_LOGIN_ASSIST", "1")
    _set_default_env("MAGALU_SELENIUM_HEADLESS", "1" if args.headless else "0")

    result = MagaluAdapter().search(args.query, timeout_seconds=args.timeout)

    print(f"status={result.status}")
    print(f"offers={len(result.offers)}")
    print(f"error={result.error_message or ''}")
    for index, offer in enumerate(result.offers, start=1):
        print(f"[{index}] {offer.product_title} | {offer.total_price} | {offer.product_url}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())