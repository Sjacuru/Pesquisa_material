# FILE: search_ranking/text_normalization.py
# RESPONSIBILITY: Shared text normalization utilities for deterministic matching/classification.
# EXPORTS: normalize_text
# DEPENDS_ON: None.

from __future__ import annotations


def normalize_text(value: object) -> str:
	return " ".join(str(value or "").strip().lower().split())
