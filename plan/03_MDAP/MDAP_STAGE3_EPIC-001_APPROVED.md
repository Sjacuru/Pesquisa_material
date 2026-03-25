# MDAP Stage 3 — EPIC-001 (Module Details)

## Stage Status
- Execution Status: COMPLETE
- Human Gate Status: APPROVED
- Epic: EPIC-001
- Input Artifacts:
  - `MDAP_STAGE1_EPIC-001_APPROVED.md` (approved)
  - `MDAP_STAGE2_EPIC-001_APPROVED.md` (approved)

## Pre-Gate Validation (must pass)
1. Stage 1 approved module list available ✅
2. Stage 2 approved dependency map available ✅
3. Unresolved items affecting EPIC-001 identified from handoff/context ✅ (`THRESHOLD-002`)

Gate Decision: PASS (proceed with Stage 3 output)
---

## A) Completed Module Templates

- User Stories: US-1
- Module Type: Integration
  - AC1: Given a valid mixed-format PDF, output contains extracted item lines with applicable category fields. (PASS/FAIL)
  - AC2: Every extracted field includes confidence in range [0.00, 1.00]. (PASS/FAIL)
- Public Interface:
  - Inputs: uploaded_pdf_document, category_matrix_reference
---

**Approved — Stage 3 complete. Proceeded to Stage 4 (Scope & Risk Review).**
  - Side Effects: writes extraction events to audit logs
- Dependencies: none
- Consumed By: MODULE-001-02, MODULE-001-06
- Isolation Level: PARTIAL
- Parallel?: YES
- Risk Level: HIGH
- Risk Justification: External document parsing and OCR variability can cause data loss if not controlled.
- Flag for Review: YES
- Expert Domain: Architect / Data Extraction
- Cross-Epic Dep?: NO
- Constraint Notes: THRESHOLD-002 unresolved; throughput/performance benchmarking is environment-dependent and must remain configurable.

### MODULE-001-02: Confidence Gating Router
- Responsibility: Route extracted fields into accept/review/reject paths based on configured extraction confidence bands.
- User Stories: US-2
- Module Type: Domain Logic
- Acceptance Criteria:
  - AC1: Confidence >= 0.90 is routed to auto-accept. (PASS/FAIL)
  - AC2: Confidence 0.70 to 0.89 is routed to manual review. (PASS/FAIL)
  - AC3: Confidence < 0.70 is routed to reject with correction request. (PASS/FAIL)
- Public Interface:
  - Inputs: extracted_items_with_confidence
  - Outputs: accepted_fields, review_queue_fields, rejected_fields
  - Side Effects: writes gate-decision events to audit logs
- Dependencies: MODULE-001-01
- Consumed By: MODULE-001-03
- Isolation Level: YES
- Parallel?: NO
- Risk Level: MEDIUM
- Risk Justification: Threshold misrouting can propagate invalid data to canonicalization.
- Flag for Review: YES
- Expert Domain: Architect / QA
- Cross-Epic Dep?: NO
- Constraint Notes: No unresolved assumption dependency; threshold bands are fixed by FR criteria.

### MODULE-001-03: Quantity & Unit Normalizer
- Responsibility: Normalize item quantities/units to canonical values and route ambiguous conversions to review.
- User Stories: US-3
- Module Type: Domain Logic
- Acceptance Criteria:
  - AC1: Recognized units normalize to canonical set only. (PASS/FAIL)
  - AC2: Ambiguous or unsupported conversions are routed to review and not auto-normalized. (PASS/FAIL)
  - AC3: Both original and normalized values are preserved for traceability. (PASS/FAIL)
- Public Interface:
  - Inputs: accepted_fields
  - Outputs: normalized_items, normalization_review_items
  - Side Effects: writes normalization decisions to audit logs
- Dependencies: MODULE-001-02
- Consumed By: MODULE-001-04
- Isolation Level: YES
- Parallel?: NO
- Risk Level: MEDIUM
- Risk Justification: Incorrect normalization can compromise deduplication and downstream eligibility.
- Flag for Review: YES
- Expert Domain: Domain Lead / QA
- Cross-Epic Dep?: NO
- Constraint Notes: No unresolved assumption dependency; canonical unit set is defined in PRD decision sheet.

### MODULE-001-04: Duplicate Resolution Coordinator
- Responsibility: Merge exact duplicates deterministically and route probable duplicates to merge review queue.
- User Stories: US-4
- Module Type: Domain Logic
- Acceptance Criteria:
  - AC1: Exact duplicates merge deterministically into one canonical item. (PASS/FAIL)
  - AC2: Probable duplicates route to merge review queue. (PASS/FAIL)
  - AC3: Merge decisions are recorded once with no silent item loss. (PASS/FAIL)
- Public Interface:
  - Inputs: normalized_items
  - Outputs: canonical_item_list, probable_duplicate_queue
  - Side Effects: writes merge-resolution audit entries
- Dependencies: MODULE-001-03
- Consumed By: MODULE-001-05
- Isolation Level: PARTIAL
- Parallel?: NO
- Risk Level: HIGH
- Risk Justification: Incorrect merge logic can cause irreversible data loss or duplication.
- Flag for Review: YES
- Expert Domain: Architect / QA
- Cross-Epic Dep?: NO
- Constraint Notes: No unresolved assumption dependency for EPIC-001; deterministic behavior required.

### MODULE-001-05: Category Rules & Eligibility Validator
- Responsibility: Enforce required fields, forbidden constraints, and hard-constraint gates to determine pre-search eligibility state.
- User Stories: US-5, US-6, US-7
- Module Type: Domain Logic
- Acceptance Criteria:
  - AC1: Missing required fields route item to review and block auto-accept. (PASS/FAIL)
  - AC2: Forbidden field violations route item to review and block auto-accept. (PASS/FAIL)
  - AC3: Hard-constraint failures override confidence and mark item invalid until corrected. (PASS/FAIL)
- Public Interface:
  - Inputs: canonical_item_list, category_rules_matrix
  - Outputs: eligible_items_precheck, review_required_items, invalid_items
  - Side Effects: writes validation and eligibility audit entries
- Dependencies: MODULE-001-04
- Consumed By: MODULE-001-07
- Isolation Level: PARTIAL
- Parallel?: NO
- Risk Level: HIGH
- Risk Justification: Core compliance gate; mistakes directly permit invalid items into search.
- Flag for Review: YES
- Expert Domain: Architect / Domain Lead
- Cross-Epic Dep?: NO
- Constraint Notes: THRESHOLD-002 unresolved may affect runtime SLA observability but not binary gate semantics.

### MODULE-001-06: ISBN Normalization & Validation
- Responsibility: Normalize ISBN strings and validate strict ISBN-10/ISBN-13 format for exact identifier matching.
- User Stories: US-8
- Module Type: Domain Logic
- Acceptance Criteria:
  - AC1: Input ISBN is normalized by removing separators/punctuation. (PASS/FAIL)
  - AC2: Only ISBN-10 or ISBN-13 format is accepted as valid. (PASS/FAIL)
  - AC3: Matching uses normalized exact string equality only. (PASS/FAIL)
- Public Interface:
  - Inputs: extracted_items_with_confidence
  - Outputs: isbn_validated_items, isbn_invalid_items
  - Side Effects: writes ISBN validation outcomes to audit logs
- Dependencies: MODULE-001-01
- Consumed By: MODULE-001-07
- Isolation Level: YES
- Parallel?: YES
- Risk Level: MEDIUM
- Risk Justification: Identifier normalization errors can cause false matches or false exclusions.
- Flag for Review: YES
- Expert Domain: QA / Domain Lead
- Cross-Epic Dep?: NO
- Constraint Notes: No unresolved assumption dependency for EPIC-001.

### MODULE-001-07: Missing-ISBN Search Gate
- Responsibility: Block Book/Dictionary items without valid ISBN from search until user completion confirms eligibility.
- User Stories: US-9
- Module Type: Interface
- Acceptance Criteria:
  - AC1: Book/Dictionary items missing valid ISBN are blocked from search. (PASS/FAIL)
  - AC2: After valid ISBN completion, blocked item becomes search-eligible. (PASS/FAIL)
  - AC3: If ISBN remains missing/invalid, item status remains review_required. (PASS/FAIL)
- Public Interface:
  - Inputs: eligible_items_precheck, isbn_validated_items, user_isbn_completion_events
  - Outputs: search_eligible_items, search_blocked_items
  - Side Effects: writes search-gate transitions to audit logs
- Dependencies: MODULE-001-05, MODULE-001-06
- Consumed By: EPIC-003 search entry (FR-015 prerequisite)
- Isolation Level: PARTIAL
- Parallel?: NO
- Risk Level: MEDIUM
- Risk Justification: Incorrect gate behavior can leak ineligible items to search or block valid items.
- Flag for Review: YES
- Expert Domain: Architect / QA
- Cross-Epic Dep?: NO
- Constraint Notes: Must preserve conditional gate behavior for Book/Dictionary only; no unresolved assumption resolution allowed.

---

## B) Coverage Matrix

- `US-1 -> MODULE-001-01 | Covered: YES`
- `US-2 -> MODULE-001-02 | Covered: YES`
- `US-3 -> MODULE-001-03 | Covered: YES`
- `US-4 -> MODULE-001-04 | Covered: YES`
- `US-5 -> MODULE-001-05 | Covered: YES`
- `US-6 -> MODULE-001-05 | Covered: YES`
- `US-7 -> MODULE-001-05 | Covered: YES`
- `US-8 -> MODULE-001-06 | Covered: YES`
- `US-9 -> MODULE-001-07 | Covered: YES`

Coverage Result: `9/9 user stories covered`

---

## C) Constraint Ledger

- `THRESHOLD-002 -> MODULE-001-01, MODULE-001-05 -> runtime performance reference environment unresolved; module design must keep performance parameters/environment assumptions configurable and not hard-coded.`
- `ASSUMPTION-003 -> not applicable to EPIC-001 modules (impacts EPIC-004 export formatting).`
- `ASSUMPTION-004 -> not applicable to EPIC-001 modules (impacts EPIC-002 brand taxonomy).`

---

## Stage 3 Validation Checklist

- All fields populated for every module: ✅
- Acceptance criteria binary and testable: ✅
- No unresolved item treated as resolved: ✅
- Coverage matrix has zero uncovered stories: ✅

---

## Human Gate (Stage 3)

Decision Required:
- ✅ APPROVE (move to Stage 4)
- ❌ REWORK (module detail/template issues)

Reviewer Notes:
- Approved by user in review chat. Proceed to Stage 4.

Reviewer:
- User

Date:
- March 24, 2026
