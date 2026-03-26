# FILE: tests/unit/workflow_export/test_user_edit_handler.py
# MODULE: MODULE-004-01 — User Edit Handler
# EPIC: EPIC-004 — User Workflow
# RESPONSIBILITY: Reserve unit tests for user-edit workflow acceptance criteria.
# EXPORTS: Unit test stub.
# DEPENDS_ON: workflow_export/user_edit_handler.py.
# ACCEPTANCE_CRITERIA:
#   - Editable-field boundaries remain testable from this unit boundary.
#   - Edit handling remains separate from version persistence.
# HUMAN_REVIEW: No.

from workflow_export.user_edit_handler import handle_user_edit


def _material() -> dict:
	return {
		"result_id": "mat-1",
		"title": "Livro",
		"category": "book",
		"source_id": "src-1",
		"extraction_timestamp": "2026-03-25T10:00:00+00:00",
		"original_source_url": "https://example.com/item/1",
		"provenance_token": "prov-1",
	}


def _user() -> dict:
	return {"userId": "user-1", "sessionId": "sess-1", "role": "operator"}


def _categories() -> set[str]:
	return {"book", "dictionary", "notebook", "apostila", "general supplies"}


def test_accepts_editable_field_title() -> None:
	store: list[dict] = []
	output = handle_user_edit(
		material_item=_material(),
		edit_request={"fieldName": "title", "oldValue": "Livro", "newValue": "Livro Atualizado", "reasonNote": "typo"},
		user_context=_user(),
		category_contract=_categories(),
		local_edit_store=store,
	)

	assert output["editResult"]["status"] == "accepted"
	assert len(store) == 1


def test_rejects_immutable_field_edit() -> None:
	store: list[dict] = []
	output = handle_user_edit(
		material_item=_material(),
		edit_request={"fieldName": "source_id", "oldValue": "src-1", "newValue": "src-2"},
		user_context=_user(),
		category_contract=_categories(),
		local_edit_store=store,
	)

	assert output["editResult"]["status"] == "rejected"
	assert output["editResult"]["reasonCode"] == "immutable_field"
	assert store == []


def test_rejects_unknown_field_schema_violation() -> None:
	store: list[dict] = []
	output = handle_user_edit(
		material_item=_material(),
		edit_request={"fieldName": "price", "oldValue": "10", "newValue": "12"},
		user_context=_user(),
		category_contract=_categories(),
		local_edit_store=store,
	)

	assert output["editResult"]["reasonCode"] == "schema_violation"


def test_category_edit_must_validate_against_contract() -> None:
	store: list[dict] = []
	output = handle_user_edit(
		material_item=_material(),
		edit_request={"fieldName": "category", "oldValue": "book", "newValue": "invalid_cat"},
		user_context=_user(),
		category_contract=_categories(),
		local_edit_store=store,
	)

	assert output["editResult"]["reasonCode"] == "invalid_category"
	assert store == []


def test_title_longer_than_500_is_rejected() -> None:
	store: list[dict] = []
	output = handle_user_edit(
		material_item=_material(),
		edit_request={"fieldName": "title", "oldValue": "Livro", "newValue": "x" * 501},
		user_context=_user(),
		category_contract=_categories(),
		local_edit_store=store,
	)

	assert output["editResult"]["reasonCode"] == "schema_violation"


def test_blank_value_rejected_for_non_blankable_field() -> None:
	store: list[dict] = []
	output = handle_user_edit(
		material_item=_material(),
		edit_request={"fieldName": "title", "oldValue": "Livro", "newValue": ""},
		user_context=_user(),
		category_contract=_categories(),
		local_edit_store=store,
	)

	assert output["editResult"]["reasonCode"] == "missing_value"


def test_blank_value_allowed_for_notes() -> None:
	store: list[dict] = []
	output = handle_user_edit(
		material_item=_material(),
		edit_request={"fieldName": "notes", "oldValue": "abc", "newValue": ""},
		user_context=_user(),
		category_contract=_categories(),
		local_edit_store=store,
	)

	assert output["editResult"]["status"] == "accepted"


def test_accepted_edit_record_contains_required_fields() -> None:
	store: list[dict] = []
	output = handle_user_edit(
		material_item=_material(),
		edit_request={"fieldName": "title", "oldValue": "Livro", "newValue": "Livro 2", "reasonNote": "fix"},
		user_context=_user(),
		category_contract=_categories(),
		local_edit_store=store,
	)

	record = output["editRecord"]
	assert record is not None
	assert record["userId"] == "user-1"
	assert record["fieldName"] == "title"
	assert record["oldValue"] == "Livro"
	assert record["newValue"] == "Livro 2"
	assert "timestamp" in record


def test_same_valid_input_same_validation_result() -> None:
	store1: list[dict] = []
	store2: list[dict] = []
	request = {"fieldName": "subtitle", "oldValue": "", "newValue": "sub", "reasonNote": "add"}

	out1 = handle_user_edit(_material(), request, _user(), _categories(), store1)
	out2 = handle_user_edit(_material(), request, _user(), _categories(), store2)

	assert out1["editResult"]["status"] == out2["editResult"]["status"] == "accepted"
	assert out1["editResult"]["reasonCode"] == out2["editResult"]["reasonCode"] == "accepted"


def test_accepts_portuguese_field_alias_for_title_and_persists_canonical_field_name() -> None:
	store: list[dict] = []
	output = handle_user_edit(
		material_item=_material(),
		edit_request={"fieldName": "título", "oldValue": "Livro", "newValue": "Livro Atualizado"},
		user_context=_user(),
		category_contract=_categories(),
		local_edit_store=store,
	)

	assert output["editResult"]["status"] == "accepted"
	assert output["editRecord"]["fieldName"] == "title"


def test_rejects_portuguese_alias_of_immutable_field() -> None:
	store: list[dict] = []
	output = handle_user_edit(
		material_item=_material(),
		edit_request={"fieldName": "id_fonte", "oldValue": "src-1", "newValue": "src-2"},
		user_context=_user(),
		category_contract=_categories(),
		local_edit_store=store,
	)

	assert output["editResult"]["status"] == "rejected"
	assert output["editResult"]["reasonCode"] == "immutable_field"


def test_accepts_portuguese_category_value_and_persists_canonical_category() -> None:
	store: list[dict] = []
	output = handle_user_edit(
		material_item=_material(),
		edit_request={"fieldName": "categoria", "oldValue": "book", "newValue": "livro"},
		user_context=_user(),
		category_contract=_categories(),
		local_edit_store=store,
	)

	assert output["editResult"]["status"] == "accepted"
	assert output["editRecord"]["fieldName"] == "category"
	assert output["editRecord"]["newValue"] == "book"


def test_accepts_school_exclusive_boolean_edit() -> None:
	store: list[dict] = []
	output = handle_user_edit(
		material_item=_material(),
		edit_request={"fieldName": "school_exclusive", "oldValue": False, "newValue": True, "reasonNote": "school rule"},
		user_context=_user(),
		category_contract=_categories(),
		local_edit_store=store,
	)

	assert output["editResult"]["status"] == "accepted"
	assert output["editRecord"]["fieldName"] == "school_exclusive"
	assert output["editRecord"]["newValue"] is True


def test_accepts_portuguese_alias_for_school_exclusive_with_string_bool() -> None:
	store: list[dict] = []
	output = handle_user_edit(
		material_item=_material(),
		edit_request={"fieldName": "exclusivo_escola", "oldValue": False, "newValue": "sim", "reasonNote": "override"},
		user_context=_user(),
		category_contract=_categories(),
		local_edit_store=store,
	)

	assert output["editResult"]["status"] == "accepted"
	assert output["editRecord"]["fieldName"] == "school_exclusive"
	assert output["editRecord"]["newValue"] is True


def test_rejects_invalid_school_exclusive_value() -> None:
	store: list[dict] = []
	output = handle_user_edit(
		material_item=_material(),
		edit_request={"fieldName": "school_exclusive", "oldValue": False, "newValue": "maybe", "reasonNote": ""},
		user_context=_user(),
		category_contract=_categories(),
		local_edit_store=store,
	)

	assert output["editResult"]["status"] == "rejected"
	assert output["editResult"]["reasonCode"] == "schema_violation"
