# FILE: source_governance/brand_substitution_audit_logger.py
# MODULE: MODULE-002-02 — Brand Substitution Audit Logger
# EPIC: EPIC-002 — Brand Handling & Source Trust
# RESPONSIBILITY: Persist audit-ready brand substitution reason-code events.
# EXPORTS: Brand substitution audit logging stub.
# DEPENDS_ON: source_governance/brand_expansion_approval_gate.py, platform/observability.py.
# ACCEPTANCE_CRITERIA:
#   - Reason-code events are modeled as explicit audit records.
#   - Logging responsibility remains separate from approval decision logic.
# HUMAN_REVIEW: No.

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone


def _iso_timestamp_now() -> str:
	return datetime.now(timezone.utc).isoformat()


def append_substitution_audit_record(
	audit_log_store: list[dict],
	expansion_approval_decision: dict,
	reason_code: str | None,
	event_timestamp: str | None = None,
) -> dict | None:
	"""
	Append one immutable substitution audit record for approved expansions only.

	Returns the appended record when created, otherwise None.
	"""
	if expansion_approval_decision.get("decision_state") != "approved":
		return None

	record = {
		"item_id": expansion_approval_decision.get("item_id"),
		"decision_state": "approved",
		"reason_code": reason_code,
		"event_timestamp": event_timestamp or _iso_timestamp_now(),
		"same_brand_offer_count": expansion_approval_decision.get("same_brand_offer_count"),
		"candidate_brand_pool": deepcopy(expansion_approval_decision.get("candidate_brand_pool", [])),
	}

	audit_log_store.append(record)
	return deepcopy(record)
