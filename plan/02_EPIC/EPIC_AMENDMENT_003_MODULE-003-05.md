# EPIC-003 Amendment: Add MODULE-003-05 (School Exclusivity Resolver)

**References**: EPIC_OUTPUT.md, MDAP Stage 5 EPIC-003 (approved baseline)  
**Status**: PENDING MDAP CIR-001 APPROVAL  
**Amendment Date**: March 26, 2026

---

## 1. Change Summary

**Original EPIC-003**: 4 modules, 4 user stories, 4 FRs (FR-015, FR-016, FR-017, FR-021)

**Amended EPIC-003**: 5 modules, 5 user stories, 5 FRs (adds MODULE-003-05, US-014, FR-022)

---

## 2. New Module Addition

### MODULE-003-05: School Exclusivity Resolver

**User Story**: US-014
> As the system, I resolve school-defined seller constraints and validate them against available sources, so that items exclusive to specific sellers are routed to those sellers and conflicts are logged for operator review.

**Epic**: EPIC-003  
**FRs Covered**: FR-022 (new)  
**Risk Level**: HIGH (precedence logic, conflict handling)  
**Expert Domains**: [Business Rule Logic, Conflict Resolution, Audit Logging]

**Responsibility Chain**:
1. Consume extracted item with school_exclusive, required_sellers, preferred_sellers fields
2. Validate required sellers against active/eligible sources (from MODULE-002-04)
3. Apply source-of-information precedence (document beats user; user beats system default)
4. Determine resolution status: eligible, review_required, or conflict
5. Log all decisions to audit trail
6. Pass resolved exclusivity context to MODULE-003-01 (query orchestrator)

**Public Interface**:
```
INPUT:
  - item: dict with school_exclusive, required_sellers, preferred_sellers
  - active_sources: list of eligible sellers (from MODULE-002-04)
  - document_notation_rules: dict (from MODULE-001-01 pre-pass)
  - user_annotations: dict (from MODULE-004-01 edits, optional)

OUTPUT:
  - resolved_item: dict with validated exclusivity state
  - resolution_status: "eligible" | "review_required"
  - resolution_reason: str (e.g., "no_active_required_sellers", "document_beats_user")
  - audit_log_entry: dict with all conflict decisions

SIDE EFFECTS:
  - Write resolution decision to versioned audit trail
  - Log conflicts for operator review
```

**Blocked By**: MODULE-001-07 (Missing-ISBN Search Gate), MODULE-002-04 (Search Eligibility Site Filter)  
**Blocks**: MODULE-003-01 (Query Orchestrator)

---

## 3. Updated Module List for EPIC-003

| Module ID | Name | User Story | FR | Risk | Status |
|-----------|------|------------|-----|------|--------|
| MODULE-003-01 | Query Orchestrator | US-010 | FR-015 | HIGH | Approved (extended for exclusivity) |
| MODULE-003-02 | Match Classifier | US-011 | FR-016 | MEDIUM | Approved (unchanged) |
| MODULE-003-03 | Ranking Engine | US-012 | FR-017 | HIGH | Approved (extended for preferred sellers) |
| MODULE-003-04 | Apostila Routing Guard | US-013 | FR-021 | MEDIUM | Approved (unchanged) |
| **MODULE-003-05** | **School Exclusivity Resolver** | **US-014** | **FR-022** | **HIGH** | **NEW (MDAP CIR-001)** |

**Total Modules**: 5 (was 4)  
**Total User Stories Covered**: 5/5  
**Total FRs Covered**: 5 (was 4; adds FR-022)

---

## 4. Updated Critical Path

**Original**: MODULE-001-05 → MODULE-001-07 → MODULE-003-01 → MODULE-003-02 → MODULE-003-03

**Amended**:
```
MODULE-001-07 (Missing-ISBN Search Gate)
MODULE-002-04 (Search Eligibility Site Filter)
  ↓
MODULE-003-05 (School Exclusivity Resolver) ← NEW
    ↓
MODULE-003-01 (Query Orchestrator)
    ↓
MODULE-003-02 (Match Classifier)
    ↓
MODULE-003-03 (Ranking Engine)
```

**Path Length**: +1 module (MODULE-003-05 now in critical path)

---

## 5. Dependencies Summary

### Intra-EPIC-003 Dependencies
| From | To | Type |
|------|-----|------|
| MODULE-003-05 | MODULE-003-01 | Sequential blocking |
| MODULE-003-01 | MODULE-003-02 | Sequential blocking (unchanged) |
| MODULE-003-02 | MODULE-003-03 | Sequential blocking (unchanged) |
| MODULE-003-01 | MODULE-003-04 | Parallel branch (unchanged) |

### Cross-Epic Dependencies (NEW)
| Consuming Module | From Epic | Depends On | Type |
|------------------|-----------|------------|------|
| MODULE-003-05 | EPIC-003 | MODULE-001-07 | Forward blocking |
| MODULE-003-05 | EPIC-003 | MODULE-002-04 | Forward blocking |

**Direction Check**: ✓ Valid forward-blocking (no reverse dependencies introduced)

---

## 6. Contract Extensions

### MODULE-001-01 (PDF Ingestion & Field Extraction)
- **Extension**: Now extracts school_exclusive, required_sellers, preferred_sellers fields
- **No Breaking Change**: Adds fields; existing fields unchanged

### MODULE-003-01 (Query Orchestrator)
- **Extension**: Accepts resolved exclusivity context from MODULE-003-05; routes query based on school_exclusive flag
- **Contract Change**: Query input now includes exclusivity state; output routing logic updated
- **No Breaking Change**: Existing non-exclusive items routed as before

### MODULE-003-03 (Ranking Engine)
- **Extension**: Preferred sellers used as secondary sort key (tie-break only)
- **No Breaking Change**: Composite score calculation unchanged; new sort pass added after score normalization

### MODULE-004-01 (User Edit Handler)
- **Extension**: Operator can edit school_exclusive field
- **Contract Change**: Editable fields now include school_exclusive
- **No Breaking Change**: Existing field edits unchanged

---

## 7. Sign-Off

**EPIC-003 Amendment Status**: Ready for MDAP CIR-001

**Next Step**: Run MDAP Change Impact Record (CIR-001) for MODULE-003-05 only
- Stages 1-5 for new module
- Re-check cross-epic dependencies
- Human gate required before implementation