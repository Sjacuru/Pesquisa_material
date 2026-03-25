# FILE: source_governance/site_failure_monitor_auto_suspension.py
# MODULE: MODULE-002-05 — Site Failure Monitor & Auto-Suspension
# EPIC: EPIC-002 — Brand Handling & Source Trust
# RESPONSIBILITY: Track source failure streaks and transition site lifecycle state when suspension criteria are met.
# EXPORTS: Source failure monitoring and suspension stub.
# DEPENDS_ON: source_governance/website_onboarding_trust_classifier.py, platform/observability.py.
# ACCEPTANCE_CRITERIA:
#   - Failure-monitoring state remains explicit and auditable.
#   - Suspension transitions are represented separately from search filtering.
# HUMAN_REVIEW: Yes — operational control and source availability.

from __future__ import annotations

from copy import deepcopy


def _initial_site_state() -> dict[str, object]:
	return {
		"failure_streak": 0,
		"is_suspended": False,
	}


def update_site_suspension_state(
	site_id: str,
	retry_outcomes: list[bool],
	current_state: dict[str, dict[str, object]],
	suspension_threshold_config: dict[str, int],
	revalidation_event: bool = False,
) -> tuple[dict[str, object], dict[str, object]]:
	"""
	Update one site state using one query-cycle retry outcome list.

	AC1: streak increments only when first 3 retry attempts fail.
	AC2: switches to suspended when streak reaches configured threshold.
	AC3: suspended state persists until explicit revalidation event.
	"""
	threshold = int(suspension_threshold_config.get("failure_streak_threshold", 5))
	state = deepcopy(current_state.get(site_id, _initial_site_state()))

	if revalidation_event:
		state["is_suspended"] = False
		state["failure_streak"] = 0
		status = {
			"site_id": site_id,
			"is_suspended": False,
			"transition": "revalidated",
		}
		return status, state

	if state["is_suspended"]:
		status = {
			"site_id": site_id,
			"is_suspended": True,
			"transition": "no_change",
		}
		return status, state

	first_three = retry_outcomes[:3]
	three_failed = len(first_three) == 3 and all(outcome is False for outcome in first_three)

	if three_failed:
		state["failure_streak"] = int(state.get("failure_streak", 0)) + 1
	else:
		state["failure_streak"] = 0

	transition = "no_change"
	if int(state["failure_streak"]) >= threshold:
		state["is_suspended"] = True
		transition = "suspended"

	status = {
		"site_id": site_id,
		"is_suspended": bool(state["is_suspended"]),
		"transition": transition,
	}
	return status, state


def process_site_failure_events(
	per_site_query_attempt_events: list[dict],
	retry_outcomes: dict[str, list[bool]],
	suspension_threshold_config: dict[str, int],
	current_state: dict[str, dict[str, object]] | None = None,
	revalidation_events: set[str] | None = None,
) -> tuple[dict[str, dict[str, object]], dict[str, dict[str, object]]]:
	"""
	Batch-update site suspension states.

	Returns:
	  updated_suspension_status: {site_id: {is_suspended, transition}}
	  failure_streak_state: {site_id: {failure_streak, is_suspended}}
	"""
	state = deepcopy(current_state or {})
	updated_suspension_status: dict[str, dict[str, object]] = {}
	revalidation_events = revalidation_events or set()

	for event in per_site_query_attempt_events:
		site_id = str(event.get("site_id") or "")
		if not site_id:
			continue

		status, next_state = update_site_suspension_state(
			site_id=site_id,
			retry_outcomes=retry_outcomes.get(site_id, []),
			current_state=state,
			suspension_threshold_config=suspension_threshold_config,
			revalidation_event=site_id in revalidation_events,
		)
		state[site_id] = next_state
		updated_suspension_status[site_id] = status

	return updated_suspension_status, state
