from __future__ import annotations

from datetime import datetime, timezone


def _utc_now() -> datetime:
	return datetime.now(timezone.utc)


def _clamp_confidence(value: float) -> float:
	if value < 0.0:
		return 0.0
	if value > 1.0:
		return 1.0
	return round(value, 2)


def _safe_int(value: object, default: int = 0) -> int:
	try:
		return int(value)
	except (TypeError, ValueError):
		return default


def _build_prompt_context(item: dict) -> dict:
	return {
		"item_id": item.get("item_id") or item.get("line_index"),
		"name": item.get("line_text") or item.get("name"),
		"category": ((item.get("fields") or {}).get("category") or {}).get("value") or item.get("category"),
		"document_notation_rules": dict(item.get("document_notation_rules") or {}),
	}


def invoke_llm_fallback(
	item: dict,
	llm_config: dict,
	llm_invoke_fn,
	audit_log: list[dict] | None = None,
) -> dict:
	if item.get("directive_resolved") is True:
		return {"skipped": True, "skip_reason": "directive_already_resolved"}

	if not callable(llm_invoke_fn):
		raise ValueError("llm_invoke_fn must be callable when Stage B is enabled")

	max_retries = max(0, _safe_int(llm_config.get("max_retries"), 0))
	max_latency_ms = _safe_int(llm_config.get("max_latency_ms"), 0)
	if max_latency_ms <= 0:
		raise ValueError("llm_config.max_latency_ms must be > 0 when Stage B is enabled")

	shadow_mode = bool(llm_config.get("shadow_mode", True))
	prompt_context = _build_prompt_context(item)

	attempt_count = 0
	last_error_reason = ""

	for _ in range(max_retries + 1):
		attempt_count += 1
		try:
			response = llm_invoke_fn(prompt_context, llm_config)
			llm_result = {
				"school_exclusive": bool(response.get("school_exclusive", False)),
				"required_sellers": list(response.get("required_sellers") or []),
				"preferred_sellers": list(response.get("preferred_sellers") or []),
				"llm_confidence": _clamp_confidence(float(response.get("llm_confidence", 0.0))),
				"llm_rationale": str(response.get("llm_rationale") or ""),
				"llm_model_id": str(response.get("llm_model_id") or ""),
				"call_timestamp": _utc_now(),
				"shadow_mode": shadow_mode,
			}

			if isinstance(audit_log, list):
				audit_log.append(
					{
						"event": "llm_call_success",
						"item_id": prompt_context.get("item_id"),
						"attempt_count": attempt_count,
						"shadow_mode": shadow_mode,
						"llm_model_id": llm_result["llm_model_id"],
						"llm_confidence": llm_result["llm_confidence"],
						"timestamp": llm_result["call_timestamp"],
					}
				)

			return {"llm_result": llm_result}
		except Exception as exc:
			last_error_reason = str(exc)

	error_payload = {
		"requires_human_review": True,
		"error_reason": last_error_reason or "llm_call_failed",
		"attempt_count": attempt_count,
		"last_error_timestamp": _utc_now(),
	}

	if isinstance(audit_log, list):
		audit_log.append(
			{
				"event": "llm_call_failure",
				"item_id": prompt_context.get("item_id"),
				"attempt_count": attempt_count,
				"shadow_mode": shadow_mode,
				"error_reason": error_payload["error_reason"],
				"timestamp": error_payload["last_error_timestamp"],
			}
		)

	return {"error_payload": error_payload}
