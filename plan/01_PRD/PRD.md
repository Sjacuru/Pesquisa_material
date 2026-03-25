# PRD: School Material Price Finder (Brazil MVP)

## PHASE 1 OUTPUT — Sections 1–3

### Section 1: Executive Summary

School Material Price Finder is a Brazil-focused tool for parents, school administrators, and budget-conscious shoppers who need to buy complete school lists from mixed document formats while controlling total spend. It addresses the need to compare required items across trusted retailers and marketplaces, including shipping in the final cost view, so users can make faster purchase decisions with confidence. The measurable success outcome for MVP is that one full school list can be processed and compared within up to 10 minutes.

### Section 2: Problem Statement

#### 2.1 The Problem/Gap

People responsible for school purchases must assemble complete material lists that often include varied item types and specific constraints (for example, exact book identifiers and mandatory item conditions). Today, finding the lowest delivered price for each required item across multiple trusted sellers is a fragmented, repetitive, and error-prone task, especially when lists come from mixed-quality files.

#### 2.2 Who Experiences This Problem

This problem is experienced by school list users in Brazil, especially parents, school administrators, and budget-conscious shoppers managing mandatory purchases for students. They must balance completeness, correctness, and cost while dealing with many item categories and strict requirements that cannot be ignored.

#### 2.3 Why Existing Solutions Are Insufficient

Current shopping behavior typically depends on manual searching across separate websites and marketplaces, with no single consolidated view of the full required list and no consistent way to compare total delivered prices item by item. This makes it difficult to maintain trust, apply item-specific constraints consistently, and verify that the final selection still matches school requirements.

#### 2.4 Consequence of Not Solving

If this problem is not addressed, users continue to spend significant time on repetitive comparison work, risk purchasing incorrect or non-compliant items, and may pay more than necessary due to incomplete price visibility. The result is avoidable financial waste, delayed purchasing decisions, and lower confidence in whether the final cart truly meets the school list.

### Section 3: User Personas

#### PERSONA-001: School List User

- **Role**: Parent, school administrator, or budget-conscious shopper
- **Primary Goal**: Find a complete school material list at the lowest total delivered cost while preserving required item constraints.
- **Primary Pain Point**: School material price comparison is currently manual, time-consuming, and difficult to do accurately across multiple sources.

## PHASE 2 OUTPUT — Sections 4–6

### Section 4: Functional Requirements

#### FR-001 [MUST]: The system shall extract item fields (name, quantity, subject, ISBN when applicable) from typed text and handwritten/image content in uploaded PDF school lists.
**Acceptance Criteria:**
- Given a valid school list PDF containing typed and handwritten/image regions, when extraction runs, then each extracted line item shall include detected category and at least the fields applicable to that category matrix row.
- Given extraction output, when the pipeline stores results, then each extracted field shall include a numeric extraction confidence score in the interval [0.00, 1.00].
- Given PDF parsing fails for any page, when processing completes, then the system shall mark the page as failed and route all affected items to manual review queue (not silent drop).

**Source**: PERSONA-001 goal "find a complete school material list" + PRD Decision Sheet section Data & Extraction / Business Objectives

**Depends On**: None

**Priority**: [MUST] — reason: Extraction is the entry point for all downstream validation and price search.

---

#### FR-002 [MUST]: The system shall apply extraction-confidence gating before canonicalization.
**Acceptance Criteria:**
- Given an extracted field confidence score ≥ 0.90, when gating executes, then the field shall be auto-accepted.
- Given an extracted field confidence score between 0.70 and 0.89 inclusive, when gating executes, then the field shall be routed to manual review before canonicalization.
- Given an extracted field confidence score < 0.70, when gating executes, then the field shall be rejected and a user correction request shall be created.

**Source**: PRD Decision Sheet section Matching & Ranking / Confidence Thresholds

**Depends On**: FR-001

**Priority**: [MUST] — reason: Confidence bands are explicit acceptance gates in the MVP decision rules.

---

#### FR-003 [MUST]: The system shall normalize item quantities and units to the canonical unit set (un, pacote, caixa, g, kg, ml, L, cm, mm).
**Acceptance Criteria:**
- Given extracted units from source lists, when normalization runs, then output units shall be one of: un, pacote, caixa, g, kg, ml, L, cm, mm.
- Given an unrecognized or ambiguous conversion, when normalization runs, then the item shall be routed to review queue and not auto-normalized.
- Given successful normalization, when canonical item is saved, then original value and normalized value shall both be stored.

**Source**: PRD Decision Sheet section Duplicate Detection / Data & Extraction

**Depends On**: FR-001

**Priority**: [MUST] — reason: Unit normalization is required for deduplication and comparable search/ranking.

---

#### FR-004 [MUST]: The system shall deduplicate extracted items using exact-duplicate rules and route probable duplicates to merge review queue.
**Acceptance Criteria:**
- Given two items with same category + name/title + mandatory identifiers + core specs, when deduplication runs, then they shall be merged as exact duplicate.
- Given high text similarity with compatible specs/units but not exact duplicate, when deduplication runs, then items shall be marked probable duplicate and routed to merge review queue.
- Given a manual merge decision, when decision is submitted, then canonical list shall update exactly once and merge resolution shall be logged.

**Source**: PRD Decision Sheet section Duplicate Detection / Validation Gates

**Depends On**: FR-003

**Priority**: [MUST] — reason: Canonical list quality depends on deterministic duplicate handling.

---

#### FR-005 [MUST]: The system shall enforce required (R) fields per category based on the authoritative category matrix.
**Acceptance Criteria:**
- Given an item categorized as Book, when validation runs, then required fields (name, quantity, subject, title, authors, publisher) shall be present.
- Given any category with missing required field(s), when validation runs, then item shall be routed to manual review queue and excluded from auto-accept canonicalization.
- Given all required fields present, when validation runs, then item shall pass the required-field gate.

**Source**: PRD Decision Sheet section Data & Extraction / Category Matrix

**Depends On**: FR-001, FR-002

**Priority**: [MUST] — reason: Category-specific required fields are a core correctness constraint.

---

#### FR-006 [MUST]: The system shall enforce forbidden (F) field/value constraints per category based on the authoritative category matrix.
**Acceptance Criteria:**
- Given a category where attribute is marked F, when validation runs, then populated forbidden attribute/value shall trigger validation failure.
- Given Apostila category, when validation runs, then any ISBN value shall fail validation.
- Given forbidden-field failure, when validation completes, then item shall be routed to review queue and not auto-accepted.

**Source**: PRD Decision Sheet section Data & Extraction / Category Matrix / Apostila Special Case

**Depends On**: FR-005

**Priority**: [MUST] — reason: Forbidden constraints prevent invalid catalog entries and wrong offer matching.

---

#### FR-007 [MUST]: The system shall enforce hard constraints (HC) per category and route HC failures to review queue without auto-accept.
**Acceptance Criteria:**
- Given category HC definitions (for example ISBN required for Book/Dictionary), when validation runs, then HC checks shall execute before search eligibility.
- Given any HC failure, when confidence score is evaluated, then HC failure shall override confidence and item status shall be invalid.
- Given HC failure, when pipeline continues, then item shall be routed to review queue and excluded from candidate ranking until corrected.

**Source**: PRD Decision Sheet section Category Matrix / Matching & Ranking (Hard constraint rule)

**Depends On**: FR-005, FR-006

**Priority**: [MUST] — reason: HC override is explicitly mandated and protects requirement compliance.

---

#### FR-008 [MUST]: The system shall validate and normalize ISBN values by accepting only ISBN-10 or ISBN-13 and stripping hyphens, spaces, and punctuation before comparison.
**Acceptance Criteria:**
- Given an ISBN input containing hyphens/spaces/punctuation, when normalization runs, then output shall contain only normalized ISBN characters.
- Given an ISBN not conforming to ISBN-10 or ISBN-13 format, when validation runs, then item shall fail ISBN validation.
- Given two normalized ISBN strings, when equality check runs, then matching shall use exact string equality only.

**Source**: PRD Decision Sheet section ISBN Rule

**Depends On**: FR-001

**Priority**: [MUST] — reason: ISBN matching rules are mandatory for book/dictionary accuracy.

---

#### FR-009 [MUST]: The system shall require user completion of missing ISBN for Book and Dictionary items before search.
**Acceptance Criteria:**
- Given a Book or Dictionary item with missing ISBN after extraction, when search is requested, then search for that item shall be blocked.
- Given missing ISBN prompt is displayed, when user provides ISBN and validation passes, then item becomes eligible for search.
- Given ISBN remains missing, when processing ends, then item status shall remain review_required.

**Source**: PRD Decision Sheet section ISBN Rule

**Depends On**: FR-008

**Priority**: [MUST] — reason: Decision sheet explicitly requires ISBN completion before search.

---

#### FR-010 [MUST]: The system shall default matching to exact brand and request per-item user approval before cross-brand expansion when fewer than 3 same-brand offers are found.
**Acceptance Criteria:**
- Given same-brand offer count is 3 or more, when matching runs, then system shall keep exact-brand scope and not prompt for brand expansion.
- Given same-brand offer count is less than 3, when matching runs, then system shall create a per-item user prompt before searching other brands.
- Given user denies brand expansion, when matching continues, then only same-brand offers shall remain eligible.

**Source**: PRD Decision Sheet section Brand Substitution Policy

**Depends On**: FR-015

**Priority**: [MUST] — reason: Brand substitution policy is an explicit decision rule for trust and relevance.

---

#### FR-011 [SHOULD]: The system shall record brand-substitution reason codes for every approved cross-brand expansion decision.
**Acceptance Criteria:**
- Given user approves cross-brand expansion, when decision is saved, then a substitution reason code shall be stored.
- Given multiple expansions for one item, when audit data is queried, then each expansion event shall include timestamp and reason code.
- Given no cross-brand expansion, when item audit is queried, then no substitution reason code shall exist for that item.

**Source**: PRD Decision Sheet section Brand Substitution Policy

**Depends On**: FR-010

**Priority**: [SHOULD] — reason: Reason codes improve traceability and tuning but do not block MVP execution.

---

#### FR-012 [MUST]: The system shall onboard websites using domain/HTTPS validation and ReclameAqui-based trust classification.
**Acceptance Criteria:**
- Given operator submits a new website, when onboarding validation runs, then domain format and HTTPS reachability checks shall execute.
- Given onboarding trust check runs, when ReclameAqui status is retrieved, then site shall be classified as allowed, review_required, or blocked.
- Given onboarding validation fails, when workflow completes, then site shall not be activated for search.

**Source**: PRD Decision Sheet section Sources & Trust / Website Onboarding

**Depends On**: None

**Priority**: [MUST] — reason: Search scope quality depends on explicit trust and technical validation gates.

---

#### FR-013 [MUST]: The system shall block explicitly bad-rated websites and activate only allowed or review_required websites for search.
**Acceptance Criteria:**
- Given site classification is blocked (explicitly bad-rated), when search list is built, then site shall be excluded.
- Given site classification is allowed or review_required and not suspended, when search list is built, then site shall be included.
- Given a blocked site exists in operator records, when dashboard displays site status, then status shall be visible as blocked.

**Source**: PRD Decision Sheet section Trust Rule / Website Onboarding

**Depends On**: FR-012

**Priority**: [MUST] — reason: Blocking bad-rated sources is a hard trust rule in MVP.

---

#### FR-014 [SHOULD]: The system shall auto-suspend websites after a configurable failure streak and route suspended sites to review queue.
**Acceptance Criteria:**
- Given a site reaches configured consecutive failure threshold, when health tracking updates, then site status shall change to suspended.
- Given site becomes suspended, when search list is built, then suspended site shall be excluded.
- Given suspension event occurs, when audit is queried, then failure streak count and suspension timestamp shall be present.

**Source**: PRD Decision Sheet section Website Onboarding (Suspend)

**Depends On**: FR-012

**Priority**: [SHOULD] — reason: Auto-suspension improves resilience but initial MVP can operate with manual oversight.

---

#### FR-015 [MUST]: The system shall query all activated websites for each search-eligible item.
**Acceptance Criteria:**
- Given an item passes validation gates, when search starts, then requests shall be sent to every website with status active (allowed or review_required, not suspended).
- Given a website is blocked or suspended, when search starts, then no request shall be sent to that website.
- Given search execution completes, when logs are inspected, then each item shall show attempted website list and per-site result status.

**Source**: PERSONA-001 pain point "price comparison is currently manual and difficult across multiple sources" + PRD Decision Sheet section Sources & Trust / Business Objectives

**Depends On**: FR-007, FR-013

**Priority**: [MUST] — reason: Complete multi-site querying is essential to price-comparison value.

---

#### FR-016 [MUST]: The system shall classify matches by confidence thresholds and hard-constraint outcome before ranking.
**Acceptance Criteria:**
- Given matching confidence ≥ 0.92 and HC satisfied, when classification runs, then candidate status shall be candidate.
- Given matching confidence between 0.75 and 0.91 inclusive, when classification runs, then candidate status shall be review_required.
- Given matching confidence < 0.75 or any HC failure, when classification runs, then candidate status shall be invalid and excluded from ranked results.

**Source**: PRD Decision Sheet section Matching & Ranking / Confidence Thresholds

**Depends On**: FR-007, FR-015

**Priority**: [MUST] — reason: Candidate eligibility thresholds are explicit and non-optional in decision rules.

---

#### FR-017 [MUST]: The system shall rank valid candidates by lowest total delivered price (item price + shipping) and apply seller trust signal.
**Acceptance Criteria:**
- Given multiple valid candidates for one item, when ranking runs, then primary sort key shall be ascending total delivered price = item price + shipping.
- Given a candidate fails HC (wrong ISBN or forbidden specs), when ranking input is prepared, then candidate shall be excluded before sorting.
- Given two candidates have equivalent total delivered price, when tie-break applies, then seller trust signal (marketplace reputation + ReclameAqui classification) shall determine higher rank.

**Source**: PERSONA-001 goal "find a complete school material list at the lowest total delivered cost" + PRD Decision Sheet section Ranking Formula

**Depends On**: FR-013, FR-016

**Priority**: [MUST] — reason: Lowest delivered price with trust-aware filtering is the core product outcome.

---

#### FR-018 [MUST]: The system shall allow users to edit item fields before search and apply edited values as downstream matching overrides.
**Acceptance Criteria:**
- Given extracted item fields are displayed, when user edits a field before search, then updated value shall be saved successfully.
- Given edited and extracted values both exist, when matching executes, then edited value shall be used as authoritative.
- Given user has not edited a field, when matching executes, then extracted/canonical value shall be used.

**Source**: PERSONA-001 pain point "difficult to do accurately across multiple sources" + PRD Decision Sheet section Item Characteristic Editing (enables user correction and accuracy)

**Depends On**: FR-001, FR-004

**Priority**: [MUST] — reason: User correction capability is required to resolve extraction ambiguity before search.

---

#### FR-019 [MUST]: The system shall version item changes with reason and timestamp for every user edit and merge resolution.
**Acceptance Criteria:**
- Given a user edits an item field, when save is confirmed, then an immutable version record with reason and timestamp shall be created.
- Given a merge decision is made in duplicate review, when merge is applied, then merge action with decision reason and timestamp shall be recorded.
- Given item history is requested, when query executes, then versions shall be returned in chronological order.

**Source**: PRD Decision Sheet section Item Characteristic Editing / Validation Gates

**Depends On**: FR-018

**Priority**: [MUST] — reason: Version traceability is necessary for audit, debugging, and pilot validation.

---

#### FR-020 [MUST]: The system shall export results in Excel and CSV including item, selected offer, price, alternatives, confidence, and source URL.
**Acceptance Criteria:**
- Given ranked results are available, when user triggers Excel export, then output file shall include item, selected offer, price, alternatives, confidence, and source URL columns.
- Given ranked results are available, when user triggers CSV export, then output file shall include the same fields as Excel export.
- Given export completes, when sample rows are validated, then each exported item shall map to one selected offer and include alternatives metadata.

**Source**: PERSONA-001 goal "make faster purchase decisions" + PRD Decision Sheet section Export / Validation Gates

**Depends On**: FR-017

**Priority**: [MUST] — reason: Export formats are explicit MVP deliverables for operational use.

---

#### FR-021 [SHOULD]: The system shall route Apostila items to external (non-marketplace) sources only.
**Acceptance Criteria:**
- Given an item category is Apostila, when source routing runs, then marketplace channels shall be excluded.
- Given Apostila item has source tag Reprografia, when search executes, then only configured external sources shall be queried.
- Given Apostila item is incorrectly matched to marketplace offer, when validation runs, then candidate shall be marked invalid.

**Source**: PRD Decision Sheet section Apostila Special Case / Validation Gates

**Depends On**: FR-006, FR-015

**Priority**: [SHOULD] — reason: Special-case routing is important for correctness but can be staged after core search flow.

---

### Section 5: Non-Functional Requirements

#### NFR-001 [MUST]: The system shall process one school material list end-to-end (extract, deduplicate, validate, search, rank, export) within 10 minutes for MVP conditions.
**Acceptance Criteria:**
- Given a list with up to [THRESHOLD NEEDED — maximum items per list not defined in source] items, when user starts processing, then completion time from upload to results display shall be ≤ 10 minutes.
- Given performance test execution, when measured on [THRESHOLD NEEDED — reference hardware/environment not defined in source], then median end-to-end runtime across test runs shall be ≤ 10 minutes.
- Given runtime exceeds 10 minutes, when monitoring evaluates run, then run shall be flagged as SLA breach.

**Source**: PERSONA-001 pain point "time-consuming" manual process → PRD Decision Sheet section Performance Target (measurable success: one list in ≤ 10 minutes) + [THRESHOLD NEEDED — max list size and reference environment are unspecified]

**Priority**: [MUST] — reason: MVP viability depends on keeping user wait time within the stated target.

---

#### NFR-002 [SHOULD]: The system shall maintain structured audit logs for extraction, confidence gating, validation, matching classification, and ranking decisions.
**Acceptance Criteria:**
- Given extraction runs, when item is persisted, then logs shall include extraction confidence and resulting gate status (auto-accept/review/reject).
- Given matching runs, when candidate is classified, then logs shall include confidence band result (candidate/review_required/invalid) and HC pass/fail flag.
- Given ranking output is produced, when audit query runs by item ID, then log trail shall reconstruct decision path from extraction to selected offer.

**Source**: PRD Decision Sheet section Confidence Thresholds / Validation Gates

**Priority**: [SHOULD] — reason: Decision traceability accelerates debugging and pilot-quality validation.

---

#### NFR-003 [SHOULD]: The system shall maintain versioned change history for item edits and merge resolutions with reason and timestamp.
**Acceptance Criteria:**
- Given user edits any item field, when transaction commits, then version history entry with reason and timestamp shall be stored.
- Given duplicate merge is auto or manual, when merge finalizes, then merge decision metadata shall be stored in history.
- Given history is queried by item ID and date range, when response returns, then all relevant entries shall be retrievable in chronological order.

**Source**: PRD Decision Sheet section Item Characteristic Editing / Validation Gates

**Priority**: [SHOULD] — reason: Maintainable operations require reproducible history for corrections and rollback analysis.

---

#### NFR-004 [SHOULD]: The system shall provide observability for website health tracking, failure streak counters, and suspension events.
**Acceptance Criteria:**
- Given site request failures occur, when health metrics update, then per-site consecutive failure streak shall be recorded.
- Given failure streak reaches configured threshold, when suspension triggers, then suspension event with timestamp shall be logged.
- Given operator queries site status, when dashboard/report is generated, then current state (active/suspended/blocked) and last validation result shall be visible.

**Source**: PRD Decision Sheet section Website Onboarding (Recheck/Suspend)

**Priority**: [SHOULD] — reason: Operational maintainability depends on diagnosable source reliability behavior.

---

#### NFR-005 [COULD]: The system shall expose configurable log-retention and query filters for pilot diagnostics.
**Acceptance Criteria:**
- Given audit logs exist, when operator applies filters by item ID/action type/date range, then matching records shall be returned.
- Given retention period configuration changes, when policy is applied, then records older than configured duration shall be purged or archived per configuration.
- Given retention policy value is absent, when deployment validation runs, then system shall raise [THRESHOLD NEEDED — retention duration not defined in source].

**Source**: [ASSUMPTION — Decision Sheet requires rich logging/auditability but does not define retention/query policy thresholds]

**Priority**: [COULD] — reason: Diagnostic flexibility is beneficial but not required to deliver core MVP function.

---

### Section 6: MoSCoW Priority Summary

| Priority | Requirement IDs |
|----------|-----------------|
| MUST | FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-012, FR-013, FR-015, FR-016, FR-017, FR-018, FR-019, FR-020, NFR-001 |
| SHOULD | FR-011, FR-014, FR-021, NFR-002, NFR-003, NFR-004 |
| COULD | NFR-005 |
| WONT | None |

---
## HANDOFF NOTE

This Phase 2 output will be consumed by Phase 3 (PROMPT-3-GOVERNANCE).
All FR/NFR IDs assigned here are CANONICAL and will not change in downstream phases.
Do NOT modify this output after Phase 2 completion.
## PHASE 3 OUTPUT — Sections 7–10

### Section 7: Out of Scope

**Multi-user access control**
- Description: Authentication/authorization for multiple user roles and shared workspaces is excluded from MVP.
- Reason: Explicitly deferred in the Decision Sheet out-of-scope list.

**LGPD/commercial compliance**
- Description: Legal/privacy compliance workflows and commercial operation controls are not part of MVP delivery.
- Reason: Explicitly deferred in the Decision Sheet out-of-scope list.

**Product image matching**
- Description: Image-based product identification or visual similarity matching is excluded.
- Reason: Explicitly deferred in the Decision Sheet out-of-scope list.

**Shipping address localization (uses marketplace default)**
- Description: Per-user address/geolocation shipping customization is not implemented; marketplace default shipping is used.
- Reason: Explicitly deferred in the Decision Sheet out-of-scope list.

**Price history or predictive analytics**
- Description: Historical price tracking, forecasting, or predictive recommendation features are excluded.
- Reason: Explicitly deferred in the Decision Sheet out-of-scope list.

---

### Section 8: Open Questions

**OQ-001**: [ASSUMPTION-001] Persona scope was interpreted as a single generalized School List User.

**Affected Requirements**: FR-012, FR-018, FR-020

**Options**:
- Option A: Keep one generic persona for MVP simplicity (lower analysis overhead, less segmented UX).
- Option B: Split into sub-personas (parent vs school admin) for different workflow defaults (better targeting, higher complexity).

**Required Resolution By**: EPIC

**Notes**: Phase 1 intentionally fixed one persona to avoid over-assumption; this impacts workflow defaults and dashboard prioritization.

---

**OQ-002**: [ASSUMPTION-002] Scope ceiling statement is not explicitly labeled in Phase 1 and was interpreted from Executive Summary sentence 1.

**Affected Requirements**: FR-001 through FR-021, NFR-001 through NFR-005

**Options**:
- Option A: Treat Executive Summary sentence 1 as canonical scope ceiling (fastest continuity).
- Option B: Add an explicit one-line scope ceiling statement at PRD sign-off (clearer governance anchor).

**Required Resolution By**: PRD sign-off

**Notes**: Downstream artifacts currently use the exact sentence from Section 1 to avoid introducing new wording.

---

**OQ-003**: [ASSUMPTION-003] Export formatting details are unspecified (column ordering, locale decimal separators, date/time formatting).

**Affected Requirements**: FR-020

**Options**:
- Option A: Define deterministic export schema and locale in EPIC acceptance criteria (higher interoperability).
- Option B: Keep schema implementation-defined in MVP and validate only required column presence (faster delivery, weaker consistency).

**Required Resolution By**: EPIC

**Notes**: Decision Sheet mandates Excel/CSV fields but not presentation/order specifics.

---

**OQ-004**: [ASSUMPTION-004] Brand substitution reason-code taxonomy is not defined.

**Affected Requirements**: FR-011

**Options**:
- Option A: Use controlled code list (e.g., availability_gap, price_gap, user_preference) with strict validation.
- Option B: Use free-text reason at MVP with later taxonomy migration.

**Required Resolution By**: EPIC

**Notes**: A controlled taxonomy improves audit analytics; free-text accelerates implementation.

---

**OQ-005**: [THRESHOLD-001] Maximum items per list is missing for 10-minute SLA validation.

**Affected Requirements**: NFR-001

**Options**:
- Option A: Define fixed MVP list-size ceiling (e.g., pilot envelope) and test against it.
- Option B: Define tiered SLA by list-size bands.

**Required Resolution By**: PRD sign-off

**Notes**: Without a list-size ceiling, NFR-001 is not objectively testable.

---

**OQ-006**: [THRESHOLD-002] Reference hardware/environment for performance measurement is missing.

**Affected Requirements**: NFR-001

**Options**:
- Option A: Define baseline execution environment (CPU/RAM/network) for SLA tests.
- Option B: Define normalized synthetic benchmark profile with reproducible workload.

**Required Resolution By**: PRD sign-off

**Notes**: Runtime claims are non-comparable without a fixed measurement environment.

---

**OQ-007**: [THRESHOLD-003] Log retention duration is missing.

**Affected Requirements**: NFR-005

**Options**:
- Option A: Set fixed retention (e.g., 90/180 days) for pilot diagnostics.
- Option B: Separate hot retention and cold archive windows.

**Required Resolution By**: EPIC

**Notes**: NFR-005 explicitly marks this as [THRESHOLD NEEDED].

---

**OQ-008**: [THRESHOLD-004] Auto-suspension failure streak threshold is configurable but unspecified.

**Affected Requirements**: FR-014, NFR-004

**Options**:
- Option A: Global threshold for all websites (simpler operations).
- Option B: Per-category or per-domain threshold (better precision, higher maintenance).

**Required Resolution By**: EPIC

**Notes**: Missing threshold affects reliability behavior and false-suspension risk.

---

**OQ-009**: [THRESHOLD-005] Peak concurrent user target for non-degraded operation is missing.

**Affected Requirements**: NFR-001, FR-015

**Options**:
- Option A: Define pilot concurrency target (e.g., single-operator/small cohort).
- Option B: Define stress envelope tiers with separate SLOs.

**Required Resolution By**: MDAP

**Notes**: Concurrency is needed for realistic performance and capacity planning.

---

**OQ-010**: [THRESHOLD-006] Per-website search completion rate target is missing.

**Affected Requirements**: FR-015, NFR-004

**Options**:
- Option A: Define minimum successful query percentage per site.
- Option B: Define minimum successful completion by item across all active sites.

**Required Resolution By**: MDAP

**Notes**: Needed to separate acceptable transient failures from systemic source issues.

---

**OQ-011**: [THRESHOLD-007] Maximum PDF upload size/pages not specified.

**Affected Requirements**: FR-001, NFR-001

**Options**:
- Option A: Set hard file-size/page-count cap for MVP.
- Option B: Define soft cap with asynchronous fallback processing.

**Required Resolution By**: EPIC

**Notes**: Ingestion limits are required for predictable extraction performance.

---

**OQ-012**: [CONFLICT-001] FR-015 queries all activated websites per item, while FR-021 routes Apostila items to external-only sources.

**Affected Requirements**: FR-015, FR-021

**Options**:
- Option A: Clarify FR-015 as “all activated websites eligible for the item category”.
- Option B: Promote Apostila routing rule to MUST and encode as hard pre-filter before query fan-out.

**Required Resolution By**: EPIC

**Notes**: Current wording can be interpreted as unconditional all-site fan-out, contradicting Apostila restrictions.

---

**OQ-013**: [CONFLICT-002] Premise tension exists between “personal use, non-commercial” and “scalable nationally”.

**Affected Requirements**: NFR-001, NFR-004

**Options**:
- Option A: Keep MVP strictly personal-use and defer scale strategy post-MVP.
- Option B: Define a phased path where architecture allows national expansion without changing MVP commercial scope.

**Required Resolution By**: PRD sign-off

**Notes**: This is a governance contradiction in product framing, not a direct FR logic error.

---

### Section 9: Success Metrics

**SM-001**: End-to-end processing SLA compliance

**Measurement**: Percentage of completed runs with upload-to-results time ≤ 10 minutes.

**Baseline**: [UNKNOWN — establish at launch]

**Target**: ≥ 95% of runs within SLA after pilot stabilization.

**Linked to**: NFR-001

**Notes**: Final target validity depends on OQ-005/OQ-006 resolution.

---

**SM-002**: Pilot canonical list generation completion

**Measurement**: Count of pilot PDFs that produce canonical lists with logged merge outcomes.

**Baseline**: [UNKNOWN — establish at launch]

**Target**: 8/8 pilot lists completed successfully.

**Linked to**: FR-001, FR-004, FR-019

**Notes**: Directly derived from validation gate #1.

---

**SM-003**: ISBN validation enforcement accuracy

**Measurement**: Percentage of book/dictionary items that pass only when normalized ISBN is valid and exact-matched.

**Baseline**: [UNKNOWN — establish at launch]

**Target**: 100% enforcement; 0 accepted mismatches.

**Linked to**: FR-008, FR-009

**Notes**: Validates hard-constraint integrity for ISBN-sensitive categories.

---

**SM-004**: Low-confidence routing integrity

**Measurement**: Percentage of extraction/matching results below acceptance bands routed to review/correction (no silent auto-acceptance).

**Baseline**: [UNKNOWN — establish at launch]

**Target**: 100% correct routing.

**Linked to**: FR-002, FR-016, NFR-002

**Notes**: Derived from confidence-threshold governance and validation gate #6.

---

**SM-005**: Trust blocking correctness

**Measurement**: Percentage of explicitly bad-rated domains blocked from search activation.

**Baseline**: [UNKNOWN — establish at launch]

**Target**: 100% blocked-domain exclusion.

**Linked to**: FR-012, FR-013

**Notes**: Derived from validation gate #5 and trust rule.

---

**SM-006**: Search query completion rate by source

**Measurement**: Successful site query responses divided by attempted site queries per run.

**Baseline**: [UNKNOWN — establish at launch]

**Target**: [UNKNOWN — establish at launch]

**Linked to**: FR-015, NFR-004

**Notes**: Numeric target depends on OQ-010 threshold definition.

---

**SM-007**: Ranking validity leakage

**Measurement**: Percentage of final ranked offers later found to violate hard constraints.

**Baseline**: [UNKNOWN — establish at launch]

**Target**: 0% invalid ranked offers.

**Linked to**: FR-007, FR-016, FR-017

**Notes**: Ensures HC override is respected end-to-end.

---

**SM-008**: Export completeness conformance

**Measurement**: Percentage of exported rows containing mandatory fields (item, selected offer, price, alternatives, confidence, source URL).

**Baseline**: [UNKNOWN — establish at launch]

**Target**: 100% conformance across Excel and CSV.

**Linked to**: FR-020

**Notes**: Column-order/format specifics remain open in OQ-003.

---

**SM-009**: Duplicate handling quality

**Measurement**: Share of duplicate decisions judged correct in sampled QA review (auto-merge + manual merge queue outcomes).

**Baseline**: [UNKNOWN — establish at launch]

**Target**: ≥ 95% decision accuracy.

**Linked to**: FR-004, NFR-003

**Notes**: Measures practical quality of exact/probable duplicate logic.

---

**SM-010**: Unit normalization success rate

**Measurement**: Percentage of extracted unit values normalized to canonical set without unresolved ambiguity.

**Baseline**: [UNKNOWN — establish at launch]

**Target**: ≥ 99% normalized or correctly routed to review.

**Linked to**: FR-003

**Notes**: Aligns with canonicalization quality expectations.

---

**SM-011**: Pilot user adoption

**Measurement**: Number of active pilot users running at least one complete list per period.

**Baseline**: [UNKNOWN — establish at launch]

**Target**: [UNKNOWN — establish at launch]

**Linked to**: FR-018, FR-020

**Notes**: User-count target not provided in source inputs.

---

**SM-012**: Cost-saving outcome versus manual workflow

**Measurement**: Relative total delivered price difference between system-selected basket and user manual baseline basket.

**Baseline**: [UNKNOWN — establish at launch]

**Target**: [UNKNOWN — establish at launch]

**Linked to**: FR-015, FR-017

**Notes**: Requires launch baseline instrumentation and manual benchmark definition.

---

**SM-013**: User satisfaction for decision confidence

**Measurement**: Post-run survey score for trust and usefulness of recommendations.

**Baseline**: [UNKNOWN — establish at launch]

**Target**: [UNKNOWN — establish at launch]

**Linked to**: FR-010, FR-013, FR-017

**Notes**: Suggested for pilot governance; exact instrument to be defined later.

---

### Section 10: Granularity Rule & Epic Recommendation

## Section 10: Granularity Rule

**Recommendation**: 6 Epics recommended for Phase 1 development (within 3-10 target range).

### Proposed Epic Groupings

**EPIC-01: PDF Extraction & Canonicalization Pipeline** (estimated 4 weeks)
- Covers: FR-001, FR-002, FR-003, FR-004
- Dependencies: None
- Risk: Medium
- Rationale: Establishes ingestion, confidence gates, normalization, and deduplicated canonical list as the core entry pipeline.

**EPIC-02: Category Validation & ISBN Enforcement** (estimated 3 weeks)
- Covers: FR-005, FR-006, FR-007, FR-008, FR-009
- Dependencies: EPIC-01
- Risk: Medium
- Rationale: Consolidates rule-matrix enforcement and ISBN hard constraints before any search eligibility.

**EPIC-03: Website Onboarding & Trust Governance** (estimated 3 weeks)
- Covers: FR-012, FR-013, FR-014
- Dependencies: None
- Risk: Medium
- Rationale: Defines trusted searchable source set and site lifecycle (activation/block/suspension).

**EPIC-04: Search, Matching, and Price Ranking** (estimated 4 weeks)
- Covers: FR-010, FR-011, FR-015, FR-016, FR-017, FR-021
- Dependencies: EPIC-02, EPIC-03
- Risk: High
- Rationale: Combines cross-site querying, confidence classification, brand-fallback flow, and trust-aware delivered-price ranking.

**EPIC-05: User Editing, Versioning, and Auditability** (estimated 3 weeks)
- Covers: FR-018, FR-019, NFR-002, NFR-003
- Dependencies: EPIC-01
- Risk: Medium
- Rationale: Implements controlled user corrections and full traceability required by governance and pilot validation.

**EPIC-06: Results Delivery, Export, and Performance Observability** (estimated 3 weeks)
- Covers: FR-020, NFR-001, NFR-004, NFR-005
- Dependencies: EPIC-04, EPIC-05
- Risk: Medium
- Rationale: Packages user-facing outputs, SLA instrumentation, and operational diagnostics for MVP acceptance.

### Granularity Assessment

- ✅ All proposed epic scopes are individually estimable within ≤ 5-week windows.
- ⚠️ FR-015 + FR-017 integration may exceed 5 weeks if broad source heterogeneity and trust-signal normalization are larger than expected; split search connectors vs ranking core at EPIC phase if needed.

### Scope Ceiling Confirmation

**Scope Ceiling** (from Section 1 Executive Summary):
"School Material Price Finder is a Brazil-focused tool for parents, school administrators, and budget-conscious shoppers who need to buy complete school lists from mixed document formats while controlling total spend."

**Validation**: All 6 Epics + their FR/NFR remain within scope ceiling. No scope creep detected.

---

### [PRD_HANDOFF_BLOCK]

[PRD_HANDOFF_BLOCK]

FR_IN_SCOPE:
- FR-001: Extract mixed-PDF item fields reliably
- FR-002: Gate extraction by confidence bands
- FR-003: Normalize quantities and canonical units
- FR-004: Deduplicate items and queue merges
- FR-005: Enforce category required field rules
- FR-006: Enforce category forbidden constraints
- FR-007: Apply hard constraints before search
- FR-008: Normalize and validate ISBN formats
- FR-009: Require missing ISBN before search
- FR-010: Request approval for brand fallback
- FR-011: Log cross-brand substitution reason codes
- FR-012: Onboard websites with trust validation
- FR-013: Block bad-rated sites from search
- FR-014: Auto-suspend sites after failures threshold
- FR-015: Query all activated eligible websites
- FR-016: Classify matches via confidence thresholds
- FR-017: Rank by delivered price plus trust
- FR-018: Allow pre-search item field edits
- FR-019: Version edits and merge decisions
- FR-020: Export results to Excel and CSV
- FR-021: Route Apostila to external sources

NFR_MUST_SHOULD:
- NFR-001: [MUST] - Complete list processing within ten minutes
- NFR-002: [SHOULD] - Keep structured decision audit logs
- NFR-003: [SHOULD] - Preserve versioned change history records
- NFR-004: [SHOULD] - Track website health and suspensions
- NFR-005: [COULD] - Configure retention and log filters

SCOPE_CEILING:
"School Material Price Finder is a Brazil-focused tool for parents, school administrators, and budget-conscious shoppers who need to buy complete school lists from mixed document formats while controlling total spend."

PERSONAS:
- PERSONA-001: School List User

UNRESOLVED_ASSUMPTIONS:
- [ASSUMPTION-001]: Persona model is a single generalized School List User without role-specific workflow variants.
- [ASSUMPTION-002]: Executive Summary sentence 1 is treated as the canonical scope ceiling statement.
- [ASSUMPTION-003]: Export schema formatting details (column order, locale decimals, date format) remain undefined.
- [ASSUMPTION-004]: Brand substitution reason-code taxonomy remains undefined.

UNRESOLVED_THRESHOLDS:
- [THRESHOLD-001]: NFR-001 | Missing: Maximum items per list for 10-minute SLA validation.
- [THRESHOLD-002]: NFR-001 | Missing: Reference hardware/environment for performance measurement.
- [THRESHOLD-003]: NFR-005 | Missing: Audit-log retention duration.
- [THRESHOLD-004]: FR-014/NFR-004 | Missing: Consecutive failure count triggering auto-suspension.
- [THRESHOLD-005]: NFR-001/FR-015 | Missing: Peak concurrent users without degradation.
- [THRESHOLD-006]: FR-015/NFR-004 | Missing: Minimum per-website search completion rate.
- [THRESHOLD-007]: FR-001/NFR-001 | Missing: Maximum PDF upload size/page count.

[/PRD_HANDOFF_BLOCK]
