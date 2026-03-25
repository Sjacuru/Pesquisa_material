# FILE: tests/integration/test_source_governance_to_query_execution.py
# MODULE: integration — Source Governance to Query Execution Flow
# EPIC: EPIC-002 + EPIC-003 — Cross-Component Flow
# RESPONSIBILITY: Reserve integration tests for eligible-source handoff into query execution.
# EXPORTS: Integration test stub.
# DEPENDS_ON: source_governance/, search_ranking/.
# ACCEPTANCE_CRITERIA:
#   - Eligible-source state remains testable as an input to query execution.
#   - Suspended or ineligible sites remain explicitly excluded in the flow boundary.
# HUMAN_REVIEW: No.

from source_governance.search_eligibility_site_filter import build_searchable_site_set
from source_governance.site_failure_monitor_auto_suspension import process_site_failure_events
from source_governance.website_onboarding_trust_classifier import evaluate_website_onboarding
from search_ranking.query_orchestrator import orchestrate_query


def _ok_executor(source: dict, query: dict, timeout_seconds: float) -> dict:
	return {"results": [{"title": f"result-{source['site_id']}"}]}


def test_eligible_sites_feed_into_query_execution_after_onboarding() -> None:
	allowed_result = evaluate_website_onboarding(
		{
			"domain": "example.com",
			"label": "Good Store",
			"metadata": {"https_reachable": True, "trust_signal": "allowed"},
		}
	)

	site_trust_classifications = {
		"site-good": allowed_result,
	}
	suspension_status_registry: dict[str, dict] = {}

	searchable_sites, audit_entries = build_searchable_site_set(
		site_trust_classifications=site_trust_classifications,
		suspension_status_registry=suspension_status_registry,
	)

	assert len(searchable_sites) == 1
	assert searchable_sites[0]["site_id"] == "site-good"

	result = orchestrate_query(
		query={"text": "math book", "categoryID": "book"},
		validation_result={"is_valid": True, "dependency_chain_validated": True},
		eligible_sources=searchable_sites,
		source_query_executor=_ok_executor,
	)

	assert result["aggregatedResults"]["completionStatus"] == "complete"
	assert result["sourceMetadata"]["queriedCount"] == 1


def test_blocked_site_is_excluded_from_query_execution() -> None:
	blocked_result = evaluate_website_onboarding(
		{
			"domain": "bad-site.com",
			"label": "Dodgy Store",
			"metadata": {"https_reachable": True, "trust_signal": "blocked"},
		}
	)

	site_trust_classifications = {
		"site-bad": blocked_result,
	}

	searchable_sites, audit_entries = build_searchable_site_set(
		site_trust_classifications=site_trust_classifications,
		suspension_status_registry={},
	)

	assert searchable_sites == []
	bad_entry = next((e for e in audit_entries if e["site_id"] == "site-bad"), None)
	assert bad_entry is not None
	assert bad_entry["reason"] == "blocked"

	result = orchestrate_query(
		query={"text": "math book", "categoryID": "book"},
		validation_result={"is_valid": True, "dependency_chain_validated": True},
		eligible_sources=searchable_sites,
		source_query_executor=_ok_executor,
	)

	assert result["sourceMetadata"]["queriedCount"] == 0
	assert result["aggregatedResults"]["resultChunks"] == []


def test_auto_suspended_site_is_excluded_from_query_execution() -> None:
	allowed_result = evaluate_website_onboarding(
		{
			"domain": "flaky.com",
			"label": "Flaky Store",
			"metadata": {"https_reachable": True, "trust_signal": "allowed"},
		}
	)

	failure_events = [{"site_id": "site-flaky"} for _ in range(5)]
	retry_outcomes_map = {"site-flaky": [False, False, False]}
	suspension_config = {"failure_streak_threshold": 5}

	current_state: dict[str, dict] = {}
	for event in failure_events:
		_, current_state = process_site_failure_events(
			per_site_query_attempt_events=[event],
			retry_outcomes=retry_outcomes_map,
			suspension_threshold_config=suspension_config,
			current_state=current_state,
		)

	assert current_state["site-flaky"]["is_suspended"] is True

	site_trust_classifications = {"site-flaky": allowed_result}
	suspension_status_registry = {"site-flaky": current_state["site-flaky"]}

	searchable_sites, audit_entries = build_searchable_site_set(
		site_trust_classifications=site_trust_classifications,
		suspension_status_registry=suspension_status_registry,
	)

	assert searchable_sites == []
	flaky_entry = next((e for e in audit_entries if e["site_id"] == "site-flaky"), None)
	assert flaky_entry is not None
	assert flaky_entry["reason"] == "suspended"
