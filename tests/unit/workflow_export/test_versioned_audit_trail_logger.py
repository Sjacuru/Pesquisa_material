# FILE: tests/unit/workflow_export/test_versioned_audit_trail_logger.py
# MODULE: MODULE-004-02 — Versioned Audit Trail Logger
# EPIC: EPIC-004 — User Workflow
# RESPONSIBILITY: Reserve unit tests for append-only version-history acceptance criteria.
# EXPORTS: Unit test stub.
# DEPENDS_ON: workflow_export/versioned_audit_trail_logger.py.
# ACCEPTANCE_CRITERIA:
#   - Append-only history rules remain testable from this unit boundary.
#   - Versioning remains separate from export generation.
# HUMAN_REVIEW: No.

from workflow_export.versioned_audit_trail_logger import (
	append_version_entry,
	get_audit_history,
	get_version_diff,
)


def _accepted_edit(material_id: str, field_name: str, old_value: object, new_value: object, timestamp: str) -> tuple[dict, dict]:
	return (
		{"status": "accepted", "reasonCode": "accepted"},
		{
			"materialId": material_id,
			"userId": "user-1",
			"fieldName": field_name,
			"oldValue": old_value,
			"newValue": new_value,
			"timestamp": timestamp,
		},
	)


def test_every_accepted_edit_produces_one_version_entry() -> None:
	ledger: list[dict] = []
	index: dict[str, int] = {}
	edit_result, edit_record = _accepted_edit("mat-1", "title", "A", "B", "2026-03-25T10:00:00+00:00")

	entry = append_version_entry(edit_result, edit_record, ledger, index)

	assert entry is not None
	assert len(ledger) == 1
	assert ledger[0]["versionNumber"] == 1


def test_version_numbers_are_gapless_and_strictly_increasing_per_material() -> None:
	ledger: list[dict] = []
	index: dict[str, int] = {}
	for i in range(1, 4):
		result, record = _accepted_edit("mat-1", "title", f"v{i-1}", f"v{i}", f"2026-03-25T10:0{i}:00+00:00")
		append_version_entry(result, record, ledger, index)

	versions = [entry["versionNumber"] for entry in ledger if entry["materialId"] == "mat-1"]
	assert versions == [1, 2, 3]


def test_rejected_edits_do_not_generate_version_entries() -> None:
	ledger: list[dict] = []
	index: dict[str, int] = {}
	entry = append_version_entry(
		{"status": "rejected", "reasonCode": "schema_violation"},
		{"materialId": "mat-1", "fieldName": "title", "oldValue": "A", "newValue": ""},
		ledger,
		index,
	)

	assert entry is None
	assert ledger == []


def test_history_retrieval_returns_entries_in_version_order() -> None:
	ledger: list[dict] = []
	index: dict[str, int] = {}
	for field, old, new, ts in [
		("title", "A", "B", "2026-03-25T10:00:00+00:00"),
		("category", "book", "dictionary", "2026-03-25T10:01:00+00:00"),
	]:
		result, record = _accepted_edit("mat-9", field, old, new, ts)
		append_version_entry(result, record, ledger, index)

	history = get_audit_history("mat-9", ledger)
	versions = [entry["versionNumber"] for entry in history["entries"]]
	assert versions == [1, 2]
	assert history["latestVersion"] == 2


def test_diff_output_for_same_version_pair_is_deterministic() -> None:
	ledger: list[dict] = []
	index: dict[str, int] = {}
	for field, old, new, ts in [
		("title", "A", "B", "2026-03-25T10:00:00+00:00"),
		("notes", "", "x", "2026-03-25T10:01:00+00:00"),
		("title", "B", "C", "2026-03-25T10:02:00+00:00"),
	]:
		result, record = _accepted_edit("mat-10", field, old, new, ts)
		append_version_entry(result, record, ledger, index)

	first = get_version_diff("mat-10", 1, 3, ledger)
	second = get_version_diff("mat-10", 1, 3, ledger)
	assert first == second


def test_retention_policy_is_configurable_without_mutating_surviving_payloads() -> None:
	ledger: list[dict] = []
	index: dict[str, int] = {}
	for i in range(1, 5):
		result, record = _accepted_edit("mat-22", "title", f"v{i-1}", f"v{i}", f"2026-03-25T10:0{i}:00+00:00")
		append_version_entry(result, record, ledger, index)

	retained = get_audit_history("mat-22", ledger, retention_policy={"mode": "retain_last_n", "n": 2})
	assert [entry["versionNumber"] for entry in retained["entries"]] == [3, 4]
	assert retained["entries"][0]["newValue"] == "v3"


def test_historical_entries_are_not_overwritten_by_returned_objects() -> None:
	ledger: list[dict] = []
	index: dict[str, int] = {}
	result, record = _accepted_edit("mat-50", "title", "A", "B", "2026-03-25T10:00:00+00:00")
	append_version_entry(result, record, ledger, index)

	history = get_audit_history("mat-50", ledger)
	history["entries"][0]["newValue"] = "tampered"

	assert ledger[0]["newValue"] == "B"
