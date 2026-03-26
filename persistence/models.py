import uuid

from django.db import models


class UploadBatch(models.Model):
	class Status(models.TextChoices):
		UPLOADED = "uploaded", "Uploaded"
		EXTRACTED = "extracted", "Extracted"
		REVIEW_REQUIRED = "review_required", "Review Required"
		FAILED = "failed", "Failed"

	public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
	source_filename = models.CharField(max_length=255)
	status = models.CharField(max_length=32, choices=Status.choices, default=Status.UPLOADED)
	uploaded_at = models.DateTimeField(auto_now_add=True)
	notes = models.TextField(blank=True, default="")

	class Meta:
		ordering = ["-uploaded_at"]


class CanonicalItem(models.Model):
	upload_batch = models.ForeignKey(UploadBatch, on_delete=models.CASCADE, related_name="items")
	item_code = models.CharField(max_length=64)
	name = models.CharField(max_length=255)
	category = models.CharField(max_length=64)
	quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
	unit = models.CharField(max_length=32, default="un")
	isbn_normalized = models.CharField(max_length=13, blank=True, default="")
	search_ready = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["upload_batch", "item_code"], name="uq_canonical_item_batch_code")
		]
		ordering = ["name"]


class SourceSite(models.Model):
	class TrustStatus(models.TextChoices):
		ALLOWED = "allowed", "Allowed"
		REVIEW_REQUIRED = "review_required", "Review Required"
		BLOCKED = "blocked", "Blocked"
		SUSPENDED = "suspended", "Suspended"

	site_id = models.CharField(max_length=80, unique=True)
	label = models.CharField(max_length=120)
	trust_status = models.CharField(max_length=32, choices=TrustStatus.choices, default=TrustStatus.REVIEW_REQUIRED)
	is_search_eligible = models.BooleanField(default=False)
	last_healthcheck_at = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["site_id"]


class SearchJob(models.Model):
	class Status(models.TextChoices):
		PENDING = "pending", "Pending"
		RUNNING = "running", "Running"
		COMPLETE = "complete", "Complete"
		PARTIAL = "partial", "Partial"
		FAILED = "failed", "Failed"
		REVIEW_REQUIRED = "review_required", "Review Required"

	canonical_item = models.ForeignKey(CanonicalItem, on_delete=models.SET_NULL, null=True, blank=True, related_name="search_jobs")
	status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
	queried_sources_count = models.PositiveIntegerField(default=0)
	timeout_count = models.PositiveIntegerField(default=0)
	error_count = models.PositiveIntegerField(default=0)
	rejection_reason = models.CharField(max_length=120, blank=True, default="")
	started_at = models.DateTimeField(null=True, blank=True)
	completed_at = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]


class VersionEvent(models.Model):
	material_id = models.CharField(max_length=64)
	version_number = models.PositiveIntegerField()
	field_name = models.CharField(max_length=64)
	old_value = models.JSONField(null=True, blank=True)
	new_value = models.JSONField(null=True, blank=True)
	timestamp = models.DateTimeField()
	actor_id = models.CharField(max_length=64, blank=True, default="")
	reason_code = models.CharField(max_length=64, blank=True, default="")
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["material_id", "version_number"], name="uq_version_event_material_version")
		]
		ordering = ["material_id", "version_number"]
