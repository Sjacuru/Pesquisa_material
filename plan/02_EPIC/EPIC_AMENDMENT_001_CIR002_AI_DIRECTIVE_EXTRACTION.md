# EPIC-001 Amendment: Add Modules MODULE-001-08, MODULE-001-09, MODULE-001-10
## Change Impact Record — CIR-002

**References**: EPIC_OUTPUT.md, MDAP STAGE1–STAGE5 EPIC-001 (approved baseline); PRD_ADDENDUM_FR023_AI_DIRECTIVE_EXTRACTION.md  
**Status**: PENDING MDAP MIA-001 APPROVAL  
**Amendment Date**: March 27, 2026  
**Change Type**: Module Addition (visible scope change to approved EPIC — three new modules)  
**Impact Level**: HIGH (LLM external dependency; new reconciliation logic; critical-path extension)

---

## 0. Governance Baseline

### Immutable Reference
- **EPIC Baseline**: EPIC-001 with 7 approved modules (MODULE-001-01 through MODULE-001-07)
- **FR Range**: FR-001 through FR-021 (immutable baseline); FR-023 added via PRD addendum
- **Scope Ceiling**: School Material Price Finder is a Brazil-focused tool for parents, school administrators, and budget-conscious shoppers who need to buy complete school lists from mixed document formats while controlling total spend.

### Governance Rules Applied
- ✓ **GC-2**: Acceptance criteria are binary/verifiable
- ✓ **GC-8**: FR/module identifiers remain canonical (no renumbering)
- ✓ **Forward-blocking**: Dependencies remain forward-only; no reverse blocking
- ✓ **No invented thresholds**: All unresolved thresholds are explicitly tagged `[THRESHOLD NEEDED]`

---

## 1. Change Summary

**Original EPIC-001**: 7 modules, 9 user stories, 9 FRs (FR-001..FR-009)

**Amended EPIC-001**: 10 modules, 10 user stories, 10 FRs (adds MODULE-001-08, MODULE-001-09, MODULE-001-10, US-015, FR-023)

### 1.5 New User Story

**US-015**: As a system, I extract school directive annotations reliably from diverse PDF formats using deterministic parsing with LLM fallback, so that school exclusivity rules are honored without excessive manual review.

**Maps To**: FR-023  
**Covered By**: MODULE-001-08 (deterministic leg), MODULE-001-09 (LLM fallback leg), MODULE-001-10 (reconciliation leg)  
**Status**: NEW

---

## 2. New Modules Addition

---

### MODULE-001-08: Deterministic Directive Parser

**User Story**: US-015 (partial — deterministic leg)
> As the system, I parse directive notation from PDF extraction output using rule-based logic, so that school_exclusive, required_sellers, and preferred_sellers fields are populated with deterministic confidence scores before any LLM fallback is considered.

**Epic**: EPIC-001  
**FRs Covered**: FR-023 (deterministic leg), FR-001 (extension — directive fields added to extraction output)  
**Risk Level**: MEDIUM (rule-based only; no external dependency; notation rules may need maintenance as new formats emerge)  
**Expert Domains**: [Pattern Matching, Confidence Scoring, Data Normalization]

**Responsibility Chain**:
1. Accept MODULE-001-01 extraction output (item fields + document notation rules dict)
2. Apply notation rules to each item's text for directive marker detection
3. Assign deterministic_directive_confidence per item
4. Emit deterministic directive fields (partial contract): school_exclusive, required_sellers, preferred_sellers, directive_confidence, decision_source=deterministic
5. If directive_confidence ≥ [THRESHOLD-LLM-01], mark item as directive_resolved=true — no LLM needed
6. If directive_confidence < [THRESHOLD-LLM-01], mark item as directive_resolved=false — forward to MODULE-001-09

**Public Interface**:
```
INPUT:
  - extracted_item: dict (from MODULE-001-01)
  - document_notation_rules: dict (from MODULE-001-01 pre-pass)

OUTPUT:
  - item_with_deterministic_directive: dict {
      school_exclusive: bool,
      required_sellers: list[str],
      preferred_sellers: list[str],
      directive_confidence: float [0.00–1.00],
      decision_source: "deterministic",
      directive_resolved: bool,
      directive_extraction_timestamp: datetime,
      requires_human_review: None,
      llm_rationale: None,
      llm_model_id: None
    }

SIDE EFFECTS:
  - None (pure transform; audit written by MODULE-004-02 on finalization)
```

**Blocked By**: MODULE-001-01 (PDF Ingestion & Field Extraction)  
**Blocks**: MODULE-001-09 (LLM Fallback Gateway — for unresolved items only), MODULE-001-10 (Directive Reconciliation Resolver)

---

### MODULE-001-09: LLM Fallback Gateway

**User Story**: US-015 (partial — LLM fallback leg)
> As the system, I invoke the configured LLM provider for items where deterministic directive confidence is below threshold, so that ambiguous notation cases are handled without defaulting all of them to manual review.

**Epic**: EPIC-001  
**FRs Covered**: FR-023 (LLM fallback leg)  
**Risk Level**: HIGH (external LLM dependency; latency; per-call cost; non-determinism; provider availability)  
**Expert Domains**: [LLM Integration, Retry Logic, Cost/Latency Budgeting, Prompt Engineering]

**Responsibility Chain**:
1. Accept items from MODULE-001-08 where directive_resolved=false
2. Construct LLM prompt from item context (name, category, raw extracted text, document notation rules)
3. Invoke configured LLM provider with retry policy (max attempts: [THRESHOLD-LLM-03 derived])
4. Parse LLM response: extract directive fields, llm_confidence, llm_rationale, llm_model_id
5. Return structured LLM output to MODULE-001-10 (reconciliation)
6. On timeout/error after retries: emit error_payload with requires_human_review=true

**Shadow Mode Behavior**:
- While shadow mode is active, MODULE-001-09 invokes LLM and records all outputs
- Shadow outputs are logged to audit trail with shadow_mode=true flag
- Shadow outputs are NOT written to canonical directive fields in live records
- Shadow mode exits only after THRESHOLD-LLM-04 precision is achieved over THRESHOLD-LLM-05 samples (human gate)

**Public Interface**:
```
INPUT:
  - item: dict with directive_resolved=false (from MODULE-001-08)
  - llm_config: { provider, model_id, max_latency_ms, max_retries }

OUTPUT (success):
  - llm_result: dict {
      school_exclusive: bool,
      required_sellers: list[str],
      preferred_sellers: list[str],
      llm_confidence: float [0.00–1.00],
      llm_rationale: string,
      llm_model_id: string,
      call_timestamp: datetime,
      shadow_mode: bool
    }

OUTPUT (failure):
  - error_payload: dict {
      requires_human_review: true,
      error_reason: string,
      attempt_count: int,
      last_error_timestamp: datetime
    }

SIDE EFFECTS:
  - LLM call logged to audit trail (always, including errors)
```

**Blocked By**: MODULE-001-08 (Deterministic Directive Parser — only receives items with directive_resolved=false)  
**Blocks**: MODULE-001-10 (Directive Reconciliation Resolver)

**[THRESHOLD NEEDED]**:
- THRESHOLD-LLM-01: trigger confidence floor (consumed by MODULE-001-08 to flag items)
- THRESHOLD-LLM-03: maximum LLM call latency before timeout
- THRESHOLD-LLM-04: shadow mode precision floor for live-promotion gate
- THRESHOLD-LLM-05: shadow mode minimum sample size for gate

---

### MODULE-001-10: Directive Reconciliation Resolver

**User Story**: US-015 (reconciliation leg)
> As the system, I merge deterministic and LLM directive outputs using an explicit precedence policy, set the final decision_source, and write the full decision record to the audit trail, so that the directive contract delivered to MODULE-003-05 is traceable and correct.

**Epic**: EPIC-001  
**FRs Covered**: FR-023 (reconciliation leg)  
**Risk Level**: HIGH (conflict handling; precedence policy correctness; audit integrity)  
**Expert Domains**: [Business Rule Logic, Conflict Resolution, Audit Logging]

**Responsibility Chain**:
1. Accept deterministic output from MODULE-001-08 (always present)
2. Accept LLM output from MODULE-001-09 (present only if invoked; may be error_payload)
3. Apply reconciliation precedence policy:
   - **RULE 1**: If deterministic_directive_confidence ≥ THRESHOLD-LLM-01 → use deterministic, decision_source=deterministic
   - **RULE 2**: If LLM invoked and llm_confidence ≥ THRESHOLD-LLM-02 → use LLM result, decision_source=llm_fallback
   - **RULE 3**: If both below thresholds → requires_human_review=true, decision_source=none
  - **RULE 4**: If requires_human_review=true, final item state is review_required even when base item confidence would otherwise auto-accept under FR-002
4. Assemble final directive contract per FR-023 Section 4 schema
5. Emit final item to MODULE-001-07 gate (or downstream eligibility check)
6. Write reconciliation decision record to audit trail (MODULE-004-02)

**Public Interface**:
```
INPUT:
  - deterministic_output: dict (from MODULE-001-08)
  - llm_output: dict | error_payload | None (from MODULE-001-09 if invoked)

OUTPUT:
  - resolved_item: dict {
      school_exclusive: bool,
      required_sellers: list[str],
      preferred_sellers: list[str],
      directive_confidence: float,
      decision_source: "deterministic" | "llm_fallback" | "human_override",
      requires_human_review: bool,
      llm_rationale: string | None,
      llm_model_id: string | None,
      directive_extraction_timestamp: datetime
    }

SIDE EFFECTS:
  - Write reconciliation_decision record to audit trail (MODULE-004-02)
  - If requires_human_review=true: add item to review queue
```

**[THRESHOLD NEEDED]**:
- THRESHOLD-LLM-02: LLM output confidence floor for auto-acceptance; consumed by reconciliation RULE 2

**Blocked By**: MODULE-001-08 (Deterministic Directive Parser), MODULE-001-09 (LLM Fallback Gateway — for items that required LLM), THRESHOLD-LLM-02 (unresolved auto-accept floor)  
**Blocks**: MODULE-001-07 (Missing ISBN Search Gate — directive contract must be resolved before ISBN gate proceeds to MODULE-003-05)

---

## 3. Updated Module List for EPIC-001

| Module ID | Name | FR(s) | Risk | Status |
|-----------|------|-------|------|--------|
| MODULE-001-01 | PDF Ingestion & Field Extraction | FR-001 | HIGH | Approved (extended — emits notation_rules dict) |
| MODULE-001-02 | Confidence Gating Router | FR-002 | MEDIUM | Approved (extended — separate directive gating lane) |
| MODULE-001-03 | Quantity/Unit Normalizer | FR-003 | LOW | Approved (unchanged) |
| MODULE-001-04 | Duplicate Resolution Coordinator | FR-004 | HIGH | Approved (unchanged) |
| MODULE-001-05 | Category Rules Eligibility Validator | FR-005, FR-006, FR-007 | HIGH | Approved (unchanged) |
| MODULE-001-06 | ISBN Normalization Validation | FR-008 | LOW | Approved (unchanged) |
| MODULE-001-07 | Missing ISBN Search Gate | FR-009 | MEDIUM | Approved (extended — receives enriched item with directive contract) |
| **MODULE-001-08** | **Deterministic Directive Parser** | **FR-023, FR-001 (extension)** | **MEDIUM** | **NEW (MDAP MIA-001)** |
| **MODULE-001-09** | **LLM Fallback Gateway** | **FR-023** | **HIGH** | **NEW (MDAP MIA-001)** |
| **MODULE-001-10** | **Directive Reconciliation Resolver** | **FR-023** | **HIGH** | **NEW (MDAP MIA-001)** |

**Total Modules**: 10 (was 7)  
**Total FRs Covered**: 10 (was 9; adds FR-023)

---

## 3.5 Implementation Staging & Threshold Blockers

### Stage A: Deterministic Directive Parser (MODULE-001-08)
- **Deliverable**: Deterministic parser logic; decision_source="deterministic"
- **Threshold Blockers**: None
- **Gate**: Deterministic routing and contract fields validated by tests

### Stage B: LLM Fallback Gateway (MODULE-001-09)
- **Deliverable**: LLM invocation, retry/timeout policy, shadow-mode logging
- **Threshold Blockers**:
  - ☐ THRESHOLD-LLM-01 (trigger confidence floor)
  - ☐ THRESHOLD-LLM-03 (max latency timeout)
- **Gate**: Cannot activate Stage B behavior until both thresholds are resolved

### Stage C: Directive Reconciliation Resolver (MODULE-001-10)
- **Deliverable**: Reconciliation RULES 1–4 and review_required routing
- **Threshold Blockers**:
  - ☐ THRESHOLD-LLM-02 (LLM auto-accept floor)
- **Gate**: Cannot activate Stage C behavior until THRESHOLD-LLM-02 is resolved

### Stage D: Shadow Mode Exit (promotion gate)
- **Deliverable**: Precision measurement and live-mode promotion decision
- **Threshold Blockers**:
  - ☐ THRESHOLD-LLM-04 (precision floor)
  - ☐ THRESHOLD-LLM-05 (minimum sample size)
- **Gate**: Shadow mode exit requires both thresholds resolved plus human gate approval

---

## 4. Updated Critical Path

**Original**:
```
MODULE-001-01 → MODULE-001-02 → MODULE-001-03 → MODULE-001-04
     → MODULE-001-05 → MODULE-001-06 → MODULE-001-07
```

**Amended**:
```
MODULE-001-01 (PDF Ingestion & Field Extraction)
    ↓
MODULE-001-08 (Deterministic Directive Parser)      ← NEW
  ↓
[DECISION: directive_resolved=true?]
  ├─ YES → skip LLM and forward deterministic output
  └─ NO  → MODULE-001-09 (LLM Fallback Gateway)   ← NEW (conditional branch)
       ↓
MODULE-001-10 (Directive Reconciliation Resolver)   ← NEW
    ↓
MODULE-001-02 (Confidence Gating Router) ──── (existing items pipeline unchanged)
MODULE-001-03 (Quantity/Unit Normalizer)
MODULE-001-04 (Duplicate Resolution Coordinator)
MODULE-001-05 (Category Rules Eligibility Validator)
MODULE-001-06 (ISBN Normalization Validation)
    ↓
MODULE-001-07 (Missing ISBN Search Gate — now receives item with directive contract)
    ↓
MODULE-003-05 (School Exclusivity Resolver — EPIC-003)
```

**Path Length**: +3 modules added; MODULE-001-09 on conditional branch (only activates for low-confidence directive items)

---

## 5. Dependencies Summary

### Intra-EPIC-001 Dependencies

| From | To | Type |
|------|----|------|
| MODULE-001-01 | MODULE-001-08 | Sequential (notation_rules dict) |
| MODULE-001-08 | MODULE-001-09 | Conditional sequential (only unresolved items) |
| MODULE-001-08 | MODULE-001-10 | Sequential (deterministic output always flows here) |
| MODULE-001-09 | MODULE-001-10 | Sequential (LLM output flows here when invoked) |
| MODULE-001-10 | MODULE-001-07 | Sequential (resolved directive contract required before ISBN gate) |

### Cross-Epic Dependencies

| Consuming Module | From Epic | Depends On | Type |
|------------------|-----------|------------|------|
| MODULE-003-05 | EPIC-003 | MODULE-001-10 | Forward blocking (directive contract required) |
| MODULE-001-10 | EPIC-001 | MODULE-004-02 | Side-effect (audit trail write — not blocking) |

**Direction Check**: ✓ Valid forward-blocking (no reverse dependencies introduced)

### Cross-Epic Dependency: MODULE-004-02 Audit Schema Contract

**Dependency**: MODULE-001-10 depends on MODULE-004-02 accepting directive extraction reconciliation records.

**Required logical schema**:
```
reconciliation_audit_record = {
  item_id: str,
  decision_source: "deterministic" | "llm_fallback" | "human_override",
  deterministic_confidence: float,
  llm_confidence: float | None,
  requires_human_review: bool,
  shadow_mode: bool,
  timestamp: datetime,
  reconciliation_rationale: str
}
```

**Coordination required**: MIA-001 (MODULE-001-10) and EPIC-004/MODULE-004-02 schema evolution must stay aligned before implementation.

### Circular Dependency Check
- ✓ NO CYCLES — new modules extend the existing linear ingestion path; LLM branch is conditional and forward-only

---

## 6. Extensions to Existing Approved Modules

### MODULE-001-01 (PDF Ingestion & Field Extraction) — EXTENDED
- Addition: Emit `document_notation_rules` dict alongside extracted items
- Change: notation rule pre-pass (scan footnotes, legends, metadata for exclusivity markers) added as step 0
- No existing AC removed or weakened

### MODULE-001-01 Extension Detail

**Original Output Contract**:
```
extracted_items: list[dict]
```

**Extended Output Contract**:
```
extracted_items: list[dict]
document_notation_rules: dict   # NEW marker → seller mapping from pre-pass step 0
```

**Implementation Note**: This extension adds metadata output only; it does not remove or weaken prior MODULE-001-01 acceptance criteria.

### MODULE-001-02 (Confidence Gating Router) — EXTENDED
- Addition: Second gating lane for directive_confidence field (uses THRESHOLD-LLM-01/LLM-02, NOT the existing 0.90/0.70 thresholds)
- Existing item-level confidence gating unchanged
- Directive gate is additive; if directive resolution fails, final state is `review_required` even when base item confidence would auto-accept

### MODULE-001-07 (Missing ISBN Search Gate) — NOTE
- Receives enriched item with directive contract fields appended
- No existing logic changed; new fields are passthrough

---

## 7. Contract Extensions

### Extended Item Schema (additions to established contract)

```
# New fields appended to canonical item by MODULE-001-10 output:
directive_confidence: float           # winning confidence score
decision_source: enum                 # deterministic | llm_fallback | human_override
requires_human_review: bool           # true when no path produced sufficient confidence
llm_rationale: string | None          # non-null only when llm_fallback
llm_model_id: string | None           # non-null only when LLM was invoked
directive_extraction_timestamp: datetime
```

---

## 8. Risk Register

| Module | Risk | Severity | Mitigation |
|--------|------|----------|------------|
| MODULE-001-09 | LLM provider unavailable | HIGH | Retry policy + graceful fallback to requires_human_review=true; never halt pipeline |
| MODULE-001-09 | LLM latency exceeds SLA (NFR-001 — 10 min) | HIGH | THRESHOLD-LLM-03 timeout; batch/async invocation only; shadow mode de-risks live impact |
| MODULE-001-09 | LLM non-determinism (same item → different result) | MEDIUM | Reconciliation policy uses deterministic output when available; LLM acts as fallback only |
| MODULE-001-10 | Reconciliation precedence policy bug silently accepts wrong result | HIGH | Unit tests for all three reconciliation RULES; audit trail makes every decision inspectable |
| MODULE-001-08 | Notation rule set incomplete (new PDF formats) | MEDIUM | Notation rules are config-driven and maintainable without code changes; failing items fall to LLM |
| MODULE-001-08/10 | Directive contract schema evolution needed (new fields discovered post-launch) | MEDIUM | Use additive schema migration strategy with optional fields and versioned contract handling |

---

## 9. Pre-Gate Validation Checklist and CIR Sign-Off

### 9.1 Validation Summary

| Metric | Value |
|---|---|
| Governance checks passed | 9/10 |
| Governance checks pending | 1/10 (human gate decision) |
| New modules with complete interface + risk metadata | 3/3 |
| Unresolved thresholds explicitly tracked | 5/5 |

### 9.2 Rule Validation (2A–2J)

| Rule | Status | Evidence |
|------|--------|----------|
| 2A: Scope Creep | ✓ PASS | All new modules map to FR-023 scope only |
| 2B: Traceability | ✓ PASS | US-015 → FR-023 → MODULE-001-08/09/10 |
| 2C: Risk Flagging | ✓ PASS | MODULE-001-09 and MODULE-001-10 flagged HIGH with mitigations |
| 2D: Cross-Epic Direction | ✓ PASS | Forward blocking only; no reverse dependency |
| 2E: Bounded Scope | ✓ PASS | In-scope/out-of-scope defined in PRD addendum |
| 2F: Handoff Clarity | ✓ PASS | Interfaces, dependencies, and owners explicitly listed |
| 2G: AC Binary | ✓ PASS | RULE outcomes and gates are deterministic pass/fail |
| 2H: Constraint Carry | ✓ PASS | THRESHOLD-LLM-01..05 mapped to stages |
| 2I: Coverage | ✓ PASS | US-015 fully covered by three-module decomposition |
| 2J: Human Gate Control | ⚠ PENDING | Awaiting formal sign-off decisions below |

### 9.3 CIR Sign-Off Decision

**Status**: ☐ APPROVED | ☐ CONDITIONAL | ☐ REWORK REQUIRED

**Approver Sign-Off**:

| Role | Name | Decision | Date | Notes |
|------|------|----------|------|-------|
| EPIC-001 Owner | | ☐ APPROVE / ☐ REWORK | | |
| Architecture Lead | | ☐ APPROVE / ☐ REWORK | | LLM integration and SLA/cost review |
| LLM Integration Lead | | ☐ APPROVE / ☐ REWORK | | Prompting, model, retry and shadow-mode plan |

**Gate Verdict**: ☐ PASSED (all approvals obtained) | ☐ FAILED (rework required)

---

## HANDOFF NOTE

This CIR SHALL be consumed by:
- MDAP MIA-001 (module impact assessment for MODULE-001-08, MODULE-001-09, MODULE-001-10)
- Architecture phase: LLM gateway integration, provider selection, prompt versioning

All [THRESHOLD NEEDED] items (THRESHOLD-LLM-01 through THRESHOLD-LLM-05) MUST be resolved by stakeholder sign-off before Stage B implementation begins (per FR-023 Section 7 staging gate).
