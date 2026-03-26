from search_ranking.school_exclusivity_resolver import resolve_school_exclusivity


def _active_sources() -> list[dict]:
	return [
		{"site_id": "seller-a", "is_search_eligible": True},
		{"site_id": "seller-b", "is_search_eligible": True},
		{"site_id": "seller-c", "is_search_eligible": True},
	]


def test_ac1_exclusive_item_with_active_required_seller_is_eligible() -> None:
	result = resolve_school_exclusivity(
		item={
			"item_id": "i1",
			"school_exclusive": True,
			"required_sellers": ["seller-a"],
			"preferred_sellers": [],
			"exclusive_source": "document_notation",
		},
		active_sources=_active_sources(),
	)

	assert result["resolution_status"] == "eligible"
	assert result["mandatory_sources"] == ["seller-a"]


def test_ac2_exclusive_item_without_active_required_sellers_routes_review_required() -> None:
	result = resolve_school_exclusivity(
		item={
			"item_id": "i2",
			"school_exclusive": True,
			"required_sellers": ["seller-x"],
			"exclusive_source": "document_notation",
		},
		active_sources=_active_sources(),
	)

	assert result["resolution_status"] == "review_required"
	assert result["resolution_reason"] == "no_active_required_sellers"


def test_ac3_partial_required_seller_availability_keeps_eligible_and_logs_conflict() -> None:
	result = resolve_school_exclusivity(
		item={
			"item_id": "i3",
			"school_exclusive": True,
			"required_sellers": ["seller-a", "seller-x"],
			"exclusive_source": "document_notation",
		},
		active_sources=_active_sources(),
	)

	assert result["resolution_status"] == "eligible"
	assert result["mandatory_sources"] == ["seller-a"]
	assert any(conflict["conflict_type"] == "blocked_required_sellers" for conflict in result["conflicts"])


def test_ac4_non_exclusive_item_uses_all_active_sources() -> None:
	result = resolve_school_exclusivity(
		item={
			"item_id": "i4",
			"school_exclusive": False,
			"required_sellers": [],
			"preferred_sellers": ["seller-c"],
		},
		active_sources=_active_sources(),
	)

	assert result["resolution_status"] == "eligible"
	assert result["mandatory_sources"] == ["seller-a", "seller-b", "seller-c"]
	assert result["preferred_sources"] == ["seller-c"]


def test_ac5_conflicts_are_logged_with_required_fields() -> None:
	audit_log: list[dict] = []
	result = resolve_school_exclusivity(
		item={
			"item_id": "i5",
			"school_exclusive": True,
			"required_sellers": ["seller-x"],
			"exclusive_source": "document_notation",
		},
		active_sources=_active_sources(),
		audit_log=audit_log,
	)

	assert result["resolution_status"] == "review_required"
	assert len(audit_log) == 1
	entry = audit_log[0]
	assert entry["item_id"] == "i5"
	assert "timestamp" in entry
	assert isinstance(entry["conflicts"], list)


def test_ac6_document_source_precedence_beats_user_annotation_conflict() -> None:
	result = resolve_school_exclusivity(
		item={
			"item_id": "i6",
			"school_exclusive": True,
			"required_sellers": ["seller-a"],
			"exclusive_source": "document_notation",
		},
		active_sources=_active_sources(),
		user_overrides={"school_exclusive": False},
	)

	assert result["resolved_item"]["school_exclusive"] is True
	assert any(conflict["conflict_type"] == "document_vs_user_exclusive" for conflict in result["conflicts"])


def test_ac7_operator_override_can_change_exclusivity_state() -> None:
	result = resolve_school_exclusivity(
		item={
			"item_id": "i7",
			"school_exclusive": True,
			"required_sellers": ["seller-x"],
			"exclusive_source": "document_notation",
		},
		active_sources=_active_sources(),
		user_overrides={
			"operator_override": True,
			"school_exclusive": False,
			"required_sellers": [],
			"override_reason": "temporary unblock",
		},
	)

	assert result["resolution_status"] == "eligible"
	assert result["resolved_item"]["school_exclusive"] is False
	assert any(conflict["conflict_type"] == "operator_override_applied" for conflict in result["conflicts"])


def test_ac8_same_input_produces_same_decision_fields() -> None:
	item = {
		"item_id": "i8",
		"school_exclusive": True,
		"required_sellers": ["seller-a"],
		"preferred_sellers": ["seller-c"],
		"exclusive_source": "document_notation",
	}

	first = resolve_school_exclusivity(item=item, active_sources=_active_sources())
	second = resolve_school_exclusivity(item=item, active_sources=_active_sources())

	assert first["resolution_status"] == second["resolution_status"]
	assert first["resolution_reason"] == second["resolution_reason"]
	assert first["mandatory_sources"] == second["mandatory_sources"]
	assert first["preferred_sources"] == second["preferred_sources"]
