# FILE: source_adapters/category_router.py
# MODULE: Category-to-Source Router
# RESPONSIBILITY: Select which adapters to query for a given item category,
#                 and build an optimized query string from item fields.
from __future__ import annotations

import os

from source_adapters.amazon_adapter import AmazonBRAdapter
from source_adapters.base import BaseSourceAdapter
from source_adapters.estante_virtual_adapter import EstanteVirtualAdapter
from source_adapters.kalunga_adapter import KalungaAdapter
from source_adapters.magalu_adapter import MagaluAdapter
from source_adapters.mercadolivre_adapter import MercadoLivreAdapter
from source_adapters.mock_adapter import MockAdapter

# Registry of all available adapters, keyed by site_id
_ALL_ADAPTERS: dict[str, BaseSourceAdapter] = {
	"mock_test": MockAdapter(),  # For testing without website blocking
	"ml_br": MercadoLivreAdapter(),
	"ev_br": EstanteVirtualAdapter(),
	"kalunga_br": KalungaAdapter(),
	"amazon_br": AmazonBRAdapter(),
	"magalu_br": MagaluAdapter(),
}

# Which site_ids to query per category — order matters (first = highest priority)
_REAL_CATEGORY_ROUTES: dict[str, list[str]] = {
	"book":             ["ml_br", "ev_br", "amazon_br"],
	"dictionary":       ["ml_br", "ev_br", "amazon_br"],
	"apostila":         ["ml_br", "kalunga_br"],
	"notebook":         ["ml_br", "kalunga_br", "magalu_br"],
	"general supplies": ["ml_br", "kalunga_br", "magalu_br", "amazon_br"],
	"unknown":          ["ml_br", "amazon_br"],
}

_MOCK_CATEGORY_ROUTES: dict[str, list[str]] = {
	"book":             ["mock_test"],
	"dictionary":       ["mock_test"],
	"apostila":         ["mock_test"],
	"notebook":         ["mock_test"],
	"general supplies": ["mock_test"],
	"unknown":          ["mock_test"],
}

_USE_MOCK_ADAPTERS = os.getenv("USE_MOCK_ADAPTERS", "false").lower() == "true"

# Fallback when category is unrecognised
_DEFAULT_SITES = ["mock_test"] if _USE_MOCK_ADAPTERS else ["ml_br", "amazon_br"]


def get_adapters_for_category(category: str) -> list[BaseSourceAdapter]:
	"""Return the ordered list of adapters to query for the given item category."""
	routes = _MOCK_CATEGORY_ROUTES if _USE_MOCK_ADAPTERS else _REAL_CATEGORY_ROUTES
	site_ids = routes.get(category.lower().strip(), _DEFAULT_SITES)
	return [_ALL_ADAPTERS[sid] for sid in site_ids if sid in _ALL_ADAPTERS]


def build_query(item: dict) -> str:
	"""
	Construct the best search query string for a canonical item dict.
	Priority: ISBN (most precise) → title + author → name alone.

	Expected keys in item (all optional):
	  isbn_normalized, name, author, category, quantity, unit
	"""
	isbn = str(item.get("isbn_normalized") or "").strip()
	name = str(item.get("name") or "").strip()
	author = str(item.get("author") or "").strip()
	category = str(item.get("category") or "").strip().lower()

	# ISBN-based lookup: most precise for books
	if isbn and len(isbn) in (10, 13) and category in ("book", "dictionary"):
		return isbn

	# Title + author for books without ISBN
	if name and author and category in ("book", "dictionary"):
		return f"{name} {author}".strip()

	# Name + quantity context for supplies
	quantity = str(item.get("quantity") or "").strip()
	unit = str(item.get("unit") or "").strip()
	if name and quantity and unit and unit != "un":
		return f"{name} {quantity} {unit}".strip()

	return name or isbn
