from __future__ import annotations

from django.db.models import QuerySet

from persistence.models import CanonicalItem, SearchJob, SourceSite, UploadBatch, VersionEvent


class UploadBatchRepository:
	def create(self, source_filename: str, notes: str = "") -> UploadBatch:
		return UploadBatch.objects.create(source_filename=source_filename, notes=notes)

	def get_by_public_id(self, public_id) -> UploadBatch | None:
		return UploadBatch.objects.filter(public_id=public_id).first()


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
	) -> SourceSite:
		source, _ = SourceSite.objects.update_or_create(
			site_id=site_id,
			defaults={
				"label": label,
				"trust_status": trust_status,
				"is_search_eligible": is_search_eligible,
			},
		)
		return source

	def list_eligible(self) -> QuerySet[SourceSite]:
		return SourceSite.objects.filter(is_search_eligible=True).exclude(
			trust_status=SourceSite.TrustStatus.BLOCKED
		)


class SearchJobRepository:
	def create(self, canonical_item: CanonicalItem | None = None) -> SearchJob:
		return SearchJob.objects.create(canonical_item=canonical_item)

	def update_status(self, job: SearchJob, status: str, rejection_reason: str = "") -> SearchJob:
		job.status = status
		job.rejection_reason = rejection_reason
		job.save(update_fields=["status", "rejection_reason"])
		return job


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
