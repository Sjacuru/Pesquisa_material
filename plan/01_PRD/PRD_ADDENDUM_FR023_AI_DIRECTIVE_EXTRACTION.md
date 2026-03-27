# PRD Addendum: AI-Assisted Directive Extraction Fallback (FR-023)

**Status**: DRAFT — PENDING STAKEHOLDER SIGN-OFF  
**Date**: March 27, 2026  
**References**: PRD.md (FR-001..FR-021) [BASELINE — NOT MODIFIED]; PRD_ADDENDUM_FR022.md (FR-022 — school-defined seller exclusivity) [NOT MODIFIED]  
**Approver**: _________________ Date: _________  
**Architecture Lead**: _________________ Date: _________  
**Data Lead**: _________________ Date: _________

---

## 1. Executive Summary

The directive extraction fields introduced by FR-022 (school_exclusive, required_sellers, preferred_sellers) rely on pattern-based notation parsing from PDF documents. When document format is non-standard, shorthand notation is unfamiliar, or seller names are ambiguous, the deterministic parser produces low-confidence outputs that are currently routed en masse to manual review.

This addendum adds a hybrid extraction path: deterministic parsing runs first and is authoritative for all high-confidence results. When directive confidence falls below a configurable threshold, a Large Language Model (LLM) fallback is invoked as a secondary extractor. All LLM outputs carry explicit confidence, rationale, and traceability fields. LLM output is never treated as authoritative without a reconciliation pass and never overwrites a high-confidence deterministic result.

**In Scope**:
- Deterministic directive parser as mandatory first pass for all items
- LLM fallback invocation only when deterministic directive confidence < [THRESHOLD-LLM-01]
- LLM output fields: extracted directive, confidence score, rationale, model identifier
- Reconciliation resolver that merges deterministic and LLM outputs per precedence policy
- Directive extraction contract: structured output consumed by MODULE-003-05 (School Exclusivity Resolver)
- Shadow-mode gate before LLM results affect live routing decisions
- Audit trail for every LLM call, result, and reconciliation decision

**Out of Scope**:
- LLM use for non-directive fields (item name, quantity, ISBN — existing FR-001 extraction is unchanged)
- Real-time LLM invocation during user-facing request (LLM calls are batch/async)
- Choice of LLM provider or model (deferred to Architecture phase)
- LLM fine-tuning or custom model training
- Human-in-the-loop LLM output review UI (basic review queue entry is sufficient for MVP)

---

## 2. Decision Record: Hybrid Architecture Selection

### Options Considered

| Option | Description | Decision |
|--------|-------------|----------|
| A — Deterministic only | Use existing notation parser; route all uncertain items to manual review | Rejected: too many manual reviews for non-standard formats |
| B — LLM full replacement | Replace deterministic parser with LLM for all directive extraction | Rejected: non-deterministic, high cost, no audit trace guarantee |
| **C — Hybrid (deterministic first, LLM fallback)** | **Deterministic is authoritative; LLM invoked only on low-confidence outputs** | **SELECTED** |

### Rationale for Option C
- Deterministic parser handles well-structured documents reliably at zero latency and cost
- LLM cost and latency budget is spent only on genuinely ambiguous cases
- All LLM outputs are traceable (model ID, prompt hash, confidence, rationale)
- Reconciliation policy prevents LLM from silently overriding deterministic results
- Shadow mode allows quality measurement before LLM routing affects live decisions

---

## 3. New Functional Requirement

### FR-023 [MUST]: The system shall apply LLM-assisted analysis as a controlled fallback for directive field extraction when deterministic directive confidence is below threshold, merging results via an explicit reconciliation policy and recording all LLM interactions to the audit trail.

**Acceptance Criteria**:

| ID | Given | When | Then |
|----|-------|------|------|
| AC1 | Item with deterministic directive confidence ≥ [THRESHOLD-LLM-01] | Extraction pipeline runs | LLM fallback shall NOT be invoked; deterministic result is used as-is |
| AC2 | Item with deterministic directive confidence < [THRESHOLD-LLM-01] | Extraction pipeline runs | LLM fallback SHALL be invoked for that item's directive fields only |
| AC3 | LLM invocation occurs | LLM call completes | Output shall include: extracted directive fields, confidence in [0.00, 1.00], rationale string, model identifier, and call timestamp |
| AC4 | LLM output is available | Reconciliation runs | If LLM directive confidence ≥ [THRESHOLD-LLM-02] and deterministic confidence < [THRESHOLD-LLM-01], then LLM result shall be used as the canonical directive, decision_source=llm_fallback |
| AC5 | LLM output is available | Reconciliation runs | If LLM directive confidence < [THRESHOLD-LLM-02], then item shall be marked requires_human_review=true; no directive is auto-accepted |
| AC6 | LLM produces any output | Reconciliation completes | Every LLM call, result, and reconciliation decision shall be written to audit trail before item advances |
| AC7 | Human reviewer annotates directive | Override is submitted | decision_source shall be set to human_override; prior LLM and deterministic results shall remain in audit trail (not deleted) |
| AC8 | Shadow mode is active | LLM result is produced | LLM result shall be logged and measured but shall NOT affect routing or directive fields in live records |
| AC9 | LLM call fails (timeout/error) | Retry policy exhausted | Item shall be marked requires_human_review=true; fallback error and attempt count shall be logged; pipeline shall not halt |
| AC10 | Item has overall item confidence ≥ 0.90 but directive confidence remains below acceptance threshold | Confidence gates are evaluated together (FR-002 + FR-023) | Item shall be routed to review_required; directive gate blocks auto-accept until directive is resolved |

**Source**: EPIC-003 Amendment (MODULE-003-05 School Exclusivity Resolver requires reliable directive input); FR-022 directive field additions; stakeholder decision Option C — hybrid LLM fallback.

**Depends On**: FR-001 (extraction pipeline), FR-002 (confidence gating), FR-022 (directive fields)

**Priority**: [MUST] — reason: Without reliable directive detection, MODULE-003-05 receives low-quality inputs causing over-routing to review queue; hybrid fallback is the minimum viable fix consistent with the deterministic-first architecture principle.

---

## 4. Directive Extraction Contract

All modules downstream of FR-023 extraction (MODULE-003-05, MODULE-004-01, MODULE-004-02) consume this contract. The contract is immutable once MODULE-001-08 is approved.

### Per-Item Directive Output Fields

```
directive_confidence (float, 0.00–1.00)
  - Confidence of the winning directive extraction result (highest of deterministic or accepted LLM)
  - Inherited by MODULE-003-05 for routing decisions

decision_source (enum)
  - Values: "deterministic" | "llm_fallback" | "human_override"
  - Tracks which extraction path produced the accepted result

requires_human_review (bool)
  - true: no extraction path produced a high-enough confidence result
  - false: accepted result meets threshold

llm_rationale (string | None)
  - Non-null only when decision_source = "llm_fallback"
  - Human-readable explanation from LLM for its extraction decision
  - Stored in audit trail; not exposed in end-user UI

llm_model_id (string | None)
  - Model identifier (provider + model name + version) at invocation time
  - Non-null only when LLM was invoked (regardless of whether result was accepted)

directive_extraction_timestamp (datetime)
  - UTC timestamp when the directive extraction (deterministic or LLM merge) was finalized
```

**Existing FR-022 Fields** (unchanged contract; sourced by extraction, consumed by MODULE-003-05):
```
school_exclusive (bool)
required_sellers (list[str])
preferred_sellers (list[str])
exclusive_source (string — "document_notation" | "user_annotation" | None)
```

---

## 5. Scope Boundary Validation Checklist

- [x] All new/modified requirements trace to PERSONA-001 goals (reliable school-list automation with low manual effort)
- [x] FR-023 remains inside scope ceiling (complete school lists from mixed document formats)
- [x] No PRD Section 7 out-of-scope features are reintroduced (LLM fallback is internal extraction optimization, not a new product surface)

---

## 6. Impact on Downstream Phases

### EPIC Amendment (CIR-002) Impact
- Module count change: +3 modules (MODULE-001-08, MODULE-001-09, MODULE-001-10)
- EPIC-001 re-scope: extends from 7 to 10 modules; preserves forward-only dependency direction
- Cross-EPIC impact: MODULE-001-10 output becomes upstream contract for MODULE-003-05
- Risk increase: MODULE-001-09 is HIGH risk (external dependency, latency, and cost control)

### MDAP Impact
- Requires MIA-001 full stage sequence for all three new modules
- Risk profile: MODULE-001-09 HIGH, MODULE-001-08 MEDIUM, MODULE-001-10 HIGH
- Gating dependencies: THRESHOLD-LLM-01/02/03 must be resolved before Stage B/C activation

### Architecture Impact (Cost & Latency Notes)
- LLM invocation cost must be budgeted against operational constraints
- Invocation frequency remains unknown until THRESHOLD-LLM-01 is set and shadow-mode metrics are collected
- THRESHOLD-LLM-03 timeout and retry policy must be validated against NFR-001 (10-minute SLA)

---

## 7. Conflict Resolution

| Existing FR | Potential Conflict | Resolution | Status |
|---|---|---|---|
| FR-010 (Brand Fallback Approval) | LLM may suggest sellers not in active pool | No conflict. FR-023 is pre-search extraction. Active-source eligibility remains enforced downstream by MODULE-003-05 + MODULE-002-04. | ✅ RESOLVED |
| FR-018 (User Edits) | User may override LLM-produced directive | By design. AC7 allows human override and preserves traceability via decision_source=human_override. | ✅ RESOLVED |
| FR-019 (Versioning) | LLM rationale/version history storage must be explicit | AC6 requires all LLM interactions logged. Storage mechanism is escalated by OQ-FR023-02 for sign-off. | ✅ RESOLVED (pending storage choice) |
| FR-022 (Directive Fields) | FR-023 changes directive behavior | No conflict. FR-022 defines field schema; FR-023 improves extraction reliability for that schema. | ✅ RESOLVED |

---

## 8. Module Definitions (for EPIC Amendment CIR-002)

### MODULE-001-08: Deterministic Directive Parser
- **Responsibility**: Parse directive notation and emit deterministic directive contract values (including directive_confidence and decision_source=deterministic).
- **Deliverable**: Stage A deterministic contract output for every item.
- **Dependencies**: MODULE-001-01 output, FR-022 field definitions.
- **Risk Level**: MEDIUM.

### MODULE-001-09: LLM Fallback Gateway
- **Responsibility**: Invoke LLM only when directive_confidence < THRESHOLD-LLM-01; return structured directive output with confidence, rationale, and model_id.
- **Deliverable**: Controlled fallback with timeout/retry behavior and full call logging.
- **Dependencies**: MODULE-001-08 unresolved items, THRESHOLD-LLM-01, THRESHOLD-LLM-03.
- **Risk Level**: HIGH.

### MODULE-001-10: Directive Reconciliation Resolver
- **Responsibility**: Merge deterministic + LLM outputs by policy; set final decision_source and requires_human_review; persist reconciliation audit record.
- **Deliverable**: Canonical directive contract consumed downstream by MODULE-003-05.
- **Dependencies**: MODULE-001-08, MODULE-001-09 (when invoked), THRESHOLD-LLM-02.
- **Risk Level**: HIGH.

---

## 9. Threshold Registry (UNRESOLVED — Requires Stakeholder Sign-Off)

All items below are tagged `[THRESHOLD NEEDED]` per governance rule GC-8 (no invented thresholds). These MUST be resolved before EPIC Amendment CIR-002 advances past human gate.

| Threshold ID | Description | Scope | Current Value |
|-------------|-------------|-------|---------------|
| THRESHOLD-LLM-01 | Deterministic directive confidence below which LLM fallback is triggered | FR-023, AC1, AC2 | [THRESHOLD NEEDED] |
| THRESHOLD-LLM-02 | LLM output confidence floor for auto-acceptance of LLM result | FR-023, AC4, AC5 | [THRESHOLD NEEDED] |
| THRESHOLD-LLM-03 | Maximum LLM call latency (ms) per item before timeout and fallback to review queue | FR-023, AC9 | [THRESHOLD NEEDED] |
| THRESHOLD-LLM-04 | LLM precision floor required to exit shadow mode and promote to live routing | FR-023, AC8 | [THRESHOLD NEEDED] |
| THRESHOLD-LLM-05 | Minimum shadow mode sample size (item count) before shadow-mode exit gate can open | FR-023, AC8 | [THRESHOLD NEEDED] |

---

## 10. Affected Existing Requirements

### FR-001 (PDF Ingestion & Field Extraction) — EXTENDED
- No changes to original non-directive field set.
- Extension: extraction pipeline emits directive_confidence alongside FR-022 directive fields.
- Extraction stage records whether directive detection came from deterministic notation rules.

### FR-002 (Confidence Gating Router) — EXTENDED
- Original thresholds (≥0.90 auto-accept, 0.70–0.89 review, <0.70 reject) still apply to base item extraction quality.
- Directive fields use directive_confidence with THRESHOLD-LLM-01/02.
- **Resolution rule**: If directive gate fails (requires_human_review=true), item state is review_required even when overall item confidence would otherwise auto-accept.

### FR-022 (School-Defined Seller Exclusivity) — DEPENDENCY
- FR-022 introduced directive fields; FR-023 improves extraction reliability for those fields.
- FR-022 behavior and schema are not amended.
- MODULE-003-05 continues applying precedence policy without source-specific exceptions.

---

## 11. Implementation Sequence

To protect Step 1 baseline stability, FR-023 implementation is staged:

| Stage | Deliverable | Gate |
|-------|-------------|------|
| A | Directive extraction contract fields added to DB schema; MODULE-001-08 deterministic parser emits all contract fields; decision_source=deterministic always | Merge when Step 1 upload→DB baseline tests all pass |
| B | MODULE-001-09 LLM Fallback Gateway added behind feature flag; invoked only when below THRESHOLD-LLM-01 | THRESHOLD-LLM-01 and THRESHOLD-LLM-03 resolved |
| C | MODULE-001-10 Reconciliation Resolver merges outputs; requires_human_review routing live | THRESHOLD-LLM-02 resolved; shadow metrics active |
| D | Shadow mode exit gate: LLM precision ≥ THRESHOLD-LLM-04 over sample ≥ THRESHOLD-LLM-05 → promote LLM results to live routing | Human gate sign-off required; metrics attached to decision |

---

## 12. Open Questions

**OQ-FR023-01**: Should LLM fallback be disableable per-school configuration? Decision needed before Stage B.

**OQ-FR023-02 [ESCALATE TO PRD SIGN-OFF]**: Where should `llm_rationale` and full LLM call payload be persisted?
- Option A: Add structured JSON field(s) in MODULE-004-02 versioned audit trail.
- Option B: Persist in separate `llm_call_log` store/table linked by item/version IDs.
- **Decision deadline**: Before MDAP implementation design begins, because it changes MODULE-004-02 schema and persistence boundaries.

**OQ-FR023-03**: What is the escalation path when requires_human_review=true items remain unreviewed after N days?

---

## 13. Approvals and Sign-Off Gate

This addendum cannot advance beyond DRAFT until all required approvals are completed.

- [ ] Product Owner approval (scope ceiling and FR priority)
- [ ] Architecture Lead approval (integration feasibility and runtime impact)
- [ ] Data Lead approval (audit trail/persistence schema impact)

**Sign-Off Fields**  
**Product Owner**: _________________ Date: _________  
**Architecture Lead**: _________________ Date: _________  
**Data Lead**: _________________ Date: _________

---

## HANDOFF NOTE

This addendum SHALL be consumed by:
- EPIC Amendment CIR-002 (EPIC-001 extension: MODULE-001-08, MODULE-001-09, MODULE-001-10)
- MDAP MIA-001 (module impact assessment for the three new modules)
- Architecture phase (LLM integration pattern, provider selection, latency/cost budget)

All FR IDs in this addendum (FR-023) are CANONICAL from this point. Do NOT modify FR-023 ID or acceptance criteria numbering in downstream documents.
