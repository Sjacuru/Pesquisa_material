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

---

## ADR-0002: Hybrid LLM Directive Extraction Architecture Decision

**Status**: DRAFT — PENDING STAKEHOLDER SIGN-OFF (requires FR-023 PRD addendum approval)  
**Date**: March 27, 2026  
**References**: PRD_ADDENDUM_FR023_AI_DIRECTIVE_EXTRACTION.md; EPIC_AMENDMENT_001_CIR002; MDAP_MIA-001

---

### ⛔ Critical Status: Proposed, Not Baseline

ADR-0001 remains the canonical architecture baseline. ADR-0002 is a proposed amendment and MUST NOT be treated as active baseline until all approval gates are complete.

Approval gates required:
1. PRD Addendum FR-023 signed off
2. EPIC Amendment CIR-002 approved
3. MDAP MIA-001 human-gate approved

Approval paths:
- **APPROVED**: ADR-0002 constraints become active and merge into baseline architecture governance.
- **CONDITIONAL**: ADR-0002 remains pending with explicit conditions and deadlines.
- **REJECTED / REWORK**: ADR-0002 is superseded by revised amendment draft; ADR-0001 remains sole baseline.

---

### Decision

**Adopt a deterministic-first, LLM-fallback hybrid architecture for school directive field extraction (school_exclusive, required_sellers, preferred_sellers).**

Deterministic notation parsing (MODULE-001-08) runs for all items and is authoritative when confidence ≥ THRESHOLD-LLM-01. LLM invocation (MODULE-001-09) is conditional — triggered only when deterministic confidence falls below the threshold. A reconciliation module (MODULE-001-10) merges outputs using an explicit three-rule precedence policy and writes a full audit record.

This decision is **Option C** selected after explicit comparison:
- Option A (deterministic only) rejected: too many items routed to manual review for non-standard formats
- Option B (LLM full replacement) rejected: non-deterministic, high cost, no audit trace guarantee

---

### Amendments to ADR-0001 Guardrails

| Guardrail | Amendment |
|-----------|-----------|
| FR/NFR ID immutability (FR-001..FR-021) | Extended: FR-022 (via PRD_ADDENDUM_FR022 + CIR-001) and FR-023 (via PRD_ADDENDUM_FR023 + CIR-002) added. Proposed canonical range on approval: FR-001..FR-023 (both FR-022 and FR-023 pending sign-off via separate CIRs) |
| Preserve 19-module MDAP decomposition | Extended: +4 pending modules (MODULE-001-08, 001-09, 001-10 via CIR-002; MODULE-003-05 via CIR-001). On approval: 23 total modules |
| No out-of-scope features without PRD amendment | Satisfied: FR-023 PRD addendum filed and marked DRAFT pending sign-off |
| Keep carry-forward items explicit | New carry-forward: THRESHOLD-LLM-01 through THRESHOLD-LLM-05 (all unresolved, must be stakeholder decisions) |

### Additional Architecture Carry-Forward Items (Added by ADR-0002)

| Item | Scope | Resolution Required By |
|------|-------|----------------------|
| THRESHOLD-LLM-01 | LLM trigger confidence floor | Stakeholder decision — before Stage B |
| THRESHOLD-LLM-02 | LLM auto-acceptance floor | Stakeholder decision — before Stage B |
| THRESHOLD-LLM-03 | LLM call timeout budget | Stakeholder decision — before Stage B |
| THRESHOLD-LLM-04 | Shadow mode precision floor for live-promotion | Stakeholder decision — before Stage D |
| THRESHOLD-LLM-05 | Shadow mode minimum sample size | Stakeholder decision — before Stage D |
| OQ-FR023-02 (LLM rationale persistence model) | **Decision Question**: Store LLM rationale + call payload in (A) versioned audit trail JSON record (MODULE-004-02 extended schema), or (B) separate `llm_call_log` table? Impact: MODULE-004-02 schema extension required if (A) is chosen; timing: PRD sign-off before MDAP detailed design | **ESCALATED: PRD sign-off before MDAP implementation design** |
| MODULE-004-02 schema coordination | Align reconciliation_audit_record contract with MODULE-004-02 (EPIC-004 Versioned Audit Trail); required for Stage C gate (MDAP Section 6) | Before Stage C — coordinate with EPIC-004 team |
| LLM provider/model selection | Architecture implementation | Before Stage B — deferred to Architecture owner |
| LLM API credential management pattern | Architecture/security | Before Stage B — must follow secure-credential baseline |
| Prompt versioning strategy | Architecture implementation | Before Stage B |

### New Architecture Guardrails (ADR-0002)

- LLM calls are batch/async only — NEVER synchronous on user-facing request path
- LLM prompt content must contain NO personal data (item text and category context only)
- Shadow mode is a deployment configuration flag — default ON until THRESHOLD-LLM-04 precision gate clears
- Shadow mode exit requires human gate sign-off (cannot be automated gate)
- All LLM call results (success and failure) must be written to audit trail BEFORE the item advances in pipeline
- LLM output NEVER overwrites a deterministic result that is above THRESHOLD-LLM-01

**Approval Marker:** DRAFT — Locked for implementation planning only after PRD_ADDENDUM_FR023 is signed off and CIR-002 / MIA-001 are approved.
