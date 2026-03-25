# FILE: source_governance/brand_expansion_approval_gate.py
# MODULE: MODULE-002-01 — Brand Expansion Approval Gate
# EPIC: EPIC-002 — Brand Handling & Source Trust
# RESPONSIBILITY: Capture and expose user approval decisions for brand-expansion scenarios.
# EXPORTS: Brand-expansion approval stub.
# DEPENDS_ON: None.
# ACCEPTANCE_CRITERIA:
#   - Approval state remains explicit and separate from ranking logic.
#   - Denial and approval paths are both representable.
# HUMAN_REVIEW: No.

from __future__ import annotations


def evaluate_brand_expansion_gate(
	item_id: str,
	same_brand_offer_count: int,
	candidate_brand_pool: list[str],
	user_approval_decision: bool | None = None,
	reason_code: str | None = None,
) -> dict[str, object]:
	"""
	Evaluate whether cross-brand expansion is allowed for a single item.

	Rules:
	- If same-brand offers >= 3: no expansion prompt is shown.
	- If same-brand offers < 3: user approval is required before expansion.
	"""
	if same_brand_offer_count >= 3:
		return {
			"item_id": item_id,
			"same_brand_offer_count": same_brand_offer_count,
			"candidate_brand_pool": candidate_brand_pool,
			"requires_user_approval": False,
			"prompt_shown": False,
			"expansion_allowed": False,
			"decision_state": "not_needed",
			"reason_code": None,
		}

	if user_approval_decision is None:
		return {
			"item_id": item_id,
			"same_brand_offer_count": same_brand_offer_count,
			"candidate_brand_pool": candidate_brand_pool,
			"requires_user_approval": True,
			"prompt_shown": True,
			"expansion_allowed": False,
			"decision_state": "awaiting_user_approval",
			"reason_code": None,
		}

	if user_approval_decision is True:
		return {
			"item_id": item_id,
			"same_brand_offer_count": same_brand_offer_count,
			"candidate_brand_pool": candidate_brand_pool,
			"requires_user_approval": True,
			"prompt_shown": True,
			"expansion_allowed": True,
			"decision_state": "approved",
			"reason_code": reason_code,
		}

	return {
		"item_id": item_id,
		"same_brand_offer_count": same_brand_offer_count,
		"candidate_brand_pool": candidate_brand_pool,
		"requires_user_approval": True,
		"prompt_shown": True,
		"expansion_allowed": False,
		"decision_state": "denied",
		"reason_code": reason_code,
	}
