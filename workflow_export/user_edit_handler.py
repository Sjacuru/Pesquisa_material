# FILE: workflow_export/user_edit_handler.py
# MODULE: MODULE-004-01 — User Edit Handler
# EPIC: EPIC-004 — User Workflow
# RESPONSIBILITY: Apply user edits within approved editable-field boundaries.
# EXPORTS: User edit handling stub.
# DEPENDS_ON: search_ranking/ranking_engine.py, intake_canonicalization/category_rules_eligibility_validator.py.
# ACCEPTANCE_CRITERIA:
#   - Editable and non-editable field boundaries remain explicit.
#   - User edit handling remains separate from version persistence.
# HUMAN_REVIEW: No.

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone


EDITABLE_FIELDS = {
	"title",
	"category",
	"subtitle",
	"notes",
	"local_metadata_tags",
	"school_exclusive",
}

IMMUTABLE_FIELDS = {
	"source_id",
	"extraction_timestamp",
	"original_source_url",
	"provenance_token",
}

BLANK_ALLOWED_FIELDS = {
	"subtitle",
	"notes",
}


FIELD_ALIASES = {
	"title": "title",
	"titulo": "title",
	"título": "title",
	"category": "category",
	"categoria": "category",
	"subtitle": "subtitle",
	"subtitulo": "subtitle",
	"subtítulo": "subtitle",
	"notes": "notes",
	"notas": "notes",
	"observacoes": "notes",
	"observações": "notes",
	"local_metadata_tags": "local_metadata_tags",
	"metadados_locais": "local_metadata_tags",
	"tags_metadados_locais": "local_metadata_tags",
	"school_exclusive": "school_exclusive",
	"exclusivo_escola": "school_exclusive",
	"source_id": "source_id",
	"id_fonte": "source_id",
	"extraction_timestamp": "extraction_timestamp",
	"timestamp_extracao": "extraction_timestamp",
	"timestamp_extração": "extraction_timestamp",
	"original_source_url": "original_source_url",
	"url_origem": "original_source_url",
	"provenance_token": "provenance_token",
	"token_proveniencia": "provenance_token",
	"token_proveniência": "provenance_token",
}


CATEGORY_VALUE_ALIASES = {
	"book": "book",
	"livro": "book",
	"dictionary": "dictionary",
	"dicionario": "dictionary",
	"dicionário": "dictionary",
	"notebook": "notebook",
	"caderno": "notebook",
	"apostila": "apostila",
	"general supplies": "general supplies",
	"material geral": "general supplies",
	"materiais gerais": "general supplies",
}


def _now_iso() -> str:
	return datetime.now(timezone.utc).isoformat()


def _is_blank(value: object) -> bool:
	if value is None:
		return True
	if isinstance(value, str):
		return value.strip() == ""
	if isinstance(value, (list, tuple, set, dict)):
		return len(value) == 0
	return False


def _normalize_text(value: object) -> str:
	return " ".join(str(value or "").strip().lower().split())


def _canonical_field_name(field_name: object) -> str:
	return FIELD_ALIASES.get(_normalize_text(field_name), _normalize_text(field_name))


def _canonical_category_value(category_value: object) -> str:
	return CATEGORY_VALUE_ALIASES.get(
		_normalize_text(category_value),
		_normalize_text(category_value),
	)


def _parse_bool(value: object) -> bool | None:
	if isinstance(value, bool):
		return value
	normalized = _normalize_text(value)
	if normalized in {"true", "1", "yes", "y", "sim", "s"}:
		return True
	if normalized in {"false", "0", "no", "n", "nao", "não"}:
		return False
	return None


def handle_user_edit(
	material_item: dict,
	edit_request: dict,
	user_context: dict,
	category_contract: set[str],
	local_edit_store: list[dict],
) -> dict[str, object]:
	field_name = _canonical_field_name(edit_request.get("fieldName"))
	old_value = edit_request.get("oldValue")
	new_value = edit_request.get("newValue")
	reason_note = edit_request.get("reasonNote")

	if field_name in IMMUTABLE_FIELDS:
		return {
			"editResult": {
				"status": "rejected",
				"reasonCode": "immutable_field",
				"persistedEditId": None,
				"acceptedAt": None,
			},
			"editRecord": None,
		}

	if field_name not in EDITABLE_FIELDS:
		return {
			"editResult": {
				"status": "rejected",
				"reasonCode": "schema_violation",
				"persistedEditId": None,
				"acceptedAt": None,
			},
			"editRecord": None,
		}

	if field_name == "title" and len(str(new_value or "")) > 500:
		return {
			"editResult": {
				"status": "rejected",
				"reasonCode": "schema_violation",
				"persistedEditId": None,
				"acceptedAt": None,
			},
			"editRecord": None,
		}

	if field_name == "category":
		candidate = _canonical_category_value(new_value)
		allowed_categories = {_canonical_category_value(value) for value in category_contract}
		if candidate not in allowed_categories:
			return {
				"editResult": {
					"status": "rejected",
					"reasonCode": "invalid_category",
					"persistedEditId": None,
					"acceptedAt": None,
				},
				"editRecord": None,
			}
		new_value = candidate

	if field_name == "school_exclusive":
		parsed = _parse_bool(new_value)
		if parsed is None:
			return {
				"editResult": {
					"status": "rejected",
					"reasonCode": "schema_violation",
					"persistedEditId": None,
					"acceptedAt": None,
				},
				"editRecord": None,
			}
		new_value = parsed

	if _is_blank(new_value) and field_name not in BLANK_ALLOWED_FIELDS:
		return {
			"editResult": {
				"status": "rejected",
				"reasonCode": "missing_value",
				"persistedEditId": None,
				"acceptedAt": None,
			},
			"editRecord": None,
		}

	accepted_at = _now_iso()
	persisted_edit_id = f"edit-{len(local_edit_store)}"
	edit_record = {
		"editId": persisted_edit_id,
		"materialId": material_item.get("result_id") or material_item.get("material_id"),
		"userId": user_context.get("userId"),
		"sessionId": user_context.get("sessionId"),
		"fieldName": field_name,
		"oldValue": old_value,
		"newValue": new_value,
		"reasonNote": reason_note,
		"timestamp": accepted_at,
	}

	local_edit_store.append(deepcopy(edit_record))

	return {
		"editResult": {
			"status": "accepted",
			"reasonCode": "accepted",
			"persistedEditId": persisted_edit_id,
			"acceptedAt": accepted_at,
		},
		"editRecord": edit_record,
	}
