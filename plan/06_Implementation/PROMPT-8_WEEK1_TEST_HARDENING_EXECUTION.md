# PROMPT 8 - Week 1 Execution: Test Hardening and Determinism
## School Material Price Finder (Brazil MVP) - Implementation Layer

**Date**: March 27, 2026
**Sprint Week**: Week 1 of 3
**Scope**: Test hardening for ingestion/canonicalization, search/ranking, adapter contracts, and CI gate
**Reference**: `plan/06_Implementation/PROMPT-7_DEPLOYMENT_EXECUTION_BACKLOG.md`
**Canonical DOR**: `plan/06_Implementation/DEPLOYMENT_READINESS_DOR.md`

### Governance Classification
- **Type**: Week 1 Execution Prompt (Implementation Layer)
- **Operationalizes**: T7-001, T7-002, T7-003, T7-004 (from PROMPT-7 backlog)
- **FR Traceability**: FR-022, FR-024, FR-025, FR-026
- **Does NOT introduce**: New FRs, NFRs, modules, personas, or scope changes
- **Governance rules in effect**: GC-1 through GC-9 (unchanged)

---

## 1. Objective

Execute Week 1 stories from the deployment readiness backlog. The goal is to establish a test-hardened,
deterministic baseline for all EPIC-001-004 modules before integration and resilience work begins in Week 2.

**Week 1 Stories:**
- T7-001: Ingestion and Canonicalization Unit Coverage
- T7-002: Search and Ranking Determinism
- T7-003: Adapter Contract and Mapping Tests
- T7-004: CI Quality Gate Definition

**Exit Condition**: All four stories meet their Definition of Done before Week 2 begins.

---

## 2. Story T7-001 — Ingestion and Canonicalization Unit Coverage

**FR Mapping**: FR-022 (Canonicalization), FR-024 (OCR Ingestion)
**Modules Under Test**: EPIC-001 intake canonicalization module set

### 2.1 Target Test Files

| Test File | Module Covered | Priority |
|---|---|---|
| `tests/unit/intake_canonicalization/test_directive_deterministic_parser.py` | MODULE-001-01 / FR-001 | HIGH |
| `tests/unit/intake_canonicalization/test_quantity_unit_normalizer.py` | MODULE-001-03 / FR-003 | HIGH |
| `tests/unit/intake_canonicalization/test_duplicate_resolution_coordinator.py` | MODULE-001-04 / FR-004 | HIGH |
| `tests/unit/intake_canonicalization/test_confidence_gating_router.py` | MODULE-001-02 / FR-002 | HIGH |
| `tests/unit/intake_canonicalization/test_isbn_normalization_validation.py` | ISBN normalization / FR-009 | MEDIUM |
| `tests/unit/intake_canonicalization/test_missing_isbn_search_gate.py` | Missing ISBN gate | MEDIUM |
| `tests/unit/intake_canonicalization/test_category_rules_eligibility_validator.py` | FR-005 | MEDIUM |
| `tests/unit/intake_canonicalization/test_pdf_ingestion_field_extraction.py` | FR-001 PDF path | MEDIUM |
| `tests/unit/intake_canonicalization/test_ocr_extraction_processor.py` | MODULE-001-13 / FR-024 | MEDIUM |
| `tests/unit/intake_canonicalization/test_file_type_detection_router.py` | MODULE-001-11 / FR-024 | MEDIUM |
| `tests/unit/intake_canonicalization/test_pdf_coverage_layout_router.py` | MODULE-001-12 / FR-024 | MEDIUM |
| `tests/unit/intake_canonicalization/test_llm_fallback_gateway.py` | MODULE-001-14 / FR-023 | LOW |
| `tests/unit/intake_canonicalization/test_directive_audit_persistence.py` | Audit trail | LOW |
| `tests/unit/intake_canonicalization/test_directive_reconciliation_resolver.py` | Conflict resolution | LOW |
| `tests/unit/intake_canonicalization/test_directive_runtime_config.py` | Runtime config | LOW |

### 2.2 Required Edge-Case Coverage

For each HIGH-priority module, ensure tests cover:

**Directive Parser (FR-001)**:
- [ ] Missing quantity field → structured null, not exception
- [ ] Ambiguous unit strings (e.g., "cx", "unid", "pct") → normalized or flagged_ambiguous
- [ ] Item with no recognizable keyword → low-confidence output
- [ ] Multi-item line → correct split or merged pending review flag

**Quantity Normalizer (FR-003)**:
- [ ] Unit variations that map to the same canonical form (e.g., "un", "und", "unidade" → "unidade")
- [ ] Quantity with decimals (e.g., "0.5 kg") → correct scalar + unit
- [ ] Missing quantity with implied unit → `quantity: null`, `unit: null`, not fabricated value

**Duplicate Resolution (FR-004)**:
- [ ] Identical items from same source → deduplicated, not doubled
- [ ] Near-duplicate items (minor spelling diff) → queued for merge review
- [ ] Items with different quantities that are otherwise identical → flagged, not silently merged

**Confidence Gating Router (FR-002)**:
- [ ] High-confidence item → routes to search queue
- [ ] Low-confidence item → routes to human review queue
- [ ] Threshold boundary behavior (GC-5: do not invent thresholds; use existing config values)

### 2.3 Definition of Done — T7-001

- [ ] All HIGH-priority test files have edge-case tests added (missing quantity, ambiguous ISBN, OCR noise).
- [ ] All new tests pass (`pytest tests/unit/intake_canonicalization/` exits 0).
- [ ] No test asserts a fabricated threshold value (GC-5 compliance).
- [ ] Test coverage report reviewed for intake_canonicalization module directory.

---

## 3. Story T7-002 — Search and Ranking Determinism

**FR Mapping**: FR-025 (Ranking and Scoring), FR-015 (Search Execution)
**Modules Under Test**: EPIC-003 search_ranking module set

### 3.1 Target Test Files

| Test File | Module Covered | Priority |
|---|---|---|
| `tests/unit/search_ranking/test_ranking_engine.py` | Ranking / FR-025 | HIGH |
| `tests/unit/search_ranking/test_school_exclusivity_resolver.py` | Exclusivity guard / FR-016 | HIGH |
| `tests/unit/search_ranking/test_apostila_routing_guard.py` | Apostila routing / FR-017 | MEDIUM |
| `tests/unit/search_ranking/test_match_classifier.py` | Match classification | MEDIUM |
| `tests/unit/search_ranking/test_query_orchestrator.py` | Query orchestration / FR-015 | MEDIUM |

### 3.2 Required Determinism Coverage

**Ranking Engine (FR-025)**:
- [ ] Same inputs always produce the same ranked order (deterministic sort).
- [ ] Tie-break rule is explicit and documented in test comment (e.g., alphabetical by source name).
- [ ] Missing price field → item sorted to bottom, not exception.
- [ ] Zero-result input → returns empty list, no error.

**Exclusivity Guard (FR-016)**:
- [ ] School-exclusive item → filtered from non-enrolled user result set.
- [ ] Non-exclusive item → appears in all result sets.
- [ ] Guard applied before ranking (order enforced in test).
- [ ] Edge case: empty exclusivity list → all items pass guard.

**Negative-Path Coverage**:
- [ ] All-adapters-return-empty → graceful empty result, no exception.
- [ ] Malformed offer dict (missing required fields) → rejected at classifier, not propagated.
- [ ] Query string is empty or whitespace → validation error returned, no search executed.

### 3.3 Definition of Done — T7-002

- [ ] Ranking tie-break is tested and deterministic.
- [ ] Exclusivity guard negative cases are covered.
- [ ] All new tests pass (`pytest tests/unit/search_ranking/` exits 0).
- [ ] Integration smoke: `tests/integration/test_exclusivity_to_query_flow.py` still passes.

---

## 4. Story T7-003 — Adapter Contract and Mapping Tests

**FR Mapping**: FR-026 (Search Adapters), FR-021 (Source Governance)
**Modules Under Test**: `source_adapters/` (all 5 production adapters)

### 4.1 Adapter Inventory

| Adapter File | Target | Fixture Path |
|---|---|---|
| `source_adapters/amazon_adapter.py` | Amazon.com.br | `tests/fixtures/adapters/amazon_br_samples/` |
| `source_adapters/magalu_adapter.py` | Magalu.com.br | `tests/fixtures/adapters/magalu_br_samples/` |
| `source_adapters/estante_virtual_adapter.py` | EstanteVirtual.com.br | `tests/fixtures/adapters/estante_virtual_samples/` |
| `source_adapters/kalunga_adapter.py` | Kalunga.com.br | `tests/fixtures/adapters/kalunga_br_samples/` |
| `source_adapters/mercadolivre_adapter.py` | MercadoLivre.com.br | `tests/fixtures/adapters/mercadolivre_samples/` |

### 4.2 Contract Requirements Per Adapter

Each adapter must be validated against:

**Output Schema Conformance**:
- [ ] All adapters return a dict with required canonical keys: `title`, `price`, `source`, `url`.
- [ ] Optional keys (`isbn`, `author`, `condition`) are present or explicitly `None`, not absent.
- [ ] No adapter returns raw source-specific key names in final output.

**Mapping Coverage**:
- [ ] Title normalization: extra whitespace stripped, encoding correct.
- [ ] Price: returned as numeric type (float or Decimal), not string.
- [ ] Source identifier: matches the canonical source label used in `source_governance/`.
- [ ] URL: non-empty string, no truncation.

**Failure Contract**:
- [ ] Adapter receiving empty/malformed HTML fixture → returns `None` or raises typed exception, does not return partial dict.
- [ ] Adapter receiving a fixture with missing price field → returns `None` (not a zero-price offer).

### 4.3 Fixture Protocol

- All adapter tests MUST use local HTML/JSON fixtures (no network calls in unit tests).
- Fixtures must be committed under `tests/fixtures/adapters/<adapter_name>_samples/`.
- Fixture file naming: `<adapter>_valid_sample.html`, `<adapter>_missing_price.html`, `<adapter>_empty_response.html`.

### 4.4 Definition of Done — T7-003

- [ ] All 5 adapters have contract tests covering: valid sample, missing price, empty response.
- [ ] All tests use local fixtures only (no `requests` / `httpx` calls in test bodies).
- [ ] All new tests pass (`pytest tests/unit/` scoped to adapter test files exits 0).
- [ ] Source governance integration: `tests/integration/test_source_governance_to_query_execution.py` still passes.

---

## 5. Story T7-004 — CI Quality Gate Definition

**FR Mapping**: FR-026 (operationalizes build safety for all adapters/modules)
**Scope**: Define the blocking merge gate for the CI pipeline

### 5.1 Gate Requirements

The CI quality gate MUST block merge if any of the following fail:

| Gate Condition | Enforcement Point | Failure Action |
|---|---|---|
| Unit tests fail | `pytest tests/unit/` | Block merge |
| Integration tests fail | `pytest tests/integration/` | Block merge |
| Migration check fails | `python manage.py migrate --check` | Block merge |
| Import errors in source modules | `python -c "import intake_canonicalization, search_ranking, source_adapters, source_governance"` | Block merge |

### 5.2 Gate Configuration (pytest.ini / pyproject.toml)

Confirm `pytest.ini` or `pyproject.toml` contains:
- [ ] Testpaths configured to cover `tests/unit/` and `tests/integration/`.
- [ ] No test is marked `xfail` without an explicit GitHub issue reference in the reason string.
- [ ] No test uses `@pytest.mark.skip` without documented justification.

### 5.3 Minimum Stability Criteria for Merge

A pull request is mergeable only when:
- [ ] All unit tests pass (zero failures, zero errors).
- [ ] All integration tests pass (zero failures, zero errors).
- [ ] `python manage.py migrate --check` exits 0 (no pending migrations).
- [ ] No new `# type: ignore` without a GC-1 traceable comment.

### 5.4 Definition of Done — T7-004

- [ ] `pytest.ini` (or `pyproject.toml [tool.pytest.ini_options]`) reflects correct testpaths and markers.
- [ ] CI gate definition is documented (this file serves as the gate spec).
- [ ] Gate criteria reviewed and confirmed by Backend Lead before Week 2 starts.

---

## 6. Dependencies and Sequence

```
T7-001 (Ingestion Tests)  ──┐
T7-002 (Ranking Tests)    ──┤──→ T7-004 (CI Gate) ──→ Week 2 Start
T7-003 (Adapter Tests)    ──┘
```

T7-001, T7-002, and T7-003 may be executed in parallel.
T7-004 gate configuration should be finalized once T7-001 through T7-003 are green.

---

## 7. Governance Compliance

| Rule | Status | Evidence |
|---|---|---|
| GC-1 (Traceability) | PASS | All tasks map to FR-022, FR-024, FR-025, FR-026 |
| GC-5 (No Invented Thresholds) | PASS | No thresholds introduced; existing config values used |
| GC-8 (ID Immutability) | PASS | No FR/NFR IDs altered |
| Scope Ceiling | PASS | No features beyond school material comparison scope |
| No New FRs | PASS | All test work operationalizes existing approved FRs |

---

## 8. References

- `plan/06_Implementation/PROMPT-7_DEPLOYMENT_EXECUTION_BACKLOG.md` — parent backlog
- `plan/06_Implementation/DEPLOYMENT_READINESS_DOR.md` — canonical DOR and sign-off gate
- `plan/07_CONTEXT_ARCHIT/CONTEXT.md` — traveling context (canonical IDs, scope ceiling)
- `plan/06_Implementation/WEEK1_EXECUTION_CHECKLIST.md` — tactical checkbox tracker for Week 1
