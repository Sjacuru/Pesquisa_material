from __future__ import annotations

from datetime import datetime, timezone


def _as_bool(value: object) -> bool:
	if isinstance(value, bool):
		return value
	if isinstance(value, str):
		normalized = value.strip().lower()
		if normalized in {"true", "1", "yes", "sim"}:
			return True
		if normalized in {"false", "0", "no", "nao", "não"}:
			return False
	return False


def _as_list(value: object) -> list[str]:
	if isinstance(value, list):
		return [str(item).strip() for item in value if str(item).strip()]
	if isinstance(value, str):
		parts = [part.strip() for part in value.replace(";", ",").split(",")]
		return [part for part in parts if part]
	return []


def _clamp_confidence(value: float) -> float:
	if value < 0.0:
		return 0.0
	if value > 1.0:
		return 1.0
	return round(value, 2)


def _resolve_directive_confidence(
	school_exclusive: bool,
	required_sellers: list[str],
	preferred_sellers: list[str],
) -> float:
	if school_exclusive and required_sellers:
		return 0.92
	if preferred_sellers:
		return 0.78
	return 0.6


def apply_deterministic_directive_parser(
	extracted_item: dict,
	document_notation_rules: dict[str, str] | None,
	llm_trigger_threshold: float | None = None,
	directive_extraction_timestamp: datetime | None = None,
) -> dict:
	fields = extracted_item.get("fields", {})

	school_exclusive = _as_bool((fields.get("school_exclusive") or {}).get("value"))
	required_sellers = _as_list((fields.get("required_sellers") or {}).get("value"))
	preferred_sellers = _as_list((fields.get("preferred_sellers") or {}).get("value"))

	rules_valid = isinstance(document_notation_rules, dict)
	if not rules_valid:
		school_exclusive = False
		required_sellers = []
		preferred_sellers = []

	directive_confidence = _resolve_directive_confidence(
		school_exclusive=school_exclusive,
		required_sellers=required_sellers,
		preferred_sellers=preferred_sellers,
	)
	if not rules_valid:
		directive_confidence = 0.0

	resolved_by_threshold = False
	if llm_trigger_threshold is not None:
		resolved_by_threshold = directive_confidence >= float(llm_trigger_threshold)

	timestamp = directive_extraction_timestamp or datetime.now(timezone.utc)

	return {
		**dict(extracted_item),
		"school_exclusive": school_exclusive,
		"required_sellers": required_sellers,
		"preferred_sellers": preferred_sellers,
		"directive_confidence": _clamp_confidence(directive_confidence),
		"decision_source": "deterministic",
		"directive_resolved": resolved_by_threshold,
		"directive_extraction_timestamp": timestamp,
		"requires_human_review": None,
		"llm_rationale": None,
		"llm_model_id": None,
	}