# FILE: tests/unit/source_governance/test_brand_expansion_approval_gate.py
# MODULE: MODULE-002-01 — Brand Expansion Approval Gate
# EPIC: EPIC-002 — Brand Handling & Source Trust
# RESPONSIBILITY: Reserve unit tests for brand-expansion approval acceptance criteria.
# EXPORTS: Unit test stub.
# DEPENDS_ON: source_governance/brand_expansion_approval_gate.py.
# ACCEPTANCE_CRITERIA:
#   - Approval and denial outcomes are testable from this unit boundary.
#   - Approval-state handling remains separate from ranking behavior.
# HUMAN_REVIEW: No.

from source_governance.brand_expansion_approval_gate import evaluate_brand_expansion_gate


def test_ac1_same_brand_offer_count_gte_3_shows_no_prompt() -> None:
	result = evaluate_brand_expansion_gate(
		item_id="item-1",
		same_brand_offer_count=3,
		candidate_brand_pool=["Brand A", "Brand B"],
	)

	assert result["requires_user_approval"] is False
	assert result["prompt_shown"] is False
	assert result["decision_state"] == "not_needed"


def test_ac1_same_brand_offer_count_gte_3_does_not_expand() -> None:
	result = evaluate_brand_expansion_gate(
		item_id="item-2",
		same_brand_offer_count=5,
		candidate_brand_pool=["Brand A", "Brand B"],
		user_approval_decision=True,
	)

	assert result["expansion_allowed"] is False


def test_ac2_same_brand_offer_count_below_3_requires_per_item_approval() -> None:
	result = evaluate_brand_expansion_gate(
		item_id="item-3",
		same_brand_offer_count=2,
		candidate_brand_pool=["Brand A", "Brand B"],
	)

	assert result["requires_user_approval"] is True
	assert result["prompt_shown"] is True
	assert result["decision_state"] == "awaiting_user_approval"


def test_ac2_below_3_approved_decision_allows_expansion() -> None:
	result = evaluate_brand_expansion_gate(
		item_id="item-4",
		same_brand_offer_count=1,
		candidate_brand_pool=["Brand A", "Brand B"],
		user_approval_decision=True,
	)

	assert result["decision_state"] == "approved"
	assert result["expansion_allowed"] is True


def test_denial_path_is_explicitly_representable() -> None:
	result = evaluate_brand_expansion_gate(
		item_id="item-5",
		same_brand_offer_count=0,
		candidate_brand_pool=["Brand A", "Brand B"],
		user_approval_decision=False,
	)

	assert result["decision_state"] == "denied"
	assert result["expansion_allowed"] is False


def test_reason_code_is_runtime_configured_value_and_passed_through() -> None:
	result = evaluate_brand_expansion_gate(
		item_id="item-6",
		same_brand_offer_count=1,
		candidate_brand_pool=["Brand A", "Brand B"],
		user_approval_decision=True,
		reason_code="CUSTOM_TAXONOMY_CODE",
	)

	assert result["reason_code"] == "CUSTOM_TAXONOMY_CODE"
