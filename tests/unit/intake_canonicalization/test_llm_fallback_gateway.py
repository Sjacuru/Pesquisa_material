from intake_canonicalization.llm_fallback_gateway import invoke_llm_fallback


def _llm_success(prompt_context: dict, llm_config: dict) -> dict:
	_ = prompt_context
	_ = llm_config
	return {
		"school_exclusive": True,
		"required_sellers": ["Loja Alpha"],
		"preferred_sellers": ["Loja Beta"],
		"llm_confidence": 0.86,
		"llm_rationale": "notation ambiguous; seller requirement inferred",
		"llm_model_id": "provider-x/model-y@v1",
	}


def _llm_failure(prompt_context: dict, llm_config: dict) -> dict:
	_ = prompt_context
	_ = llm_config
	raise RuntimeError("timeout")


def _unresolved_item() -> dict:
	return {
		"item_id": "line-0",
		"line_text": "Uniforme escolar *",
		"directive_resolved": False,
		"fields": {"category": {"value": "general supplies"}},
		"document_notation_rules": {"*": "Loja Alpha"},
	}


def test_llm_gateway_returns_structured_success_result() -> None:
	audit_log: list[dict] = []
	outcome = invoke_llm_fallback(
		item=_unresolved_item(),
		llm_config={"max_latency_ms": 1500, "max_retries": 1, "shadow_mode": True},
		llm_invoke_fn=_llm_success,
		audit_log=audit_log,
	)

	assert "llm_result" in outcome
	result = outcome["llm_result"]
	assert result["school_exclusive"] is True
	assert result["required_sellers"] == ["Loja Alpha"]
	assert result["llm_confidence"] == 0.86
	assert result["shadow_mode"] is True
	assert len(audit_log) == 1
	assert audit_log[0]["event"] == "llm_call_success"


def test_llm_gateway_returns_error_payload_after_failure() -> None:
	audit_log: list[dict] = []
	outcome = invoke_llm_fallback(
		item=_unresolved_item(),
		llm_config={"max_latency_ms": 1500, "max_retries": 1, "shadow_mode": True},
		llm_invoke_fn=_llm_failure,
		audit_log=audit_log,
	)

	assert "error_payload" in outcome
	error_payload = outcome["error_payload"]
	assert error_payload["requires_human_review"] is True
	assert error_payload["attempt_count"] == 2
	assert "timeout" in error_payload["error_reason"]
	assert len(audit_log) == 1
	assert audit_log[0]["event"] == "llm_call_failure"
