import pytest

from intake_canonicalization.pdf_ingestion_field_extraction import extract_item_candidates


def _category_matrix() -> dict[str, dict[str, str]]:
	return {
		"book": {"name": "R", "isbn": "HC", "quantity": "R"},
		"general supplies": {"name": "R", "quantity": "R"},
	}


def _llm_stub(prompt_context: dict, llm_config: dict) -> dict:
	_ = prompt_context
	_ = llm_config
	return {
		"school_exclusive": True,
		"required_sellers": ["Loja Zeta"],
		"preferred_sellers": [],
		"llm_confidence": 0.91,
		"llm_rationale": "rule inference",
		"llm_model_id": "provider/model@1",
	}


def test_default_flow_keeps_stage_a_only() -> None:
	document = {"content_type": "application/pdf", "text": "Item sem marcador"}
	items = extract_item_candidates(document, _category_matrix())

	assert len(items) == 1
	assert items[0]["decision_source"] == "deterministic"
	assert items[0]["requires_human_review"] is None


def test_enabled_stage_b_and_c_applies_reconciliation() -> None:
	audit_log: list[dict] = []
	llm_call_log: list[dict] = []
	document = {"content_type": "application/pdf", "text": "Item sem marcador"}
	items = extract_item_candidates(
		document,
		_category_matrix(),
		directive_runtime_config={
			"stage_b_enabled": True,
			"stage_c_enabled": True,
			"llm_trigger_threshold": 0.9,
			"llm_accept_threshold": 0.8,
			"llm_max_latency_ms": 1500,
			"llm_max_retries": 0,
			"shadow_mode": False,
			"llm_persistence_mode": "separate_log",
		},
		llm_invoke_fn=_llm_stub,
		audit_log=audit_log,
		llm_call_log=llm_call_log,
	)

	assert len(items) == 1
	assert items[0]["decision_source"] == "llm_fallback"
	assert items[0]["requires_human_review"] is False
	assert items[0]["required_sellers"] == ["Loja Zeta"]
	assert any(entry.get("event") == "llm_call_success" for entry in audit_log)
	assert any(entry.get("event") == "directive_reconciliation" for entry in audit_log)
	assert any(entry.get("event") == "llm_call_log" for entry in llm_call_log)
	reconciliation_entry = next(entry for entry in audit_log if entry.get("event") == "directive_reconciliation")
	assert reconciliation_entry.get("llm_payload_ref", {}).get("store") == "llm_call_log"


def test_stage_b_guard_raises_when_threshold_missing() -> None:
	document = {"content_type": "application/pdf", "text": "Item sem marcador"}
	with pytest.raises(ValueError):
		extract_item_candidates(
			document,
			_category_matrix(),
			directive_runtime_config={
				"stage_b_enabled": True,
				"stage_c_enabled": False,
				"llm_max_latency_ms": 1500,
			},
			llm_invoke_fn=_llm_stub,
		)
