# PROMPT 7 - Deployment Execution Backlog (Implementation Layer)

## Governance Classification

This document is an implementation execution backlog and delivery orchestration artifact.
It does not define new business scope and does not create a new EPIC.

- Canonical DOR document: `plan/06_Implementation/DEPLOYMENT_READINESS_DOR.md`
- Functional scope authority remains in the approved EPIC set (4 EPICs total)
- Functional requirement inventory remains FR-001 to FR-026

## Objective

Execute deployment-readiness work already implied by approved scope:

- Hardening tests and verification gates
- Source adapter quality and fallback behavior
- Operational resilience and observability
- Safe rollout readiness

## Story Backlog (Execution)

### Week 1 - Test Hardening and Determinism

1. Story T7-001: Ingestion and Canonicalization Unit Coverage
- Expand tests for parser, normalization, duplicate handling, and confidence routing.
- Ensure deterministic behavior for edge cases (missing quantity, ambiguous ISBN, OCR noise).

2. Story T7-002: Search and Ranking Determinism
- Add ranking determinism and tie-break tests.
- Validate exclusivity guard behavior and negative-path handling.

3. Story T7-003: Adapter Contract and Mapping Tests
- Add adapter contract tests across `ml_br`, `ev_br`, `kalunga_br`, `amazon_br`, `magalu_br`.
- Validate normalization mapping into canonical offer schema.

4. Story T7-004: CI Quality Gate Definition
- Define blocking gate for unit/integration tests and migration checks.
- Enforce minimum stability criteria for merge.

### Week 2 - Integration and Resilience

1. Story T7-005: End-to-End Workflow Integration
- Cover upload -> parse -> search -> edit -> export flow in integration tests.
- Validate audit trail generation for user edits and version events.

2. Story T7-006: Failure Injection and Fallbacks
- Simulate source failure/timeouts and assert fallback/retry behavior.
- Validate source eligibility guard and suspension handling paths.

3. Story T7-007: Concurrency and Job Runner Reliability
- Validate job lifecycle status transitions and idempotency.
- Add resilience checks for repeated trigger/retry scenarios.

### Week 3 - Deploy Readiness and Rollout

1. Story T7-008: Performance Baseline and SLO Checks
- Baseline critical path latency for ingestion and search execution.
- Define acceptable thresholds and regression alarms.

2. Story T7-009: Observability and Runbook Completion
- Ensure structured logs, key metrics, and error categorization are documented.
- Finalize operator runbook for incident triage and rollback triggers.

3. Story T7-010: Release Candidate and Go/No-Go
- Execute smoke suite on release candidate.
- Validate migration safety, rollback plan, and deployment checklist sign-off.

## Definition of Ready (Execution Stories)

A story can start when:

- Scope maps to existing approved FRs/EPICs
- Inputs and dependencies are explicit
- Test acceptance criteria are written
- Operational impact is identified

## Definition of Done (Execution Stories)

A story is complete when:

- Tests implemented and passing in CI
- Required docs updated (runbook/checklist if applicable)
- Evidence of validation is linked
- No governance scope drift introduced

## Appendix A - Ticket to Requirement Traceability

| Ticket | Description | Requirement Mapping |
|---|---|---|
| T7-001 | Ingestion and canonicalization unit coverage | FR-022, FR-024 |
| T7-002 | Search and ranking determinism | FR-025 |
| T7-003 | Adapter contract and mapping tests | FR-021, FR-026 |
| T7-004 | CI quality gate definition | FR-026 |
| T7-005 | End-to-end workflow integration | FR-024, FR-025, FR-026 |
| T7-006 | Failure injection and fallbacks | FR-021, FR-025 |
| T7-007 | Concurrency and job runner reliability | FR-024 |
| T7-008 | Performance baseline and SLO checks | FR-026 |
| T7-009 | Observability and runbook completion | FR-026 |
| T7-010 | Release candidate and go/no-go | FR-026 |

## Appendix B - Adapter Testing Inventory

| Source Key | Adapter Module | Category Focus | Test Type |
|---|---|---|---|
| `ml_br` | `source_adapters/ml_adapter.py` | marketplace_general | contract + mapping + fallback |
| `ev_br` | `source_adapters/ev_adapter.py` | books and didactic | contract + mapping + fallback |
| `kalunga_br` | `source_adapters/kalunga_adapter.py` | school supplies | contract + mapping + fallback |
| `amazon_br` | `source_adapters/amazon_adapter.py` | books and mixed catalog | contract + mapping + fallback |
| `magalu_br` | `source_adapters/magalu_adapter.py` | mixed catalog and electronics | contract + mapping + fallback |

## Reference Notes

- Superseded planning classification docs are archived/deprecated for traceability only.
- Canonical implementation readiness reference is `plan/06_Implementation/DEPLOYMENT_READINESS_DOR.md`.
