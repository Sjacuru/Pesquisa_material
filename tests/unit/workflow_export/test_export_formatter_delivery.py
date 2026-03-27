# FILE: tests/unit/workflow_export/test_export_formatter_delivery.py
# MODULE: MODULE-004-03 — Export Formatter & Delivery
# EPIC: EPIC-004 — User Workflow
# RESPONSIBILITY: Reserve unit tests for PDF/CSV/JSON export acceptance criteria.
# EXPORTS: Unit test stub.
# DEPENDS_ON: workflow_export/export_formatter_delivery.py.
# ACCEPTANCE_CRITERIA:
#   - Supported export formats remain testable as PDF, CSV, and JSON.
#   - Export delivery remains separate from edit and audit responsibilities.
# HUMAN_REVIEW: No.

from copy import deepcopy

from workflow_export.export_formatter_delivery import export_formatter_delivery


def _curated_set() -> dict:
	return {
		"records": [
			{
				"materialId": "mat-2",
				"latestValues": {
					"title": "Title B",
					"category": "book",
				},
			},
			{
				"materialId": "mat-1",
				"latestValues": {
					"title": "Title A",
					"category": "dictionary",
				},
			},
		],
	}


def _version_context() -> dict:
	return {
		"byMaterial": {
			"mat-1": {
				"latestVersion": 3,
				"entries": [
					{"versionNumber": 1},
					{"versionNumber": 2},
					{"versionNumber": 3},
				],
			},
			"mat-2": {
				"latestVersion": 1,
				"entries": [{"versionNumber": 1}],
			},
		},
	}


def _user_context() -> dict:
	return {"userId": "user-7", "sessionId": "session-1", "role": "editor"}


def test_only_supported_formats_pdf_csv_json_are_accepted() -> None:
	for export_format in ["pdf", "csv", "json", "PDF", "CSV", "JSON"]:
		result = export_formatter_delivery(
			_curated_set(),
			_version_context(),
			{"format": export_format},
			_user_context(),
			format_adapters=None,
			export_event_log=[],
		)

		assert result["deliveryResult"]["status"] == "success"


def test_unsupported_format_request_is_rejected_with_explicit_reason() -> None:
	result = export_formatter_delivery(
		_curated_set(),
		_version_context(),
		{"format": "xml"},
		_user_context(),
		format_adapters=None,
		export_event_log=[],
	)

	assert result["deliveryResult"]["status"] == "validation_failure"
	assert result["deliveryResult"]["reasonCode"] == "unsupported_format"


def test_empty_export_request_is_rejected_with_explicit_reason() -> None:
	result = export_formatter_delivery(
		{"records": []},
		_version_context(),
		{"format": "json"},
		_user_context(),
		format_adapters=None,
		export_event_log=[],
	)

	assert result["deliveryResult"]["status"] == "validation_failure"
	assert result["deliveryResult"]["reasonCode"] == "empty_export"


def test_export_payload_contains_latest_values_and_version_metadata_for_every_record() -> None:
	result = export_formatter_delivery(
		_curated_set(),
		_version_context(),
		{"format": "json"},
		_user_context(),
		format_adapters=None,
		export_event_log=[],
	)

	records = result["exportArtifact"]["payload"]["records"]
	assert len(records) == 2
	assert records[0]["materialId"] == "mat-1"
	assert records[0]["latestValues"]["title"] == "Title A"
	assert records[0]["versionMetadata"]["latestVersion"] == 3
	assert records[1]["materialId"] == "mat-2"
	assert records[1]["versionMetadata"]["latestVersion"] == 1


def test_export_operation_does_not_mutate_material_state_or_audit_history() -> None:
	curated_set = _curated_set()
	version_context = _version_context()
	curated_before = deepcopy(curated_set)
	context_before = deepcopy(version_context)

	export_formatter_delivery(
		curated_set,
		version_context,
		{"format": "csv"},
		_user_context(),
		format_adapters=None,
		export_event_log=[],
	)

	assert curated_set == curated_before
	assert version_context == context_before


def test_same_input_dataset_and_format_produce_structurally_identical_payload() -> None:
	first = export_formatter_delivery(
		_curated_set(),
		_version_context(),
		{"format": "pdf"},
		_user_context(),
		format_adapters=None,
		export_event_log=[],
	)
	second = export_formatter_delivery(
		_curated_set(),
		_version_context(),
		{"format": "pdf"},
		_user_context(),
		format_adapters=None,
		export_event_log=[],
	)

	assert first["exportArtifact"]["payload"] == second["exportArtifact"]["payload"]


def test_export_event_log_contains_required_fields() -> None:
	export_event_log: list[dict] = []
	result = export_formatter_delivery(
		_curated_set(),
		_version_context(),
		{"format": "json"},
		_user_context(),
		format_adapters=None,
		export_event_log=export_event_log,
	)

	assert len(export_event_log) == 1
	event = export_event_log[0]
	assert event["userId"] == "user-7"
	assert event["format"] == "json"
	assert event["itemCount"] == 2
	assert event["artifactId"] == result["deliveryResult"]["artifactId"]
	assert isinstance(event["timestamp"], str)


def test_delivery_result_distinguishes_rendering_failure_state() -> None:
	def _failing_adapter(payload: dict) -> dict:
		raise RuntimeError("boom")

	result = export_formatter_delivery(
		_curated_set(),
		_version_context(),
		{"format": "json"},
		_user_context(),
		format_adapters={"json": _failing_adapter},
		export_event_log=[],
	)

	assert result["deliveryResult"]["status"] == "rendering_failure"
	assert result["deliveryResult"]["reasonCode"] == "rendering_failed"


def test_csv_delivery_includes_business_readable_headers() -> None:
	result = export_formatter_delivery(
		_curated_set(),
		_version_context(),
		{"format": "csv"},
		_user_context(),
		format_adapters=None,
		export_event_log=[],
	)

	artifact = result["deliveryResult"]["artifact"]
	assert isinstance(artifact, str)
	assert "Item,Category,Quantity,Unit,Price,Source,URL,Version,Last Edited By,Notes" in artifact
