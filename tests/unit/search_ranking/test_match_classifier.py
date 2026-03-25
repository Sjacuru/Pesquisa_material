# FILE: tests/unit/search_ranking/test_match_classifier.py
# MODULE: MODULE-003-02 — Match Classifier
# EPIC: EPIC-003 — Search & Ranking
# RESPONSIBILITY: Reserve unit tests for match-classification acceptance criteria.
# EXPORTS: Unit test stub.
# DEPENDS_ON: search_ranking/match_classifier.py.
# ACCEPTANCE_CRITERIA:
#   - Valid, review-required, and invalid candidate states are testable.
#   - Classification responsibility remains separate from ranking behavior.
# HUMAN_REVIEW: No.

from search_ranking.match_classifier import ALLOWED_CLASSIFICATION_LABELS, classify_matches


def test_transforms_all_results_to_canonical_schema() -> None:
	queue = {
		"resultChunks": [
			{"source_id": "s1", "result": {"title": "Livro Algebra", "author": "A", "isbn": "9780306406157"}},
			{"source_id": "s2", "result": {"name": "Workbook Math", "authors": "B"}},
		]
	}

	output = classify_matches(queue)
	results = output["classifiedResults"]["results"]

	assert len(results) == 2
	for result in results:
		assert set(result.keys()) >= {
			"result_id",
			"source_id",
			"title",
			"author",
			"isbn",
			"classification_label",
			"provenance",
		}


def test_zero_result_loss_input_count_equals_output_count() -> None:
	queue = {
		"resultChunks": [
			{"source_id": "s1", "result": {"title": "a"}},
			{"source_id": "s2", "result": {"title": "b"}},
			{"source_id": "s3", "result": {"title": "c"}},
		]
	}

	output = classify_matches(queue)
	assert len(output["classifiedResults"]["results"]) == 3


def test_dedup_detects_exact_isbn_matches() -> None:
	queue = {
		"resultChunks": [
			{"source_id": "s1", "result": {"title": "Book A", "author": "Auth", "isbn": "978-0-306-40615-7"}},
			{"source_id": "s2", "result": {"title": "Book A second", "author": "Auth", "isbn": "9780306406157"}},
		]
	}

	output = classify_matches(queue)
	links = output["classifiedResults"]["deduplicationLinks"]

	assert len(links) == 1
	assert links[0]["method"] == "isbn"


def test_dedup_fallback_title_author_fuzzy_match() -> None:
	queue = {
		"resultChunks": [
			{"source_id": "s1", "result": {"title": "Calculus 9th Edition", "author": "James Stewart"}},
			{"source_id": "s2", "result": {"title": "Calculus 9th Editon", "author": "James Stewart"}},
		]
	}

	output = classify_matches(queue)
	links = output["classifiedResults"]["deduplicationLinks"]

	assert len(links) == 1
	assert links[0]["method"] == "title_author_fuzzy"


def test_classification_labels_are_from_fixed_enum_only() -> None:
	queue = {
		"resultChunks": [
			{"source_id": "s1", "result": {"title": "Workbook of Algebra"}},
			{"source_id": "s2", "result": {"title": "Dictionary Reference"}},
			{"source_id": "s3", "result": {"title": "General Item"}},
		]
	}

	output = classify_matches(queue)
	for result in output["classifiedResults"]["results"]:
		assert result["classification_label"] in ALLOWED_CLASSIFICATION_LABELS


def test_classification_accepts_portuguese_solution_manual_terms() -> None:
	queue = {
		"resultChunks": [
			{"source_id": "s1", "result": {"title": "Matemática - Solucionário"}},
			{"source_id": "s2", "result": {"title": "Física - Gabarito Oficial"}},
		]
	}

	output = classify_matches(queue)
	labels = [result["classification_label"] for result in output["classifiedResults"]["results"]]

	assert labels == ["Solution Manual", "Solution Manual"]


def test_classification_accepts_portuguese_workbook_terms() -> None:
	queue = {
		"resultChunks": [
			{"source_id": "s1", "result": {"title": "Caderno de Atividades de Português"}},
			{"source_id": "s2", "result": {"title": "Exercícios de Álgebra"}},
		]
	}

	output = classify_matches(queue)
	labels = [result["classification_label"] for result in output["classifiedResults"]["results"]]

	assert labels == ["Workbook", "Workbook"]


def test_classification_accepts_portuguese_reference_terms() -> None:
	queue = {
		"resultChunks": [
			{"source_id": "s1", "result": {"title": "Dicionário Escolar"}},
			{"source_id": "s2", "result": {"title": "Guia de Referência"}},
		]
	}

	output = classify_matches(queue)
	labels = [result["classification_label"] for result in output["classifiedResults"]["results"]]

	assert labels == ["Reference", "Reference"]


def test_isbn_normalization_reuses_separator_stripping_behavior() -> None:
	queue = {
		"resultChunks": [
			{"source_id": "s1", "result": {"title": "Livro A", "isbn": "978-0-306-40615-7"}},
			{"source_id": "s2", "result": {"title": "Livro B", "isbn": "9780306406157"}},
		]
	}

	output = classify_matches(queue)
	links = output["classifiedResults"]["deduplicationLinks"]

	assert len(links) == 1
	assert links[0]["method"] == "isbn"


def test_preserves_source_provenance_chain() -> None:
	queue = {"resultChunks": [{"source_id": "source-xyz", "result": {"title": "Item"}}]}
	output = classify_matches(queue)
	item = output["classifiedResults"]["results"][0]

	assert item["provenance"]["source_id"] == "source-xyz"
	assert item["source_id"] == "source-xyz"


def test_oversized_result_is_marked_rejected_without_silent_drop() -> None:
	large_text = "x" * 6000
	queue = {
		"resultChunks": [
			{"source_id": "s1", "result": {"title": large_text}},
		]
	}

	output = classify_matches(queue)
	results = output["classifiedResults"]["results"]

	assert len(results) == 1
	assert results[0]["oversized_rejected"] is True
	assert output["classificationMetrics"]["schemaFailureCount"] == 1


def test_preserves_input_order_no_reranking_in_classifier() -> None:
	queue = {
		"resultChunks": [
			{"source_id": "s1", "result": {"title": "first"}},
			{"source_id": "s2", "result": {"title": "second"}},
			{"source_id": "s3", "result": {"title": "third"}},
		]
	}

	output = classify_matches(queue)
	ids = [result["source_id"] for result in output["classifiedResults"]["results"]]

	assert ids == ["s1", "s2", "s3"]


def test_brand_substitution_context_injected_when_available() -> None:
	queue = {"resultChunks": [{"source_id": "s1", "result": {"title": "book"}}]}
	context = {"result-0": {"reason_code": "LOW_SAME_BRAND_COVERAGE"}}

	output = classify_matches(queue, brand_substitution_context=context)
	item = output["classifiedResults"]["results"][0]

	assert item["brand_substitution_context"] == {"reason_code": "LOW_SAME_BRAND_COVERAGE"}
