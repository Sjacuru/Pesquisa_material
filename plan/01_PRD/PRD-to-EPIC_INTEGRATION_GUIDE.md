# PRD-to-EPIC INTEGRATION GUIDE
## Consuming Full PRD + CONTEXT.md Without Hallucination Risk

**Project:** School Material Price Finder (Brazil MVP)  
**Date:** March 23, 2026  
**Audience:** EPIC phase analyst/PM generating Epic decomposition  
**Purpose:** Navigate full PRD efficiently while maintaining hallucination prevention guardrails

---

## Overview: Why This Guide Exists

Your PRD is 42 pages (10K+ tokens). The EPIC blueprint is another 20 pages (4-5K tokens). Combined input could exceed 15K tokens, increasing risk of:
- **FR ID hallucination** (Claude forgets or conflates FR numbers)
- **Dependency confusion** (misses blocking relationships or invents circular dependencies)
- **Threshold invention** (LLM guesses reasonable numbers instead of flagging unknowns)
- **Scope creep** (unspoken assumptions become features)

**This guide prevents hallucination by:**
1. **Structuring PRD navigation** — Know exactly where each requirement family lives
2. **Materializing dependencies** — Complete FR-001 to FR-021 dependency map (no guessing)
3. **Locking assumptions** — Explicit sign-off required before EPIC proceeds
4. **Protecting scope** — Out-of-scope list prevents feature creep
5. **Enforcing ID permanence** — No renumbering downstream (GC-8)

---

## Section A: Partitioned PRD Strategy

### How Full PRD is Organized (Approximate Page Ranges)

This guide tells you WHERE to find each requirement family when you need deep context.

| Section | Page Range | Content | When to Reference |
|---------|-----------|---------|---|
| **Executive Summary + Problem** | Pages 1-2 | Scope ceiling, user need, market gap | PRD sign-off validation; scope disputes |
| **Personas** | Page 2 | PERSONA-001 definition | Workflow defaults; UX assumptions |
| **FR-001 to FR-009** | Pages 3-7 | Data Extraction & Validation | Epic 1 decomposition |
| **FR-010 to FR-014** | Pages 8-10 | Brand Handling & Source Trust | Epic 2 decomposition |
| **FR-015 to FR-017** | Pages 11-13 | Search & Ranking | Epic 3 decomposition |
| **FR-018 to FR-021** | Pages 14-16 | User Workflow & Export | Epic 4 decomposition |
| **NFR-001 to NFR-005** | Pages 17-19 | Non-Functional Requirements | All Epics (cross-cutting concerns) |
| **Section 6: MoSCoW Summary** | Page 20 | Priority table (MUST/SHOULD/COULD/WONT) | Epic prioritization |
| **Section 7: Out of Scope** | Pages 21-22 | Explicitly deferred features | Scope dispute resolution; epic boundaries |
| **Section 8: Open Questions** | Pages 23-30 | Unresolved items (OQ-001 through OQ-012+) | ASSUMPTION acknowledgment; threshold decisions |
| **Section 9: Success Metrics** | Pages 31-35 | Post-launch validation (SM-001 through SM-011+) | Epic acceptance criteria alignment |
| **Section 10 & Handoff** | Pages 36-42 | Granularity rule; PRD_HANDOFF_BLOCK | Quick reference; downstream handoff |

### Requirement Family Organization

#### **Data Extraction & Validation Pipeline (FR-001 to FR-009)**
**What:** Intake mixed-format school lists, extract item fields, validate, deduplicate, enforce category rules, normalize units and ISBNs.  
**PRD Sections:** Functional Requirements subsection "Data & Extraction"  
**Key Acceptance Criteria:** Confidence scoring, exact/probable duplicates, required field enforcement, ISBN validation  
**Key Decision Sheet Reference:** "Data & Extraction / Category Matrix"  
**EPIC Implication:** This is likely ONE Epic (or could split into 2 if extraction + validation are separate concerns)

#### **Brand Handling & Source Trust (FR-010 to FR-014)**
**What:** Request brand substitution approval, log reason codes, onboard & validate websites, block bad sites, auto-suspend after failures.  
**PRD Sections:** Functional Requirements subsection "Sources & Trust"  
**Key Acceptance Criteria:** Domain/HTTPS validation, ReclameAqui trust classification, site activation gates  
**Key Decision Sheet Reference:** "Brand Substitution Policy"; "Website Onboarding"  
**EPIC Implication:** ONE Epic (source management is cohesive concern; can parallelize with extraction)

#### **Search & Ranking (FR-015 to FR-017)**
**What:** Query all activated websites, classify matches by confidence, rank by delivered price + trust score.  
**PRD Sections:** Functional Requirements subsection "Matching & Ranking"  
**Key Acceptance Criteria:** Query all active eligible sites (only); confidence classification gates; ranking formula includes trust  
**Key Decision Sheet Reference:** "Matching & Ranking / Confidence Thresholds"  
**EPIC Implication:** ONE Epic (dependent on Extraction + Source Trust completing)

#### **User Workflow & Export (FR-018 to FR-021)**
**What:** Allow pre-search item field edits, version decisions, export results to Excel/CSV, route Apostila items to external sources.  
**PRD Sections:** Functional Requirements subsection "User Interface"  
**Key Acceptance Criteria:** Edit versioning with audit trail, export format consistency, Apostila routing conditions  
**Key Decision Sheet Reference:** "User Interface"; "Apostila Routing Policy"  
**EPIC Implication:** ONE Epic (can proceed in parallel with search, merges final user-facing output)

#### **Non-Functional Requirements (All FRs)**
**What:** Performance (10-min SLA), Auditability (structured logs), History (versioning), Health tracking (website monitoring), Diagnostics (log filters)  
**PRD Sections:** Non-Functional Requirements section  
**Key Acceptance Criteria:** Thresholds for SLA, log structure, retention policies, monitoring dashboards  
**EPIC Implication:** Cross-cutting concerns; distribute across Epics (e.g., FR-001 gets performance target, FR-012 gets health tracking)

---

## Section B: Complete FR-001 to FR-021 Dependency Map

### Overview: Three Critical Execution Chains

Your software has **three major execution chains** that define Epic sequencing:

1. **Item Processing Chain** (FR-001 → ... → FR-020): Main data pipeline
2. **ISBN Validation Chain** (FR-001 → FR-008 → FR-009 → FR-015): Conditional, affects specific item categories
3. **Source Trust Chain** (FR-012 → FR-013 → FR-015): Parallel to Item Processing; merges at search

### Complete Dependency Matrix (All 21 FRs)

```
DEPENDENCY RULES:
- Direct Dependency: FR-X "Depends On" FR-Y (stated in PRD)
- Inferred Dependency: FR-X cannot pass acceptance criteria without FR-Y output
- Conditional Gate: FR-X blocks FR-Y only under specific conditions (e.g., only for Books)
- Parallel: FR-X and FR-Y can execute concurrently; merge later
```

#### **FR-001: Extract mixed-PDF item fields reliably**
```
Depends On: None (entry point)
Blocks: FR-002, FR-003, FR-005, FR-008, FR-018 (direct dependencies in PRD)
Inferred Blocking: FR-004, FR-006, FR-007, FR-009, FR-010, FR-012, FR-015 
  (all downstream; no extracted items = no downstream pipeline)
Conditional: FR-001 does NOT block FR-012, FR-013, FR-014 (source management 
  can proceed in parallel)
Execution Phase: Epic 1 (Data Extraction & Validation)
```

#### **FR-002: Gate extraction by confidence bands**
```
Depends On: FR-001 (extraction must produce items + confidence scores)
Blocks: FR-003, FR-004, FR-005 (low-confidence items routed to manual review, 
  not mainstream pipeline)
Inferred Blocking: FR-006, FR-007, FR-009, FR-015
Execution Phase: Epic 1
Chain: FR-001 → FR-002 → {FR-003, FR-004} (item confidence flow)
```

#### **FR-003: Normalize quantities and canonical units**
```
Depends On: FR-001 (extracted quantity values)
Also Requires: FR-002 (gating ensures only high-confidence items passed)
Blocks: FR-004 (deduplication requires normalized values to match)
Inferred Blocking: FR-005, FR-006, FR-007, FR-015
Execution Phase: Epic 1
Chain: FR-001 → FR-002 → FR-003 → FR-004
```

#### **FR-004: Deduplicate items and queue merges**
```
Depends On: FR-003 (requires normalized quantities for exact/probable matching)
Inferred Dependency: FR-001 (extracted items)
Blocks: FR-005 (canonical list created here; validation runs on canonical list)
Inferred Blocking: FR-006, FR-007, FR-009, FR-015
Acceptance Criteria: Creates ONE canonical deduplicated list; routes ambiguous 
  pairs to manual merge review
Execution Phase: Epic 1
Chain: FR-001 → FR-003 → FR-004 → FR-005
NOTE: This is a critical inferred dependency not explicitly stated in PRD Depends-On; 
  the Decision Sheet says "canonical list created before search/validation flow"
```

#### **FR-005: Enforce category required field rules**
```
Depends On: FR-004 (operates on canonical deduplicated list)
Blocks: FR-006 (required fields must be present before forbidden constraint check)
Inferred Blocking: FR-007, FR-009, FR-015
Acceptance Criteria: Given item category (Book, Uniform, etc.), validate required 
  fields present (e.g., Book requires name, quantity, title, authors, publisher)
Execution Phase: Epic 1
Chain: FR-004 → FR-005 → FR-006 → FR-007
```

#### **FR-006: Enforce category forbidden constraints**
```
Depends On: FR-005 (required fields must pass first)
Blocks: FR-007 (hard constraints applied after business logic validation)
Inferred Blocking: FR-009, FR-015
Acceptance Criteria: Given item category, reject invalid field combinations 
  (e.g., Book cannot have supplier SKU if no brand)
Execution Phase: Epic 1
Chain: FR-005 → FR-006 → FR-007
```

#### **FR-007: Apply hard constraints before search**
```
Depends On: FR-006 (category validation must complete)
Blocks: FR-015 (hard constraints are REQUIRED precondition to search eligibility)
Acceptance Criteria: Apply business rules (e.g., no items without required fields; 
  no items with forbidden constraint violations) before search eligibility determination
Execution Phase: Epic 1
Chain: FR-006 → FR-007 → (merge with FR-012/013/014 output) → FR-015
NOTE: FR-007 is NOT parallel to FR-015; it's a hard precondition.
```

#### **FR-008: Normalize and validate ISBN formats**
```
Depends On: FR-001 (extracted ISBN values)
Blocks: FR-009 (requirement to check ISBN validity before search)
Inferred Blocking: FR-015 (only for Book/Dictionary items)
Acceptance Criteria: Given extracted ISBN string, validate format (10 or 13 digit), 
  normalize to canonical representation
Execution Phase: Epic 1
Chain: FR-001 → FR-008 → FR-009 → (conditional gate) → FR-015
Conditional: Only applies to Book and Dictionary categories
```

#### **FR-009: Require missing ISBN before search**
```
Depends On: FR-008 (ISBN validation must run first)
Blocks: FR-015 (only for Book/Dictionary items; if ISBN missing after FR-008, 
  item blocked from search; must be provided by user before proceeding)
Acceptance Criteria: Given Book/Dictionary item with missing/invalid ISBN after 
  FR-008, block from search until user provides ISBN (via FR-018 edit)
Execution Phase: Epic 1
Chain: FR-008 → FR-009 → (conditional gate to FR-015 for Books only)
Conditional Gate Rule: IF (category = Book OR Dictionary) AND (ISBN = missing/invalid) 
  THEN block from FR-015 search
```

#### **FR-010: Request approval for brand fallback**
```
Depends On: None (source-management parallel track)
Blocks: FR-011 (reason logging for approvals only)
Inferred Blocking: FR-015 (only applies if brand substitution occurs during matching)
Acceptance Criteria: When search would match competitor brand instead of required 
  brand, show approval dialog; log approval decision
Execution Phase: Epic 2 (Brand Handling & Source Trust)
Chain: FR-010 → FR-011 (parallel with Item Processing)
NOTE: FR-010 and FR-021 are NOT dependent (both operate on search phase from 
  different angles; FR-021 narrows source set, FR-010 governs brand expansion 
  within active sources)
```

#### **FR-011: Log cross-brand substitution reason codes**
```
Depends On: FR-010 (log reasons when brand substitution approved)
Blocks: None (logging only; does not gate downstream flow)
Inferred Blocking: None
Acceptance Criteria: When FR-010 approval is used, log reason code (e.g., 
  "competitor_lower_price", "required_brand_unavailable")
Execution Phase: Epic 2
Chain: FR-010 → FR-011
Note: Reason-code taxonomy is [ASSUMPTION-004] — undefined; EPIC must define or defer
```

#### **FR-012: Onboard websites with trust validation**
```
Depends On: None (parallel to extraction pipeline)
Blocks: FR-013 (cannot block bad sites until sites are onboarded)
Blocks: FR-015 (cannot query sites until they are onboarded/validated)
Acceptance Criteria: Given operator submits new website, validate domain format, 
  HTTPS reachability, and ReclameAqui trust status; classify as allowed/review_required/blocked
Execution Phase: Epic 2
Chain: FR-012 → {FR-013, FR-015}
Execution Model: Can run in parallel with Epic 1 (Item Processing); must complete 
  before Epic 3 (Search) can begin
```

#### **FR-013: Block bad-rated sites from search**
```
Depends On: FR-012 (site trust classification must run first)
Blocks: FR-015 (only bad-rated sites blocked; good-rated and review-required sites 
  may be queried)
Acceptance Criteria: Given site classified as blocked by FR-012, ensure it does 
  not appear in FR-015 search query
Execution Phase: Epic 2
Chain: FR-012 → FR-013 → FR-015
Execution Model: Prerequisite to Epic 3
```

#### **FR-014: Auto-suspend sites after failures threshold**
```
Depends On: FR-012 (site must be onboarded before monitoring)
Blocks: FR-015 (indirectly; suspended sites treated as blocked in query set)
Inferred Blocking: FR-016, FR-017 (affects ranking if site was previously queried)
Acceptance Criteria: Monitor each site's search query success rate; if consecutive 
  failures exceed [THRESHOLD-004], auto-suspend and exclude from FR-015 queries
Execution Phase: Epic 2 (operates post-search, feeds back to eligibility)
Chain: FR-012 → FR-014 (monitoring loop)
Threshold Needed: [THRESHOLD-004] Consecutive failure count triggering suspension 
  (e.g., "5 failures in 1 hour")
```

#### **FR-015: Query all activated eligible websites**
```
Depends On: FR-007 (hard constraints gate eligibility)
Also Requires: FR-012, FR-013 (site eligibility determined)
Conditional Requirement: FR-009 (Book/Dictionary items must have valid ISBN)
Blocks: FR-016, FR-017 (search results feed into matching & ranking)
Blocks: FR-020 (results must exist before export)
Blocks: FR-021 (Apostila routing only applies to search results)
Acceptance Criteria: Given item passes FR-007 hard constraints AND (if Book/Dictionary) 
  passes FR-009 ISBN check, query ALL activated eligible websites (those onboarded 
  by FR-012, not blocked by FR-013, not suspended by FR-014)
Execution Phase: Epic 3 (Search & Ranking)
Chain A (Item-driven): FR-007 → FR-015
Chain B (Source-driven): FR-013 → FR-015
Conditional Chain (ISBN-driven): FR-009 → FR-015 (only Books/Dictionaries)
Execution Model: Epic 3 cannot start until Epic 1 (FR-007) AND Epic 2 (FR-013) complete
```

#### **FR-016: Classify matches via confidence thresholds**
```
Depends On: FR-015 (search results must exist)
Blocks: FR-017 (ranking requires match classification)
Blocks: FR-020 (export presents ranked results)
Acceptance Criteria: For each search result from FR-015, classify confidence 
  (exact_match, probable_match, review_required) using thresholds
Execution Phase: Epic 3
Chain: FR-015 → FR-016 → FR-017
```

#### **FR-017: Rank by delivered price plus trust**
```
Depends On: FR-016 (results must be classified)
Also Requires: FR-010, FR-011 (trust score includes brand substitution cost/flag)
Blocks: FR-020 (export presents top-ranked results)
Blocks: FR-019 (versioning operates on ranked output)
Acceptance Criteria: Given classified matches from FR-016, sort by (item_delivered_price 
  + trust_penalty); trust includes site quality (FR-012) + brand substitution flag (FR-010)
Execution Phase: Epic 3
Chain: FR-016 → FR-017 → {FR-019, FR-020}
```

#### **FR-018: Allow pre-search item field edits**
```
Depends On: FR-001 (extracted fields are what gets edited)
Also Enables: FR-009 (user can supply missing ISBN here)
Blocks: FR-019 (versioning tracks edits)
Inferred Blocking: FR-015 (user edits may change search eligibility; re-check constraints)
Acceptance Criteria: Allow user to modify extracted item fields (name, quantity, 
  category, ISBN, etc.) before search is triggered; edit creates version entry
Execution Phase: Epic 4 (User Workflow & Export)
Chain: FR-001 → FR-018 → FR-019
Execution Model: Can proceed in parallel with Epic 1; must merge before final output
```

#### **FR-019: Version edits and merge decisions**
```
Depends On: FR-018 (edits must exist before versioning)
Also Requires: FR-004 (merge decisions made during deduplication)
Blocks: FR-020 (export presents final versioned list)
Inferred Blocking: FR-017 (ranking may differ if user edits change item specs)
Acceptance Criteria: Maintain audit trail of all edits (pre-search) and merge 
  decisions (deduplication); each version linked to user action + timestamp
Execution Phase: Epic 4
Chain: FR-018 → FR-019 → FR-020
```

#### **FR-020: Export results to Excel and CSV**
```
Depends On: FR-017 (final ranked results needed)
Also Requires: FR-019 (versioned edits included in export)
Blocks: None (terminal output)
Inferred Blocking: None
Acceptance Criteria: Given final ranked list from FR-017 + versioned edits from 
  FR-019, export to Excel (.xlsx) and CSV (.csv) with consistent column structure
Execution Phase: Epic 4
Chain: FR-017 → FR-020 (user-facing deliverable)
NOTE: Export formatting details [ASSUMPTION-003] undefined; MDAP phase defines 
  column order, locale, date format
```

#### **FR-021: Route Apostila to external sources**
```
Depends On: FR-015 (search results exist)
Inferred Blocking: None (routing applies post-search, doesn't block)
Blocks: None (terminal decision; routes items to external-only source list)
Acceptance Criteria: Given search result for Apostila item, route to external-sources-only 
  list (do not rank against internal marketplace results)
Execution Phase: Epic 3 or 4 (post-search categorization)
Chain: FR-015 → FR-021 (downstream categorization)
NOTE: FR-021 does NOT depend on FR-010; both operate independently. FR-021 narrows 
  source set, FR-010 governs brand within remaining set. For Apostila, practical 
  order is FR-021 first, then FR-010 applies only within restricted source set.
```

---

### Dependency Map Summary Table

| FR | Depends On | Blocks | Chain Position | Epic Assignment | Conditional? |
|---|---|---|---|---|---|
| FR-001 | None | FR-002, FR-003, FR-005, FR-008, FR-018 | Entry | Epic 1 | No |
| FR-002 | FR-001 | FR-003, FR-004, FR-005 | Early | Epic 1 | No |
| FR-003 | FR-001 | FR-004 | Mid-early | Epic 1 | No |
| FR-004 | FR-003 | FR-005 | Mid-early | Epic 1 | No |
| FR-005 | FR-004 | FR-006 | Mid | Epic 1 | No |
| FR-006 | FR-005 | FR-007 | Mid | Epic 1 | No |
| FR-007 | FR-006 | FR-015 | Late-early | Epic 1 | No |
| FR-008 | FR-001 | FR-009 | Early | Epic 1 | No |
| FR-009 | FR-008 | FR-015 | Mid | Epic 1 | Yes (Books/Dicts only) |
| FR-010 | None | FR-011 | Parallel | Epic 2 | No |
| FR-011 | FR-010 | None | Parallel | Epic 2 | No |
| FR-012 | None | FR-013, FR-015 | Parallel Entry | Epic 2 | No |
| FR-013 | FR-012 | FR-015 | Parallel Mid | Epic 2 | No |
| FR-014 | FR-012 | FR-015 (indirect) | Parallel Mid | Epic 2 | No |
| FR-015 | FR-007, FR-013, [FR-009] | FR-016, FR-017, FR-020, FR-021 | Junction | Epic 3 | Yes (ISBN conditional) |
| FR-016 | FR-015 | FR-017, FR-020 | Mid | Epic 3 | No |
| FR-017 | FR-016 | FR-020, FR-019 | Late | Epic 3 | No |
| FR-018 | FR-001 | FR-019 | Parallel | Epic 4 | No |
| FR-019 | FR-018, FR-004 | FR-020 | Late Parallel | Epic 4 | No |
| FR-020 | FR-017, FR-019 | None | Terminal | Epic 4 | No |
| FR-021 | FR-015 | None | Terminal | Epic 3/4 | No |

---

### Critical Blocking Chains (Simplified for Epic Planning)

#### **Main Item Processing Chain** (Serial; blocks each other)
```
FR-001 (Extract)
  ↓
FR-002 (Gate by confidence)
  ↓
FR-003 (Normalize units)
  ↓
FR-004 (Deduplicate)
  ↓
FR-005 (Required fields)
  ↓
FR-006 (Forbidden constraints)
  ↓
FR-007 (Hard constraints)
  ↓
FR-015 (Query websites)
  ↓
FR-016 (Classify matches)
  ↓
FR-017 (Rank by price + trust)
  ↓
FR-020 (Export results)
```
**Effort:** ~8-12 weeks (Epic 1 + Epic 3 combined)  
**Critical Path:** Do not parallelize this chain; each step depends on previous output.

#### **ISBN Validation Chain** (Conditional; only Books/Dictionaries)
```
FR-001 (Extract)
  ↓
FR-008 (Normalize ISBN)
  ↓
FR-009 (Require missing ISBN)
  ↓
[Gate to FR-015 only if ISBN valid for Books/Dicts]
```
**Effort:** ~1-2 weeks (subset of Epic 1)  
**Conditional:** Does not apply to non-Book items.

#### **Source Trust Chain** (Parallel to Item Processing; merges at search)
```
FR-012 (Onboard websites)
  ↓
FR-013 (Block bad sites)
  ↓
[Feed eligible site list to FR-015]

Parallel:
FR-010 (Brand approval)
  ↓
FR-011 (Log reason codes)
  ↓
[Feed trust score to FR-017 ranking]

FR-014 (Auto-suspend)
  ↓
[Continuous monitoring; affects site eligibility for FR-015]
```
**Effort:** ~4-6 weeks (Epic 2)  
**Execution Model:** Parallel with Epic 1; must complete before Epic 3 begins.

#### **User Workflow Chain** (Parallel; merges before final output)
```
FR-001 (Extract)
  ↓
FR-018 (Allow edits)
  ↓
FR-019 (Version decisions)
  ↓
[Merge with FR-017 output for FR-020 export]
```
**Effort:** ~2-3 weeks (Epic 4)  
**Execution Model:** Can proceed in parallel with Epics 1-3; merges final output.

---

## Section C: Hallucination Prevention Tactics

### Tactic 1: Structured Block Consumption

**How to prevent:** Claude hallucinating FR numbers or conflating requirements.

**Protocol:**
1. Before decomposing any Epic, copy the [FR_IN_SCOPE] block from CONTEXT.md
2. Cross-reference each Epic's FRs against this master list
3. If FR ID appears in your Epic that's NOT in the master list, STOP and escalate

**Example:**
```
WRONG: "Epic 1 will implement FR-001, FR-002, FR-003, FR-004, FR-005, 
         FR-012 (brand approval)"
RIGHT: Cross-check against [FR_IN_SCOPE]. FR-012 is in Epic 2 (Source Trust), 
        not Epic 1. Correct to FR-001 through FR-009.
```

### Tactic 2: Dependency Map Reference

**How to prevent:** Claude inventing dependencies or missing blockers.

**Protocol:**
1. For each Epic, identify which FRs it owns (from Section A)
2. Check the Complete Dependency Matrix (Section B) for all dependencies
3. Document: "Epic [N] owns FR-X, which depends on FR-Y (owned by Epic [M])"
4. If circular dependency appears, escalate to product owner

**Example:**
```
WRONG: "Epic 1 owns FR-001 through FR-009. FR-009 has no external dependencies."
RIGHT: "Epic 1 owns FR-001 through FR-009. FR-009 depends on FR-008 (within Epic 1). 
        FR-009 blocks FR-015 (Epic 3), creating inter-Epic dependency. 
        Epic 3 cannot start until Epic 1 completes FR-009."
```

### Tactic 3: Threshold Gating

**How to prevent:** Claude inventing threshold values for unresolved items.

**Protocol:**
1. Identify all [THRESHOLD NEEDED] items in CONTEXT.md Handoff Block
2. For each threshold, note which FR(s) it affects
3. During Epic decomposition, STOP if you encounter FR acceptance criteria requiring a threshold
4. Document: "BLOCKED — THRESHOLD-XXX must be resolved before this Epic can proceed"
5. Do NOT invent a number

**Example:**
```
WRONG: "FR-001 acceptance criteria requires processing max 200 items in 10 minutes 
        (reasonable MVP limit)"
RIGHT: "FR-001 acceptance criteria requires processing [THRESHOLD-001] items in 10 minutes. 
        THRESHOLD-001 is unresolved and assigned to PRD sign-off phase. 
        This Epic cannot finalize acceptance criteria until THRESHOLD-001 is provided."
```

### Tactic 4: Assumption Acknowledgment

**How to prevent:** Claude assuming sub-personas or undefined taxonomies that weren't in PRD.

**Protocol:**
1. Note all [ASSUMPTION] items from CONTEXT.md Handoff Block before Epic begins
2. If Epic decomposition requires NEW assumptions (e.g., "parents need mobile app"), STOP
3. Document: "This Epic requires [NEW ASSUMPTION]: X. This must be validated against PRD or PRD must be amended."
4. Do NOT introduce assumptions silently; escalate to product owner

**Example:**
```
WRONG: "Epic 4 (User Workflow) will support both parent and admin roles with 
        different dashboard layouts (reasonable distinction)."
RIGHT: "ASSUMPTION-001 explicitly limits scope to single persona (School List User). 
        Epic 4 decomposition must apply uniform workflow defaults. If sub-personas 
        are needed, ASSUMPTION-001 must be resolved and PRD amended."
```

### Tactic 5: Scope Creep Detection

**How to prevent:** Claude adding features not in PRD Scope Ceiling.

**Protocol:**
1. Before Epic decomposition, review Section 7 (Out of Scope) from PRD
2. For each Epic user story or task, verify it traces back to an FR in [FR_IN_SCOPE]
3. If a story references capability NOT in [FR_IN_SCOPE], STOP and escalate
4. Use this phrase: "Feature X is not in Scope Ceiling (CONTEXT.md) and is listed as out-of-scope in PRD Section 7"

**Example:**
```
WRONG: "Epic 2 should include API endpoints for third-party integrations 
        (reasonable future feature)."
RIGHT: "API for third-party integrations is explicitly listed in PRD Section 7 (Out of Scope). 
        Epic 2 will NOT include this. If needed, PRD must be amended."
```

### Tactic 6: ID Permanence Enforcement (GC-8)

**How to prevent:** Renumbering, merging, or splitting FRs downstream.

**Protocol:**
1. When decomposing FR into user stories/tasks, DO NOT create new sub-IDs like "FR-001.1" or "FR-001a"
2. Use FR ID as-is (FR-001) and reference it consistently
3. If decomposition reveals an FR is too large, DO NOT split the FR
4. Instead, document in Epic: "FR-001 requires N sub-tasks (T-001, T-002, ...) but FR ID remains FR-001"

**Example:**
```
WRONG: 
  FR-001.1 Extract text fields
  FR-001.2 Extract image fields
  FR-001.3 Validate field count
  
RIGHT:
  FR-001 [EPIC 1, STORY 1-3]: Extract mixed-PDF item fields reliably
    - T-001: Extract text fields from PDF
    - T-002: Extract image fields from PDF
    - T-003: Validate extracted field count
```

---

## Section D: EPIC Phase Checkpoints

### Checkpoint 1: Pre-Epic Gate (Before Epic Decomposition Starts)

**Verify:**
- [ ] CONTEXT.md [THRESHOLD_ASSUMPTION_RESOLUTION_GATE] is CLEAR (all boxes checked, signed off)
- [ ] ASSUMPTION-001 (single persona) is resolved (Option A or B recorded)
- [ ] THRESHOLD-001 (max items per list) is decided by product owner
- [ ] THRESHOLD-007 (max PDF upload size) is decided by product owner
- [ ] No new scope has been introduced since PRD sign-off

**If any item is incomplete:** Do NOT proceed to Epic decomposition. Escalate to product owner and wait for gate clearance.

**Gate Status:** ☐ BLOCKED / ☐ **CLEARED**

---

### Checkpoint 2: During Epic Decomposition (For Each Epic)

**For Epic 1 (Data Extraction & Validation), verify:**
- [ ] Owns FR-001 through FR-009 (check against [FR_IN_SCOPE])
- [ ] Dependency chain is correct: FR-001 → FR-002 → FR-003 → FR-004 → FR-005 → FR-006 → FR-007
- [ ] FR-008 → FR-009 is a conditional branch (only for Books/Dictionaries)
- [ ] No FR from Epic 2 or 3 is mentioned
- [ ] All FRs reference their source (PRD section) explicitly
- [ ] Acceptance criteria do not invent values for [THRESHOLD-001] (max items)

**For Epic 2 (Brand Handling & Source Trust), verify:**
- [ ] Owns FR-010 through FR-014 (check against [FR_IN_SCOPE])
- [ ] Dependency chain is correct: FR-012 → {FR-013, FR-014} (parallel)
- [ ] FR-010 → FR-011 (parallel track)
- [ ] Clarifies: "FR-010 and FR-021 are NOT dependent"
- [ ] Acceptance criteria flag [THRESHOLD-004] (failure count) as unresolved if used
- [ ] Documents: "This Epic can execute in parallel with Epic 1; must complete before Epic 3"

**For Epic 3 (Search & Ranking), verify:**
- [ ] Owns FR-015, FR-016, FR-017, FR-021 (check against [FR_IN_SCOPE])
- [ ] Documents: "Epic 3 cannot start until Epic 1 (FR-007) and Epic 2 (FR-013) complete"
- [ ] FR-015 acceptance criteria document conditional gates:
  - "Query all activated eligible websites (from FR-012/013/014)"
  - "For Book/Dictionary items, only if FR-009 ISBN check passes"
- [ ] FR-017 ranking includes trust score (from FR-012)
- [ ] FR-021 routing is documented independently (not dependent on FR-010)
- [ ] Acceptance criteria reference [THRESHOLD-006] (per-site completion rate) if used; flag as unresolved

**For Epic 4 (User Workflow & Export), verify:**
- [ ] Owns FR-018, FR-019, FR-020 (check against [FR_IN_SCOPE])
- [ ] Documents: "Can execute in parallel with Epics 1-3; merges final output"
- [ ] FR-018 enables FR-009 ISBN supply (cross-references Epic 1)
- [ ] FR-019 versioning tracks both edits (FR-018) and merge decisions (FR-004)
- [ ] FR-020 export references [ASSUMPTION-003] (formatting undefined); defers to MDAP
- [ ] Acceptance criteria do not invent export format details

---

### Checkpoint 3: Inter-Epic Dependency Validation

**Create an Epic dependency matrix:**

| Epic | Owns FRs | Depends On | Blocks | Can Parallelize With |
|---|---|---|---|---|
| Epic 1 | FR-001–009 | None (entry) | FR-007 output needed for Epic 3 | Epic 2, Epic 4 |
| Epic 2 | FR-010–014 | None (entry) | FR-013 output needed for Epic 3 | Epic 1, Epic 4 |
| Epic 3 | FR-015–017, FR-021 | Epic 1 (FR-007), Epic 2 (FR-013) | Final search results | Epic 4 |
| Epic 4 | FR-018–020 | Epic 1 (FR-001, FR-004) | Final export output | Epic 1, Epic 2, (merge with 3) |

**Verify:**
- [ ] No circular dependencies (e.g., Epic A → Epic B → Epic A)
- [ ] All blocking relationships documented in Epic stories
- [ ] Parallelization plan is clear (which Epics can run concurrently)
- [ ] Critical path identified (Epic 1 → Epic 3 → Epic 4 is slowest, ~14+ weeks)

---

### Checkpoint 4: Post-Epic Validation (Before Handoff to MDAP)

**Verify:**
- [ ] All 21 FRs are assigned to exactly ONE Epic (no orphans, no duplicates)
- [ ] All 5 NFRs are distributed across Epics (cross-cutting concerns)
- [ ] No FR IDs were renumbered, merged, or split (GC-8 enforced)
- [ ] All [ASSUMPTION] items from CONTEXT.md are acknowledged in Epic narrative
- [ ] All [THRESHOLD] items are flagged or resolved in Epic acceptance criteria
- [ ] Scope Ceiling remains immutable (no out-of-scope features added)
- [ ] Epic priorities align with MoSCoW tiers (MUST FRs in foundational Epics)

**Sign-Off:** 
- [ ] EPIC phase analyst: _________________ Date: _______
- [ ] Product Owner: _________________ Date: _______

---

## How to Use This Guide in Your EPIC Prompt

When you're ready to generate EPIC decomposition:

### **Include in EPIC Prompt:**
1. Full PRD (all 42 pages) — for narrative context
2. CONTEXT.md — for quick reference blocks
3. This entire PRD-to-EPIC-INTEGRATION-GUIDE.md — for dependency map and tactics
4. PRD Section 7 (Out of Scope) — to prevent feature creep

### **Do NOT Include:**
- Redundant summaries or condensed versions
- Speculative thresholds or assumptions
- Generated Epic examples (start fresh)

### **Instruct Claude (EPIC phase):**
"Use Section B (Complete Dependency Map) to decompose 21 FRs into 3-4 Epics. Maintain FR ID integrity (GC-8). For each Epic, reference the dependency chains and identify which [THRESHOLD] items block acceptance criteria. Do not invent thresholds; flag them as [UNRESOLVED]. Apply Hallucination Prevention Tactics (Section C) throughout. Complete Checkpoints (Section D) before finalizing Epic structure."

---

**Document Status:** ✅ COMPLETE  
**Version:** PRD-to-EPIC Integration v1.0  
**Next Phase:** EPIC generation (with this guide as primary reference)  
**Questions?** Reference CONTEXT.md (THRESHOLD_ASSUMPTION_RESOLUTION_GATE) for blockers; escalate to product owner.