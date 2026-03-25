# FILE: tests/integration/test_edit_history_to_export_flow.py
# MODULE: integration — Edit History to Export Flow
# EPIC: EPIC-004 — Cross-Component Flow
# RESPONSIBILITY: Reserve integration tests for version-history handoff into export generation.
# EXPORTS: Integration test stub.
# DEPENDS_ON: workflow_export/.
# ACCEPTANCE_CRITERIA:
#   - Versioned state remains testable as an input to export generation.
#   - Supported export-format boundaries remain explicit in the integration flow.
# HUMAN_REVIEW: No.

from workflow_export.export_formatter_delivery import export_formatter_delivery
from workflow_export.user_edit_handler import handle_user_edit
from workflow_export.versioned_audit_trail_logger import append_version_entry, get_audit_history


def _make_material(result_id: str) -> dict:
	return {"result_id": result_id, "title": "Initial Title"}


def _user_context() -> dict:
	return {"userId": "user-1", "sessionId": "s1", "role": "editor"}


def _category_contract() -> set[str]:
	return {"book", "dictionary", "notebook", "apostila", "general supplies"}


def test_versioned_state_feeds_export_generation() -> None:
	local_edit_store: list[dict] = []
	version_ledger: list[dict] = []
	version_index: dict[str, int] = {}

	material = _make_material("mat-flow-1")

	edit_result = handle_user_edit(
		material_item=material,
		edit_request={"fieldName": "title", "oldValue": "Initial Title", "newValue": "Updated Title", "reasonNote": ""},
		user_context=_user_context(),
		category_contract=_category_contract(),
		local_edit_store=local_edit_store,
	)

	assert edit_result["editResult"]["status"] == "accepted"

	append_version_entry(
		edit_result=edit_result["editResult"],
		edit_record=edit_result["editRecord"],
		version_ledger=version_ledger,
		version_index=version_index,
	)

	history = get_audit_history("mat-flow-1", version_ledger)
	assert history["latestVersion"] == 1

	curated_set = {
		"records": [
			{
				"materialId": "mat-flow-1",
				"latestValues": {"title": "Updated Title"},
			}
		]
	}
	version_context = {
		"byMaterial": {
			"mat-flow-1": history,
		}
	}

	export_event_log: list[dict] = []
	result = export_formatter_delivery(
		curated_set=curated_set,
		version_context=version_context,
		export_request={"format": "json"},
		user_context=_user_context(),
		format_adapters=None,
		export_event_log=export_event_log,
	)

	assert result["deliveryResult"]["status"] == "success"
	records = result["exportArtifact"]["payload"]["records"]
	assert records[0]["materialId"] == "mat-flow-1"
	assert records[0]["versionMetadata"]["latestVersion"] == 1
	assert len(export_event_log) == 1


def test_unsupported_format_is_rejected_at_export_boundary() -> None:
	curated_set = {
		"records": [{"materialId": "mat-flow-2", "latestValues": {"title": "A Book"}}]
	}

	result = export_formatter_delivery(
		curated_set=curated_set,
		version_context={},
		export_request={"format": "docx"},
		user_context=_user_context(),
		format_adapters=None,
		export_event_log=[],
	)

	assert result["deliveryResult"]["status"] == "validation_failure"
	assert result["deliveryResult"]["reasonCode"] == "unsupported_format"
