from intake_canonicalization.directive_reconciliation_resolver import (
	reconcile_directive_outputs,
)


def _deterministic_item(confidence: float) -> dict:
	return {
		"item_id": "line-1",
		"school_exclusive": True,
		"required_sellers": ["Loja Alpha"],
		"preferred_sellers": ["Loja Beta"],
		"directive_confidence": confidence,
		"decision_source": "deterministic",
	}


def test_rule_1_keeps_deterministic_when_above_trigger() -> None:
	audit_log: list[dict] = []
	result = reconcile_directive_outputs(
		deterministic_output=_deterministic_item(0.93),
		llm_result={
			"school_exclusive": False,
			"required_sellers": [],
			"preferred_sellers": [],
			"llm_confidence": 0.95,
			"llm_rationale": "llm",
			"llm_model_id": "model",
		},
		error_payload=None,
		llm_trigger_threshold=0.9,
		llm_accept_threshold=0.8,
		audit_log=audit_log,
	)

	assert result["resolved_item"]["decision_source"] == "deterministic"
	assert result["reconciliation_rule"] == "RULE 1"
	assert result["resolved_item"]["requires_human_review"] is False
	assert len(audit_log) == 2
	assert any(entry.get("event") == "llm_payload_audit_json" for entry in audit_log)
	assert any(entry.get("event") == "directive_reconciliation" for entry in audit_log)


def test_rule_2_uses_llm_when_deterministic_below_and_llm_above_accept() -> None:
	result = reconcile_directive_outputs(
		deterministic_output=_deterministic_item(0.45),
		llm_result={
			"school_exclusive": False,
			"required_sellers": [],
			"preferred_sellers": ["Loja Delta"],
			"llm_confidence": 0.87,
			"llm_rationale": "high confidence",
			"llm_model_id": "model-v2",
		},
		error_payload=None,
		llm_trigger_threshold=0.9,
		llm_accept_threshold=0.8,
	)

	assert result["resolved_item"]["decision_source"] == "llm_fallback"
	assert result["reconciliation_rule"] == "RULE 2"
	assert result["resolved_item"]["llm_model_id"] == "model-v2"


def test_rule_3_forces_review_on_error_payload() -> None:
	result = reconcile_directive_outputs(
		deterministic_output=_deterministic_item(0.2),
		llm_result=None,
		error_payload={"requires_human_review": True, "error_reason": "timeout"},
		llm_trigger_threshold=0.9,
		llm_accept_threshold=0.8,
	)

	assert result["resolved_item"]["decision_source"] == "none"
	assert result["resolved_item"]["requires_human_review"] is True
	assert result["review_queue_required"] is True
	assert result["reconciliation_rule"] == "RULE 3"
