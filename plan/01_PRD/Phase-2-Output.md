# PRD: School Material Price Finder (Brazil MVP)
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
