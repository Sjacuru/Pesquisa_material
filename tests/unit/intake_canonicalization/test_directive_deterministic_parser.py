from datetime import datetime, timezone

from intake_canonicalization.directive_deterministic_parser import (
	apply_deterministic_directive_parser,
)


def _base_item() -> dict:
	return {
		"line_index": 0,
		"line_text": "Uniforme escolar somente Loja Alpha",
		"fields": {
			"school_exclusive": {"value": True, "confidence": 0.9},
			"required_sellers": {"value": ["Loja Alpha"], "confidence": 0.88},
			"preferred_sellers": {"value": ["Loja Beta"], "confidence": 0.82},
		},
	}


def test_stage_a_resolves_true_when_threshold_is_met() -> None:
	fixed_timestamp = datetime(2026, 3, 27, tzinfo=timezone.utc)
	output = apply_deterministic_directive_parser(
		extracted_item=_base_item(),
		document_notation_rules={"*": "Loja Alpha"},
		llm_trigger_threshold=0.9,
		directive_extraction_timestamp=fixed_timestamp,
	)

	assert output["decision_source"] == "deterministic"
	assert output["directive_confidence"] == 0.92
	assert output["directive_resolved"] is True
	assert output["requires_human_review"] is None
	assert output["llm_rationale"] is None
	assert output["llm_model_id"] is None
	assert output["directive_extraction_timestamp"] == fixed_timestamp


def test_stage_a_keeps_unresolved_when_threshold_not_provided() -> None:
	output = apply_deterministic_directive_parser(
		extracted_item=_base_item(),
		document_notation_rules={"*": "Loja Alpha"},
	)

	assert output["directive_resolved"] is False


def test_stage_a_fallback_when_notation_rules_invalid() -> None:
	output = apply_deterministic_directive_parser(
		extracted_item=_base_item(),
		document_notation_rules=None,
		llm_trigger_threshold=0.8,
	)

	assert output["school_exclusive"] is False
	assert output["required_sellers"] == []
	assert output["preferred_sellers"] == []
	assert output["directive_confidence"] == 0.0
	assert output["directive_resolved"] is False
