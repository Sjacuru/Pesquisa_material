# MDAP Stage 4: Scope & Risk Review
## EPIC-004: User Editing, Versioned Traceability, and Export Delivery

**Status**: APPROVED  
**Date**: March 24, 2026  
**Reviewer**: User  
**Epic ID**: EPIC-004  
**Module Count**: 3 modules retained  
**Rejected Scope Patterns**: 3

---

## A. REJECTED SCOPE PATTERNS (Out of Scope for EPIC-004 MDAP)

### Pattern 1: Collaborative Multi-User Editing
**Proposal Summary**:  
Allow multiple users to edit the same material simultaneously with shared presence indicators, live conflict warnings, optimistic merge behavior, and comment threads.

**Why Rejected**:
- ❌ Violates Rule 2A (Scope Creep): FR-018 only requires user editing capability, not collaborative concurrency or comment workflows
- ❌ Violates Minimal Module Principle: would require collaboration/session-state modules, conflict-resolution logic, and participant-notification behavior
- ❌ Introduces unresolved assumptions around lock strategy, merge precedence, and user-role arbitration
- ✓ Can be considered later as an enhancement layer after single-user edit flow is stable

---

### Pattern 2: Edit Approval Workflow / Human Review Queue
**Proposal Summary**:  
Introduce maker-checker approval before edited records become visible in exports, including reviewer assignment, queue states, and approval/rejection reasons.

**Why Rejected**:
- ❌ No functional requirement or user story requests review workflow, queueing, or dual authorization
- ❌ Changes semantics of FR-018 by turning immediate local edit persistence into conditional approval flow
- ❌ Would require additional modules for queue management, reviewer actions, and state transitions
- ✓ Deferred as potential governance enhancement outside current MDAP scope

---

### Pattern 3: Rich Export Customization Studio
**Proposal Summary**:  
Provide template designer, per-column export customization, branding themes, conditional sections, and drag-and-drop export layout building.

**Why Rejected**:
- ❌ Violates Rule 2A (Scope Creep): FR-020 requires export delivery in supported formats, not document-design tooling
- ❌ Conflicts with ASSUMPTION-003 being unresolved; adding customization would multiply unknowns rather than contain them
- ❌ Requires UI/template-management concerns that are separate from export generation and delivery contract
- ✓ Deferred to post-ARCHITECTURE enhancement if export formatting is later formalized

---

## B. MODULE RETENTION REVIEW

| Module | Retention Status | Reason |
|--------|------------------|--------|
| MODULE-004-01 | ✓ RETAINED | Required single entry point for user edits and schema validation |
| MODULE-004-02 | ✓ RETAINED | Required for immutable versioning and audit traceability |
| MODULE-004-03 | ✓ RETAINED | Required for export assembly and delivery across supported formats |

**Retention Result**: 3/3 modules retained; no module collapse or split justified after Stage 3 review.

---

## C. HIGH / MEDIUM RISK MODULE FLAGGING & MITIGATION

### MODULE-004-01: User Edit Handler — LOW RISK
**Risk Category**: Validation Boundary  
**Expert Domains Required**: [User Input Validation, Domain Schema Enforcement]

**Risk Factors**:
1. Editable vs immutable field boundary must remain explicit and enforced consistently
2. Category validation must remain delegated to EPIC-001 contract to avoid taxonomy drift
3. Rejection reasons must remain deterministic for user-facing clarity and downstream audit consistency

**Mitigation Strategies**:
- [ ] Maintain fixed editable-field allowlist
- [ ] Reject immutable-field edits with explicit reason codes only
- [ ] Reuse EPIC-001 category contract rather than copying enum values locally

---

### MODULE-004-02: Versioned Audit Trail Logger — MEDIUM RISK
**Risk Category**: Compliance Traceability & Version Integrity  
**Expert Domains Required**: [Audit Logging, Versioning, Compliance Traceability]

**Risk Factors**:
1. Gapless version numbering must remain consistent under repeated edits on same material
2. Retention policy may create ambiguity if archival/removal behavior is not carefully designed later
3. Diff generation must remain deterministic across repeated retrievals for the same version pair
4. Any accidental mutation of historical records would break FR-019 directly

**Mitigation Strategies**:
- [ ] Enforce append-only storage contract for version ledger
- [ ] Define version-number authority at material scope only (no cross-material shared sequence)
- [ ] Preserve archived-history semantics even if older entries move storage tier later
- [ ] Validate diff determinism with repeated same-input comparisons during ARCHITECTURE phase

---

### MODULE-004-03: Export Formatter & Delivery — MEDIUM RISK
**Risk Category**: Export Contract Stability  
**Expert Domains Required**: [Document Rendering, File Export, Delivery Workflows]

**Risk Factors**:
1. ASSUMPTION-003 remains unresolved, so format details could pressure the module to absorb presentation concerns later
2. PDF/CSV/JSON rendering paths may diverge if adapter boundary is not kept strict
3. Export artifacts must include version context without mutating live state or audit history
4. Empty-set, unsupported-format, and rendering-failure paths must remain explicit and deterministic

**Mitigation Strategies**:
- [ ] Keep export assembly format-neutral; push format specifics behind adapter boundary
- [ ] Reject unsupported formats with explicit reason codes instead of fallback behavior
- [ ] Log all export attempts with artifact ID and material count for downstream traceability
- [ ] Validate identical-input export payload stability before implementation planning advances

---

## D. SCOPE CEILING VALIDATION

**In Scope**:
- ✓ Single-user metadata editing over ranked material records
- ✓ Immutable version/audit history with deterministic diff retrieval
- ✓ Export artifact generation and delivery for PDF, CSV, and JSON
- ✓ Explicit carry-forward of unresolved export-format and retention-policy items

**Out of Scope**:
- ❌ Collaborative editing / live concurrency controls
- ❌ Maker-checker approval workflow
- ❌ Export template studio / rich layout designer
- ❌ External source-system mutation or write-back
- ❌ Role-based publishing workflow beyond user attribution already required for audit trail

**Scope Ceiling Verdict**: ✓ No scope creep detected; all retained modules remain bounded to FR-018, FR-019, and FR-020

---

## E. CROSS-EPIC RISK ASSESSMENT

| Dependency | Risk | Assessment |
|------------|------|------------|
| MODULE-004-01 ← EPIC-003 ranked output | LOW | Input dependency is clear; EPIC-004 overlays edits locally and does not modify ranking pipeline |
| MODULE-004-01 ← EPIC-001 category contract | LOW | Validation dependency is narrow and explicit; no reverse blocking introduced |
| MODULE-004-03 ← MODULE-004-02 version context | MEDIUM | Export correctness depends on stable audit retrieval contract; manageable within current design |

**Cross-Epic Direction Check**: ✓ Valid forward-only dependency direction preserved

---

## F. ASSUMPTION & THRESHOLD CARRY-FORWARD

### Unresolved Items
- **ASSUMPTION-003**: Export formatting details unresolved; still deferred to ARCHITECTURE
- **THRESHOLD-003**: Log retention duration unresolved; remains runtime policy concern
- **THRESHOLD-002**: Performance reference environment unresolved; no scope effect here
- **THRESHOLD-005**: Peak concurrent users unresolved; no scope effect here

### Handling Rule
No unresolved item is treated as solved. All retained modules remain contract-safe without forcing hidden design decisions.

---

## G. RISK MATRIX SUMMARY

| Dimension | EPIC-004 Status | Benchmark | Variance |
|-----------|-----------------|-----------|----------|
| High-Risk Modules | 0 | ≤ 2 | ✓ Within limit |
| Medium-Risk Modules | 2 | ≤ 3 | ✓ Within limit |
| Low-Risk Modules | 1 | No limit | ✓ Acceptable |
| Rejected Scope Patterns | 3 | ≥ 1 | ✓ Satisfied |
| Module Retention Rate | 100% (3/3) | ≥ 75% | ✓ Exceeds |
| Unresolved Items | 4 carried forward | Explicit only | ✓ Controlled |

---

## H. MODULE SUMMARY

| Module ID | Name | Risk | Status |
|-----------|------|------|--------|
| MODULE-004-01 | User Edit Handler | LOW | ✓ Retained |
| MODULE-004-02 | Versioned Audit Trail Logger | MEDIUM | ✓ Retained |
| MODULE-004-03 | Export Formatter & Delivery | MEDIUM | ✓ Retained |

**Approved — Stage 4 complete. Proceeded to Stage 5 (Advancement Sign-Off).**
