# FILE: search_ranking/match_classifier.py
# MODULE: MODULE-003-02 — Match Classifier
# EPIC: EPIC-003 — Search & Ranking
# RESPONSIBILITY: Classify search candidates by confidence and hard-constraint state.
# EXPORTS: Match classification stub.
# DEPENDS_ON: search_ranking/query_orchestrator.py, source_governance/brand_substitution_audit_logger.py.
# ACCEPTANCE_CRITERIA:
#   - Valid, review-required, and invalid candidate states are explicit.
#   - Match classification remains separate from final ranking.
# HUMAN_REVIEW: No.

from __future__ import annotations

import json

from intake_canonicalization.isbn_normalization_validation import normalize_isbn
from search_ranking.text_normalization import normalize_text


ALLOWED_CLASSIFICATION_LABELS = {
	"Textbook",
	"Solution Manual",
	"Workbook",
	"Reference",
	"Other",
}

MAX_RESULT_OBJECT_BYTES = 5 * 1024


def _normalize_isbn(value: object) -> str:
	return normalize_isbn(str(value or ""))


def _levenshtein_distance(left: str, right: str) -> int:
	if left == right:
		return 0
	if not left:
		return len(right)
	if not right:
		return len(left)

	previous_row = list(range(len(right) + 1))
	for left_index, left_char in enumerate(left, start=1):
		current_row = [left_index]
		for right_index, right_char in enumerate(right, start=1):
			insert_cost = current_row[right_index - 1] + 1
			delete_cost = previous_row[right_index] + 1
			replace_cost = previous_row[right_index - 1] + (0 if left_char == right_char else 1)
			current_row.append(min(insert_cost, delete_cost, replace_cost))
		previous_row = current_row
	return previous_row[-1]


def _classification_label_from_canonical(canonical: dict) -> str:
	title = normalize_text(canonical.get("title"))
	if (
		"solution" in title
		or "manual" in title
		or "solucionario" in title
		or "solucionário" in title
		or "gabarito" in title
	):
		return "Solution Manual"
	if (
		"workbook" in title
		or "exercises" in title
		or "exercise" in title
		or "atividades" in title
		or "atividade" in title
		or "exercicios" in title
		or "exercícios" in title
		or "caderno de atividades" in title
	):
		return "Workbook"
	if canonical.get("isbn"):
		return "Textbook"
	if (
		"dictionary" in title
		or "reference" in title
		or "dicionario" in title
		or "dicionário" in title
		or "referencia" in title
		or "referência" in title
		or "enciclopedia" in title
		or "enciclopédia" in title
	):
		return "Reference"
	return "Other"


def _canonicalize_result(chunk: dict, index: int, max_result_object_bytes: int) -> tuple[dict, str | None]:
	raw_result = chunk.get("result") if isinstance(chunk, dict) else {}
	if not isinstance(raw_result, dict):
		raw_result = {}

	serialized = json.dumps(raw_result, ensure_ascii=False)
	serialization_size = len(serialized.encode("utf-8"))
	if serialization_size > max_result_object_bytes:
		return {
			"result_id": f"result-{index}",
			"source_id": chunk.get("source_id", "unknown"),
			"title": "",
			"author": "",
			"isbn": "",
			"classification_label": "Other",
			"oversized_rejected": True,
			"brand_substitution_context": None,
			"provenance": {
				"source_id": chunk.get("source_id", "unknown"),
				"upstream_index": index,
			},
		}, "oversized_result"

	title = raw_result.get("title") or raw_result.get("name") or ""
	author = raw_result.get("author") or raw_result.get("authors") or ""
	isbn = _normalize_isbn(raw_result.get("isbn") or "")

	canonical = {
		"result_id": f"result-{index}",
		"source_id": chunk.get("source_id", "unknown"),
		"title": str(title),
		"author": str(author),
		"isbn": isbn,
		"classification_label": "Other",
		"oversized_rejected": False,
		"brand_substitution_context": None,
		"provenance": {
			"source_id": chunk.get("source_id", "unknown"),
			"upstream_index": index,
		},
	}
	canonical["classification_label"] = _classification_label_from_canonical(canonical)
	return canonical, None


def classify_matches(
	result_queue: dict,
	brand_substitution_context: dict[str, dict] | None = None,
	max_result_object_bytes: int = MAX_RESULT_OBJECT_BYTES,
) -> dict[str, object]:
	"""
	Classify and deduplicate result queue while preserving input ordering.
	"""
	chunks = result_queue.get("resultChunks", []) if isinstance(result_queue, dict) else []
	brand_substitution_context = brand_substitution_context or {}

	classified_results: list[dict] = []
	deduplication_links: list[dict] = []
	schema_failures: list[dict] = []
	classification_distribution = {label: 0 for label in ALLOWED_CLASSIFICATION_LABELS}

	seen_isbn: dict[str, str] = {}
	seen_title_author: list[tuple[str, str, str]] = []

	for index, chunk in enumerate(chunks):
		canonical, schema_error = _canonicalize_result(chunk, index, max_result_object_bytes)
		if schema_error:
			schema_failures.append(
				{
					"result_id": canonical["result_id"],
					"reason": schema_error,
					"source_id": canonical["source_id"],
				}
			)

		if canonical["classification_label"] not in ALLOWED_CLASSIFICATION_LABELS:
			canonical["classification_label"] = "Other"

		brand_context = brand_substitution_context.get(canonical["result_id"])
		canonical["brand_substitution_context"] = brand_context

		classification_distribution[canonical["classification_label"]] += 1

		duplicate_of = None
		if canonical["isbn"]:
			duplicate_of = seen_isbn.get(canonical["isbn"])
			if duplicate_of is None:
				seen_isbn[canonical["isbn"]] = canonical["result_id"]
		else:
			title_key = normalize_text(canonical["title"])
			author_key = normalize_text(canonical["author"])
			for seen_result_id, seen_title, seen_author in seen_title_author:
				title_distance = _levenshtein_distance(title_key, seen_title)
				author_distance = _levenshtein_distance(author_key, seen_author)
				if title_distance <= 3 and author_distance <= 3:
					duplicate_of = seen_result_id
					break
			if duplicate_of is None:
				seen_title_author.append((canonical["result_id"], title_key, author_key))

		if duplicate_of:
			deduplication_links.append(
				{
					"result_id": canonical["result_id"],
					"duplicate_of": duplicate_of,
					"method": "isbn" if canonical["isbn"] else "title_author_fuzzy",
				}
			)

		classified_results.append(canonical)

	return {
		"classifiedResults": {
			"results": classified_results,
			"deduplicationLinks": deduplication_links,
		},
		"classificationMetrics": {
			"totalProcessed": len(classified_results),
			"dedupCount": len(deduplication_links),
			"classificationDistribution": classification_distribution,
			"schemaFailureCount": len(schema_failures),
		},
		"schemaFailures": schema_failures,
	}
