from __future__ import annotations

from datetime import datetime, timezone

from intake_canonicalization.directive_audit_persistence import persist_llm_payload


def _utc_now() -> datetime:
	return datetime.now(timezone.utc)


def _safe_float(value: object, default: float = 0.0) -> float:
	try:
		return float(value)
	except (TypeError, ValueError):
		return default


def _clamp_confidence(value: float) -> float:
	if value < 0.0:
		return 0.0
	if value > 1.0:
		return 1.0
	return round(value, 2)


def reconcile_directive_outputs(
	deterministic_output: dict,
	llm_result: dict | None,
	error_payload: dict | None,
	llm_trigger_threshold: float,
	llm_accept_threshold: float,
	audit_log: list[dict] | None = None,
	persistence_mode: str = "audit_json",
	directive_audit_ledger: list[dict] | None = None,
	llm_call_log_ledger: list[dict] | None = None,
) -> dict:
	if directive_audit_ledger is None:
		directive_audit_ledger = audit_log

	deterministic_confidence = _safe_float(deterministic_output.get("directive_confidence"), 0.0)
	llm_confidence = _safe_float((llm_result or {}).get("llm_confidence"), 0.0)

	requires_human_review = False
	reconciliation_rule = "RULE 1"

	if deterministic_confidence >= float(llm_trigger_threshold):
		decision_source = "deterministic"
		final_school_exclusive = bool(deterministic_output.get("school_exclusive", False))
		final_required_sellers = list(deterministic_output.get("required_sellers") or [])
		final_preferred_sellers = list(deterministic_output.get("preferred_sellers") or [])
		final_confidence = _clamp_confidence(deterministic_confidence)
		final_llm_rationale = None
		final_llm_model_id = None
	elif llm_result is not None and llm_confidence >= float(llm_accept_threshold):
		reconciliation_rule = "RULE 2"
		decision_source = "llm_fallback"
		final_school_exclusive = bool(llm_result.get("school_exclusive", False))
		final_required_sellers = list(llm_result.get("required_sellers") or [])
		final_preferred_sellers = list(llm_result.get("preferred_sellers") or [])
		final_confidence = _clamp_confidence(llm_confidence)
		final_llm_rationale = llm_result.get("llm_rationale")
		final_llm_model_id = llm_result.get("llm_model_id")
	else:
		reconciliation_rule = "RULE 3"
		requires_human_review = True
		decision_source = "none"
		final_school_exclusive = bool(deterministic_output.get("school_exclusive", False))
		final_required_sellers = list(deterministic_output.get("required_sellers") or [])
		final_preferred_sellers = list(deterministic_output.get("preferred_sellers") or [])
		final_confidence = _clamp_confidence(max(deterministic_confidence, llm_confidence))
		final_llm_rationale = None
		final_llm_model_id = None

	if error_payload is not None:
		reconciliation_rule = "RULE 3"
		requires_human_review = True
		decision_source = "none"

	resolved_item = {
		**dict(deterministic_output),
		"school_exclusive": final_school_exclusive,
		"required_sellers": final_required_sellers,
		"preferred_sellers": final_preferred_sellers,
		"directive_confidence": final_confidence,
		"decision_source": decision_source,
		"requires_human_review": requires_human_review,
		"llm_rationale": final_llm_rationale,
		"llm_model_id": final_llm_model_id,
		"directive_extraction_timestamp": _utc_now(),
	}

	reconciliation_audit_record = {
		"item_id": resolved_item.get("item_id") or resolved_item.get("line_index"),
		"decision_source": decision_source,
		"deterministic_confidence": _clamp_confidence(deterministic_confidence),
		"llm_confidence": _clamp_confidence(llm_confidence) if llm_result is not None else None,
		"requires_human_review": requires_human_review,
		"shadow_mode": bool((llm_result or {}).get("shadow_mode", False)),
		"timestamp": resolved_item["directive_extraction_timestamp"],
		"reconciliation_rationale": reconciliation_rule,
	}

	llm_payload_record = persist_llm_payload(
		item_id=reconciliation_audit_record["item_id"],
		llm_result=llm_result,
		error_payload=error_payload,
		persistence_mode=persistence_mode,
		directive_audit_ledger=directive_audit_ledger,
		llm_call_log_ledger=llm_call_log_ledger,
	)
	if llm_payload_record is not None and persistence_mode == "separate_log":
		reconciliation_audit_record["llm_payload_ref"] = {
			"store": "llm_call_log",
			"item_id": reconciliation_audit_record["item_id"],
		}

	if isinstance(directive_audit_ledger, list):
		directive_audit_ledger.append({"event": "directive_reconciliation", **reconciliation_audit_record})

	return {
		"resolved_item": resolved_item,
		"reconciliation_rule": reconciliation_rule,
		"review_queue_required": requires_human_review,
		"reconciliation_audit_record": reconciliation_audit_record,
	}
