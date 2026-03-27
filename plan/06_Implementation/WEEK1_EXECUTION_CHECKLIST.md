# Week 1 Execution Checklist
## School Material Price Finder — Deployment Readiness Sprint

**Date**: March 27, 2026
**Sprint Week**: Week 1 of 3
**Parent Backlog**: `plan/06_Implementation/PROMPT-7_DEPLOYMENT_EXECUTION_BACKLOG.md`
**Execution Guide**: `plan/06_Implementation/PROMPT-8_WEEK1_TEST_HARDENING_EXECUTION.md`
**DOR**: `plan/06_Implementation/DEPLOYMENT_READINESS_DOR.md`

### Gate Rule
No item may be marked complete unless the associated `pytest` command exits 0 with no failures or errors.

---

## T7-001: Ingestion and Canonicalization Unit Coverage

**FR Mapping**: FR-022, FR-024
**Test Directory**: `tests/unit/intake_canonicalization/`

### Edge Cases — Directive Parser
- [ ] Missing quantity field → structured null output, no exception raised
- [ ] Ambiguous unit string (e.g., "cx", "unid", "pct") → normalized or flagged_ambiguous
- [ ] Item with no recognizable keyword → low-confidence output produced
- [ ] Multi-item line → correct split or merged-pending-review flag applied

### Edge Cases — Quantity Normalizer
- [ ] "un", "und", "unidade" all normalize to the same canonical form
- [ ] Decimal quantity (e.g., "0.5 kg") → correct scalar and unit pair
- [ ] Missing quantity with implied unit → `quantity: null`, `unit: null` (not fabricated)

### Edge Cases — Duplicate Resolution Coordinator
- [ ] Identical items from same source → deduplicated, not doubled
- [ ] Near-duplicate (minor spelling difference) → queued for merge review
- [ ] Same item with different quantities → flagged, not silently merged

### Edge Cases — Confidence Gating Router
- [ ] High-confidence item → routes to search queue
- [ ] Low-confidence item → routes to human review queue
- [ ] Threshold boundary behavior uses existing config values (no invented thresholds)

### Execution Sign-Off — T7-001
- [ ] `pytest tests/unit/intake_canonicalization/` exits 0
- [ ] No test asserts a fabricated threshold value (GC-5 compliance verified)
- [ ] Coverage report reviewed for intake_canonicalization directory

---

## T7-002: Search and Ranking Determinism

**FR Mapping**: FR-025, FR-016, FR-015
**Test Directory**: `tests/unit/search_ranking/`

### Determinism — Ranking Engine
- [ ] Same inputs produce identical ranked order on repeated runs
- [ ] Tie-break rule is explicit and documented in test comment
- [ ] Missing price field → item sorted to bottom, no exception
- [ ] Zero-result input → empty list returned, no error

### Determinism — Exclusivity Guard
- [ ] School-exclusive item excluded from non-enrolled user result set
- [ ] Non-exclusive item appears in all result sets
- [ ] Guard is applied before ranking (order of operations enforced in test)
- [ ] Empty exclusivity list → all items pass guard

### Negative-Path Coverage
- [ ] All adapters return empty → graceful empty result, no exception
- [ ] Malformed offer dict (missing required fields) → rejected at classifier, not propagated
- [ ] Empty or whitespace query string → validation error returned, no search executed

### Integration Smoke
- [ ] `pytest tests/integration/test_exclusivity_to_query_flow.py` still passes (no regression)

### Execution Sign-Off — T7-002
- [ ] `pytest tests/unit/search_ranking/` exits 0
- [ ] Ranking tie-break test exists and is deterministic

---

## T7-003: Adapter Contract and Mapping Tests

**FR Mapping**: FR-026, FR-021
**Adapters**: amazon_br, magalu_br, ev_br, kalunga_br, ml_br

### Output Schema — All Adapters
- [ ] `title` key present (string, whitespace-stripped)
- [ ] `price` key present (float or Decimal, not string)
- [ ] `source` key matches canonical label used in source_governance
- [ ] `url` key is a non-empty, non-truncated string
- [ ] Optional keys (`isbn`, `author`, `condition`) are present or explicitly `None`, never absent

### Fixture Coverage — Per Adapter (5 adapters × 3 fixtures = 15 items)

**amazon_br**
- [ ] Valid sample fixture parses to correct canonical output
- [ ] Missing price fixture → returns `None`, not zero-price offer
- [ ] Empty response fixture → returns `None` or raises typed exception, not partial dict

**magalu_br**
- [ ] Valid sample fixture parses to correct canonical output
- [ ] Missing price fixture → returns `None`, not zero-price offer
- [ ] Empty response fixture → returns `None` or raises typed exception, not partial dict

**ev_br (Estante Virtual)**
- [ ] Valid sample fixture parses to correct canonical output
- [ ] Missing price fixture → returns `None`, not zero-price offer
- [ ] Empty response fixture → returns `None` or raises typed exception, not partial dict

**kalunga_br**
- [ ] Valid sample fixture parses to correct canonical output
- [ ] Missing price fixture → returns `None`, not zero-price offer
- [ ] Empty response fixture → returns `None` or raises typed exception, not partial dict

**ml_br (Mercado Livre)**
- [ ] Valid sample fixture parses to correct canonical output
- [ ] Missing price fixture → returns `None`, not zero-price offer
- [ ] Empty response fixture → returns `None` or raises typed exception, not partial dict

### Fixture Protocol Compliance
- [ ] All adapter test files use local fixtures only (no `requests`/`httpx` calls in test bodies)
- [ ] All fixture files committed under `tests/fixtures/adapters/`

### Integration Smoke
- [ ] `pytest tests/integration/test_source_governance_to_query_execution.py` still passes

### Execution Sign-Off — T7-003
- [ ] All 5 adapters have 3 fixture-backed tests each (15 passing tests minimum)
- [ ] `pytest` scoped to adapter test files exits 0

---

## T7-004: CI Quality Gate Definition

**FR Mapping**: FR-026 (operationalizes build safety)
**Files**: `pytest.ini` or `pyproject.toml [tool.pytest.ini_options]`

### Gate Conditions Verified
- [ ] `pytest tests/unit/` exits 0 (unit test gate confirmed)
- [ ] `pytest tests/integration/` exits 0 (integration test gate confirmed)
- [ ] `python manage.py migrate --check` exits 0 (no pending migrations)
- [ ] `python -c "import intake_canonicalization, search_ranking, source_adapters, source_governance"` exits 0

### pytest Configuration
- [ ] Testpaths in `pytest.ini`/`pyproject.toml` cover both `tests/unit/` and `tests/integration/`
- [ ] No test is marked `xfail` without a GitHub issue reference in the reason string
- [ ] No test uses `@pytest.mark.skip` without a documented justification comment

### Minimum Stability Criteria Enforced
- [ ] Zero unit test failures
- [ ] Zero integration test failures
- [ ] Zero pending unapplied migrations
- [ ] No new `# type: ignore` without a GC-1 traceable comment

### Execution Sign-Off — T7-004
- [ ] Gate spec reviewed by Backend Lead
- [ ] All four gate conditions manually verified and passing before Week 2

---

## Week 1 Final Sign-Off

Complete this block when all four stories are done:

| Story | All Checksboxes Done | pytest Exit 0 | Governance Compliant |
|---|---|---|---|
| T7-001 Ingestion Unit Coverage | [ ] | [ ] | [ ] |
| T7-002 Search and Ranking Determinism | [ ] | [ ] | [ ] |
| T7-003 Adapter Contract Tests | [ ] | [ ] | [ ] |
| T7-004 CI Quality Gate | [ ] | [ ] | [ ] |

**Week 1 Cleared for Week 2** (Backend Lead sign-off):
Name: _________________ Date: _________

---

## References

- `plan/06_Implementation/PROMPT-8_WEEK1_TEST_HARDENING_EXECUTION.md` — detailed execution guide
- `plan/06_Implementation/PROMPT-7_DEPLOYMENT_EXECUTION_BACKLOG.md` — parent backlog (T7-001..T7-010)
- `plan/06_Implementation/DEPLOYMENT_READINESS_DOR.md` — DOR and sprint structure
- `plan/07_CONTEXT_ARCHIT/CONTEXT.md` — canonical IDs and governance rules
