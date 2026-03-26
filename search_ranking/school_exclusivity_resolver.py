from __future__ import annotations

import re
from datetime import datetime, timezone

from search_ranking.text_normalization import normalize_text


def _now_iso() -> str:
	return datetime.now(timezone.utc).isoformat()


def _normalize_space(value: object) -> str:
	return " ".join(str(value or "").strip().split())


def _to_bool(value: object, default: bool = False) -> bool:
	if isinstance(value, bool):
		return value
	if isinstance(value, str):
		normalized = normalize_text(value)
		if normalized in {"true", "1", "yes", "y", "sim", "s"}:
			return True
		if normalized in {"false", "0", "no", "n", "nao", "não"}:
			return False
	return default


def _extract_field_value(item: dict, field_name: str, default: object) -> object:
	fields = item.get("fields", {}) if isinstance(item, dict) else {}
	field_payload = fields.get(field_name) if isinstance(fields, dict) else None
	if isinstance(field_payload, dict) and "value" in field_payload:
		return field_payload.get("value")
	if isinstance(item, dict) and field_name in item:
		return item.get(field_name)
	return default


def _ensure_list(value: object) -> list[str]:
	if value is None:
		return []
	if isinstance(value, list):
		return [_normalize_space(item) for item in value if _normalize_space(item)]
	if isinstance(value, str):
		parts = re.split(r"[,;]", value)
		return [_normalize_space(part) for part in parts if _normalize_space(part)]
	return []


def _eligible_source_ids(active_sources: list[dict]) -> list[str]:
	eligible: list[str] = []
	for source in active_sources:
		site_id = _normalize_space(source.get("site_id") or source.get("id"))
		if not site_id:
			continue
		if "is_search_eligible" in source and not bool(source.get("is_search_eligible")):
			continue
		trust_status = normalize_text(source.get("trust_classification_status"))
		if trust_status == "blocked":
			continue
		if bool(source.get("is_suspended", False)):
			continue
		eligible.append(site_id)
	return eligible


def resolve_school_exclusivity(
	item: dict,
	active_sources: list[dict],
	document_notation_rules: dict | None = None,
	user_overrides: dict | None = None,
	audit_log: list[dict] | None = None,
) -> dict[str, object]:
	"""
	Resolve school exclusivity constraints into deterministic query scope.

	Returns a payload containing resolved exclusivity state and query-ready source scope.
	"""
	_ = document_notation_rules

	base_school_exclusive = _to_bool(_extract_field_value(item, "school_exclusive", False), default=False)
	base_required_sellers = _ensure_list(_extract_field_value(item, "required_sellers", []))
	base_preferred_sellers = _ensure_list(_extract_field_value(item, "preferred_sellers", []))

	item_exclusive_source = _normalize_space(_extract_field_value(item, "exclusive_source", ""))
	if not item_exclusive_source:
		item_exclusive_source = "default"

	user_overrides = user_overrides or {}
	user_exclusive = user_overrides.get("school_exclusive")
	user_required = user_overrides.get("required_sellers")
	user_preferred = user_overrides.get("preferred_sellers")
	operator_override = bool(user_overrides.get("operator_override", False))

	conflicts: list[dict] = []

	resolved_school_exclusive = base_school_exclusive
	resolved_required_sellers = list(base_required_sellers)
	resolved_preferred_sellers = list(base_preferred_sellers)
	resolved_source = item_exclusive_source

	if item_exclusive_source == "user_annotation":
		if user_exclusive is not None:
			resolved_school_exclusive = _to_bool(user_exclusive, default=resolved_school_exclusive)
		if user_required is not None:
			resolved_required_sellers = _ensure_list(user_required)
		if user_preferred is not None:
			resolved_preferred_sellers = _ensure_list(user_preferred)
	elif item_exclusive_source == "document_notation":
		if user_exclusive is not None and _to_bool(user_exclusive, default=resolved_school_exclusive) != resolved_school_exclusive:
			conflicts.append(
				{
					"conflict_type": "document_vs_user_exclusive",
					"document_value": resolved_school_exclusive,
					"user_value": _to_bool(user_exclusive, default=resolved_school_exclusive),
				}
			)
	else:
		if user_exclusive is not None:
			resolved_school_exclusive = _to_bool(user_exclusive, default=resolved_school_exclusive)
			resolved_source = "user_annotation"
		if user_required is not None:
			resolved_required_sellers = _ensure_list(user_required)
		if user_preferred is not None:
			resolved_preferred_sellers = _ensure_list(user_preferred)

	if operator_override:
		if user_exclusive is not None:
			resolved_school_exclusive = _to_bool(user_exclusive, default=resolved_school_exclusive)
		if user_required is not None:
			resolved_required_sellers = _ensure_list(user_required)
		if user_preferred is not None:
			resolved_preferred_sellers = _ensure_list(user_preferred)
		conflicts.append(
			{
				"conflict_type": "operator_override_applied",
				"reason": _normalize_space(user_overrides.get("override_reason") or "operator_override"),
			}
		)
		resolved_source = "operator_override"

	eligible_ids = _eligible_source_ids(active_sources)
	eligible_norm_map = {normalize_text(site_id): site_id for site_id in eligible_ids}

	normalized_required = [normalize_text(site) for site in resolved_required_sellers]
	normalized_preferred = [normalize_text(site) for site in resolved_preferred_sellers]

	mandatory_sources: list[str]
	resolution_status = "eligible"
	resolution_reason = "exclusive_resolved" if resolved_school_exclusive else "non_exclusive"

	if resolved_school_exclusive:
		mandatory_sources = [
			eligible_norm_map[norm]
			for norm in normalized_required
			if norm in eligible_norm_map
		]
		blocked_required = [
			raw
			for raw, norm in zip(resolved_required_sellers, normalized_required)
			if norm and norm not in eligible_norm_map
		]
		if blocked_required:
			conflicts.append(
				{
					"conflict_type": "blocked_required_sellers",
					"blocked_sellers": blocked_required,
				}
			)
		if not mandatory_sources:
			resolution_status = "review_required"
			resolution_reason = "no_active_required_sellers"
	else:
		mandatory_sources = list(eligible_ids)

	preferred_sources_active = [
		eligible_norm_map[norm]
		for norm in normalized_preferred
		if norm in eligible_norm_map
	]

	audit_entry = {
		"timestamp": _now_iso(),
		"item_id": item.get("item_id") or item.get("result_id") or item.get("line_index"),
		"resolution_status": resolution_status,
		"resolution_reason": resolution_reason,
		"exclusive_source": resolved_source,
		"conflicts": conflicts,
		"mandatory_sources": mandatory_sources,
		"preferred_sources_active": preferred_sources_active,
	}
	if isinstance(audit_log, list):
		audit_log.append(audit_entry)

	resolved_item = {
		**dict(item),
		"school_exclusive": resolved_school_exclusive,
		"required_sellers": resolved_required_sellers,
		"preferred_sellers": resolved_preferred_sellers,
		"exclusive_source": resolved_source,
		"resolution_status": resolution_status,
		"resolution_reason": resolution_reason,
	}

	return {
		"resolved_item": resolved_item,
		"resolution_status": resolution_status,
		"resolution_reason": resolution_reason,
		"mandatory_sources": mandatory_sources,
		"preferred_sources": preferred_sources_active,
		"conflicts": conflicts,
		"audit_log_entry": audit_entry,
	}
