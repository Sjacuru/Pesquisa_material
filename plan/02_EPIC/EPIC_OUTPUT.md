# EPIC OUTPUT — School Material Price Finder (Brazil MVP)

## Epic Header
- Total Epics: 4
- Functional Coverage: 21/21 FRs
- Non-Functional Coverage: 5/5 NFRs
- Persona Model: PERSONA-001 only (single generalized School List User)
- Scope Ceiling: Brazil-focused school material comparison tool for complete lists from mixed documents, optimized for lowest delivered total spend.
- Canonical IDs: Preserved exactly (FR-001..FR-021, NFR-001..NFR-005)

### Coverage Split (Required)
- EPIC-001: 9 FRs (FR-001..FR-009)
- EPIC-002: 5 FRs (FR-010..FR-014)
- EPIC-003: 4 FRs (FR-015..FR-017, FR-021)
- EPIC-004: 3 FRs (FR-018..FR-020)

### Shared Quality Metrics (Applied Equally to All Epics)
- **DOR (Definition of Ready):** Requirement traceable to canonical FR/NFR ID; acceptance criteria are binary and measurable; no unresolved MUST-priority threshold blocking the story.
- **DOD (Definition of Done):** All acceptance criteria pass; no silent failures or skipped routing; audit log entry generated for each state transition; no data loss between epic boundaries.
- **QC target:** Correctness validated per story acceptance criteria. Deduplication and matching quality sampled in pilot per SM-009; no separate false-positive/false-negative metric tracked per epic.

## Decomposition Trace (Chunking Evidence)
- **Chunk 1 (FR-001..FR-009):** Processed and verified as EPIC-001 with 9/9 FR coverage, dependencies documented, and assumption/threshold tags propagated.
- **Chunk 2 (FR-010..FR-014):** Processed and verified as EPIC-002 with 5/5 FR coverage and source-trust chain dependencies captured.
- **Chunk 3 (FR-015..FR-017, FR-021):** Processed and verified as EPIC-003 with 4/4 FR coverage, conditional eligibility rules, and ranking chain dependencies captured.
- **Chunk 4 (FR-018..FR-020):** Processed and verified as EPIC-004 with 3/3 FR coverage and edit/version/export flow completed.
- **Final merge verification:** 21/21 FRs and 5/5 NFRs mapped; no orphaned IDs.

---

## EPIC-001: Ingestion, Canonicalization, and Validation Gating
**Derived from:** FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009; NFR-001, NFR-002

### Strategic Goal
Produce one validated, canonical item list from mixed PDF sources, with confidence gates and category/ISBN hard rules enforced before any search eligibility.

### Risk/Assumption Field
- [ASSUMPTION-001] Single persona model retained (resolved for MVP baseline).
- [ASSUMPTION-002] Scope ceiling immutable and inherited from executive summary baseline.
- [THRESHOLD-007] Max PDF upload size/pages impacts extraction throughput and failure behavior.
- [THRESHOLD-001] Max items per list constrains SLA validation for end-to-end time.
- [THRESHOLD-002] Runtime measurement environment remains deferred to MDAP.

### Epic Definition of Done
- [ ] Mixed PDF extraction returns category-aligned fields and confidence scores.
- [ ] Confidence bands route items correctly (accept/review/reject).
- [ ] Unit normalization + deduplication produce canonical list.
- [ ] Required/forbidden/category hard constraints are enforced.
- [ ] ISBN normalization/validation/completion gate blocks ineligible Book/Dictionary search.
- [ ] Audit logs capture gate outcomes.
- [ ] Canonical item schema (fields, nullability, status states) is defined and documented as the shared data contract inherited by all downstream EPICs.
- [ ] Item lifecycle states are implemented: `extracted → confidence_gated → normalized → deduplicated → validated → eligible | review_required | invalid` (+ others as pipeline grows).
- [ ] Duplicate PDF upload submissions are detected and rejected before extraction re-runs.

### User Stories
1) **As a School List User, I want items extracted from mixed-format PDFs, so that my full list can be processed without manual retyping.**
- Acceptance:
  - [ ] Extracted lines include applicable fields by category matrix.
  - [ ] Each extracted field stores confidence in [0.00,1.00].
  - [ ] [ASSUMPTION-001] Flow uses the single School List User persona only.
  - [ ] [ASSUMPTION-002] Story behavior stays inside the immutable MVP scope ceiling.
- References: FR-001

2) **As a School List User, I want confidence-based extraction gating, so that uncertain data is reviewed before canonicalization.**
- Acceptance:
  - [ ] Confidence >=0.90 auto-accepts fields.
  - [ ] Confidence 0.70-0.89 routes to manual review.
  - [ ] Confidence <0.70 rejects and requests correction.
- References: FR-002

3) **As a School List User, I want quantities and units normalized to canonical values, so that downstream matching and deduplication are consistent.**
- Acceptance:
  - [ ] Units normalize to canonical set only.
  - [ ] Ambiguous conversions route to review queue (not auto-normalized).
- References: FR-003

4) **As a School List User, I want duplicate extracted items merged or queued for review, so that I get one canonical list without silent loss.**
- Acceptance:
  - [ ] Exact duplicates merge deterministically.
  - [ ] Probable duplicates route to merge review queue.
- References: FR-004

5) **As a School List User, I want required fields validated per category, so that incomplete items are blocked from auto-accept flow.**
- Acceptance:
  - [ ] Missing required fields route to review and are not auto-accepted.
- [ ] Items with all required fields pass required-field gate.
- References: FR-005

6) **As a School List User, I want forbidden fields validated per category, so that invalid combinations fail before search.**
- Acceptance:
  - [ ] Forbidden category fields (including Apostila ISBN) trigger validation failure.
- [ ] Forbidden-field failures route to review queue and are not auto-accepted.
- References: FR-006

7) **As a School List User, I want hard constraints enforced before search eligibility, so that invalid items are excluded regardless of confidence.**
- Acceptance:
  - [ ] HC failures override confidence and mark item invalid until corrected.
- [ ] HC-invalid items are excluded from ranking/search eligibility until corrected.
- References: FR-007

8) **As a School List User, I want ISBN normalized and format-validated, so that identifier matching is exact and reliable.**
- Acceptance:
  - [ ] ISBN values accept only ISBN-10 or ISBN-13 after normalization.
  - [ ] Matching compares normalized ISBN by exact string equality.
- References: FR-008

9) **As a School List User, I want Book/Dictionary items with missing ISBN blocked before search, so that invalid identifier gaps are fixed first.**
- Acceptance:
  - [ ] Missing Book/Dictionary ISBN blocks search until user completion.
  - [ ] After valid ISBN completion, item becomes search-eligible.
- References: FR-009

---

## EPIC-002: Source Trust and Brand Governance
**Derived from:** FR-010, FR-011, FR-012, FR-013, FR-014; NFR-004, NFR-002

### Strategic Goal
Build trusted, operable search sources and governed brand fallback behavior before large-scale querying.

### Risk/Assumption Field
- [ASSUMPTION-001] Single persona model retained (resolved for MVP baseline).
- [ASSUMPTION-002] Scope ceiling immutable and inherited from executive summary baseline.
- [ASSUMPTION-004] Brand substitution reason taxonomy is not fully standardized.
- [THRESHOLD-004] Auto-suspension failure streak must be enforced consistently (configured at 5 in 1 hour per context gate).
- [THRESHOLD-006] Per-website completion rate target must be tracked (>=95% per context gate).

### Epic Definition of Done
- [ ] Website onboarding validates domain/HTTPS/trust classification.
- [ ] Blocked sites are excluded from active search set.
- [ ] Suspension policy activates on failure streak threshold.
- [ ] Brand fallback prompts are per-item and reason-coded when approved.
- [ ] Site query execution applies retry policy (3 attempts, exponential backoff) before recording a failure toward the suspension threshold.

### User Stories
1) **As a School List User, I want cross-brand expansion gated by explicit approval, so that trust and brand constraints are preserved.**
- Acceptance:
  - [ ] If same-brand offers >=3, no expansion prompt appears.
  - [ ] If same-brand offers <3, per-item approval is required for expansion.
- References: FR-010

2) **As a School List User, I want approved cross-brand substitutions reason-coded, so that decisions are auditable.**
- Acceptance:
  - [ ] Each approved expansion stores reason code and timestamp.
  - [ ] Items without expansion approval have no substitution reason-code record.
- References: FR-011

3) **As a School List User, I want websites onboarded with trust classification, so that only validated sources can enter the search pool.**
- Acceptance:
  - [ ] Domain and HTTPS checks execute during onboarding.
  - [ ] ReclameAqui status classifies site as allowed/review_required/blocked.
  - [ ] Failed onboarding prevents activation.
  - [ ] [ASSUMPTION-001] Flow uses the single School List User persona only.
  - [ ] [ASSUMPTION-002] Story behavior stays inside the immutable MVP scope ceiling.
- References: FR-012

4) **As a School List User, I want blocked bad-rated websites excluded from search, so that result quality is protected.**
- Acceptance:
  - [ ] Blocked sites never appear in searchable site set.
  - [ ] Allowed/review_required and non-suspended sites remain eligible.
- References: FR-013

5) **As a School List User, I want unstable websites auto-suspended after repeated failures, so that source reliability is maintained.**
- Acceptance:
  - [ ] Site status switches to suspended after configured failure streak threshold.
  - [ ] Site failures increment streak only after 3 retry attempts without success.
  - [ ] Suspended sites are excluded until revalidated.
- References: FR-014

---

## EPIC-003: Multi-Source Search, Match Classification, Ranking, and Apostila Routing
**Derived from:** FR-015, FR-016, FR-017, FR-021; NFR-001, NFR-002, NFR-004

### Strategic Goal
Execute category-eligible multi-source search, classify match quality, and produce trust-aware lowest-delivered-price rankings with Apostila source restrictions.

### Risk/Assumption Field
- [ASSUMPTION-001] Single persona model retained (resolved for MVP baseline).
- [ASSUMPTION-002] Scope ceiling immutable and inherited from executive summary baseline.
- [CONFLICT-001 / OQ-012] “all activated websites” must be interpreted as category-eligible set to remain consistent with Apostila external-only routing.
- [THRESHOLD-005] Concurrency target remains unresolved until MDAP.
- [THRESHOLD-002] Runtime environment still required for strict SLA comparability.

### Epic Definition of Done
- [ ] Search queries run only for search-eligible items against active eligible sites.
- [ ] Match confidence classes enforce invalid/review/candidate thresholds.
- [ ] Ranking sorts by total delivered cost with trust tie-breaks.
- [ ] Apostila items are routed to external-only sources.

### User Stories
1) **As a School List User, I want each eligible item queried across active eligible sources, so that I can compare market options comprehensively.**
- Acceptance:
  - [ ] Query fan-out excludes blocked/suspended sources.
  - [ ] Item eligibility requires prior validation gates and conditional ISBN completion for Book/Dictionary.
  - [ ] Per-site attempt/result logs are generated.
  - [ ] Items edited via FR-018 that affect ISBN or category fields are re-validated for eligibility before search inclusion.
  - [ ] Each site query retries up to 3 times with exponential backoff before marking the attempt as failed.
  - [ ] Re-running search for the same list produces identical eligibility and source sets (idempotent).
  - [ ] [ASSUMPTION-001] Flow uses the single School List User persona only.
  - [ ] [ASSUMPTION-002] Story behavior stays inside the immutable MVP scope ceiling.
- References: FR-015

2) **As a School List User, I want search results classified by confidence and hard constraints, so that invalid candidates never reach ranking output.**
- Acceptance:
  - [ ] >=0.92 with HC pass -> candidate.
  - [ ] 0.75-0.91 -> review_required.
  - [ ] <0.75 or HC failure -> invalid/excluded.
- References: FR-016

3) **As a School List User, I want ranked offers by lowest delivered total and trust signals, so that I choose reliable low-cost options quickly.**
- Acceptance:
  - [ ] Primary sort is item price + shipping.
  - [ ] HC-failing candidates are excluded before sort.
  - [ ] Tie-break uses seller trust signal.
- References: FR-017

4) **As a School List User, I want Apostila items routed to external-only sources, so that category policy is respected.**
- Acceptance:
  - [ ] Apostila excludes marketplace channels.
  - [ ] Reprografia-tagged Apostila queries only configured external sources.
  - [ ] Marketplace-matched Apostila candidates are invalidated.
- References: FR-021

---

## EPIC-004: User Editing, Versioned Traceability, and Export Delivery
**Derived from:** FR-018, FR-019, FR-020; NFR-002, NFR-003, NFR-005

### Strategic Goal
Enable user correction before search, preserve immutable change history, and deliver complete export artifacts for decision and operations.

### Risk/Assumption Field
- [ASSUMPTION-001] Single persona model retained (resolved for MVP baseline).
- [ASSUMPTION-002] Scope ceiling immutable and inherited from executive summary baseline.
- [ASSUMPTION-003] Export locale/schema formatting (ordering, decimal/date format) remains partially unspecified.
- [THRESHOLD-003] Retention duration for logs/history deferred to MDAP.

### Epic Definition of Done
- [ ] Users can edit extracted item fields pre-search and overrides are respected downstream.
- [ ] Every edit/merge decision is versioned with reason + timestamp.
- [ ] Excel and CSV exports include required columns and alternatives metadata.

### User Stories
1) **As a School List User, I want to edit extracted item fields before search, so that matching uses corrected information.**
- Acceptance:
  - [ ] Item edits save successfully before search.
  - [ ] Edited values override extracted values during matching.
  - [ ] Unedited values retain canonical extracted values.
  - [ ] Concurrent edits to the same item are rejected with a conflict notification; only one edit session is accepted at a time.
  - [ ] [ASSUMPTION-001] Flow uses the single School List User persona only.
  - [ ] [ASSUMPTION-002] Story behavior stays inside the immutable MVP scope ceiling.
- References: FR-018

2) **As a School List User, I want item and merge history versioned, so that decisions are auditable and reversible by investigation.**
- Acceptance:
  - [ ] Every edit creates immutable version with reason/timestamp.
  - [ ] Merge decisions are logged with reason/timestamp.
  - [ ] Item history is retrievable in chronological order.
- References: FR-019

3) **As a School List User, I want export files with complete decision context, so that I can share and operationalize selected offers.**
- Acceptance:
  - [ ] Excel export includes item, selected offer, price, alternatives, confidence, source URL.
  - [ ] CSV export includes same required fields.
  - [ ] Each exported row maps to one selected offer with alternatives metadata.
  - [ ] Re-triggering export for the same run produces consistent output reflecting the same ranked snapshot.
- References: FR-020

---

## Dependencies

### Dependency Map Validation Reference
- Validated against **PRD-to-EPIC_INTEGRATION_GUIDE.md — Section B (Complete FR dependency map)**.
- Confirmed chain: FR-001 -> FR-002 -> FR-003 -> FR-004 -> FR-005 -> FR-006 -> FR-007.
- Confirmed conditional chain: FR-008 -> FR-009 -> FR-015 (Book/Dictionary gate).
- Confirmed source chain: FR-012 -> FR-013 -> FR-015.

### Hard Blocking Dependencies
- EPIC-001 -> EPIC-003: Search requires validated item eligibility gates (FR-007) and conditional ISBN completion (FR-009).
- EPIC-002 -> EPIC-003: Search requires source eligibility/trust filtering (FR-012/FR-013) and suspension state (FR-014).
- EPIC-003 -> EPIC-004: Export finalization requires ranked results (FR-017) before FR-020 completion.
- Within EPIC-004: FR-018 -> FR-019 -> FR-020 is hard-ordered for full auditability.

### Soft Dependencies
- EPIC-004 editing flow can begin in parallel with EPIC-001 after extraction foundations are stable (FR-001); edits that modify ISBN or category fields trigger mandatory re-validation before EPIC-003 search inclusion.
- EPIC-002 brand governance (FR-010/FR-011) can run in parallel with EPIC-001 and converge during ranking/search operations.

### External / Phase Dependencies
- MDAP resolves THRESHOLD-002, THRESHOLD-003, THRESHOLD-005 for final non-functional closure.
- PRD governance maintains scope ceiling and canonical ID immutability.

---

## Assumptions & Open Questions

### [ASSUMPTION] Set (4)
- ASSUMPTION-001: Single generalized persona retained (resolved for MVP, keep traceability).
- ASSUMPTION-002: Scope ceiling anchored to executive summary statement (resolved, immutable).
- ASSUMPTION-003: Export formatting details remain partially undefined (carried).
- ASSUMPTION-004: Brand substitution taxonomy partially undefined (carried unless controlled taxonomy adopted now).

### [THRESHOLD] Set (7)
- THRESHOLD-001: Max items per list for SLA — **from CONTEXT.md gate decision** (3 immediate, expandable to 10).
- THRESHOLD-002: Performance reference environment — unresolved, MDAP.
- THRESHOLD-003: Log retention duration — unresolved, MDAP (provisional 90 days noted in context).
- THRESHOLD-004: Auto-suspension trigger — **from CONTEXT.md gate decision** (5 consecutive failures in 1 hour).
- THRESHOLD-005: Peak concurrent users — unresolved, MDAP.
- THRESHOLD-006: Per-site completion rate target — **from CONTEXT.md gate decision** (>=95%).
- THRESHOLD-007: PDF upload max pages/size — **from CONTEXT.md gate decision** (5 pages).

### Conflict / Clarification Items
- OQ-012: FR-015 “all activated websites” must be interpreted as category-eligible websites to avoid contradiction with FR-021.
- OQ-013: Personal-use framing vs national scalability should remain governance note, not MVP expansion scope.

---

## Coverage Matrix

| PRD ID | Requirement | Epic ID | Status |
|---|---|---|---|
| FR-001 | Extract mixed-PDF item fields | EPIC-001 | ✓ |
| FR-002 | Confidence gating before canonicalization | EPIC-001 | ✓ |
| FR-003 | Normalize quantities and units | EPIC-001 | ✓ |
| FR-004 | Deduplicate and merge-review queue | EPIC-001 | ✓ |
| FR-005 | Enforce category required fields | EPIC-001 | ✓ |
| FR-006 | Enforce category forbidden constraints | EPIC-001 | ✓ |
| FR-007 | Hard constraints before search | EPIC-001 | ✓ |
| FR-008 | Validate/normalize ISBN | EPIC-001 | ✓ |
| FR-009 | Require ISBN completion before search | EPIC-001 | ✓ |
| FR-010 | Brand fallback approval | EPIC-002 | ✓ |
| FR-011 | Brand substitution reason codes | EPIC-002 | ✓ |
| FR-012 | Website onboarding + trust validation | EPIC-002 | ✓ |
| FR-013 | Block bad-rated websites | EPIC-002 | ✓ |
| FR-014 | Auto-suspend after failure streak | EPIC-002 | ✓ |
| FR-015 | Query all activated eligible websites | EPIC-003 | ✓ |
| FR-016 | Match confidence classification | EPIC-003 | ✓ |
| FR-017 | Rank by delivered price + trust | EPIC-003 | ✓ |
| FR-018 | Pre-search item edits | EPIC-004 | ✓ |
| FR-019 | Version edits and merges | EPIC-004 | ✓ |
| FR-020 | Export Excel/CSV with required fields | EPIC-004 | ✓ |
| FR-021 | Apostila external-only routing | EPIC-003 | ✓ |
| NFR-001 | <=10 minute end-to-end processing | EPIC-001, EPIC-003 | ⚠ |
| NFR-002 | Structured audit logs | EPIC-001, EPIC-002, EPIC-003, EPIC-004 | ✓ |
| NFR-003 | Versioned change history | EPIC-004 | ✓ |
| NFR-004 | Website health/suspension observability | EPIC-002, EPIC-003 | ✓ |
| NFR-005 | Retention config and log filters | EPIC-004 | ⚠ |

Legend: ✓ Covered, ⚠ Partial (thresholds pending), ✗ Uncovered

---

## CONTEXT.md Update Block

# CONTEXT.md — Development Pipeline State

## Pipeline Stage
Current Stage: EPIC — Decomposition
Next Stage: MDAP — Module Design and Action Planning
Next Stage: Architecture creation
Next Stage: Folder structure definition

## Canonical Scope Summary
Total In-Scope Requirements: 21 FRs, 5 NFRs
Total Epics Generated: 4

## Assumption & Threshold Status
[ASSUMPTION] Items Carried Forward: 4 (ASSUMPTION-001..004)
[THRESHOLD NEEDED] Items Carried Forward: 7 (THRESHOLD-001..007)
Assumptions Resolved During EPIC Phase: 2 foundational locked (ASSUMPTION-001, ASSUMPTION-002), 2 operationally carried (ASSUMPTION-003, ASSUMPTION-004)

## List of Unresolved [ASSUMPTION] Items
- ASSUMPTION-003: Export formatting specifics unresolved (impacts EPIC-004)
- ASSUMPTION-004: Brand reason taxonomy unresolved (impacts EPIC-002)

## List of Unresolved [THRESHOLD NEEDED] Items
- THRESHOLD-002: Performance reference environment (impacts EPIC-001/003)
- THRESHOLD-003: Log retention duration (impacts EPIC-004)
- THRESHOLD-005: Peak concurrency ceiling (impacts EPIC-003)

## Confirmed Constraints
- Canonical FR/NFR IDs remain immutable across all epics.
- Scope ceiling remains immutable.
- Single persona model retained unless PRD amended.

## Key Dependencies Discovered
External Blocking Dependencies:
- MDAP threshold resolution for performance baseline, retention period, and concurrency envelope.

Out-of-Scope Dependencies:
- None newly introduced; all deferred features remain excluded per PRD Section 7.

---

## 5A — Phase Transition Note (Handoff to MDAP)

### 5A.1 Epic Summary List
- EPIC-001: Ingestion, Canonicalization, and Validation Gating
- EPIC-002: Source Trust and Brand Governance
- EPIC-003: Multi-Source Search, Match Classification, Ranking, and Apostila Routing
- EPIC-004: User Editing, Versioned Traceability, and Export Delivery

### 5A.2 Coverage Matrix Status
- FR coverage: 21/21 mapped
- NFR coverage: 5/5 distributed
- Partial statuses: NFR-001, NFR-005 pending threshold finalization

### 5A.3 Unresolved [ASSUMPTION] & [THRESHOLD NEEDED]
- Unresolved assumptions: ASSUMPTION-003, ASSUMPTION-004
- Unresolved thresholds: THRESHOLD-002, THRESHOLD-003, THRESHOLD-005

### 5A.4 Inter-Epic Dependencies
Hard Blocking:
- EPIC-001 and EPIC-002 both block EPIC-003 start.
- EPIC-003 ranked output blocks EPIC-004 export completion.

Soft:
- EPIC-004 editing/versioning flows can progress in parallel after extraction baseline.

External:
- MDAP capacity/retention/performance benchmark decisions.

### 5A.5 Open Questions / Conflicts
- Clarify categorical eligibility wording in FR-015 vs FR-021.
- Confirm whether to formalize controlled taxonomy for FR-011 in this phase or defer.

---

## Verification Checklist
- [x] FR count assignment: 9 + 5 + 4 + 3 = 21
- [x] NFR count distributed: 5
- [x] No FR duplicated or orphaned
- [x] All ASSUMPTION items flagged
- [x] All THRESHOLD items flagged without invented replacement values for unresolved items
- [x] Dependencies section includes hard/soft/external relationships
- [x] Coverage matrix includes all canonical IDs
- [x] Scope ceiling respected; no new features outside PRD
