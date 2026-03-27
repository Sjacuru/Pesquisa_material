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

import re
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from intake_canonicalization.stage_a_ingestion_pipeline import process_stage_a_ingestion
from job_runner import get_default_job_runner
from persistence.models import CanonicalItem, Offer, UploadBatch, VersionEvent, WorkflowState
from persistence.repositories import OfferRepository, VersionEventRepository, WorkflowStateRepository
from search_ranking.query_orchestrator import orchestrate_query
from search_ranking.school_exclusivity_resolver import resolve_school_exclusivity
from search_ranking.search_executor import execute_search_for_item
from workflow_export.export_formatter_delivery import export_formatter_delivery


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


def _category_matrix() -> dict[str, dict[str, str]]:
	return {
		"book": {"id": "book"},
		"dictionary": {"id": "dictionary"},
		"apostila": {"id": "apostila"},
		"notebook": {"id": "notebook"},
		"general supplies": {"id": "general supplies"},
	}


def upload_workflow(request: HttpRequest):
	"""Real upload workflow: process source file through Stage A and persist results."""
	error_message = None
	stage_a_result = None
	preview_items: list[dict] = []
	queued_jobs: list[dict] = []

	if request.method == "POST":
		uploaded_file = request.FILES.get("source_file")
		if uploaded_file is None:
			error_message = "Please choose a file to upload."
		else:
			try:
				file_bytes = uploaded_file.read()
				uploaded_document = {
					"filename": uploaded_file.name,
					"content_type": uploaded_file.content_type,
					"file_bytes": file_bytes,
				}

				stage_a_result = process_stage_a_ingestion(
					uploaded_document=uploaded_document,
					category_matrix_reference=_category_matrix(),
					include_downstream_validation=True,
					persist_to_db=True,
					persistence_notes="uploaded_via_web_workflow",
				)

				if stage_a_result.get("persistence"):
					batch_id = stage_a_result["persistence"]["upload_batch_id"]
					db_items = list(
						CanonicalItem.objects.filter(upload_batch_id=batch_id).order_by("pk")[:20]
					)

					# Trigger search for search_ready items using async queue by default.
					search_summaries: dict[int, dict] = {}
					job_runner = get_default_job_runner()
					if settings.ASYNC_SEARCH_ENABLED:
						job_runner.start()

					for db_item in db_items:
						if not db_item.search_ready:
							continue
						if settings.ASYNC_SEARCH_ENABLED:
							job_id = job_runner.submit_search_job(
								canonical_item_id=db_item.pk,
								payload={"source": "upload_workflow"},
							)
							queued_jobs.append({"item_id": db_item.pk, "job_id": job_id})
							search_summaries[db_item.pk] = {
								"queued": True,
								"job_id": job_id,
								"offers_found": None,
							}
						else:
							try:
								summary = execute_search_for_item(db_item)
								search_summaries[db_item.pk] = summary
							except Exception as exc:
								search_summaries[db_item.pk] = {"error": str(exc), "offers_found": 0}

					for db_item in db_items:
						s = search_summaries.get(db_item.pk)
						preview_items.append(
							{
								"item_id": db_item.pk,
								"line_index": db_item.item_code,
								"name": db_item.name,
								"category": db_item.category,
								"isbn": db_item.isbn_normalized,
								"requires_review": not db_item.search_ready,
								"offers_found": s.get("offers_found") if s else None,
								"search_error": s.get("error") if s else None,
								"search_job_id": s.get("job_id") if s else None,
							}
						)
				else:
					# Fallback: no persistence — build from extracted_items without item IDs
					extracted_items = list(stage_a_result.get("extracted_items") or [])
					for index, item in enumerate(extracted_items[:20]):
						fields = dict(item.get("fields") or {})
						preview_items.append(
							{
								"item_id": None,
								"line_index": item.get("line_index", index),
								"name": (fields.get("name") or {}).get("value") or item.get("line_text") or item.get("text") or "",
								"category": (fields.get("category") or {}).get("value") or item.get("category") or "",
								"isbn": (fields.get("isbn") or {}).get("value") or item.get("isbn") or "",
								"requires_review": bool(item.get("requires_human_review", False)),
								"offers_found": None,
								"search_error": None,
							}
						)
			except Exception as exc:
				error_message = str(exc)

	return render(
		request,
		"web/upload_workflow.html",
		{
			"error_message": error_message,
			"stage_a_result": stage_a_result,
			"preview_items": preview_items,
			"queued_jobs": queued_jobs,
			"has_results": stage_a_result is not None,
		},
	)


def item_search_results(request: HttpRequest, item_id: int):
	"""Display the top offers for a single CanonicalItem."""
	item = get_object_or_404(CanonicalItem, pk=item_id)
	offers = OfferRepository().best_offers_for_item(item, limit=10)

	workflow_state = None
	try:
		workflow_state = WorkflowState.objects.get(canonical_item=item)
	except WorkflowState.DoesNotExist:
		pass

	return render(
		request,
		"web/search_results.html",
		{
			"item": item,
			"offers": offers,
			"workflow_state": workflow_state,
			"needs_brand_approval": workflow_state is not None and workflow_state.state == WorkflowState.State.BRAND_APPROVAL,
		},
	)


def run_item_search(request: HttpRequest, item_id: int):
	"""POST — trigger a fresh search for a single item, then redirect to results."""
	if request.method != "POST":
		return redirect("item-search-results", item_id=item_id)
	item = get_object_or_404(CanonicalItem, pk=item_id)
	if settings.ASYNC_SEARCH_ENABLED:
		job_runner = get_default_job_runner()
		job_runner.start()
		job_runner.submit_search_job(canonical_item_id=item.pk, payload={"source": "run_item_search"})
	else:
		try:
			execute_search_for_item(item)
		except Exception:
			pass
	return redirect("item-search-results", item_id=item_id)


def job_status(request: HttpRequest, job_id: str) -> JsonResponse:
	status_payload = get_default_job_runner().get_job_status(job_id)
	status_code = 404 if status_payload.get("status") == "not_found" else 200
	return JsonResponse(status_payload, status=status_code)


_EDITABLE_CATEGORIES = ["book", "dictionary", "apostila", "notebook", "general supplies", "unknown"]


def item_edit(request: HttpRequest, item_id: int):
	"""Edit canonical item fields; writes VersionEvent audit trail on change, then re-searches."""
	item = get_object_or_404(CanonicalItem, pk=item_id)
	errors: dict[str, str] = {}

	if request.method == "POST":
		new_name = (request.POST.get("name") or "").strip()[:255]
		new_category = (request.POST.get("category") or "").strip()[:64]
		raw_isbn = re.sub(r"[^0-9Xx]", "", request.POST.get("isbn_normalized") or "").upper()
		new_isbn = raw_isbn if len(raw_isbn) in (10, 13) else ""
		new_unit = (request.POST.get("unit") or "un").strip()[:32] or "un"
		qty_str = (request.POST.get("quantity") or "1").strip().replace(",", ".")
		try:
			new_qty = Decimal(qty_str)
			if new_qty <= 0:
				new_qty = Decimal("1")
		except InvalidOperation:
			new_qty = Decimal("1")

		if not new_name:
			errors["name"] = "Name is required."

		if not errors:
			ver_repo = VersionEventRepository()
			material_id = f"canonical_item_{item.pk}"
			now = timezone.now()
			version_number = VersionEvent.objects.filter(material_id=material_id).count() + 1

			for field_name, old_val, new_val in [
				("name", item.name, new_name),
				("category", item.category, new_category),
				("isbn_normalized", item.isbn_normalized, new_isbn),
				("quantity", str(item.quantity), str(new_qty)),
				("unit", item.unit, new_unit),
			]:
				if old_val != new_val:
					ver_repo.append(
						material_id=material_id,
						version_number=version_number,
						field_name=field_name,
						old_value=old_val,
						new_value=new_val,
						timestamp=now,
						actor_id="web_user",
						reason_code="user_edit",
					)

			item.name = new_name
			item.category = new_category
			item.isbn_normalized = new_isbn
			item.quantity = new_qty
			item.unit = new_unit
			item.search_ready = True
			item.save(update_fields=["name", "category", "isbn_normalized", "quantity", "unit", "search_ready"])
			return redirect("run-item-search", item_id=item.pk)

	history = VersionEvent.objects.filter(material_id=f"canonical_item_{item.pk}").order_by("version_number")
	return render(
		request,
		"web/item_edit.html",
		{
			"item": item,
			"categories": _EDITABLE_CATEGORIES,
			"errors": errors,
			"history": history,
		},
	)


def batch_export(request: HttpRequest, batch_id: int):
	"""Preview best offer per item for a batch, with CSV download link."""
	batch = get_object_or_404(UploadBatch, pk=batch_id)
	items = list(CanonicalItem.objects.filter(upload_batch=batch).order_by("name"))
	rows = []
	for item in items:
		best = Offer.objects.filter(canonical_item=item).order_by("total_price").first()
		rows.append({"item": item, "offer": best})
	return render(
		request,
		"web/batch_export.html",
		{"batch": batch, "rows": rows},
	)


def batch_export_download(request: HttpRequest, batch_id: int):
	"""Stream a CSV with best offer per item for the batch."""
	batch = get_object_or_404(UploadBatch, pk=batch_id)
	items = list(CanonicalItem.objects.filter(upload_batch=batch).order_by("name"))

	curated_records: list[dict] = []
	version_by_material: dict[str, dict] = {}
	for item in items:
		best = Offer.objects.filter(canonical_item=item).order_by("total_price").first()
		material_id = f"canonical_item_{item.pk}"
		history_entries = list(
			VersionEvent.objects.filter(material_id=material_id)
			.order_by("version_number")
			.values("version_number", "actor_id", "timestamp")
		)
		version_by_material[material_id] = {
			"latestVersion": history_entries[-1]["version_number"] if history_entries else 0,
			"entries": [{"actor_id": entry.get("actor_id", "")} for entry in history_entries],
		}
		curated_records.append(
			{
				"materialId": material_id,
				"latestValues": {
					"name": item.name,
					"category": item.category,
					"quantity": str(item.quantity),
					"unit": item.unit,
					"price": str(best.total_price) if best else "",
					"source": (best.source_site.site_id if best and best.source_site else ""),
					"url": (best.product_url if best else ""),
				},
			}
		)

	export_result = export_formatter_delivery(
		curated_set={"records": curated_records},
		version_context={"byMaterial": version_by_material},
		export_request={"format": "csv"},
		user_context={"userId": "web_user"},
		format_adapters=None,
		export_event_log=[],
	)
	csv_content = export_result.get("deliveryResult", {}).get("artifact") or ""

	response = HttpResponse(csv_content, content_type="text/csv; charset=utf-8")
	filename = f"lista_precos_batch_{batch_id}.csv"
	response["Content-Disposition"] = f'attachment; filename="{filename}"'
	return response


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
