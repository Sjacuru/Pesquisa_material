# FILE: workflow_export/versioned_audit_trail_logger.py
# MODULE: MODULE-004-02 — Versioned Audit Trail Logger
# EPIC: EPIC-004 — User Workflow
# RESPONSIBILITY: Persist append-only version history for edits and review decisions.
# EXPORTS: Versioned audit trail stub.
# DEPENDS_ON: workflow_export/user_edit_handler.py, platform/observability.py.
# ACCEPTANCE_CRITERIA:
#   - Version history remains append-only and distinguishable from current state.
#   - Audit responsibility remains separate from export generation.
# HUMAN_REVIEW: Yes — traceability and data durability.

from __future__ import annotations

from copy import deepcopy


def append_version_entry(
	edit_result: dict,
	edit_record: dict | None,
	version_ledger: list[dict],
	version_index: dict[str, int],
) -> dict | None:
	"""
	Append exactly one immutable version entry for accepted edits.
	Returns the appended entry copy or None when edit is not accepted.
	"""
	if edit_result.get("status") != "accepted":
		return None
	if not isinstance(edit_record, dict):
		return None

	material_id = str(edit_record.get("materialId") or "")
	if not material_id:
		return None

	next_version = int(version_index.get(material_id, 0)) + 1
	version_entry = {
		"materialId": material_id,
		"versionNumber": next_version,
		"userId": edit_record.get("userId"),
		"fieldName": edit_record.get("fieldName"),
		"oldValue": edit_record.get("oldValue"),
		"newValue": edit_record.get("newValue"),
		"timestamp": edit_record.get("timestamp"),
	}

	version_ledger.append(deepcopy(version_entry))
	version_index[material_id] = next_version
	return deepcopy(version_entry)


def _apply_retention(entries: list[dict], retention_policy: dict | None) -> list[dict]:
	if not retention_policy:
		return entries

	mode = str(retention_policy.get("mode") or "none").lower()
	if mode == "retain_last_n":
		n = int(retention_policy.get("n", 0))
		if n <= 0:
			return []
		return entries[-n:]

	return entries


def get_audit_history(
	material_id: str,
	version_ledger: list[dict],
	retention_policy: dict | None = None,
) -> dict[str, object]:
	entries = [
		deepcopy(entry)
		for entry in version_ledger
		if str(entry.get("materialId") or "") == str(material_id)
	]
	entries.sort(key=lambda entry: int(entry.get("versionNumber", 0)))
	retained_entries = _apply_retention(entries, retention_policy)

	latest_version = 0
	if retained_entries:
		latest_version = int(retained_entries[-1].get("versionNumber", 0))

	return {
		"entries": retained_entries,
		"latestVersion": latest_version,
		"retentionState": {
			"inputCount": len(entries),
			"retainedCount": len(retained_entries),
			"mode": (retention_policy or {}).get("mode", "none"),
		},
	}


def get_version_diff(
	material_id: str,
	from_version: int,
	to_version: int,
	version_ledger: list[dict],
) -> dict[str, object]:
	if from_version >= to_version:
		raise ValueError("from_version must be smaller than to_version")

	entries = [
		entry
		for entry in version_ledger
		if str(entry.get("materialId") or "") == str(material_id)
		and from_version < int(entry.get("versionNumber", 0)) <= to_version
	]
	entries.sort(key=lambda entry: int(entry.get("versionNumber", 0)))

	changed_fields = [
		{
			"versionNumber": int(entry.get("versionNumber", 0)),
			"fieldName": entry.get("fieldName"),
			"oldValue": deepcopy(entry.get("oldValue")),
			"newValue": deepcopy(entry.get("newValue")),
		}
		for entry in entries
	]

	return {
		"fromVersion": from_version,
		"toVersion": to_version,
		"changedFields": changed_fields,
	}
