# PRD: School Material Price Finder (Brazil MVP)
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
