import pytest

from intake_canonicalization.directive_audit_persistence import persist_llm_payload


def test_persist_llm_payload_in_audit_json_mode() -> None:
	audit_ledger: list[dict] = []
	llm_log: list[dict] = []

	record = persist_llm_payload(
		item_id="line-1",
		llm_result={"llm_confidence": 0.82},
		error_payload=None,
		persistence_mode="audit_json",
		directive_audit_ledger=audit_ledger,
		llm_call_log_ledger=llm_log,
	)

	assert record is not None
	assert record["event"] == "llm_payload_audit_json"
	assert len(audit_ledger) == 1
	assert llm_log == []


def test_persist_llm_payload_in_separate_log_mode() -> None:
	audit_ledger: list[dict] = []
	llm_log: list[dict] = []

	record = persist_llm_payload(
		item_id="line-2",
		llm_result={"llm_confidence": 0.77},
		error_payload=None,
		persistence_mode="separate_log",
		directive_audit_ledger=audit_ledger,
		llm_call_log_ledger=llm_log,
	)

	assert record is not None
	assert record["event"] == "llm_call_log"
	assert audit_ledger == []
	assert len(llm_log) == 1


def test_persist_llm_payload_invalid_mode_raises() -> None:
	with pytest.raises(ValueError):
		persist_llm_payload(
			item_id="line-3",
			llm_result=None,
			error_payload={"error_reason": "timeout"},
			persistence_mode="unknown",
		)
