from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

from source_adapters.kalunga_adapter import KalungaAdapter


def main() -> None:
    parser = argparse.ArgumentParser(description="Debug Kalunga access and parsing for a single query.")
    parser.add_argument("query", help="Search query text sent to Kalunga /busca/{query}")
    parser.add_argument("--timeout", type=float, default=10.0, help="HTTP timeout in seconds")
    parser.add_argument(
        "--dump-dir",
        default="var/debug/kalunga",
        help="Directory where raw HTML snapshots are saved",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")

    dump_dir = Path(args.dump_dir)
    dump_dir.mkdir(parents=True, exist_ok=True)

    os.environ["KALUNGA_DEBUG"] = "1"
    os.environ["KALUNGA_DEBUG_DUMP_DIR"] = str(dump_dir)

    adapter = KalungaAdapter()
    result = adapter.search(args.query, timeout_seconds=args.timeout)

    print("\n=== Kalunga Debug Result ===")
    print(f"query: {args.query}")
    print(f"status: {result.status}")
    print(f"response_ms: {result.response_ms}")
    print(f"offers_count: {len(result.offers)}")
    if result.error_message:
        print(f"error: {result.error_message}")

    for idx, offer in enumerate(result.offers[:5], start=1):
        print(f"\n[{idx}] {offer.product_title}")
        print(f"price: {offer.total_price} {offer.currency}")
        print(f"url: {offer.product_url}")


if __name__ == "__main__":
    main()
