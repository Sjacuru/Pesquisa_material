# Architecture Decision Record (ADR-0001)

**Project:** School Material Price Finder (Brazil MVP)  
**Date:** March 25, 2026  
**Status:** Approved (Architecture Input Baseline)

---

## 1) Decision Scope

This record captures the architecture and stack decisions approved after MDAP completion (19 approved modules), and establishes the baseline for Architecture artifacts.

Canonical source references:
- `CONTEXT.md` (MDAP handoff + carry-forward items)
- `MDAP_STAGE5_EPIC-004_APPROVED.md` (phase completion and architecture advancement)

---

## 2) Approved Architecture Decisions (Pre-Stack)

### A-01 Frontend Shape
**Decision:** Server-rendered web app with small interactive components, with admin/operator screens inside the same app (role-gated).

**Rationale:**
- Lower complexity than full SPA for MVP.
- Faster delivery for forms, tables, review queues, and export workflows.
- Better traceability for audit-sensitive interactions.
- Allows gradual enhancement later without full rewrite.

### A-02 Backend Shape
**Decision:** Modular Monolith.

**Rationale:**
- Single deployable unit with clear internal module boundaries.
- Simpler local operation and debugging.
- Lower operational overhead than split services.
- Preserves future option to extract services if justified.

### A-03 Storage Baseline
**Decision:** Relational DB + file/object storage, with no cache/search index initially.

**Rationale:**
- Strong fit for structured, relationship-heavy domain data.
- Clean separation for binary artifacts (uploads/exports).
- Avoids premature infrastructure complexity.
- Cache/index can be added only if performance evidence requires it.

### A-04 Integration Approach
**Decision:** Balanced strategy: API when available + targeted scraping adapters where API is absent.

**Operational Pattern:**
- Adapter-per-source interface.
- Background job queue for search/integration waves.
- Retry with exponential backoff.
- Circuit breaker per source.

**Rationale:**
- Maintains coverage across heterogeneous retailer ecosystems.
- Aligns with source-health and suspension requirements.
- Limits blast radius of source-specific failures.

### A-05 Runtime Baseline
**Decision:** Minimal-but-effective observability, append-only business audit trail, local-first deployment, and SLA-oriented execution controls.

**Required runtime controls:**
- Structured logs with correlation IDs.
- Basic metrics (latency, timeout/error rates by source, queue behavior).
- Append-only audit events for user/operator decisions.
- Graceful degradation when some sources fail.

### A-06 FR-020 Export Format Resolution
**Decision:** FR-020 supported export formats are PDF, CSV, and JSON.

**Rationale:**
- Resolves the prior mismatch between PRD/CONTEXT wording and EPIC-004 MDAP artifacts.
- Aligns the Architecture phase with the approved EPIC-004 export-module contracts.
- Keeps ASSUMPTION-003 limited to schema/formatting details rather than format-set ambiguity.

---

## 3) Approved Stack Decisions

### S-01 Language/Runtime
**Decision:** Python 3.12.

### S-02 Deployable Shape
**Decision:** Single deployable app.

### S-03 Integration Comfort Level
**Decision:** Comfortable with targeted scraping adapters and background jobs.

### S-04 Initial Hosting Target
**Decision:** Local-only first (personal use and testing).

---

## 4) Architecture Guardrails (Must Preserve)

- Keep FR/NFR IDs immutable (FR-001..FR-021, NFR-001..NFR-005).
- Preserve approved 19-module MDAP decomposition as baseline.
- Do not introduce out-of-scope features without PRD amendment.
- Keep unresolved carry-forward items explicit in architecture outputs.

### Carry-Forward Items (from MDAP/CONTEXT)
- ASSUMPTION-003: Export schema/format details unresolved.
- ASSUMPTION-004: Brand reason-code taxonomy unresolved.
- THRESHOLD-002: Performance reference hardware/environment unresolved.
- THRESHOLD-003: Audit-log retention duration unresolved.
- THRESHOLD-005: Peak concurrent users without degradation unresolved.

### Resolved in Architecture
- FR-020 supported export formats: PDF, CSV, and JSON.

---

## 5) Next Architecture Artifacts (Execution Order)

1. **System Context & Container View**
   - Single deployable app boundaries, actor/system interactions.
2. **Module-to-Component Mapping**
   - Map all 19 MDAP modules to backend/frontend/job/adapters.
3. **Data Architecture**
   - Relational schema domains + file/object artifact model.
4. **Integration Architecture**
   - Adapter contracts, queue model, retry/backoff, circuit-breaker policy.
5. **Runtime & NFR Architecture**
   - Observability, audit model, SLA controls, local deployment blueprint.
6. **Architecture Risks + Decision Log**
   - Open items, mitigations, and ADR updates.

---

## 6) Acceptance for Architecture Kickoff

Architecture phase may proceed when all outputs above reference this ADR as baseline and remain traceable to the 19 approved MDAP modules.

**Approval Marker:** ✅ Decisions locked for Architecture artifact generation.
