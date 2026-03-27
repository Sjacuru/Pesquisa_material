import pytest

from intake_canonicalization.directive_runtime_config import parse_directive_runtime_config


def test_parse_runtime_defaults_for_disabled_stages() -> None:
	parsed = parse_directive_runtime_config(None)

	assert parsed["stage_b_enabled"] is False
	assert parsed["stage_c_enabled"] is False
	assert parsed["shadow_mode"] is True
	assert parsed["llm_persistence_mode"] == "audit_json"


def test_parse_runtime_stage_b_and_c_with_string_values() -> None:
	parsed = parse_directive_runtime_config(
		{
			"stage_b_enabled": "true",
			"stage_c_enabled": "true",
			"llm_trigger_threshold": "0.9",
			"llm_accept_threshold": "0.8",
			"llm_max_latency_ms": "1500",
			"llm_max_retries": "2",
			"shadow_mode": "false",
			"llm_persistence_mode": "separate_log",
		}
	)

	assert parsed["stage_b_enabled"] is True
	assert parsed["stage_c_enabled"] is True
	assert parsed["llm_trigger_threshold"] == 0.9
	assert parsed["llm_accept_threshold"] == 0.8
	assert parsed["llm_max_latency_ms"] == 1500
	assert parsed["llm_max_retries"] == 2
	assert parsed["shadow_mode"] is False
	assert parsed["llm_persistence_mode"] == "separate_log"


def test_parse_runtime_rejects_invalid_persistence_mode() -> None:
	with pytest.raises(ValueError):
		parse_directive_runtime_config(
			{
				"stage_b_enabled": True,
				"llm_trigger_threshold": 0.9,
				"llm_max_latency_ms": 1500,
				"llm_persistence_mode": "bad",
			}
		)


def test_parse_runtime_rejects_stage_b_without_latency() -> None:
	with pytest.raises(ValueError):
		parse_directive_runtime_config(
			{
				"stage_b_enabled": True,
				"llm_trigger_threshold": 0.9,
			}
		)
