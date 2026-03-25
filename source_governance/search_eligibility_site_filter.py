# FILE: source_governance/search_eligibility_site_filter.py
# MODULE: MODULE-002-04 — Search Eligibility Site Filter
# EPIC: EPIC-002 — Brand Handling & Source Trust
# RESPONSIBILITY: Determine whether a source site is eligible for search at runtime.
# EXPORTS: Search-eligibility filtering stub.
# DEPENDS_ON: source_governance/website_onboarding_trust_classifier.py.
# ACCEPTANCE_CRITERIA:
#   - Eligible and ineligible site states are explicit.
#   - Search filtering remains separate from onboarding classification.
# HUMAN_REVIEW: No.

from __future__ import annotations


def _is_suspended(site_id: str, suspension_status_registry: dict[str, dict]) -> bool:
	status = suspension_status_registry.get(site_id, {})
	return bool(status.get("is_suspended", False))


def build_searchable_site_set(
	site_trust_classifications: dict[str, dict],
	suspension_status_registry: dict[str, dict],
) -> tuple[list[dict], list[dict]]:
	"""
	Build searchable site set from latest trust + suspension states.

	Returns:
	  searchable_site_set: eligible site entries
	  filtering_audit_entries: explicit per-site decision outcomes
	"""
	searchable_site_set: list[dict] = []
	filtering_audit_entries: list[dict] = []

	for site_id, trust_payload in site_trust_classifications.items():
		trust_status = str(trust_payload.get("trust_classification_status", "")).strip().lower()
		suspended = _is_suspended(site_id, suspension_status_registry)

		eligible = (
			trust_status in {"allowed", "review_required"}
			and not suspended
		)

		reason = "eligible"
		if trust_status == "blocked":
			reason = "blocked"
		elif suspended:
			reason = "suspended"
		elif trust_status not in {"allowed", "review_required"}:
			reason = "unknown_trust_status"

		audit_entry = {
			"site_id": site_id,
			"trust_classification_status": trust_status,
			"is_suspended": suspended,
			"is_search_eligible": eligible,
			"reason": reason,
		}
		filtering_audit_entries.append(audit_entry)

		if eligible:
			searchable_site_set.append(
				{
					"site_id": site_id,
					"trust_classification_status": trust_status,
				}
			)

	return searchable_site_set, filtering_audit_entries
