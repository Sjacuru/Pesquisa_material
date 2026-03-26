# MDAP Change Impact Record — CIR-001
## EPIC-003: Addition of MODULE-003-05 (School Exclusivity Resolver)

**Status**: PENDING HUMAN GATE APPROVAL  
**Date**: March 26, 2026  
**Change Type**: Module Addition (visible scope change to approved EPIC)  
**Impact Level**: Medium (new module; clear responsibility; existing modules extended, not redesigned)

---

## 1. Baseline Reference

**Approved EPIC-003 Artifacts**:
- MDAP_STAGE1_EPIC-003_APPROVED.md (4 modules identified)
- MDAP_STAGE2_EPIC-003_APPROVED.md (dependency map)
- MDAP_STAGE3_EPIC-003_APPROVED.md (module details & AC)
- MDAP_STAGE4_EPIC-003_APPROVED.md (scope & risk review)
- MDAP_STAGE5_EPIC-003_APPROVED.md (advancement sign-off)
- All approved and in ARCHITECTURE phase

**Change**: Add MODULE-003-05; extend 4 existing modules

---

## 2. Stage 1: Module Identification (MODULE-003-05 Only)

### Module: MODULE-003-05 — School Exclusivity Resolver

**Responsibility**: Determine if an extracted item is school-exclusive; validate required sellers against active sources; log conflicts; route to review if needed.

**User Stories Covered**: US-014 (1 story)

**FRs Covered**: FR-022 (1 FR)

**Coverage**: ✓ 100% (1/1 story, 1/1 FR)

---

## 3. Stage 2: Dependency Mapping

### Intra-EPIC Dependencies
```
MODULE-003-05 ← [sequential input]
  - Receives: extracted item (from MODULE-001-01 via MODULE-001-07)
  - Receives: active sources list (from MODULE-002-04)
  - Feeds to: MODULE-003-01 (query orchestrator)
```

### Cross-Epic Dependencies
| Module | Upstream | Epic | Dependency |
|--------|----------|------|------------|
| MODULE-003-05 | MODULE-001-07 | EPIC-001 | Search-eligible items (via ISBN gate) |
| MODULE-003-05 | MODULE-002-04 | EPIC-002 | Active/eligible sources |

**Direction Check**: ✓ All forward-blocking (valid)

### Circular Dependency Check
- ✓ NO CYCLES (LINEAR PATH: 001-07 + 002-04 → 003-05 → 003-01 → 003-02 → 003-03 → 003-04)

### Critical Path Impact
- **Old**: 001-05 → 001-07 → 003-01 → 003-02 → 003-03
- **New**: 001-07 + 002-04 → **003-05** → 003-01 → 003-02 → 003-03
- **Change**: +1 module in critical path (MODULE-003-05 sequential)

---

## 4. Stage 3: Module Details & Acceptance Criteria

### MODULE-003-05: School Exclusivity Resolver

**Domain**: Business rule evaluation + conflict handling  
**Type**: Domain Logic  
**Risk Level**: HIGH  
**Expert Domains**: [Business Rule Logic, Conflict Resolution, Audit Logging]

**Responsibility Chain**:
1. Accept extracted item (school_exclusive, required_sellers, preferred_sellers)
2. Accept active sources list (MODULE-002-04 output)
3. Apply source-of-information precedence policy (default: document > user > default)
4. Validate required sellers exist in active sources
5. Determine resolution status (eligible, review_required)
6. Log all decisions to audit trail
7. Return resolved state to MODULE-003-01

**Acceptance Criteria**:

| ID | Criterion | Pass/Fail |
|----|-----------|-----------|
| AC1 | Exclusive item + active required sellers → Status=eligible | Verifiable |
| AC2 | Exclusive item + no active required sellers → Status=review_required, reason logged | Verifiable |
| AC3 | Exclusive item + some active required sellers → Status=eligible, conflict logged (aware, not blocking) | Verifiable |
| AC4 | Non-exclusive item → Status=eligible, all active sources available for search | Verifiable |
| AC5 | All conflicts logged with: item_id, conflict_type, source_of_info, timestamp, operator_action_if_override | Verifiable |
| AC6 | Source-precedence policy resolves conflicts consistently when both sources are present | Verifiable |
| AC7 | Operator can override exclusivity state; override logged with reason to audit trail | Verifiable |
| AC8 | Same item state → same decision (deterministic, no non-determinism) | Verifiable |

**Public Interface**:
```
INPUT:
  - item: { school_exclusive, required_sellers, preferred_sellers, ... }
  - active_sources: list of { site_id, ... }
  - (optional) document_notation_rules: dict from MODULE-001-01
  - (optional) user_overrides: dict from MODULE-004-01

OUTPUT:
  - resolved_item: { school_exclusive, required_sellers, preferred_sellers, resolution_status, ... }
  - resolution_status: "eligible" | "review_required"
  - resolution_reason: str
  - audit_log_entry: dict

SIDE EFFECTS:
  - Write resolution decision to audit trail
  - Log conflicts for operator review
```

**Constraints & Assumptions**:
- Seller identity normalization handled by MODULE-002-04 (canonical site_id)
- Document notation rules extracted by MODULE-001-01 pre-pass
- Operator override workflow owned by MODULE-004-01 (user_edit_handler)
- Audit trail persistence owned by MODULE-004-02 (versioned_audit_trail_logger)

---

## 5. Stage 4: Scope & Risk Review

### Scope Boundary (MODULE-003-05 Only)

**In Scope**:
- ✓ Determine exclusive state based on extraction + available sources
- ✓ Apply precedence rules (document > user > default)
- ✓ Validate required sellers against active set
- ✓ Log all decisions and conflicts
- ✓ Route to review_required when needed
- ✓ Pass resolved state to MODULE-003-01

**Out of Scope**:
- ❌ Operator UI for conflict display (UI layer concern)
- ❌ Dynamic seller contract negotiation
- ❌ Seller re-activation decisions
- ❌ User edit/override logic (MODULE-004-01 owns edits)

**Scope Verdict**: ✓ PASS — Clear boundary; no mission creep

---

### Risk Assessment

**Risk Level: HIGH**

| Risk Factor | Severity | Mitigation |
|-------------|----------|-----------|
| **Precedence Logic Correctness** | HIGH | Document > user > default; must be tested exhaustively (5+ scenarios) |
| **Conflict Handling Clarity** | HIGH | All conflicts logged; operator sees them; no silent behavior |
| **Determinism Requirement** | HIGH | Same input → same output; must be unit-tested for idempotence |
| **Cross-Epic Dependency Accuracy** | MEDIUM | Depends on MODULE-001-07 (ISBN gate) and MODULE-002-04 (source eligibility); both approved; low risk of interface mismatch |
| **Audit Trail Coupling** | MEDIUM | Depends on MODULE-004-02 to persist conflicts; design reviewed; low risk |

**Risk Mitigation Strategies**:
- [ ] Unit tests for all 8 ACs (precedence, validation, conflict logging)
- [ ] Integration test: extraction → exclusivity resolver → orchestrator (3-module flow)
- [ ] 5+ scenario tests: single/multi exclusive, blocked sellers, user override, non-exclusive + preferred
- [ ] Human review of precedence logic before code approval
- [ ] Audit trail spot-check (verify conflicts logged as expected)

**Risk Verdict**: ✓ ACCEPTABLE with mitigation tests

---

### Flagged Items

| Module | Risk | Expert Domains | Flag Status |
|--------|------|-----------------|-----------|
| MODULE-003-05 | HIGH | Business Rule Logic, Conflict Resolution, Audit Logging | ✓ FLAGGED |

**Expert Review Required**: Yes, before implementation begins

---

## 6. Cross-Epic Dependency Validation (Rule 2D)

**Rule**: Inter-epic dependencies must follow forward-blocking pattern only (no reverse blocking).

**Check**:
- ✓ MODULE-003-05 depends on MODULE-001-07 (forward)
- ✓ MODULE-003-05 depends on MODULE-002-04 (forward)
- ✓ MODULE-003-05 feeds to MODULE-003-01 (forward)
- ✓ No EPIC-001/002 module depends on EPIC-003 (no reverse)

**Verdict**: ✓ PASS — All forward-blocking; no reverse introduced

---

## 7. Coverage Completeness (Rule 2I)

**Rule**: Every user story must be covered; every module must map to a story.

**Check**:
- ✓ US-014 → MODULE-003-05 (new story, new module, 1:1 mapping)
- ✓ EPIC-003 coverage remains 5/5 (4 original + 1 new)
- ✓ No orphan modules

**Verdict**: ✓ PASS — Coverage 100%

---

## 8. Stage 5: Advancement Sign-Off (CIR Gate)

### Pre-Gate Validation

| Rule | Status | Evidence |
|------|--------|----------|
| 2A (Scope Creep) | ✓ PASS | All features in FR-022; no out-of-scope additions |
| 2B (Traceability) | ✓ PASS | MODULE-003-05 traces to US-014 → FR-022 |
| 2C (Risk Flagging) | ✓ PASS | HIGH-risk module flagged with expert domains |
| 2D (Cross-Epic Dir.) | ✓ PASS | All dependencies forward-blocking; no reverse |
| 2E (Bounded Scope) | ✓ PASS | In/out scope lists explicit; finite |
| 2F (Handoff Clarity) | ✓ PASS | Public interface defined with types |
| 2G (AC Binary) | ✓ PASS | All 8 ACs are pass/fail, verifiable |
| 2H (Constraint Carry) | ✓ PASS | No unresolved items introduced; seller normalization owned by EPIC-002 |
| 2I (Coverage) | ✓ PASS | 100% (US-014, FR-022) |
| 2J (Human Gate Control) | ⚠ PENDING | Human reviewer sign-off block remains open in this CIR |

---

### CIR Sign-Off Decision

**MODULE-003-05 Status**: ⚠ CONDITIONALLY APPROVED FOR ADVANCEMENT (pending human gate)

**Advancement Conditions**:
- [ ] Human reviewer (Architect or Domain Lead) reviews precedence logic
- [ ] Expert domain sign-off obtained (Business Rule Logic, Conflict Resolution)
- [ ] Mitigation tests planned (5+ scenarios, audit trail verification)

**Next Step**: Implementation begins; refer to plan/01_PRD/PRD_ADDENDUM_FR022.md for full acceptance criteria

---

### Human Gate Sign-Off

**Reviewer**: _________________ Role: _________________  
**Date**: _________________  
**Approval**: ☐ APPROVED | ☐ REWORK REQUIRED

**Comments**:
```
[Space for reviewer notes]
```

---

## 9. Summary

**Baseline**: EPIC-003 (4 modules, approved, in ARCHITECTURE phase)

**Change**: Add MODULE-003-05 (School Exclusivity Resolver)

**Impact**: 4 → 5 modules; +1 user story (US-014); +1 FR (FR-022)

**Dependencies**: Adds forward-blocking dependencies from EPIC-001/002; no reverse blocking

**Risk**: HIGH (business logic, conflict handling); acceptable with expert review + test mitigation

**CIR Gate**: ✓ PASS — Ready for implementation upon human sign-off
**CIR Gate**: ⚠ CONDITIONAL PASS — Ready for implementation only after human sign-off

---

## 10. Implementation Checklist (Post-Approval)

- [ ] Human gate sign-off obtained
- [ ] Expert domain (Business Rule Logic) reviews precedence logic
- [ ] New file: `search_ranking/school_exclusivity_resolver.py` (MODULE-003-05)
- [ ] Extend: `intake_canonicalization/pdf_ingestion_field_extraction.py` (add exclusivity fields)
- [ ] Extend: `search_ranking/query_orchestrator.py` (consume exclusivity context)
- [ ] Extend: `search_ranking/ranking_engine.py` (preferred sellers tie-break)
- [ ] Extend: `workflow_export/user_edit_handler.py` (allow school_exclusive edits)
- [ ] Extend: `config/settings.py` (add feature flag)
- [ ] Unit tests: MODULE-003-05 (8+ ACs, 5+ scenarios)
- [ ] Integration test: extraction → resolver → orchestrator
- [ ] Audit trail verification (conflicts logged correctly)
- [ ] Code review by flagged expert domain