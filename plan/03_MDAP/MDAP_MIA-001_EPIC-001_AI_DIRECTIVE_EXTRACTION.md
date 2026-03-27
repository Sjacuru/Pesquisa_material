# MDAP Module Impact Assessment — MIA-001
## EPIC-001: Addition of MODULE-001-08, MODULE-001-09, MODULE-001-10
## AI-Assisted Directive Extraction Fallback (FR-023)

**Status**: PENDING HUMAN GATE APPROVAL  
**Date**: March 27, 2026  
**Change Type**: Module Addition (3 new modules; visible scope extension to approved EPIC-001)  
**Impact Level**: HIGH (LLM external dependency; reconciliation logic; critical-path extension; threshold dependency)  
**References**:
- EPIC_OUTPUT.md (approved EPIC-001 baseline)
- MDAP_STAGE1_EPIC-001_APPROVED.md through MDAP_STAGE5_EPIC-001_APPROVED.md (all approved)
- EPIC_AMENDMENT_001_CIR002_AI_DIRECTIVE_EXTRACTION.md (PENDING)
- PRD_ADDENDUM_FR023_AI_DIRECTIVE_EXTRACTION.md (DRAFT)
- MDAP_CIR-001_EPIC-003_MODULE-003-05.md (reference pattern)

---

## 1. Baseline Reference

**Approved EPIC-001 Artifacts**:
- MDAP_STAGE1_EPIC-001_APPROVED.md (7 modules identified)
- MDAP_STAGE2_EPIC-001_APPROVED.md (dependency map)
- MDAP_STAGE3_EPIC-001_APPROVED.md (module details & AC)
- MDAP_STAGE4_EPIC-001_APPROVED.md (scope & risk review)
- MDAP_STAGE5_EPIC-001_APPROVED.md (advancement sign-off)
- All approved and in ARCHITECTURE phase

**Change**: Add 3 modules (MODULE-001-08, MODULE-001-09, MODULE-001-10); extend 3 existing modules (MODULE-001-01, MODULE-001-02, MODULE-001-07)

---

## 2. Stage 1: Module Identification

### Module: MODULE-001-08 — Deterministic Directive Parser

**Responsibility**: Apply notation rules from MODULE-001-01 to each extracted item to produce directive fields with deterministic_confidence. Route items above THRESHOLD-LLM-01 as resolved; route items below threshold to MODULE-001-09.

**User Stories Covered**: US-015 (deterministic leg)  
**FRs Covered**: FR-023, FR-001 (extension)  
**Coverage**: ✓ 100% (deterministic extraction leg of FR-023)

---

### Module: MODULE-001-09 — LLM Fallback Gateway

**Responsibility**: Invoke configured LLM provider for items where deterministic directive confidence is below THRESHOLD-LLM-01. Construct prompt from item context; parse and return structured LLM output with confidence, rationale, and model ID. Handle shadow mode, timeouts, and errors.

**User Stories Covered**: US-015 (LLM fallback leg)  
**FRs Covered**: FR-023  
**Coverage**: ✓ 100% (LLM fallback leg of FR-023)

---

### Module: MODULE-001-10 — Directive Reconciliation Resolver

**Responsibility**: Merge deterministic and LLM outputs using reconciliation precedence policy. Set final decision_source, requires_human_review, and directive_confidence. Write reconciliation decision to audit trail. Emit finalized directive contract to downstream modules.

**User Stories Covered**: US-015 (reconciliation leg)  
**FRs Covered**: FR-023  
**Coverage**: ✓ 100% (reconciliation leg of FR-023)

---

## 3. Stage 2: Dependency Mapping

### Intra-EPIC-001 Dependencies

```
MODULE-001-01 (PDF Ingestion & Field Extraction)
    ↓ extracted_item + document_notation_rules
MODULE-001-08 (Deterministic Directive Parser)
    ↓ deterministic_output (always)
    ↘ unresolved items only
      MODULE-001-09 (LLM Fallback Gateway)   [conditional branch]
          ↓ llm_output (when invoked)
MODULE-001-10 (Directive Reconciliation Resolver)
    ↓
MODULE-001-07 (Missing ISBN Search Gate)
```

### Cross-Epic Dependencies

| Module | Upstream | Epic | Dependency |
|--------|----------|------|------------|
| MODULE-001-10 | MODULE-004-02 | EPIC-004 | Side-effect: audit trail write (non-blocking; fire-and-forget within transaction) |
| MODULE-003-05 | MODULE-001-10 | EPIC-001 | Consumes directive contract; forward blocking |

**Audit Schema Contract (Cross-Epic Coordination Required)**:
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

Coordination is required between MIA-001 (MODULE-001-10) and EPIC-004/MODULE-004-02 schema evolution before implementation.

**Direction Check**: ✓ All forward-blocking (valid; no reverse dependencies)

### Circular Dependency Check
- ✓ NO CYCLES  
    Linear path with conditional branch: 001-01 → 001-08 → 001-10 (always), with optional 001-09 → 001-10 enrichment when directive_resolved=false

### Critical Path Impact

| | Before CIR-002 | After CIR-002 |
|---|---|---|
| EPIC-001 critical path | 001-01 → ...→ 001-07 | 001-01 → 001-08 → 001-10 → ...→ 001-07 (with conditional 001-09 branch before 001-10) |
| Path length change | 7 modules | 10 modules (+3) |
| Conditional branch | None | MODULE-001-09 (invoked only for low-confidence items) |

---

## 4. Stage 3: Module Details & Acceptance Criteria

### MODULE-001-08: Deterministic Directive Parser

**Domain**: Pattern Matching, Confidence Scoring  
**Type**: Domain Logic (Pure Transform)  
**Risk Level**: MEDIUM  
**Expert Domains**: [Pattern Matching, Confidence Scoring, Data Normalization]

**Responsibility Chain**:
1. Accept MODULE-001-01 output (extracted_item + document_notation_rules dict)
2. Scan item text fields for directive markers using notation_rules
3. Calculate deterministic_directive_confidence per item
4. Emit directive fields: school_exclusive, required_sellers, preferred_sellers, directive_confidence, decision_source=deterministic
5. Emit placeholder fields for reconciliation completion: requires_human_review=None, llm_rationale=None, llm_model_id=None
6. Set directive_resolved=true if confidence ≥ THRESHOLD-LLM-01; false otherwise
7. Fallback behavior: if notation_rules dict is missing or malformed, set school_exclusive=false, directive_confidence=0.00, directive_resolved=false (no hard failure)
8. Pass output to MODULE-001-10 (always); copy of unresolved items to MODULE-001-09

**Acceptance Criteria**:

| ID | Criterion | Pass/Fail |
|----|-----------|-----------|
| AC1 | Item with matching notation rule → school_exclusive=true, required_sellers populated, directive_confidence=high | Verifiable |
| AC2 | Item with no notation marker → school_exclusive=false, required_sellers=[], directive_confidence assigned | Verifiable |
| AC3 | Item with ambiguous partial notation → directive_confidence < THRESHOLD-LLM-01, directive_resolved=false | Verifiable |
| AC4 | All outputs include decision_source="deterministic" | Verifiable |
| AC5 | directive_extraction_timestamp is set in UTC at parse time | Verifiable |
| AC6 | Same item text + same notation rules + same THRESHOLD-LLM-01 value → same directive decision fields (timestamp may differ) | Verifiable |
| AC7 | Missing notation_rules dict → school_exclusive=false, directive_confidence=0.00, directive_resolved=false | Verifiable |
| AC8 | Output includes reconciliation placeholder fields (requires_human_review=None, llm_rationale=None, llm_model_id=None); MODULE-001-10 populates final values | Verifiable |

**Constraints & Assumptions**:
- Notation rules are config-driven (loaded from MODULE-001-01 pre-pass output)
- Seller name normalization handled by MODULE-002-04; this module outputs raw seller strings
- Does not invoke any external service; latency is negligible

---

### MODULE-001-09: LLM Fallback Gateway

**Domain**: LLM Integration, Retry Logic, Cost/Latency Budgeting  
**Type**: External Integration (Gateway)  
**Risk Level**: HIGH  
**Expert Domains**: [LLM Integration, Retry Logic, Cost/Latency Budgeting, Prompt Engineering]

**Responsibility Chain**:
1. Accept items with directive_resolved=false from MODULE-001-08
2. Construct prompt: item context + document notation rules (no PII; text content only)
3. Invoke LLM provider with timeout = THRESHOLD-LLM-03, max retries configured
4. On success: parse response into structured output (school_exclusive, required_sellers, preferred_sellers, llm_confidence, llm_rationale, llm_model_id)
5. On timeout/error: emit error_payload with requires_human_review=true
6. Log all calls (success and failure) to audit trail with shadow_mode flag
7. If shadow_mode=true: do NOT write result to canonical fields; log only

**Acceptance Criteria**:

| ID | Criterion | Pass/Fail |
|----|-----------|-----------|
| AC1 | Item with directive_resolved=false → LLM is invoked exactly once (with retries if needed) | Verifiable |
| AC2 | Item with directive_resolved=true → LLM is NOT invoked | Verifiable |
| AC3 | LLM success → output includes school_exclusive, required_sellers, preferred_sellers, llm_confidence [0.00–1.00], llm_rationale, llm_model_id, call_timestamp | Verifiable |
| AC4 | LLM timeout or error after all retries → error_payload with requires_human_review=true, attempt_count, last_error_timestamp | Verifiable |
| AC5 | All LLM calls (success and failure) written to audit trail before returning | Verifiable |
| AC6 | shadow_mode=true → LLM output NOT written to canonical item fields; logged only | Verifiable |
| AC7 | shadow_mode=false → LLM output forwarded to MODULE-001-10 for reconciliation | Verifiable |
| AC8 | LLM call failure does NOT halt the pipeline; item proceeds with error_payload | Verifiable |
| AC9 | Prompt contains no personal data; only item text, category, notation context | Verifiable |

**Constraints & Assumptions**:
- LLM provider, model, and API key are external configuration (not hardcoded)
- THRESHOLD-LLM-01, THRESHOLD-LLM-03 must be resolved before this module is activated
- Shadow mode flag is controlled by deployment configuration
- THRESHOLD-LLM-04 and THRESHOLD-LLM-05 control shadow mode exit gate (human sign-off required)

---

### MODULE-001-10: Directive Reconciliation Resolver

**Domain**: Business Rule Logic, Conflict Resolution, Audit Logging  
**Type**: Domain Logic  
**Risk Level**: HIGH  
**Expert Domains**: [Business Rule Logic, Conflict Resolution, Audit Logging]

**Responsibility Chain**:
1. Accept deterministic output from MODULE-001-08 (always present)
2. Accept LLM output from MODULE-001-09 (present only if invoked; may be error_payload)
3. Apply reconciliation policy:
   - RULE 1: deterministic_confidence ≥ THRESHOLD-LLM-01 → use deterministic, decision_source=deterministic
   - RULE 2: LLM invoked + llm_confidence ≥ THRESHOLD-LLM-02 → use LLM, decision_source=llm_fallback
    - RULE 3: deterministic below threshold AND (LLM below threshold OR LLM not invoked OR error_payload received) → requires_human_review=true, decision_source=none
    - RULE 4: if requires_human_review=true, item state is review_required even if base item confidence would auto-accept under FR-002
4. Assemble complete directive contract per FR-023 Section 4 schema
5. Write reconciliation_decision record to audit trail
6. If requires_human_review=true: add to review queue
7. Emit resolved_item to MODULE-001-07

**Acceptance Criteria**:

| ID | Criterion | Pass/Fail |
|----|-----------|-----------|
| AC1 | RULE 1 fires correctly: deterministic ≥ THRESHOLD-LLM-01 → decision_source=deterministic, LLM result ignored | Verifiable |
| AC2 | RULE 2 fires correctly: LLM ≥ THRESHOLD-LLM-02 (deterministic not sufficient) → decision_source=llm_fallback | Verifiable |
| AC3 | RULE 3 fires correctly: unresolved/failed LLM path (including error_payload) → requires_human_review=true | Verifiable |
| AC4 | Reconciliation record written to audit trail for every item (all three RULE outcomes) | Verifiable |
| AC5 | requires_human_review=true items added to review queue | Verifiable |
| AC6 | human_override applied via MODULE-004-01 → decision_source=human_override; prior results preserved in audit trail | Verifiable |
| AC7 | RULE 2 result includes llm_rationale and llm_model_id in output contract | Verifiable |
| AC8 | Same deterministic + LLM inputs + same threshold values → same reconciliation decision (timestamp may differ) | Verifiable |
| AC9 | Output always includes complete directive contract schema regardless of which RULE applied | Verifiable |
| AC10 | requires_human_review=true forces review_required state even when base item confidence is auto-accept eligible | Verifiable |
| AC11 | When MODULE-001-09 returns error_payload, MODULE-001-10 sets decision_source=none, requires_human_review=true, and routes item to review queue | Verifiable |

**Constraints & Assumptions**:
- THRESHOLD-LLM-02 must be resolved before this module is activated
- Audit trail write is handled by MODULE-004-02 (versioned_audit_trail_logger)
- Human override pathway is owned by MODULE-004-01 (user_edit_handler); this module only reads overrides
- Audit consistency guarantee: reconciliation must not complete with silent audit loss; successful audit write acknowledgment or durable retry registration is required before completion state is finalized

---

## 5. Stage 4: Scope & Risk Review

### Scope Boundary

**In Scope for all three modules**:
- ✓ Directive field extraction and confidence scoring (MODULE-001-08)
- ✓ LLM call lifecycle: prompt, invoke, parse, retry, timeout, error (MODULE-001-09)
- ✓ Shadow mode logging without affecting canonical records (MODULE-001-09)
- ✓ Reconciliation policy (4 RULES) and final directive contract assembly (MODULE-001-10)
- ✓ Audit trail write for all decisions (MODULE-001-10 via MODULE-004-02)
- ✓ Review queue routing for unresolvable items (MODULE-001-10)

**Out of Scope**:
- ❌ LLM provider selection, model fine-tuning, prompt management tooling (Architecture concern)
- ❌ Human review UI for directive fields (existing review queue is sufficient for MVP)
- ❌ LLM use for non-directive fields (item name, quantity, ISBN — FR-001 is unchanged)
- ❌ Real-time LLM invocation during user-facing requests (batch/async only)
- ❌ Seller name normalization (MODULE-002-04 owns this)

**Scope Verdict**: ✓ PASS — Clear boundary; no mission creep; all three modules have distinct, non-overlapping responsibilities

---

### Risk Assessment

**MODULE-001-08: MEDIUM**
- Notation rule incompleteness is the primary risk; mitigated by config-driven rules (no code change needed for new formats) and fallback to LLM
- No external dependency; deterministic; latency negligible

**MODULE-001-09: HIGH**
- LLM provider outage → treated as error_payload, item routed to review queue, pipeline does not halt
- LLM latency budget collision with NFR-001 (10 min SLA): mitigated by async/batch mode; THRESHOLD-LLM-03 timeout enforced
- LLM non-determinism: contained by reconciliation module — LLM acts as fallback only; deterministic output always present
- Data leakage: mitigated by AC9 requiring no PII in prompt (item text + category only)
- Shadow mode de-risks all live impact until precision gate clears

**MODULE-001-10: HIGH**
- Precedence policy bug silently accepting wrong result: mitigated by unit tests for all three RULES + audit trail on every decision
- Missing THRESHOLD values: blocked gates prevent activation until stakeholder resolves THRESHOLD-LLM-01 and THRESHOLD-LLM-02

---

## 6. Stage 5: Advancement Sign-Off

### Implementation Staging Plan

| Stage | Deliverable | Gate Condition |
|-------|-------------|----------------|
| A | MODULE-001-08 live: deterministic parser only; all items get directive contract with decision_source=deterministic | Implementation can start immediately after CIR-002 approval; production activation requires deterministic module tests passing and Step 1 baseline integration tests passing; no THRESHOLD values required |
| B | MODULE-001-09 live in shadow mode: LLM invoked for low-confidence items; outputs logged only | THRESHOLD-LLM-01 and THRESHOLD-LLM-03 resolved; LLM provider/model/API contract finalized by Architecture; prompt template + response parsing contract finalized |
| C | MODULE-001-10 live: reconciliation active; requires_human_review routing live | THRESHOLD-LLM-02 resolved; shadow mode running |
| D | Shadow mode exit: LLM results promoted to canonical | Precision ≥ THRESHOLD-LLM-04 in ≥ THRESHOLD-LLM-05 samples; **HUMAN GATE SIGN-OFF REQUIRED** |

### Human Gate Checklist

- [ ] THRESHOLD-LLM-01 resolved (stakeholder decision required)
- [ ] THRESHOLD-LLM-02 resolved (stakeholder decision required)
- [ ] THRESHOLD-LLM-03 resolved (stakeholder decision required)
- [ ] THRESHOLD-LLM-04 resolved (stakeholder decision required)
- [ ] THRESHOLD-LLM-05 resolved (stakeholder decision required)
- [ ] OQ-FR023-02 resolved at PRD sign-off (llm_rationale persistence model decided before MODULE-001-09/001-10 detailed design)
- [ ] MODULE-004-02 schema reviewed/extended to accept `reconciliation_audit_record` contract (coordination with EPIC-004 team)
- [ ] LLM provider/model selected (Architecture phase output — deferred)
- [ ] LLM API contract finalized (request/response schema and error model)
- [ ] Prompt template and response parsing contract finalized
- [ ] Shadow mode sample collected and precision measured against THRESHOLD-LLM-04
- [ ] Stage D live-routing promotion approved by Product Owner + Architecture Lead

### 6.5 Shadow Mode Precision Measurement Criteria

**Metric Definition Owner**: Product Owner + Data/QA Lead + LLM Integration Lead

- Ground truth source: human-reviewed directive annotations for shadow-mode sample items
- Candidate metric baseline: field-level agreement rate for directive fields (`school_exclusive`, `required_sellers`, `preferred_sellers`)
- Target threshold: THRESHOLD-LLM-04 (value unresolved)
- Sample minimum: THRESHOLD-LLM-05 (value unresolved)
- Final metric formula and scoring rubric are required before Stage D gate decision

### 6.6 Human Gate Sign-Off Block

| Role | Name | Decision | Date | Notes |
|------|------|----------|------|-------|
| EPIC-001 Owner | | ☐ APPROVE / ☐ REWORK | | |
| LLM Integration Lead | | ☐ APPROVE / ☐ REWORK | | HIGH-risk module (MODULE-001-09) expert review |
| Risk/Mitigation Lead | | ☐ APPROVE / ☐ REWORK | | Threshold roadmap and shadow-mode risk model |
| Data/QA Lead | | ☐ APPROVE / ☐ REWORK | | Stage D precision measurement criteria |

**Overall MIA-001 Status**: ☐ APPROVED | ☐ CONDITIONAL | ☐ REWORK REQUIRED

**Conditions (if CONDITIONAL)**:
- [ ] Condition 1: ______________________________
- [ ] Condition 2: ______________________________

**MIA-001 Advancement Verdict**: ☐ GATE PASSED | ☐ GATE PENDING CONDITIONS | ☐ GATE FAILED

### Advancement Recommendation

**Status**: BLOCKED — 5 threshold values unresolved (THRESHOLD-LLM-01 through THRESHOLD-LLM-05)

**Recommendation**: Stage A can be developed immediately after CIR-002 approval and integrated in parallel with Step 1 baseline work; production activation still requires Step 1 integration tests passing. Stages B–D remain BLOCKED pending thresholds, OQ-FR023-02 resolution, and Architecture LLM contract finalization.

**Reviewer**: _________________  
**Date approved**: _________  
**Conditions**: Stage A implementation only; full advancement gate requires all Human Gate Checklist items complete.
