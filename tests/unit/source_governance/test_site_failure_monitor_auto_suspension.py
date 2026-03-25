# FILE: tests/unit/source_governance/test_site_failure_monitor_auto_suspension.py
# MODULE: MODULE-002-05 — Site Failure Monitor & Auto-Suspension
# EPIC: EPIC-002 — Brand Handling & Source Trust
# RESPONSIBILITY: Reserve unit tests for source-failure monitoring and suspension acceptance criteria.
# EXPORTS: Unit test stub.
# DEPENDS_ON: source_governance/site_failure_monitor_auto_suspension.py.
# ACCEPTANCE_CRITERIA:
#   - Failure streak handling is testable from this unit boundary.
#   - Suspension transitions remain explicitly assertable.
# HUMAN_REVIEW: No.

from source_governance.site_failure_monitor_auto_suspension import (
	process_site_failure_events,
	update_site_suspension_state,
)


def test_ac1_streak_increments_only_after_three_failed_retries() -> None:
	status, state = update_site_suspension_state(
		site_id="site-a",
		retry_outcomes=[False, False, False],
		current_state={},
		suspension_threshold_config={"failure_streak_threshold": 5},
	)

	assert status["is_suspended"] is False
	assert state["failure_streak"] == 1


def test_ac1_less_than_three_attempts_does_not_increment_streak() -> None:
	status, state = update_site_suspension_state(
		site_id="site-a",
		retry_outcomes=[False, False],
		current_state={"site-a": {"failure_streak": 2, "is_suspended": False}},
		suspension_threshold_config={"failure_streak_threshold": 5},
	)

	assert status["is_suspended"] is False
	assert state["failure_streak"] == 0


def test_ac1_any_success_within_three_attempts_resets_streak() -> None:
	status, state = update_site_suspension_state(
		site_id="site-a",
		retry_outcomes=[False, True, False],
		current_state={"site-a": {"failure_streak": 3, "is_suspended": False}},
		suspension_threshold_config={"failure_streak_threshold": 5},
	)

	assert status["is_suspended"] is False
	assert state["failure_streak"] == 0


def test_ac2_site_suspends_when_threshold_reached() -> None:
	status, state = update_site_suspension_state(
		site_id="site-b",
		retry_outcomes=[False, False, False],
		current_state={"site-b": {"failure_streak": 4, "is_suspended": False}},
		suspension_threshold_config={"failure_streak_threshold": 5},
	)

	assert state["failure_streak"] == 5
	assert status["is_suspended"] is True
	assert status["transition"] == "suspended"


def test_ac3_suspended_site_remains_suspended_until_revalidation() -> None:
	status, state = update_site_suspension_state(
		site_id="site-c",
		retry_outcomes=[True, True, True],
		current_state={"site-c": {"failure_streak": 7, "is_suspended": True}},
		suspension_threshold_config={"failure_streak_threshold": 5},
	)

	assert status["is_suspended"] is True
	assert state["is_suspended"] is True
	assert state["failure_streak"] == 7


def test_ac3_revalidation_event_unsuspends_and_resets_streak() -> None:
	status, state = update_site_suspension_state(
		site_id="site-c",
		retry_outcomes=[False, False, False],
		current_state={"site-c": {"failure_streak": 7, "is_suspended": True}},
		suspension_threshold_config={"failure_streak_threshold": 5},
		revalidation_event=True,
	)

	assert status["is_suspended"] is False
	assert status["transition"] == "revalidated"
	assert state["failure_streak"] == 0


def test_batch_processing_returns_updated_status_and_state() -> None:
	events = [{"site_id": "site-1"}, {"site_id": "site-2"}]
	outcomes = {
		"site-1": [False, False, False],
		"site-2": [False, True, False],
	}

	updated_suspension_status, failure_streak_state = process_site_failure_events(
		per_site_query_attempt_events=events,
		retry_outcomes=outcomes,
		suspension_threshold_config={"failure_streak_threshold": 2},
	)

	assert set(updated_suspension_status.keys()) == {"site-1", "site-2"}
	assert failure_streak_state["site-1"]["failure_streak"] == 1
	assert failure_streak_state["site-2"]["failure_streak"] == 0
