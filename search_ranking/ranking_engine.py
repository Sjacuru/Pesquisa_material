# FILE: search_ranking/ranking_engine.py
# MODULE: MODULE-003-03 — Ranking Engine
# EPIC: EPIC-003 — Search & Ranking
# RESPONSIBILITY: Order valid offers by delivered price and trust-aware ranking rules.
# EXPORTS: Ranking engine stub.
# DEPENDS_ON: search_ranking/match_classifier.py, source_governance/site_failure_monitor_auto_suspension.py.
# ACCEPTANCE_CRITERIA:
#   - Ranking responsibility remains separate from candidate retrieval and classification.
#   - Trust and delivered-price signals are represented as explicit ranking inputs.
# HUMAN_REVIEW: Yes — algorithmic correctness and SLA impact.

from __future__ import annotations

from search_ranking.text_normalization import normalize_text


DEFAULT_WEIGHTS = {
	"reputation_weight": 0.25,
	"recency_weight": 0.25,
	"similarity_weight": 0.25,
	"classification_weight": 0.25,
}


def _validate_weights(score_weights: dict[str, float]) -> dict[str, float]:
	required = {
		"reputation_weight",
		"recency_weight",
		"similarity_weight",
		"classification_weight",
	}
	if set(score_weights.keys()) != required:
		raise ValueError("score_weights must include all four required weights")

	for key in required:
		value = float(score_weights[key])
		if value <= 0:
			raise ValueError("all active weights must be > 0")

	total = sum(float(score_weights[key]) for key in required)
	if abs(total - 1.0) > 0.01:
		raise ValueError("sum(weights) must equal 1.0 ± 0.01")

	return {key: float(score_weights[key]) for key in required}


def _token_similarity(query_text: str, title_text: str) -> float:
	query_tokens = set(str(query_text or "").lower().split())
	title_tokens = set(str(title_text or "").lower().split())
	if not query_tokens or not title_tokens:
		return 0.5
	intersection = len(query_tokens.intersection(title_tokens))
	union = len(query_tokens.union(title_tokens))
	if union == 0:
		return 0.5
	return intersection / union


def _classification_signal(label: str) -> float:
	normalized_label = normalize_text(label)
	if normalized_label in {"textbook", "livro didatico", "livro didático"}:
		return 1.0
	if normalized_label in {"workbook", "caderno de atividades", "livro de exercicios", "livro de exercícios"}:
		return 0.85
	if normalized_label in {"solution manual", "manual de solucoes", "manual de soluções", "gabarito", "solucionario", "solucionário"}:
		return 0.8
	if normalized_label in {"reference", "referencia", "referência", "dicionario", "dicionário", "enciclopedia", "enciclopédia"}:
		return 0.75
	return 0.6


def _reputation_from_failure_rate(site_id: str, source_reputation_index: dict[str, object]) -> float:
	payload = source_reputation_index.get(site_id)
	failure_rate: float | None = None

	if isinstance(payload, (int, float)):
		failure_rate = float(payload)
	elif isinstance(payload, dict):
		candidate = payload.get("failure_rate")
		if isinstance(candidate, (int, float)):
			failure_rate = float(candidate)

	if failure_rate is None:
		return 0.5

	clamped = min(1.0, max(0.0, failure_rate))
	return 1.0 - clamped


def _normalize_scores(scores: list[float]) -> list[float]:
	if not scores:
		return []

	lowest = min(scores)
	highest = max(scores)
	if highest == lowest:
		return [100.0 for _ in scores]

	return [((score - lowest) / (highest - lowest)) * 100.0 for score in scores]


def _percentile_25(scores: list[float]) -> float:
	if not scores:
		return 0.0
	ordered = sorted(scores)
	index = int((len(ordered) - 1) * 0.25)
	return ordered[index]


def rank_results(
	classified_results: dict,
	score_weights: dict[str, float] | None,
	source_reputation_index: dict[str, object],
	query_text: str = "",
) -> dict[str, object]:
	"""
	Rank classified results by deterministic composite score and normalize to 0-100.
	"""
	weights = _validate_weights(score_weights or DEFAULT_WEIGHTS)
	items = (
		classified_results.get("results", [])
		if isinstance(classified_results, dict)
		else []
	)

	scored_rows: list[dict] = []
	for index, item in enumerate(items):
		site_id = str(item.get("source_id") or "")
		reputation_score = _reputation_from_failure_rate(site_id, source_reputation_index)
		recency_days = item.get("recency_days")
		if isinstance(recency_days, (int, float)):
			recency_score = max(0.0, min(1.0, 1.0 - (float(recency_days) / 365.0)))
		else:
			recency_score = 0.5
		similarity_score = _token_similarity(query_text, str(item.get("title") or ""))
		classification_score = _classification_signal(str(item.get("classification_label") or "Other"))

		composite_score = (
			weights["reputation_weight"] * reputation_score
			+ weights["recency_weight"] * recency_score
			+ weights["similarity_weight"] * similarity_score
			+ weights["classification_weight"] * classification_score
		)

		scored_rows.append(
			{
				"original_index": index,
				"item": dict(item),
				"composite_score": composite_score,
			}
		)

	sorted_rows = sorted(
		scored_rows,
		key=lambda row: (-row["composite_score"], row["original_index"]),
	)

	raw_sorted_scores = [row["composite_score"] for row in sorted_rows]
	normalized_scores = _normalize_scores(raw_sorted_scores)
	percentile_25 = _percentile_25(normalized_scores)

	ranked_output_results: list[dict] = []
	for row, normalized_score in zip(sorted_rows, normalized_scores):
		result = {
			**row["item"],
			"composite_score": round(row["composite_score"], 6),
			"normalized_score": round(normalized_score, 2),
			"low_confidence_flag": normalized_score <= percentile_25,
		}
		ranked_output_results.append(result)

	tied_rank_count = 0
	for current, nxt in zip(normalized_scores, normalized_scores[1:]):
		if abs(current - nxt) < 1e-9:
			tied_rank_count += 1

	flagged_count = sum(1 for result in ranked_output_results if result["low_confidence_flag"])

	return {
		"rankedResults": {
			"results": ranked_output_results,
			"compositeScores": [result["composite_score"] for result in ranked_output_results],
			"lowConfidenceFlags": [result["low_confidence_flag"] for result in ranked_output_results],
			"orderingLocked": True,
		},
		"rankingMetrics": {
			"scoreDistribution": [result["normalized_score"] for result in ranked_output_results],
			"tiedRankCount": tied_rank_count,
			"flaggedCount": flagged_count,
		},
	}
