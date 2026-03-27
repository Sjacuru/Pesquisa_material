# FILE: source_adapters/base.py
# MODULE: Source Adapter Base
# RESPONSIBILITY: Define the shared contract and data structures for all source adapters.
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional


@dataclass
class OfferResult:
	"""Normalized offer from a single source site."""
	source_site_id: str
	product_title: str
	seller_name: str
	item_price: Decimal
	shipping_cost: Optional[Decimal]  # None = unknown; Decimal("0") = confirmed free
	total_price: Decimal
	currency: str
	product_url: str
	condition: str  # "new" | "used" | "unknown"
	confidence: float = 1.0
	raw_data: dict = field(default_factory=dict)


@dataclass
class AdapterResult:
	"""Full result from one adapter call."""
	source_site_id: str
	query_text: str
	status: str  # "ok" | "empty" | "timeout" | "error"
	offers: list[OfferResult] = field(default_factory=list)
	error_message: str = ""
	response_ms: Optional[int] = None


class BaseSourceAdapter(ABC):
	site_id: str
	label: str
	categories: list[str]

	@abstractmethod
	def search(self, query: str, timeout_seconds: float = 10.0) -> AdapterResult:
		"""Search the source for the given query string. Must not raise."""
		...

	def _elapsed_ms(self, start: float) -> int:
		return int((time.monotonic() - start) * 1000)
