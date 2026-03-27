from __future__ import annotations

from copy import deepcopy


def persist_llm_payload(
	item_id: object,
	llm_result: dict | None,
	error_payload: dict | None,
	persistence_mode: str = "audit_json",
	directive_audit_ledger: list[dict] | None = None,
	llm_call_log_ledger: list[dict] | None = None,
) -> dict | None:
	mode = str(persistence_mode or "audit_json").strip().lower()
	payload = {
		"item_id": item_id,
		"llm_result": deepcopy(llm_result) if isinstance(llm_result, dict) else None,
		"error_payload": deepcopy(error_payload) if isinstance(error_payload, dict) else None,
	}

	if mode == "audit_json":
		if isinstance(directive_audit_ledger, list):
			record = {"event": "llm_payload_audit_json", **payload}
			directive_audit_ledger.append(record)
			return deepcopy(record)
		return None

	if mode == "separate_log":
		if isinstance(llm_call_log_ledger, list):
			record = {"event": "llm_call_log", **payload}
			llm_call_log_ledger.append(record)
			return deepcopy(record)
		return None

	raise ValueError("persistence_mode must be one of: audit_json, separate_log")
