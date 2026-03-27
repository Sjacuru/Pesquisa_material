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

	class IntegrationType(models.TextChoices):
		API = "api", "API"
		SCRAPING = "scraping", "Scraping"

	site_id = models.CharField(max_length=80, unique=True)
	label = models.CharField(max_length=120)
	trust_status = models.CharField(max_length=32, choices=TrustStatus.choices, default=TrustStatus.REVIEW_REQUIRED)
	is_search_eligible = models.BooleanField(default=False)
	integration_type = models.CharField(max_length=32, choices=IntegrationType.choices, default=IntegrationType.SCRAPING)
	categories = models.JSONField(default=list, blank=True)
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


class Offer(models.Model):
	class Condition(models.TextChoices):
		NEW = "new", "New"
		USED = "used", "Used"
		UNKNOWN = "unknown", "Unknown"

	canonical_item = models.ForeignKey(CanonicalItem, on_delete=models.CASCADE, related_name="offers")
	source_site = models.ForeignKey(SourceSite, on_delete=models.SET_NULL, null=True, blank=True, related_name="offers")
	search_job = models.ForeignKey(SearchJob, on_delete=models.SET_NULL, null=True, blank=True, related_name="offers")
	product_title = models.CharField(max_length=512, blank=True, default="")
	seller_name = models.CharField(max_length=255, blank=True, default="")
	item_price = models.DecimalField(max_digits=12, decimal_places=2)
	shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	total_price = models.DecimalField(max_digits=12, decimal_places=2)
	currency = models.CharField(max_length=3, default="BRL")
	product_url = models.URLField(max_length=2048)
	condition = models.CharField(max_length=32, choices=Condition.choices, default=Condition.NEW)
	confidence = models.FloatField(default=1.0)
	retrieved_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["total_price"]


class SearchExecution(models.Model):
	class Status(models.TextChoices):
		OK = "ok", "OK"
		EMPTY = "empty", "Empty"
		TIMEOUT = "timeout", "Timeout"
		ERROR = "error", "Error"

	search_job = models.ForeignKey(SearchJob, on_delete=models.CASCADE, related_name="executions")
	source_site = models.ForeignKey(SourceSite, on_delete=models.SET_NULL, null=True, blank=True, related_name="executions")
	query_text = models.CharField(max_length=512)
	status = models.CharField(max_length=32, choices=Status.choices, default=Status.OK)
	results_count = models.PositiveIntegerField(default=0)
	error_message = models.TextField(blank=True, default="")
	response_ms = models.PositiveIntegerField(null=True, blank=True)
	requested_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-requested_at"]


class WorkflowState(models.Model):
	class State(models.TextChoices):
		REVIEW_QUEUE = "review_queue", "Review Queue"
		DRAFT = "draft", "Draft"
		BRAND_APPROVAL = "brand_approval", "Brand Approval"
		EXPORT_READY = "export_ready", "Export Ready"
		ARCHIVED = "archived", "Archived"

	canonical_item = models.OneToOneField(CanonicalItem, on_delete=models.CASCADE, related_name="workflow_state")
	state = models.CharField(max_length=32, choices=State.choices, default=State.DRAFT)
	state_data = models.JSONField(default=dict, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-updated_at"]


class JobQueueEntry(models.Model):
	class Status(models.TextChoices):
		PENDING = "pending", "Pending"
		RUNNING = "running", "Running"
		RETRYING = "retrying", "Retrying"
		COMPLETED = "completed", "Completed"
		FAILED = "failed", "Failed"

	job_id = models.CharField(max_length=64, unique=True)
	job_type = models.CharField(max_length=32, default="search_item")
	status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
	canonical_item = models.ForeignKey(CanonicalItem, on_delete=models.CASCADE, null=True, blank=True, related_name="job_queue_entries")
	upload_batch = models.ForeignKey(UploadBatch, on_delete=models.CASCADE, null=True, blank=True, related_name="job_queue_entries")
	attempt_count = models.PositiveIntegerField(default=0)
	max_retries = models.PositiveIntegerField(default=3)
	next_retry_at = models.DateTimeField(null=True, blank=True)
	payload = models.JSONField(default=dict, blank=True)
	result = models.JSONField(default=dict, blank=True)
	error_message = models.TextField(blank=True, default="")
	created_at = models.DateTimeField(auto_now_add=True)
	started_at = models.DateTimeField(null=True, blank=True)
	completed_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		ordering = ["created_at"]
		indexes = [
			models.Index(fields=["status", "created_at"]),
			models.Index(fields=["job_id"]),
		]


class JobExecutionLog(models.Model):
	job = models.ForeignKey(JobQueueEntry, on_delete=models.CASCADE, related_name="execution_logs")
	attempt_number = models.PositiveIntegerField()
	status = models.CharField(max_length=32)
	duration_ms = models.PositiveIntegerField(default=0)
	error_message = models.TextField(blank=True, default="")
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["created_at"]
