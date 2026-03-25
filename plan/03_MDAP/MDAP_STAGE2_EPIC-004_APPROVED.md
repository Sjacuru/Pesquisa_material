# MDAP Stage 2: Dependency Mapping & Critical Path
## EPIC-004: User Editing, Versioned Traceability, and Export Delivery

**Status**: APPROVED  
**Date**: March 24, 2026  
**Reviewer**: User  
**Epic ID**: EPIC-004  
**Module Count**: 3 modules  
**Cycles Detected**: NONE

---

## A. INTRA-EPIC DEPENDENCY MAP

```
 ┌─────────────────────────────────────────────────┐
 │               EPIC-004 MODULE CHAIN              │
 │                                                  │
 │  [EPIC-003 ranked output]                        │
 │         ↓                                        │
 │  MODULE-004-01: User Edit Handler                │
 │         ↓  (edit records)                        │
 │  MODULE-004-02: Versioned Audit Trail Logger     │
 │         ↓  (version history + material set)      │
 │  MODULE-004-03: Export Formatter & Delivery      │
 │         ↓                                        │
 │         [End User]                               │
 └─────────────────────────────────────────────────┘
```

**Dependency Edges (Intra-EPIC-004)**:

| From | To | Dependency Type | Data Passed |
|------|----|-----------------|-------------|
| MODULE-004-01 | MODULE-004-02 | Blocking sequential | Edit records (user ID, timestamp, field, old→new, reason) |
| MODULE-004-02 | MODULE-004-03 | Blocking sequential | Version history + material set with audit context |

**Workstream Count**: 1 (single linear chain — no parallel branches within EPIC-004)

---

## B. CROSS-EPIC DEPENDENCY MAP

| Consuming Module | Upstream Module | From Epic | Dependency | Direction |
|-----------------|-----------------|-----------|------------|-----------|
| MODULE-004-01 | MODULE-003-03 (Ranking Engine output) | EPIC-003 | Ranked material set (the items user will edit) | ← Valid forward |
| MODULE-004-01 | MODULE-001-05 (Category Validation Gate) | EPIC-001 | Category enum used to validate edit field values | ← Valid forward |

**Notes**:
- MODULE-004-01 depends on EPIC-003 producing a ranked result set before any edits can be initiated
- MODULE-004-01 depends on EPIC-001 category validation gate for schema enforcement on category field edits — it does **not** duplicate the validation logic; it delegates to EPIC-001's enum contract
- No EPIC-001/002/003 module depends on EPIC-004 in any direction

---

## C. CIRCULAR DEPENDENCY CHECK

**Intra-EPIC-004**:
- 004-01 → 004-02 → 004-03 → (end user)
- No back-edges possible in this linear chain

**Cross-Epic**:
- EPIC-004 depends on EPIC-001 and EPIC-003
- EPIC-001 has no dependency on EPIC-004
- EPIC-003 has no dependency on EPIC-004

**Result**: ✓ NO CYCLES DETECTED — acyclic DAG confirmed

---

## D. CRITICAL PATH

```
MODULE-001-05 (Category Validation Gate)   ←── prerequisite
         ↓
MODULE-003-01 → MODULE-003-02 → MODULE-003-03 (Ranking Engine)   ←── prerequisite
         ↓
MODULE-004-01 (User Edit Handler)
         ↓
MODULE-004-02 (Versioned Audit Trail Logger)
         ↓
MODULE-004-03 (Export Formatter & Delivery)
         ↓
       [Done]
```

**Critical Path Summary**: Full EPIC-001 category gate → Full EPIC-003 ranking output → All 3 EPIC-004 modules in sequence. No step can be parallelized within EPIC-004; each module produces the input consumed by the next.

---

## E. PARALLEL WORKSTREAMS

**Within EPIC-004**: None. All 3 modules are sequentially dependent.

**Cross-Epic Parallelism Opportunity** (informational):
- MODULE-004-02 and MODULE-004-03 development can begin in parallel with MODULE-004-01 implementation, since their interfaces are known from Stage 1 contracts. However, at **runtime** they are strictly sequential.

---

## F. CROSS-EPIC DIRECTION VALIDATION (Rule 5A.4)

| Dependency | Direction | Valid? | Justification |
|------------|-----------|--------|---------------|
| EPIC-004 ← EPIC-001 (category enum) | Forward | ✓ Yes | EPIC-004 consumes prior Epic output; EPIC-001 unaware of EPIC-004 |
| EPIC-004 ← EPIC-003 (ranked results) | Forward | ✓ Yes | EPIC-004 is final Epic; depends on EPIC-003 output; not reverse |

**No reverse blocking introduced.** ✓

---

## G. UNRESOLVED ITEMS CARRY-FORWARD

| Item | Category | Impact on Dependency Map | Status |
|------|----------|--------------------------|--------|
| ASSUMPTION-003 | Export format specs | MODULE-004-03 interface stays format-agnostic; deferred to ARCHITECTURE | Unresolved |
| THRESHOLD-003 | Log retention duration | MODULE-004-02 accepts runtime `retention_policy` param; no structural impact | Unresolved |
| THRESHOLD-002 | Performance reference env | No structural dependency impact at MDAP phase | Inherited carry-forward |
| THRESHOLD-005 | Peak concurrent users | No structural dependency impact at MDAP phase | Inherited carry-forward |

---

## H. STAGE 2 SUMMARY

| Check | Result |
|-------|--------|
| Intra-epic edges mapped | ✓ 2 edges (001→002, 002→003) |
| Cross-epic edges mapped | ✓ 2 edges (from EPIC-001, EPIC-003) |
| Cycle detection | ✓ NO CYCLES |
| Critical path identified | ✓ Linear: EPIC-001 → EPIC-003 → 004-01 → 004-02 → 004-03 |
| Parallel workstreams | ✓ None (single chain) |
| Cross-epic direction valid | ✓ All forward-blocking |
| Unresolved items tracked | ✓ 4 items carried forward |

**Approved — Stage 2 complete. Proceeded to Stage 3 (Module Details & Acceptance Criteria).**
