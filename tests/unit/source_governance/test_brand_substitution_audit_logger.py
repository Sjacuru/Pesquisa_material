# FILE: tests/unit/source_governance/test_brand_substitution_audit_logger.py
# MODULE: MODULE-002-02 — Brand Substitution Audit Logger
# EPIC: EPIC-002 — Brand Handling & Source Trust
# RESPONSIBILITY: Reserve unit tests for substitution-audit logging acceptance criteria.
# EXPORTS: Unit test stub.
# DEPENDS_ON: source_governance/brand_substitution_audit_logger.py.
# ACCEPTANCE_CRITERIA:
#   - Reason-code audit events are testable from this unit boundary.
#   - Logging responsibility remains isolated from approval logic.
# HUMAN_REVIEW: No.

from source_governance.brand_substitution_audit_logger import append_substitution_audit_record


def test_ac1_approved_expansion_persists_reason_code_and_timestamp() -> None:
	audit_log_store: list[dict] = []
	decision = {
		"item_id": "item-100",
		"decision_state": "approved",
		"same_brand_offer_count": 1,
		"candidate_brand_pool": ["Brand B", "Brand C"],
	}

	created = append_substitution_audit_record(
		audit_log_store=audit_log_store,
		expansion_approval_decision=decision,
		reason_code="LOW_SAME_BRAND_COVERAGE",
		event_timestamp="2026-03-25T10:00:00+00:00",
	)

	assert created is not None
	assert len(audit_log_store) == 1
	assert created["reason_code"] == "LOW_SAME_BRAND_COVERAGE"
	assert created["event_timestamp"] == "2026-03-25T10:00:00+00:00"


def test_ac2_non_approved_decision_creates_no_record() -> None:
	audit_log_store: list[dict] = []
	denied_decision = {
		"item_id": "item-101",
		"decision_state": "denied",
		"same_brand_offer_count": 1,
		"candidate_brand_pool": ["Brand B"],
	}

	created = append_substitution_audit_record(
		audit_log_store=audit_log_store,
		expansion_approval_decision=denied_decision,
		reason_code="SHOULD_NOT_BE_SAVED",
		event_timestamp="2026-03-25T10:00:00+00:00",
	)

	assert created is None
	assert audit_log_store == []


def test_ac2_awaiting_approval_decision_creates_no_record() -> None:
	audit_log_store: list[dict] = []
	awaiting_decision = {
		"item_id": "item-102",
		"decision_state": "awaiting_user_approval",
		"same_brand_offer_count": 2,
		"candidate_brand_pool": ["Brand X"],
	}

	created = append_substitution_audit_record(
		audit_log_store=audit_log_store,
		expansion_approval_decision=awaiting_decision,
		reason_code="PENDING",
	)

	assert created is None
	assert audit_log_store == []


def test_ac3_multiple_approved_expansions_append_distinct_entries() -> None:
	audit_log_store: list[dict] = []
	decision = {
		"item_id": "item-200",
		"decision_state": "approved",
		"same_brand_offer_count": 0,
		"candidate_brand_pool": ["Brand N", "Brand M"],
	}

	first = append_substitution_audit_record(
		audit_log_store=audit_log_store,
		expansion_approval_decision=decision,
		reason_code="CODE_A",
		event_timestamp="2026-03-25T10:00:00+00:00",
	)
	second = append_substitution_audit_record(
		audit_log_store=audit_log_store,
		expansion_approval_decision=decision,
		reason_code="CODE_B",
		event_timestamp="2026-03-25T10:05:00+00:00",
	)

	assert len(audit_log_store) == 2
	assert first is not None and second is not None
	assert audit_log_store[0] != audit_log_store[1]
	assert audit_log_store[0]["reason_code"] == "CODE_A"
	assert audit_log_store[1]["reason_code"] == "CODE_B"


def test_ac3_returned_record_is_immutable_copy_not_store_reference() -> None:
	audit_log_store: list[dict] = []
	decision = {
		"item_id": "item-300",
		"decision_state": "approved",
		"same_brand_offer_count": 1,
		"candidate_brand_pool": ["Brand Q"],
	}

	created = append_substitution_audit_record(
		audit_log_store=audit_log_store,
		expansion_approval_decision=decision,
		reason_code="IMMUTABLE_TEST",
		event_timestamp="2026-03-25T11:00:00+00:00",
	)

	assert created is not None
	created["reason_code"] = "MUTATED_OUTSIDE"
	assert audit_log_store[0]["reason_code"] == "IMMUTABLE_TEST"
