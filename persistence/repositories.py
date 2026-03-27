from __future__ import annotations

import re
from decimal import Decimal
from typing import Optional

from django.db.models import QuerySet
from django.utils import timezone

from persistence.models import (
	CanonicalItem,
	Offer,
	SearchExecution,
	SearchJob,
	SourceSite,
	UploadBatch,
	VersionEvent,
	WorkflowState,
	JobQueueEntry,
	JobExecutionLog,
)


class UploadBatchRepository:
	def create(self, source_filename: str, notes: str = "") -> UploadBatch:
		return UploadBatch.objects.create(source_filename=source_filename, notes=notes)

	def get_by_public_id(self, public_id) -> UploadBatch | None:
		return UploadBatch.objects.filter(public_id=public_id).first()

	def update_status(self, upload_batch: UploadBatch, status: str, notes: str | None = None) -> UploadBatch:
		upload_batch.status = status
		if notes is not None:
			upload_batch.notes = notes
			upload_batch.save(update_fields=["status", "notes"])
		else:
			upload_batch.save(update_fields=["status"])
		return upload_batch


class CanonicalItemRepository:
	def create(
		self,
		upload_batch: UploadBatch,
		item_code: str,
		name: str,
		category: str,
		quantity,
		unit: str,
		isbn_normalized: str = "",
		search_ready: bool = False,
	) -> CanonicalItem:
		return CanonicalItem.objects.create(
			upload_batch=upload_batch,
			item_code=item_code,
			name=name,
			category=category,
			quantity=quantity,
			unit=unit,
			isbn_normalized=isbn_normalized,
			search_ready=search_ready,
		)

	def list_by_batch(self, upload_batch: UploadBatch) -> QuerySet[CanonicalItem]:
		return CanonicalItem.objects.filter(upload_batch=upload_batch).order_by("name")


class SourceSiteRepository:
	def upsert(
		self,
		site_id: str,
		label: str,
		trust_status: str,
		is_search_eligible: bool,
		integration_type: str = "scraping",
		categories: list[str] | None = None,
	) -> SourceSite:
		source, _ = SourceSite.objects.update_or_create(
			site_id=site_id,
			defaults={
				"label": label,
				"trust_status": trust_status,
				"is_search_eligible": is_search_eligible,
				"integration_type": integration_type,
				"categories": categories or [],
			},
		)
		return source

	def list_eligible(self) -> QuerySet[SourceSite]:
		return SourceSite.objects.filter(is_search_eligible=True).exclude(
			trust_status=SourceSite.TrustStatus.BLOCKED
		)

	def list_eligible_for_category(self, category: str) -> QuerySet[SourceSite]:
		return (
			SourceSite.objects.filter(is_search_eligible=True, categories__contains=[category])
			.exclude(trust_status__in=[SourceSite.TrustStatus.BLOCKED, SourceSite.TrustStatus.SUSPENDED])
		)


class SearchJobRepository:
	def create(self, canonical_item: CanonicalItem | None = None) -> SearchJob:
		return SearchJob.objects.create(canonical_item=canonical_item)

	def update_status(self, job: SearchJob, status: str, rejection_reason: str = "") -> SearchJob:
		job.status = status
		job.rejection_reason = rejection_reason
		update_fields = ["status", "rejection_reason"]
		if status == SearchJob.Status.RUNNING and job.started_at is None:
			job.started_at = timezone.now()
			update_fields.append("started_at")
		if status in (SearchJob.Status.COMPLETE, SearchJob.Status.PARTIAL, SearchJob.Status.FAILED):
			job.completed_at = timezone.now()
			update_fields.append("completed_at")
		job.save(update_fields=update_fields)
		return job


class JobQueueRepository:
	def create(
		self,
		job_id: str,
		canonical_item: CanonicalItem | None,
		upload_batch: UploadBatch | None,
		payload: dict | None = None,
		job_type: str = "search_item",
		max_retries: int = 3,
	) -> JobQueueEntry:
		return JobQueueEntry.objects.create(
			job_id=job_id,
			job_type=job_type,
			canonical_item=canonical_item,
			upload_batch=upload_batch,
			payload=payload or {},
			max_retries=max_retries,
		)

	def get_by_job_id(self, job_id: str) -> JobQueueEntry | None:
		return JobQueueEntry.objects.filter(job_id=job_id).first()

	def list_pending(self, limit: int = 10) -> QuerySet[JobQueueEntry]:
		return JobQueueEntry.objects.filter(status=JobQueueEntry.Status.PENDING).order_by("created_at")[:limit]

	def list_retrying_due(self, now, limit: int = 10) -> QuerySet[JobQueueEntry]:
		return (
			JobQueueEntry.objects.filter(status=JobQueueEntry.Status.RETRYING, next_retry_at__lte=now)
			.order_by("next_retry_at", "created_at")[:limit]
		)

	def mark_running(self, job: JobQueueEntry) -> JobQueueEntry:
		job.status = JobQueueEntry.Status.RUNNING
		job.attempt_count = int(job.attempt_count) + 1
		job.started_at = timezone.now()
		job.save(update_fields=["status", "attempt_count", "started_at"])
		return job

	def mark_retrying(self, job: JobQueueEntry, error_message: str, next_retry_at) -> JobQueueEntry:
		job.status = JobQueueEntry.Status.RETRYING
		job.error_message = error_message
		job.next_retry_at = next_retry_at
		job.save(update_fields=["status", "error_message", "next_retry_at"])
		return job

	def mark_failed(self, job: JobQueueEntry, error_message: str) -> JobQueueEntry:
		job.status = JobQueueEntry.Status.FAILED
		job.error_message = error_message
		job.completed_at = timezone.now()
		job.save(update_fields=["status", "error_message", "completed_at"])
		return job

	def mark_completed(self, job: JobQueueEntry, result: dict | None = None) -> JobQueueEntry:
		job.status = JobQueueEntry.Status.COMPLETED
		job.result = result or {}
		job.error_message = ""
		job.completed_at = timezone.now()
		job.save(update_fields=["status", "result", "error_message", "completed_at"])
		return job


class JobExecutionLogRepository:
	def create(self, job: JobQueueEntry, attempt_number: int, status: str, duration_ms: int, error_message: str = "") -> JobExecutionLog:
		return JobExecutionLog.objects.create(
			job=job,
			attempt_number=attempt_number,
			status=status,
			duration_ms=duration_ms,
			error_message=error_message,
		)


class VersionEventRepository:
	def append(
		self,
		material_id: str,
		version_number: int,
		field_name: str,
		old_value,
		new_value,
		timestamp,
		actor_id: str = "",
		reason_code: str = "",
	) -> VersionEvent:
		return VersionEvent.objects.create(
			material_id=material_id,
			version_number=version_number,
			field_name=field_name,
			old_value=old_value,
			new_value=new_value,
			timestamp=timestamp,
			actor_id=actor_id,
			reason_code=reason_code,
		)

	def list_material_history(self, material_id: str) -> QuerySet[VersionEvent]:
		return VersionEvent.objects.filter(material_id=material_id).order_by("version_number")


def _to_decimal_quantity(quantity_raw: object) -> Decimal:
	if quantity_raw is None:
		return Decimal("1")

	if isinstance(quantity_raw, (int, float, Decimal)):
		try:
			value = Decimal(str(quantity_raw))
			return value if value > 0 else Decimal("1")
		except Exception:
			return Decimal("1")

	text = str(quantity_raw).strip()
	if not text:
		return Decimal("1")

	match = re.search(r"\d+(?:[\.,]\d+)?", text)
	if not match:
		return Decimal("1")

	normalized = match.group(0).replace(",", ".")
	try:
		value = Decimal(normalized)
		return value if value > 0 else Decimal("1")
	except Exception:
		return Decimal("1")


def _extract_unit(quantity_raw: object) -> str:
	if quantity_raw is None:
		return "un"

	text = str(quantity_raw).strip()
	if not text:
		return "un"

	match = re.search(r"(?:\d+(?:[\.,]\d+)?)\s*([A-Za-zÀ-ÖØ-öø-ÿ]+)", text)
	if not match:
		return "un"

	unit = match.group(1).strip().lower()
	return unit or "un"


def persist_stage_a_result(
	stage_a_result: dict,
	source_filename: str,
	notes: str = "",
	upload_batch_repo: UploadBatchRepository | None = None,
	canonical_item_repo: CanonicalItemRepository | None = None,
) -> dict:
	"""Persist Stage A output into UploadBatch and CanonicalItem records."""
	upload_batch_repo = upload_batch_repo or UploadBatchRepository()
	canonical_item_repo = canonical_item_repo or CanonicalItemRepository()

	upload_batch = upload_batch_repo.create(source_filename=source_filename, notes=notes)

	route_mode = str(stage_a_result.get("route_mode") or "review_required")
	detected_type = str(stage_a_result.get("detected_type") or "unknown")
	extracted_items = list(stage_a_result.get("extracted_items") or [])

	persisted_items: list[CanonicalItem] = []

	for index, item in enumerate(extracted_items):
		fields = dict(item.get("fields") or {})

		name_value = (fields.get("name") or {}).get("value") or item.get("line_text") or item.get("text") or ""
		name = str(name_value).strip() or f"Item {index + 1}"

		category_value = (fields.get("category") or {}).get("value") or item.get("category") or detected_type or "unknown"
		category = str(category_value).strip() or "unknown"

		quantity_raw = (fields.get("quantity") or {}).get("value")
		if quantity_raw is None:
			quantity_raw = item.get("quantity")

		isbn_raw = (fields.get("isbn") or {}).get("value") or item.get("isbn") or ""
		isbn_normalized = re.sub(r"[^0-9Xx]", "", str(isbn_raw)).upper()
		if len(isbn_normalized) not in (10, 13):
			isbn_normalized = ""

		line_index = item.get("line_index", index)
		item_code = f"{route_mode}-{line_index if isinstance(line_index, int) else index}"

		requires_review = bool(item.get("requires_human_review", False))
		search_ready = bool(route_mode == "native_text" and not requires_review)

		persisted_item = canonical_item_repo.create(
			upload_batch=upload_batch,
			item_code=item_code,
			name=name[:255],
			category=category[:64],
			quantity=_to_decimal_quantity(quantity_raw),
			unit=_extract_unit(quantity_raw)[:32],
			isbn_normalized=isbn_normalized,
			search_ready=search_ready,
		)
		persisted_items.append(persisted_item)

	if route_mode == "review_required":
		status = UploadBatch.Status.REVIEW_REQUIRED
	elif not persisted_items:
		status = UploadBatch.Status.FAILED
	elif any(not item.search_ready for item in persisted_items):
		status = UploadBatch.Status.REVIEW_REQUIRED
	else:
		status = UploadBatch.Status.EXTRACTED

	upload_batch_repo.update_status(upload_batch, status=status)

	return {
		"upload_batch": upload_batch,
		"canonical_items": persisted_items,
		"status": status,
	}


class OfferRepository:
	def create(
		self,
		canonical_item: CanonicalItem,
		source_site: SourceSite | None,
		search_job: SearchJob | None,
		product_title: str,
		seller_name: str,
		item_price: Decimal,
		shipping_cost: Optional[Decimal],
		total_price: Decimal,
		currency: str,
		product_url: str,
		condition: str = "new",
		confidence: float = 1.0,
	) -> Offer:
		return Offer.objects.create(
			canonical_item=canonical_item,
			source_site=source_site,
			search_job=search_job,
			product_title=product_title[:512],
			seller_name=seller_name[:255],
			item_price=item_price,
			shipping_cost=shipping_cost,
			total_price=total_price,
			currency=currency[:3],
			product_url=product_url[:2048],
			condition=condition,
			confidence=confidence,
		)

	def list_for_item(self, canonical_item: CanonicalItem) -> QuerySet[Offer]:
		return Offer.objects.filter(canonical_item=canonical_item).order_by("total_price")

	def best_offers_for_item(self, canonical_item: CanonicalItem, limit: int = 5) -> QuerySet[Offer]:
		return self.list_for_item(canonical_item)[:limit]


class SearchExecutionRepository:
	def create(
		self,
		search_job: SearchJob,
		source_site: SourceSite | None,
		query_text: str,
		status: str,
		results_count: int = 0,
		error_message: str = "",
		response_ms: Optional[int] = None,
	) -> SearchExecution:
		return SearchExecution.objects.create(
			search_job=search_job,
			source_site=source_site,
			query_text=query_text[:512],
			status=status,
			results_count=results_count,
			error_message=error_message,
			response_ms=response_ms,
		)

	def list_for_job(self, search_job: SearchJob) -> QuerySet[SearchExecution]:
		return SearchExecution.objects.filter(search_job=search_job).order_by("-requested_at")


class WorkflowStateRepository:
	def get_or_create(self, canonical_item: CanonicalItem) -> WorkflowState:
		state, _ = WorkflowState.objects.get_or_create(
			canonical_item=canonical_item,
			defaults={"state": WorkflowState.State.DRAFT},
		)
		return state

	def transition(self, canonical_item: CanonicalItem, new_state: str, state_data: dict | None = None) -> WorkflowState:
		state = self.get_or_create(canonical_item)
		state.state = new_state
		if state_data is not None:
			state.state_data = state_data
		state.save(update_fields=["state", "state_data", "updated_at"])
		return state

	def list_in_state(self, state: str) -> QuerySet[WorkflowState]:
		return WorkflowState.objects.filter(state=state).select_related("canonical_item")
