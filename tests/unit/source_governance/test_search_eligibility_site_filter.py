# FILE: tests/unit/source_governance/test_search_eligibility_site_filter.py
# MODULE: MODULE-002-04 — Search Eligibility Site Filter
# EPIC: EPIC-002 — Brand Handling & Source Trust
# RESPONSIBILITY: Reserve unit tests for search-eligibility filtering acceptance criteria.
# EXPORTS: Unit test stub.
# DEPENDS_ON: source_governance/search_eligibility_site_filter.py.
# ACCEPTANCE_CRITERIA:
#   - Eligible and ineligible site states are testable from this unit boundary.
#   - Filtering behavior remains separate from onboarding classification.
# HUMAN_REVIEW: No.

from source_governance.search_eligibility_site_filter import build_searchable_site_set


def test_ac1_blocked_sites_are_always_excluded() -> None:
	trust = {
		"site-a": {"trust_classification_status": "blocked"},
		"site-b": {"trust_classification_status": "allowed"},
	}
	suspension = {
		"site-a": {"is_suspended": False},
		"site-b": {"is_suspended": False},
	}

	searchable, audit = build_searchable_site_set(trust, suspension)

	assert [entry["site_id"] for entry in searchable] == ["site-b"]
	blocked_audit = [entry for entry in audit if entry["site_id"] == "site-a"][0]
	assert blocked_audit["is_search_eligible"] is False
	assert blocked_audit["reason"] == "blocked"


def test_ac2_allowed_and_review_required_non_suspended_are_included() -> None:
	trust = {
		"site-1": {"trust_classification_status": "allowed"},
		"site-2": {"trust_classification_status": "review_required"},
	}
	suspension = {
		"site-1": {"is_suspended": False},
		"site-2": {"is_suspended": False},
	}

	searchable, _ = build_searchable_site_set(trust, suspension)
	ids = [entry["site_id"] for entry in searchable]

	assert set(ids) == {"site-1", "site-2"}


def test_ac2_suspended_site_is_excluded_even_if_allowed() -> None:
	trust = {"site-3": {"trust_classification_status": "allowed"}}
	suspension = {"site-3": {"is_suspended": True}}

	searchable, audit = build_searchable_site_set(trust, suspension)

	assert searchable == []
	assert audit[0]["is_search_eligible"] is False
	assert audit[0]["reason"] == "suspended"


def test_ac3_filter_uses_latest_states_at_filter_time() -> None:
	trust = {"site-4": {"trust_classification_status": "review_required"}}

	searchable_before, _ = build_searchable_site_set(
		trust,
		{"site-4": {"is_suspended": False}},
	)
	searchable_after, audit_after = build_searchable_site_set(
		trust,
		{"site-4": {"is_suspended": True}},
	)

	assert len(searchable_before) == 1
	assert searchable_after == []
	assert audit_after[0]["is_search_eligible"] is False


def test_unknown_trust_status_is_not_included() -> None:
	trust = {"site-5": {"trust_classification_status": "something_else"}}
	suspension = {"site-5": {"is_suspended": False}}

	searchable, audit = build_searchable_site_set(trust, suspension)

	assert searchable == []
	assert audit[0]["reason"] == "unknown_trust_status"
