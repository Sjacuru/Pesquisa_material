from __future__ import annotations


def _as_bool(value: object, default: bool = False) -> bool:
	if isinstance(value, bool):
		return value
	if isinstance(value, str):
		normalized = value.strip().lower()
		if normalized in {"true", "1", "yes", "sim"}:
			return True
		if normalized in {"false", "0", "no", "nao", "não"}:
			return False
	return default


def _as_float(value: object, key: str) -> float:
	try:
		return float(value)
	except (TypeError, ValueError):
		raise ValueError(f"{key} must be a numeric value") from None


def _as_int(value: object, key: str) -> int:
	try:
		return int(value)
	except (TypeError, ValueError):
		raise ValueError(f"{key} must be an integer value") from None


def parse_directive_runtime_config(raw_config: dict | None) -> dict:
	config = dict(raw_config or {})

	stage_b_enabled = _as_bool(config.get("stage_b_enabled", False), default=False)
	stage_c_enabled = _as_bool(config.get("stage_c_enabled", False), default=False)

	parsed = {
		"stage_b_enabled": stage_b_enabled,
		"stage_c_enabled": stage_c_enabled,
		"shadow_mode": _as_bool(config.get("shadow_mode", True), default=True),
		"llm_provider": config.get("llm_provider"),
		"llm_model_id": config.get("llm_model_id"),
		"llm_persistence_mode": str(config.get("llm_persistence_mode", "audit_json")),
	}

	if stage_c_enabled and not stage_b_enabled:
		raise ValueError("stage_c_enabled requires stage_b_enabled=true")

	if stage_b_enabled:
		if config.get("llm_trigger_threshold") is None:
			raise ValueError("Stage B requires llm_trigger_threshold")
		if config.get("llm_max_latency_ms") is None:
			raise ValueError("Stage B requires llm_max_latency_ms")

		parsed["llm_trigger_threshold"] = _as_float(config.get("llm_trigger_threshold"), "llm_trigger_threshold")
		parsed["llm_max_latency_ms"] = _as_int(config.get("llm_max_latency_ms"), "llm_max_latency_ms")
		parsed["llm_max_retries"] = _as_int(config.get("llm_max_retries", 0), "llm_max_retries")

		if parsed["llm_max_latency_ms"] <= 0:
			raise ValueError("llm_max_latency_ms must be > 0")
		if parsed["llm_max_retries"] < 0:
			raise ValueError("llm_max_retries must be >= 0")

	if stage_c_enabled:
		if config.get("llm_accept_threshold") is None:
			raise ValueError("Stage C requires llm_accept_threshold")
		parsed["llm_accept_threshold"] = _as_float(config.get("llm_accept_threshold"), "llm_accept_threshold")

	if parsed["llm_persistence_mode"] not in {"audit_json", "separate_log"}:
		raise ValueError("llm_persistence_mode must be one of: audit_json, separate_log")

	return parsed
