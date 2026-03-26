# FILE: web/views.py
# MODULE: support — Delivery Layer Views
# EPIC: Architecture — Server-Rendered Delivery
# RESPONSIBILITY: Reserve the server-rendered request-entry boundary for approved user workflows.
# EXPORTS: Delivery-layer view placeholders for upload, review, search, edit, and export flows.
# DEPENDS_ON: intake_canonicalization/, source_governance/, search_ranking/, workflow_export/.
# ACCEPTANCE_CRITERIA:
#   - User-facing workflow entry points are clearly separated from domain logic.
#   - Only approved high-level workflows are represented by this delivery boundary.
# HUMAN_REVIEW: Yes — user-facing workflow entry layer.

import json
from urllib.parse import urlencode

from django.http import HttpRequest, JsonResponse
from django.shortcuts import render

from search_ranking.query_orchestrator import orchestrate_query
from search_ranking.school_exclusivity_resolver import resolve_school_exclusivity


def _split_csv(value: str) -> list[str]:
	return [chunk.strip() for chunk in str(value or "").split(",") if chunk.strip()]


def _mock_executor(source: dict, query: dict, timeout_seconds: float) -> dict:
	return {"results": [{"title": f"{query.get('text', '')}-{source.get('site_id')}"}]}


def _run_exclusivity_flow(item: dict, active_sources: list[dict]) -> tuple[dict, dict]:
	resolution = resolve_school_exclusivity(item=item, active_sources=active_sources)
	query_result = orchestrate_query(
		query={"text": str(item.get("name") or "item"), "categoryID": "general supplies"},
		validation_result={"is_valid": True, "dependency_chain_validated": True},
		eligible_sources=active_sources,
		source_query_executor=_mock_executor,
		exclusivity_context={
			"school_exclusive": resolution["resolved_item"]["school_exclusive"],
			"resolution_status": resolution["resolution_status"],
			"resolution_reason": resolution["resolution_reason"],
			"mandatory_sources": resolution["mandatory_sources"],
		},
	)
	return resolution, query_result


def health(request: HttpRequest) -> JsonResponse:
	return JsonResponse({"status": "ok", "phase": "scaffold"})


_SAMPLE_UPLOAD_JSON = json.dumps(
	[
		{
			"item_id": "item-001",
			"name": "Caderno 10 matérias",
			"school_exclusive": False,
			"required_sellers": [],
			"preferred_sellers": ["seller-a"],
			"exclusive_source": "default",
		},
		{
			"item_id": "item-002",
			"name": "Uniforme escolar",
			"school_exclusive": True,
			"required_sellers": ["seller-a"],
			"preferred_sellers": [],
			"exclusive_source": "document_notation",
		},
		{
			"item_id": "item-003",
			"name": "Kit de artes exclusivo",
			"school_exclusive": True,
			"required_sellers": ["seller-xyz"],
			"preferred_sellers": [],
			"exclusive_source": "document_notation",
		},
	],
	indent=2,
	ensure_ascii=False,
)

_DEFAULT_ACTIVE_SOURCES_CSV = "seller-a,seller-b,seller-c"


def _build_review_params(item: dict, active_sources_raw: str) -> str:
	params = {
		"item_name": str(item.get("name") or ""),
		"required_sellers": ",".join(item.get("required_sellers") or []),
		"preferred_sellers": ",".join(item.get("preferred_sellers") or []),
		"active_sources": active_sources_raw,
		"school_exclusive": "on" if item.get("school_exclusive") else "",
		"exclusive_source": str(item.get("exclusive_source") or "default"),
	}
	return urlencode(params)


def upload_workflow(request: HttpRequest):
	"""Batch upload simulation: resolves exclusivity on a JSON list of items."""
	parse_error = None
	eligible_items: list[dict] = []
	review_required_items: list[dict] = []
	active_sources_raw = _DEFAULT_ACTIVE_SOURCES_CSV
	items_json_display = _SAMPLE_UPLOAD_JSON

	if request.method == "POST":
		active_sources_raw = str(request.POST.get("active_sources") or _DEFAULT_ACTIVE_SOURCES_CSV)
		items_json_display = str(request.POST.get("items_json") or "")
		active_sources = [
			{"site_id": sid, "is_search_eligible": True}
			for sid in _split_csv(active_sources_raw)
		]
		try:
			raw = json.loads(items_json_display)
			items = raw if isinstance(raw, list) else [raw]
			for item in items:
				resolution = resolve_school_exclusivity(item=item, active_sources=active_sources)
				entry = {
					"item_id": item.get("item_id", ""),
					"name": item.get("name", ""),
					"resolution_status": resolution["resolution_status"],
					"resolution_reason": resolution["resolution_reason"],
					"mandatory_sources": resolution["mandatory_sources"],
					"preferred_sources": resolution["preferred_sources"],
					"conflicts": resolution["conflicts"],
					"review_params": _build_review_params(item, active_sources_raw),
				}
				if resolution["resolution_status"] == "review_required":
					review_required_items.append(entry)
				else:
					eligible_items.append(entry)
		except (json.JSONDecodeError, TypeError, KeyError) as exc:
			parse_error = str(exc)

	return render(
		request,
		"web/upload_workflow.html",
		{
			"items_json": items_json_display,
			"active_sources": active_sources_raw,
			"eligible_items": eligible_items,
			"review_required_items": review_required_items,
			"parse_error": parse_error,
			"has_results": request.method == "POST" and parse_error is None,
		},
	)


def exclusivity_demo(request: HttpRequest):
	active_sources = [
		{"site_id": "seller-a", "is_search_eligible": True},
		{"site_id": "seller-b", "is_search_eligible": True},
	]

	eligible_item = {
		"item_id": "demo-eligible",
		"name": "Uniforme escolar",
		"school_exclusive": True,
		"required_sellers": ["seller-a"],
		"preferred_sellers": ["seller-b"],
		"exclusive_source": "document_notation",
	}
	review_item = {
		"item_id": "demo-review",
		"name": "Uniforme esportivo",
		"school_exclusive": True,
		"required_sellers": ["seller-x"],
		"preferred_sellers": [],
		"exclusive_source": "document_notation",
	}

	eligible_resolution, eligible_query = _run_exclusivity_flow(eligible_item, active_sources)
	review_resolution, review_query = _run_exclusivity_flow(review_item, active_sources)

	scenarios = [
		{
			"name": "Eligible scenario",
			"item_name": eligible_item["name"],
			"resolution_status": eligible_resolution["resolution_status"],
			"resolution_reason": eligible_resolution["resolution_reason"],
			"mandatory_sources": eligible_resolution["mandatory_sources"],
			"completion_status": eligible_query["aggregatedResults"]["completionStatus"],
			"queried_count": eligible_query["sourceMetadata"]["queriedCount"],
			"result_count": len(eligible_query["aggregatedResults"]["resultChunks"]),
			"rejection_reason": eligible_query["aggregatedResults"].get("rejectionReason"),
		},
		{
			"name": "Review-required scenario",
			"item_name": review_item["name"],
			"resolution_status": review_resolution["resolution_status"],
			"resolution_reason": review_resolution["resolution_reason"],
			"mandatory_sources": review_resolution["mandatory_sources"],
			"completion_status": review_query["aggregatedResults"]["completionStatus"],
			"queried_count": review_query["sourceMetadata"]["queriedCount"],
			"result_count": len(review_query["aggregatedResults"]["resultChunks"]),
			"rejection_reason": review_query["aggregatedResults"].get("rejectionReason"),
		},
	]

	return render(request, "web/exclusivity_demo.html", {"scenarios": scenarios})


def exclusivity_review(request: HttpRequest):
	# Pre-fill from GET params when arriving from upload workflow
	back_url = request.GET.get("back", "")
	form_values = {
		"item_name": request.GET.get("item_name", "Uniforme escolar"),
		"required_sellers": request.GET.get("required_sellers", "seller-a"),
		"preferred_sellers": request.GET.get("preferred_sellers", "seller-b"),
		"active_sources": request.GET.get("active_sources", "seller-a,seller-b"),
		"school_exclusive": request.GET.get("school_exclusive", "on") == "on",
		"exclusive_source": request.GET.get("exclusive_source", "document_notation"),
	}

	result = None
	query_outcome = None

	if request.method == "POST":
		form_values = {
			"item_name": str(request.POST.get("item_name") or "Item"),
			"required_sellers": str(request.POST.get("required_sellers") or ""),
			"preferred_sellers": str(request.POST.get("preferred_sellers") or ""),
			"active_sources": str(request.POST.get("active_sources") or ""),
			"school_exclusive": request.POST.get("school_exclusive") == "on",
			"exclusive_source": str(request.POST.get("exclusive_source") or "default"),
		}

		active_sources = [
			{"site_id": site_id, "is_search_eligible": True}
			for site_id in _split_csv(form_values["active_sources"])
		]
		item = {
			"item_id": "manual-review-item",
			"name": form_values["item_name"],
			"school_exclusive": form_values["school_exclusive"],
			"required_sellers": _split_csv(form_values["required_sellers"]),
			"preferred_sellers": _split_csv(form_values["preferred_sellers"]),
			"exclusive_source": form_values["exclusive_source"],
		}

		resolution, query_result = _run_exclusivity_flow(item, active_sources)
		result = {
			"resolution_status": resolution["resolution_status"],
			"resolution_reason": resolution["resolution_reason"],
			"mandatory_sources": resolution["mandatory_sources"],
			"preferred_sources": resolution["preferred_sources"],
			"conflicts": resolution["conflicts"],
		}
		query_outcome = {
			"completion_status": query_result["aggregatedResults"]["completionStatus"],
			"rejection_reason": query_result["aggregatedResults"].get("rejectionReason"),
			"queried_count": query_result["sourceMetadata"]["queriedCount"],
			"result_count": len(query_result["aggregatedResults"]["resultChunks"]),
		}

	return render(
		request,
		"web/exclusivity_review.html",
		{
			"form_values": form_values,
			"result": result,
			"query_outcome": query_outcome,
			"back_url": back_url,
		},
	)
