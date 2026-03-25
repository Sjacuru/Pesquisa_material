# MDAP Stage 1: Module Identification & User Story Coverage
## EPIC-004: User Editing, Versioned Traceability, and Export Delivery

**Status**: APPROVED  
**Date**: March 24, 2026  
**Reviewer**: User  
**Epic ID**: EPIC-004  
**Module Count**: 3 modules identified  
**User Story Coverage**: 3/3

---

## A. EPIC-004 SCOPE DEFINITION

**Epic Goal**: Enable end-users to edit search results, maintain a full versioned audit trail of all changes, and export curated material selections in multiple formats.

**Functional Requirements Addressed**:
- FR-018: User editing of material metadata (title corrections, category reassignments)
- FR-019: Versioned audit trail of all edits with user attribution and timestamps
- FR-020: Export delivery in multiple formats (PDF, CSV, JSON)

**User Stories**:
- **US-014**: User edits material metadata (title, category, ISBN) with local schema validation
- **US-015**: System maintains versioned audit trail with user identity, timestamp, and content diff
- **US-016**: User exports curated material set to PDF/CSV/JSON with format options

**Cross-Epic Blocking Dependencies**:
- Requires EPIC-003 ranked result output (provides the material set to edit)
- Requires EPIC-001 category system (edit validation against category enum)
- No reverse blocking: EPIC-004 output does not modify any EPIC-001/002/003 contracts

**Key Unresolved Item (Inherited)**:
- ASSUMPTION-003: Export format specifications (PDF styling, CSV delimiter, JSON schema) — unresolved in PRD; modules designed format-agnostic

---

## B. MODULE IDENTIFICATION

### MODULE-004-01: User Edit Handler
**Responsibility**: Accept user-initiated edits to material metadata; validate against schema; persist with full tagging.

**User Stories Covered**: US-014  
**FRs Covered**: FR-018

**Responsibility Chain**:
1. Consume material item from EPIC-003 ranked result set
2. Accept edit request (field name, old value, new value, optional reason note)
3. Validate new value against schema constraints (title ≤ 500 chars; category ∈ EPIC-001 CATEGORY_ENUM)
4. Reject edits on source-immutable fields (ISBN, source ID, extraction date)
5. Persist edit record with: user ID, timestamp, field, old→new values, reason note
6. Return edit confirmation (success/failure + timestamp)

**Blocked By**: None (leaf input module)  
**Blocks**: MODULE-004-02

---

### MODULE-004-02: Versioned Audit Trail Logger
**Responsibility**: Consume edit records and maintain an immutable, versioned audit log with diff-based retrieval.

**User Stories Covered**: US-015  
**FRs Covered**: FR-019

**Responsibility Chain**:
1. Consume edit records from MODULE-004-01
2. Append to immutable audit log (version N+1; no deletion or modification of history)
3. Maintain version index: sequence number, timestamp, user ID, field, content diff (old→new)
4. Expose query interface: full version history by material ID; diff between versions; filter by user/date range
5. Version numbering is gapless and immutable

**Key Constraint**:
- THRESHOLD-003 (log retention duration): Unresolved; module accepts configurable `retention_policy` parameter at runtime

**Blocked By**: MODULE-004-01  
**Blocks**: MODULE-004-03

---

### MODULE-004-03: Export Formatter & Delivery
**Responsibility**: Accept curated material set with version context; render to selected format; deliver to user.

**User Stories Covered**: US-016  
**FRs Covered**: FR-020

**Responsibility Chain**:
1. Consume material list (IDs + edit history from MODULE-004-02)
2. Accept format selection from user (PDF, CSV, or JSON)
3. Fetch version history per material from audit trail
4. Render to selected format with metadata (user, timestamp, version, field values)
5. Generate file and deliver (download or archive)
6. Log export event (user ID, format, timestamp, material count)

**Key Constraint**:
- ASSUMPTION-003 (export formatting): Format specification details unresolved; this module is format-agnostic at MDAP phase; format adapters deferred to ARCHITECTURE phase

**Blocked By**: MODULE-004-02  
**Blocks**: None (end-of-chain; output goes to user)

---

## C. COVERAGE MATRIX

| User Story | Module | Status |
|-----------|--------|--------|
| US-014: User edits metadata | MODULE-004-01 | ✓ Covered |
| US-015: Versioned audit trail | MODULE-004-02 | ✓ Covered |
| US-016: Export curated set | MODULE-004-03 | ✓ Covered |

**Coverage**: 3/3 (100%)

---

## D. FR TRACEABILITY

| FR ID | Title | Module | Status |
|-------|-------|--------|--------|
| FR-018 | User editing of material metadata | MODULE-004-01 | ✓ Covered |
| FR-019 | Versioned audit trail with attribution | MODULE-004-02 | ✓ Covered |
| FR-020 | Export delivery in multiple formats | MODULE-004-03 | ✓ Covered |

**FR Coverage for EPIC-004**: 3/3 (100%)

---

## E. MINIMAL MODULE PRINCIPLE VALIDATION

Could this be fewer than 3 modules?

- Merging MODULE-004-01 + MODULE-004-02: ❌ Edit validation logic mixed with audit/versioning logic; loses independent testability
- Merging MODULE-004-02 + MODULE-004-03: ❌ Internal record-keeping (audit) mixed with external-facing rendering (export); conceptually incompatible
- 1 module for all three: ❌ Violates single responsibility; untestable in isolation

**Conclusion**: 3 is the minimal count satisfying Single Responsibility, Independent Testability, and Explicit Dependencies.

---

## F. DEPENDENCY MAP (Intra-EPIC-004)

```
MODULE-004-01 (User Edit Handler)
    ↓
MODULE-004-02 (Versioned Audit Trail Logger)
    ↓
MODULE-004-03 (Export Formatter & Delivery)
    ↓
[End User]
```

Linear sequential chain — no parallel workstreams, no cycles.

---

## G. CROSS-EPIC DEPENDENCIES

| Module | Upstream Dependency | From Epic | Direction |
|--------|-------------------|-----------|-----------|
| MODULE-004-01 | Ranked result set (material input) | EPIC-003 | ← Valid forward |
| MODULE-004-01 | Category validation enum | EPIC-001 | ← Valid forward |

- ✓ No EPIC-001/002/003 module depends on EPIC-004 (no reverse blocking)

---

## H. UNRESOLVED ITEMS CARRY-FORWARD

| Item | Category | Status |
|------|----------|--------|
| ASSUMPTION-003 | Export formatting specs | Unresolved → ARCHITECTURE |
| THRESHOLD-003 | Log retention duration | Unresolved → ARCHITECTURE |
| THRESHOLD-002 | Performance reference environment | Inherited carry-forward |
| THRESHOLD-005 | Peak concurrent users | Inherited carry-forward |

---

## I. PRELIMINARY RISK ASSESSMENT

| Module | Risk Level | Domain(s) |
|--------|-----------|-----------|
| MODULE-004-01 | LOW | User input handling, schema validation |
| MODULE-004-02 | MEDIUM | Versioning logic, audit compliance, diff calculation |
| MODULE-004-03 | MEDIUM | Format rendering, file I/O, ASSUMPTION-003 exposure |

---

## J. MODULE SUMMARY

| Module ID | Name | US | FR | Risk |
|-----------|------|----|----|------|
| MODULE-004-01 | User Edit Handler | US-014 | FR-018 | LOW |
| MODULE-004-02 | Versioned Audit Trail Logger | US-015 | FR-019 | MEDIUM |
| MODULE-004-03 | Export Formatter & Delivery | US-016 | FR-020 | MEDIUM |

**Approved — Stage 1 complete. Proceeded to Stage 2 (Dependency Mapping).**
