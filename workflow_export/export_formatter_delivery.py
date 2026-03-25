# FILE: workflow_export/export_formatter_delivery.py
# MODULE: MODULE-004-03 — Export Formatter & Delivery
# EPIC: EPIC-004 — User Workflow
# RESPONSIBILITY: Generate and deliver PDF, CSV, and JSON export artifacts from approved state.
# EXPORTS: Export formatting and delivery stub.
# DEPENDS_ON: workflow_export/versioned_audit_trail_logger.py, platform/storage.py.
# ACCEPTANCE_CRITERIA:
#   - Supported export formats remain explicit as PDF, CSV, and JSON.
#   - Export delivery remains separate from edit and audit responsibilities.
# HUMAN_REVIEW: Yes — file generation and delivery risk.

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json


SUPPORTED_FORMATS = {"pdf", "csv", "json"}


def _now_iso() -> str:
	return datetime.now(timezone.utc).isoformat()


def _canonical_format(value: object) -> str:
	return str(value or "").strip().lower()


def _material_id_from_record(record: dict) -> str:
	return str(
		record.get("materialId")
		or record.get("material_id")
		or record.get("result_id")
		or ""
	)


def _extract_records(curated_set: dict) -> list[dict]:
	records = curated_set.get("records")
	if not isinstance(records, list):
		return []
	return [deepcopy(record) for record in records if isinstance(record, dict)]


def _extract_selected_fields(curated_set: dict) -> list[str] | None:
	selected_fields = curated_set.get("selectedFields")
	if not isinstance(selected_fields, list):
		return None
	fields = [str(field) for field in selected_fields]
	return fields if fields else None


def _extract_latest_values(record: dict, selected_fields: list[str] | None) -> dict:
	latest_values = deepcopy(record.get("latestValues") or record.get("values") or {})
	if not isinstance(latest_values, dict):
		latest_values = {}

	if selected_fields is None:
		return latest_values

	return {
		field: latest_values.get(field)
		for field in selected_fields
		if field in latest_values
	}


def _version_metadata_for_material(material_id: str, version_context: dict) -> dict:
	by_material = version_context.get("byMaterial")
	if isinstance(by_material, dict):
		history = by_material.get(material_id)
		if isinstance(history, dict):
			entries = deepcopy(history.get("entries") or [])
			if not isinstance(entries, list):
				entries = []
			return {
				"latestVersion": int(history.get("latestVersion", 0)),
				"entryCount": len(entries),
			}

	material_histories = version_context.get("materialHistories")
	if isinstance(material_histories, list):
		for history in material_histories:
			if not isinstance(history, dict):
				continue
			if str(history.get("materialId") or "") != material_id:
				continue
			entries = deepcopy(history.get("entries") or [])
			if not isinstance(entries, list):
				entries = []
			return {
				"latestVersion": int(history.get("latestVersion", 0)),
				"entryCount": len(entries),
			}

	return {"latestVersion": 0, "entryCount": 0}


def _build_export_payload(curated_set: dict, version_context: dict, export_format: str) -> dict:
	records = _extract_records(curated_set)
	selected_fields = _extract_selected_fields(curated_set)

	payload_records = []
	for record in records:
		material_id = _material_id_from_record(record)
		payload_records.append(
			{
				"materialId": material_id,
				"latestValues": _extract_latest_values(record, selected_fields),
				"versionMetadata": _version_metadata_for_material(material_id, version_context),
			}
		)

	payload_records.sort(key=lambda item: item["materialId"])

	return {
		"format": export_format,
		"recordCount": len(payload_records),
		"records": payload_records,
	}


def _default_render_adapter(export_format: str, payload: dict) -> dict:
	return {
		"contentType": f"application/{export_format}",
		"payload": deepcopy(payload),
	}


def _render_with_adapter(export_format: str, payload: dict, format_adapters: dict | None) -> dict:
	adapters = format_adapters or {}
	adapter = adapters.get(export_format)
	if adapter is None:
		return _default_render_adapter(export_format, payload)

	return adapter(deepcopy(payload))


def export_formatter_delivery(
	curated_set: dict,
	version_context: dict,
	export_request: dict,
	user_context: dict,
	format_adapters: dict | None,
	export_event_log: list[dict],
) -> dict[str, object]:
	export_format = _canonical_format(export_request.get("format"))
	if export_format not in SUPPORTED_FORMATS:
		return {
			"exportArtifact": None,
			"deliveryResult": {
				"status": "validation_failure",
				"reasonCode": "unsupported_format",
				"artifactId": None,
				"deliveredAt": None,
			},
			"exportEvent": None,
		}

	if len(_extract_records(curated_set)) == 0:
		return {
			"exportArtifact": None,
			"deliveryResult": {
				"status": "validation_failure",
				"reasonCode": "empty_export",
				"artifactId": None,
				"deliveredAt": None,
			},
			"exportEvent": None,
		}

	payload = _build_export_payload(
		deepcopy(curated_set),
		deepcopy(version_context),
		export_format,
	)

	payload_signature = json.dumps(payload, sort_keys=True, separators=(",", ":"))
	artifact_id = f"artifact-{sha256(payload_signature.encode('utf-8')).hexdigest()[:16]}"
	generated_at = _now_iso()

	try:
		content_ref = _render_with_adapter(export_format, payload, format_adapters)
	except Exception:
		return {
			"exportArtifact": None,
			"deliveryResult": {
				"status": "rendering_failure",
				"reasonCode": "rendering_failed",
				"artifactId": None,
				"deliveredAt": None,
			},
			"exportEvent": None,
		}

	export_artifact = {
		"artifactId": artifact_id,
		"format": export_format,
		"contentRef": content_ref,
		"generatedAt": generated_at,
		"payload": payload,
	}

	delivery_result = {
		"status": "success",
		"reasonCode": "delivered",
		"artifactId": artifact_id,
		"deliveredAt": generated_at,
	}

	export_event = {
		"userId": user_context.get("userId"),
		"format": export_format,
		"itemCount": payload["recordCount"],
		"timestamp": generated_at,
		"artifactId": artifact_id,
	}
	export_event_log.append(deepcopy(export_event))

	return {
		"exportArtifact": export_artifact,
		"deliveryResult": delivery_result,
		"exportEvent": export_event,
	}
