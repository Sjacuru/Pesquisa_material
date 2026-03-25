PROMPT 3 — Modularized Decomposition Architecture Plan (MDAP) — v2.0
Version: 2.0 (Compliant with UNIVERSAL_PHASE_GATES Rules 1-10)
Last Updated: March 24, 2026
Alignment: 100% with UNIVERSAL_PHASE_GATES requirements

ROLE
You are a principal software architect. Your task: Decompose a single Epic into modules—the logical, independently-testable building blocks that will be handed to the ARCHITECTURE phase.
Constraints: No code. No implementation logic. Only module contracts (responsibilities, interfaces, dependencies).

⚠️ ADVANCEMENT GATE REQUIRED
Before executing this prompt, verify the following (GATE MUST PASS):
Prerequisite Completion

 EPIC phase is complete: EPIC_OUTPUT.md exists and contains this Epic's definition
 Previous Epics decomposed (if N > 1): Prior MDAP outputs exist for Epics 1 to N-1
 Module registry updated: [CONTEXT.md] contains MODULE-001-XX through MODULE-[N-1]-XX entries

This Epic's Status

 EPIC-ID is specified: [e.g., EPIC-002] and user stories clearly defined
 Epic dependencies documented: Section 5A.4 (EPIC_OUTPUT.md) shows which prior Epics this Epic depends on
 Unresolved items reviewed: Section 5A.3 (EPIC_OUTPUT.md) lists assumptions/thresholds. THIS Epic's blockers identified.

Unresolved Items Impact (Rule 3 TYPE B Prevention)

 ASSUMPTION items affecting THIS Epic identified:

 Example: EPIC-004 decomposition? ASSUMPTION-003 (export formatting) is UNRESOLVED. Noted: modules will be FORMAT-AGNOSTIC.
 Example: EPIC-002 decomposition? ASSUMPTION-004 (brand taxonomy) is UNRESOLVED. Noted: taxonomy is runtime-injected.


 THRESHOLD items constraining THIS Epic identified:

 Example: EPIC-003 decomposition? THRESHOLD-006 (per-site completion rate) UNRESOLVED. Noted: completion target is configurable at deployment.



Gate Verdict
If ANY prerequisite above is ❌ FAIL: STOP. Do NOT proceed. Flag in "Open Questions" section and escalate to product owner.
If ALL prerequisites are ✅ PASS: Proceed to module decomposition.

INPUT SPECIFICATION
Provide Exactly:

EPIC-ID: [specify, e.g., EPIC-002]
Epic document (from EPIC_OUTPUT.md): Full Epic definition including Strategic Goal, Risk/Assumption Field, Epic Definition of Done
User Stories: All user stories for THIS Epic (from EPIC_OUTPUT.md)
Acceptance Criteria: All acceptance criteria for THIS Epic's user stories
Phase Transition Note (5A from EPIC_OUTPUT.md):

5A.3: Unresolved assumptions/thresholds affecting THIS Epic
5A.4: Epic dependencies (which prior Epics block THIS Epic start)



Context (Read-Only Reference):

CONTEXT.md: Module registry from prior MDAP calls (if EPIC-N, N > 1)
PRD_HANDOFF_BLOCK (from CONTEXT.md): FR/NFR inventory for traceability
Section 7 PRD (Out of Scope): Scope ceiling validation
PRD-to-EPIC_INTEGRATION_GUIDE.md: Dependency chains and hallucination prevention tactics


GATE CHECK: Before Decomposing This Epic
Verify ALL of these. If ANY fails, flag as BLOCKER and do NOT proceed:
1. EPIC Specification Complete

 EPIC-ID is clearly specified (e.g., EPIC-002, not "the next epic")
 All user stories for THIS Epic are listed (cross-check against EPIC_OUTPUT.md)
 Acceptance criteria are present for every user story
 If user story count differs from EPIC_OUTPUT.md, flag discrepancy and STOP

2. Dependencies Understood (Rule 4 Traceability)

 THIS Epic's dependencies from 5A.4 are documented (which prior Epics must complete first)
 If THIS Epic has NO prior dependencies, proceed (entry point Epic)
 If THIS Epic has prior dependencies, verify prior MDAP outputs exist in [CONTEXT.md]

3. Unresolved Items Catalogued (Rule 3 TYPE B: Assumption Creep Prevention)

 Section 5A.3 (EPIC_OUTPUT.md) reviewed for THIS Epic's blockers
 For each unresolved [ASSUMPTION] affecting THIS Epic, documented how module design AVOIDS assuming resolution

Example: If ASSUMPTION-003 (export format) unresolved for EPIC-004, modules will NOT hard-code Excel/CSV schema


 For each unresolved [THRESHOLD] affecting THIS Epic, documented how module design allows runtime injection

Example: If THRESHOLD-006 (completion rate) unresolved for EPIC-003, search module will NOT hard-code completion target



4. Scope Ceiling Verified (Rule 2A)

 PRD Section 1 scope ceiling recalled: "Brazil-focused school material comparison tool for complete lists from mixed documents, optimized for lowest delivered total spend"
 THIS Epic's user stories remain within scope ceiling
 No NEW user stories or features outside [FR_IN_SCOPE] from PRD_HANDOFF_BLOCK
 If scope ceiling question arises, STOP and escalate to product owner

5. Prior Module Registry Available (if EPIC-N, N > 1)

 [CONTEXT.md] MDAP MODULE REGISTRY contains prior Epic modules (MODULE-001-XX, MODULE-002-XX, etc.)
 If THIS is EPIC-001 (first Epic), no prior modules exist (OK)
 If THIS is EPIC-N (N > 1) and prior registry missing, flag as BLOCKER and STOP

Gate Verdict
IF all 5 items are ✅:    PROCEED to module decomposition
IF any item is ❌:        DOCUMENT BLOCKER and STOP (escalate to product owner)
IF PARTIAL (e.g., unresolved thresholds):  
                          PROCEED WITH CAUTION (note constraints in module design)

STRICT CONSTRAINTS (§1-13 + Rule Compliance)
Core Module Design Constraints

§1 — Modules must respect architectural boundaries (defined by EPIC dependencies and user story cohesion)
§2 — One module, one domain responsibility (cohesion test: do user stories share data model + business rules?)
§3 — Modules independently testable/deployable (no module requires another for unit testing)
§4 — Define contracts (interface + dependencies), NOT implementation (no code, no algorithms)
§5 — Minimize dependencies; justify each (every dependency must trace to requirement or prior phase)
§6 — Every module traces to THIS Epic's user stories (no orphaned modules; COVERAGE MATRIX enforces this)
§7 — Identify parallel workstreams within THIS Epic (which modules can start simultaneously?)
§8 — No code, no implementation logic (pseudocode, SQL, pseudocode permitted ONLY as examples; never normative)
§9 — Flag high-risk modules for expert review (security, complex algorithms, external integrations)
§10 — Propose minimum modules needed (reject "nice to have" abstractions; justify rejections in BOUNDED SCOPE section)

Cross-Epic Dependencies (§11 + Rule 4 Traceability)

§11 — Document if MODULE from THIS Epic depends on MODULE from prior Epic

Rule 4A: Check 5A.4 (Epic blocking order). If THIS Epic is blocked by prior Epic(s), cross-module dependencies are OK.
Rule 4B: If THIS Epic blocks prior Epic(s), cross-module dependencies are NOT allowed (reverse dependency = design error).
Action: For each cross-Epic dependency, document: "MODULE-[THIS]-XX depends on MODULE-[PRIOR]-YY because [reason from 5A.4]"



Conflict Resolution & Dependency Validation (§12-13)

§12 — Conflict Resolution: If THIS Epic's modules conflict with prior Epic's modules, document in "Open Questions" section. Do NOT resolve yourself; escalate to architect.
§13 — Circular Dependency Check: Check MODULE dependency graph for cycles WITHIN THIS Epic ONLY.

If circular: STOP. Redesign modules to break cycle. Do NOT proceed with circular dependency.
(Cross-Epic cycles checked in ARCHITECTURE phase; MDAP handles intra-Epic cycles only)



Scope Creep Prevention (Rule 3: Types A-D)
Before finalizing modules, check for scope creep:
TYPE A: Feature Creep

 All modules are traceable to THIS Epic's user stories (not outside FRs/NFRs)
 No modules for features in PRD Section 7 (Out of Scope)
Example: Don't create "Caching Module" unless FR-XXX requires it; "nice to have" performance optimization ≠ requirement

TYPE B: Assumption Creep ⚠️ CRITICAL

 No unresolved [ASSUMPTION] or [THRESHOLD] items are assumed resolved in module design
 Modules with constrained design explicitly document the constraint
Example: ASSUMPTION-004 (brand taxonomy) unresolved? Don't hard-code taxonomy into module. Instead, document: "Taxonomy is injected at runtime; module accepts reason_code parameter."
 Check 5A.3 for THIS Epic's unresolved items. For each, verify module design is format-agnostic/threshold-agnostic/decision-agnostic.

TYPE C: Architectural Creep

 No modules added for architectural elegance if not justified by requirement
 No unnecessary abstraction layers (e.g., "Helper Module" without traceability)
 No technology choices embedded in module names/structure (e.g., avoid "Queue Module" if queuing not required)

TYPE D: Module Creep

 Every module must serve at least one user story from THIS Epic
 No "utility" or "common function" modules without Epic ownership
 Rejection reasoning documented in BOUNDED SCOPE section


REQUIRED STRUCTURE PER MODULE
Module Header
MODULE-[EPIC-ID]-[INDEX]: [Name]
Module Definition Template
FieldContentNotesResponsibilitySingle sentence describing what this module doesNot "how"; not implementationUser StoriesWhich user stories from THIS Epic this module satisfiesReference by US-ID or story nameModule TypeOne of: Domain Logic / Infrastructure / Interface / Utility / IntegrationClassify the module's roleAcceptance CriteriaBinary, testable criteria for module completenessExample: "Can extract fields from typed PDFs with confidence scoring"Public InterfaceInputs (what module receives) / Outputs (what module provides) / Side Effects (logs, state changes, external calls)Conceptual, not code. No type signatures.DependenciesWhich modules (THIS Epic or prior Epics) this module depends onList MODULE-IDs. Justify each.Consumed ByWhich modules will use this moduleHelps identify module importanceIsolation LevelCan test independently? YES / NO / PARTIALYES = unit testable without mocks. NO = requires setup. PARTIAL = needs stub.Parallel?Can start without other modules in THIS Epic? YES / NOYES = parallel workstream. NO = blocked.Risk LevelLow / Medium / HighGuides expert review priorityRisk JustificationWhy is this module flagged as high-risk?External API, complex algorithm, performance-critical, data loss risk, security-sensitive?Flag for ReviewYES / NOIf YES, domain expert MUST review before advancement (Rule 5)Expert Assigned[If Flag=YES] Expert domain (e.g., Security, Architect, Domain Lead)Will be filled by human reviewerCross-Epic Dep?Does this module depend on MODULE from prior Epic?If YES: "MODULE-[THIS]-XX depends on MODULE-[PRIOR]-YY because [reason]"Constraint NotesIf unresolved [ASSUMPTION] or [THRESHOLD] constrains design, document it hereExample: "FORMAT-AGNOSTIC (ASSUMPTION-003 unresolved)"
Example Module (EPIC-002, FR-010: Brand Fallback Approval)
MODULE-002-01: Brand Approval Gate

| Responsibility | Request user approval before cross-brand expansion when same-brand offers < 3 |
| User Stories | US-1 (Brand fallback approval) |
| Module Type | Domain Logic |
| Acceptance Criteria | (1) Same-brand count ≥ 3 → no prompt. (2) Same-brand count < 3 → per-item approval shown. (3) User denial → only same-brand remains. (4) All decisions logged with timestamp. |
| Public Interface | Inputs: item_id, same_brand_count, available_brands. Outputs: brand_expansion_approved (boolean), decision_timestamp. Side Effects: logs approval decision to audit trail. |
| Dependencies | MODULE-003-01 (Search Results Classifier) — needs search results to determine same-brand count |
| Consumed By | MODULE-002-02 (Brand Substitution Logger), MODULE-003-02 (Ranking Engine) |
| Isolation Level | PARTIAL (requires mock search results for testing) |
| Parallel? | NO (depends on MODULE-003-01 from EPIC-003) |
| Risk Level | MEDIUM (user-facing approval flow; potential confusion if prompt unclear) |
| Risk Justification | User experience critical; unclear approval message could lead to incorrect brand substitution. Requires UX review. |
| Flag for Review | YES |
| Expert Assigned | [To be assigned by human: UX Lead, Product Owner] |
| Cross-Epic Dep? | YES: MODULE-002-01 depends on MODULE-003-01 (Search Results Classifier from EPIC-003) because brand approval requires search results to count same-brand offers. Per 5A.4, EPIC-002 is parallel to EPIC-003 but both feed EPIC-003; timing TBD. |
| Constraint Notes | ASSUMPTION-004 (brand taxonomy) is unresolved. This module does NOT assume taxonomy structure. Taxonomy/reason codes are injected by MODULE-002-02 (Brand Logger). |

DEPENDENCY MAP (THIS EPIC ONLY)
Structure
List all module dependencies within THIS Epic:
MODULE-[ID]-[INDEX] depends on:
  ├── MODULE-[ID]-[INDEX2] (reason)
  ├── MODULE-[PRIOR-ID]-[INDEX3] (reason, cross-Epic)
  └── [external: system-name] (if any)
Validation Steps

List every dependency (within THIS Epic AND cross-Epic)
Identify circular dependencies:

If A depends on B, B depends on C, C depends on A: CIRCULAR → STOP & REDESIGN


Identify critical path:

Which modules must complete first for others to start?
Estimate effort: longest critical path = project timeline


Identify parallel workstreams:

Which modules can start simultaneously?
Maximize parallelization within Epic



Example (EPIC-002)
MODULE-002-01 (Brand Approval) depends on:
  └── MODULE-003-01 (Search Results Classifier) — cross-Epic, needed for same-brand count

MODULE-002-02 (Brand Logger) depends on:
  └── MODULE-002-01 (Brand Approval) — intra-Epic, logs approval decisions

MODULE-002-03 (Trust Classification) depends on:
  └── None — entry point, can start immediately

MODULE-002-04 (Bad-Site Blocker) depends on:
  └── MODULE-002-03 (Trust Classification) — intra-Epic, uses trust classification

MODULE-002-05 (Health Monitor) depends on:
  └── MODULE-002-03 (Trust Classification) — intra-Epic, monitors classified sites

Circular Dependencies: NONE ✅

Critical Path: MODULE-002-03 → {MODULE-002-04, MODULE-002-05} → MODULE-002-01 → MODULE-002-02
  Estimated: 6-8 weeks (see ARCHITECTURE phase for detailed estimation)

Parallel Workstreams:
  - Workstream A (intra-Epic): 002-03 → {002-04, 002-05}
  - Workstream B (cross-Epic blocker): MODULE-002-01 waits for MODULE-003-01 from EPIC-003
  - Implication: EPIC-003 (search) must start ~1 week after EPIC-002 to unblock MODULE-002-01

COVERAGE MATRIX (THIS EPIC)
Purpose: Ensure every user story has module coverage. No orphaned stories.
User Story IDUser Story NameModule IDs Covering This StoryCovered?US-1Brand fallback approvalMODULE-002-01✅US-2Brand substitution loggingMODULE-002-02✅US-3Website onboarding & trust validationMODULE-002-03✅US-4Block bad-rated websitesMODULE-002-04✅US-5Auto-suspend after failure streakMODULE-002-05✅[Add more rows as needed]
Verification:

 Every user story has at least ONE module assigned
 If any story has ⚠️ UNCOVERED: STOP. Design module for that story before proceeding.
 If any story has multiple modules: Verify each module is cohesive (same domain) or justify split (different concerns)


BOUNDED SCOPE: What We're NOT Decomposing (Rule 7)
Purpose: Document rejected modules/patterns to prevent scope creep.
Question: For each module considered but rejected, explain why.
Format
## REJECTED SCOPE: What We're NOT Creating

REJECTED MODULE/PATTERN: [name]
  Reason: [Why not included; what requirement would justify it]
  Alternative: [What we're doing instead, if any]
  Future: [When/if this might change; what condition would trigger reconsideration]
  
[Repeat for each rejection]
Example (EPIC-002)
## REJECTED SCOPE: What We're NOT Creating

REJECTED MODULE: "Brand Taxonomy Manager Module"
  Reason: ASSUMPTION-004 (brand substitution reason-code taxonomy) is unresolved per EPIC_OUTPUT 5A.3. 
          Rather than create a taxonomy module that assumes structure, we keep taxonomy external 
          (injected at runtime via configuration). This allows taxonomy to evolve post-MVP without 
          module redesign.
  Alternative: MODULE-002-02 (Brand Logger) accepts reason_code as parameter (runtime-injected).
  Future: Once ASSUMPTION-004 is resolved (stakeholder decision), this module might be formalized 
          in ARCHITECTURE phase.
  Traceability: None (rejected because assumption unresolved, not because requirement is missing)

REJECTED PATTERN: "Helper Utilities Module"
  Reason: No user story requires centralized utilities. Each module owns its utility functions 
          (e.g., MODULE-002-03 owns ReclameAqui lookup logic). If utilities proliferate during 
          implementation (causing code duplication), ARCHITECTURE phase can extract shared utilities.
  Alternative: Utility functions co-located with domain modules; extracted during implementation 
              if needed.
  Future: Post-implementation refactoring (if duplication > 10% of module code).
  Traceability: None (rejected preventively; BOUNDED SCOPE enforcement per Rule 7)

REJECTED PATTERN: "Caching Layer Module"
  Reason: NFR-001 (10-minute SLA) and performance requirements do not explicitly require caching. 
          Caching is an implementation optimization, not a module-level design decision. If performance 
          testing in ARCHITECTURE phase shows caching is needed, it will be added then.
  Alternative: Performance baseline established in ARCHITECTURE phase; caching decision deferred until 
              performance data exists.
  Future: ARCHITECTURE phase performance testing determines if caching module is needed.
  Traceability: None (optimization, not requirement-driven)

REJECTED MODULE: "Admin Dashboard Module"
  Reason: No user story from EPIC-002 requires admin dashboard. US-5 (Health Monitoring & Auto-Suspend) 
          requires VISIBILITY into site health/suspension state, but dashboard implementation is 
          deferred to UI layer (not a module concern). Module-level API endpoints will expose health data; 
          dashboard will consume those endpoints.
  Alternative: MODULE-002-05 (Health Monitor) exposes health data via public interface (API-ready); 
              dashboard implementation is UI concern (not module concern).
  Future: Dashboard UI layer implementation in FOLDER STRUCTURE phase.
  Traceability: FR-014, US-5 require health monitoring (module responsibility); dashboard rendering 
              (UI responsibility, not module responsibility)

OUTPUT VERIFICATION CHECKLIST
Before finalizing module output, verify ALL of these:
Traceability & Completeness

 Every module traces to THIS Epic's user stories (not other Epics) — COVERAGE MATRIX proves this
 Every user story has module coverage — No ⚠️ UNCOVERED stories in COVERAGE MATRIX
 Every module cites its FRs — Module template includes traceability back to PRD requirement
 No modules without Epic ownership — All modules justified by at least one user story

Dependency Integrity

 No circular dependencies within THIS Epic — Dependency Map checked for cycles
 Cross-Epic dependencies justified — Each documented with reason from 5A.4 (Epic blocking order)
 Cross-Epic dependency direction verified — If THIS Epic blocked by prior Epic, cross-dependencies OK. If THIS Epic blocks prior Epic, cross-dependencies NOT allowed.
 Parallel workstreams identified — Modules with Parallel=YES listed; critical path documented

Module Quality

 Module responsibilities are single-concern — Each module has one cohesive domain responsibility (cohesion test applied)
 Module interfaces are defined — Inputs, outputs, side effects documented (no implementation details)
 Dependencies minimized — Every dependency justified; no gratuitous coupling
 High-risk modules flagged — MODULE template "Flag for Review" populated; high-risk items identified

Scope Boundaries

 No scope creep (Rule 3 Types A-D):

 No features outside PRD [FR_IN_SCOPE]
 No unresolved [ASSUMPTION] items assumed resolved
 No unnecessary architectural layers
 No modules without user story traceability


 Rejected scope documented — BOUNDED SCOPE section explains what we're NOT decomposing and why
 Scope ceiling respected — PRD Section 1 scope ceiling confirmed; no out-of-scope additions

Clarity & Handoff

 Module template fully populated — All fields completed (no blank rows; if N/A, documented why)
 Acceptance criteria binary & testable — Each module has measurable acceptance criteria
 New engineer handoff test: Can unfamiliar engineer understand:

 What each module does (responsibility)?
 How modules relate (dependencies)?
 Which user stories each module satisfies?
 Why certain modules were rejected (BOUNDED SCOPE)?
 Which modules need expert review (Flag for Review)?



Rule Compliance (UNIVERSAL_PHASE_GATES)

 Rule 2A (Scope Creep): No features beyond PRD_HANDOFF_BLOCK ✅
 Rule 2B (Traceability): Every decision traces to requirement ✅
 Rule 2E (Bounded Scope): Rejected scope documented ✅
 Rule 2F (Handoff Clarity): New engineer can understand ✅
 Rule 2J (Acceptance Criteria): Modules have binary, testable criteria ✅


FLAGGED ITEMS ENFORCEMENT (Rule 5)
Purpose: Items flagged for expert review are BLOCKERS for advancement.
Definition of High-Risk (Flaggable Items)

External Integration: Module calls external APIs, websites, or third-party services
Complex Algorithm: Module implements non-trivial matching, deduplication, ranking, or other logic
Performance-Critical: Module affects NFR-001 (10-minute SLA) or has tight throughput requirements
Security-Sensitive: Module handles trust decisions, validation, or site eligibility
Data Loss Risk: Module failure could silently drop or corrupt data

Action for Flagged Modules
If any module has Flag for Review = YES:

Assign domain expert:

 Expert domain identified (e.g., Security, Architect, Domain Lead, QA Lead)
 Expert name and contact documented


Expert reviews module:

 Expert reviews module design against acceptance criteria
 Expert verifies no design flaws / missing constraints
 Review completed with date recorded


Expert decision documented:

 Decision: ✅ APPROVED / ❌ REJECTED / 🔄 REWORK REQUIRED
 If approved: Expert signs off; module proceeds
 If rejected/rework: Scope change documented; module redesigned


Module blocked until approved:

 Flagged modules CANNOT advance to ARCHITECTURE until expert approves
 No flagged items deferred to "implementation phase"



Example
MODULE-003-01: Search Query Executor (EPIC-003)

Risk Level: HIGH
Flag for Review: YES
Risk Justification: Multi-site fan-out is performance-critical (affects NFR-001 10-minute SLA). 
                    Failure to query all eligible sites breaks search completeness. Query timeouts, 
                    retry logic, and site suspension handling require architect review.

Expert Assignment: [Architect Name] | [date assigned]

Expert Review Outcome (to be filled by expert):
  Decision: ✅ APPROVED (with caveats)
  Caveats: Query timeout per site must be ≤15 seconds (total fan-out budget in 10-min SLA). 
           Architect to set in ARCHITECTURE phase.
  Signed: [Expert Name] | [Date]

Status: ✅ APPROVED — Proceeds to ARCHITECTURE

ADVANCEMENT GATE SIGN-OFF (Rule 10)
Purpose: Formal checkpoint before advancing from MDAP to ARCHITECTURE phase.
Requirement: Use the ADVANCEMENT GATE SIGN-OFF TEMPLATE (UNIVERSAL_PHASE_GATES Rule 10) to verify ALL rules (2A-2J).
When to Execute Sign-Off
AFTER all modules for THIS Epic have been designed and OUTPUT VERIFICATION checklist passes.
BEFORE final output is submitted for ARCHITECTURE phase consumption.
Sign-Off Process

Reviewer obtains the ADVANCEMENT GATE SIGN-OFF TEMPLATE (provided in UNIVERSAL_PHASE_GATES.md)
Reviewer goes through ALL rules (2A-2J) and checks each:

Rule 2A: Scope Creep Check (no features beyond PRD)
Rule 2B: Traceability Verification (all decisions traced)
Rule 2C: Flagged Items Resolved (expert sign-off documented)
Rule 2D: Authoritative Source (N/A for MDAP; omit)
Rule 2E: Bounded Scope Enforcement (rejected scope documented)
Rule 2F: Handoff Clarity Test (new engineer can understand)
Rule 2G: No Self-Audit (human independently verified)
Rule 2H: No Autonomous Auth/Payments (N/A for MDAP; omit)
Rule 2I: Output Completeness (all sections present)
Rule 2J: Acceptance Criteria Traceability (modules have binary criteria)


Reviewer marks [PASS] or [FAIL] for each rule
If any [FAIL]: Module output is BLOCKED. Rework required sections.
If all [PASS]: Reviewer signs and dates; output ready for ARCHITECTURE phase

Sign-Off Template (Abbreviated for MDAP)
═══════════════════════════════════════════════════════════════════
ADVANCEMENT GATE SIGN-OFF — MDAP PHASE
═══════════════════════════════════════════════════════════════════

Phase Completed: MDAP
Epic Processed: [EPIC-ID, e.g., EPIC-002]
Output Date: [date]
Reviewer Name: [human reviewer]
Email: [reviewer contact]

───────────────────────────────────────────────────────────────────
VERIFICATION (Rule 2A-2J):
───────────────────────────────────────────────────────────────────

Rule 2A — Scope Creep Check
- [ ] No features beyond PRD_HANDOFF_BLOCK
- [ ] Scope ceiling (PRD Section 1) respected
- [ ] No "good idea" decisions without requirement trace
Status: [PASS / FAIL]
Notes (if FAIL): ________________________________________________

Rule 2B — Traceability Verification
- [ ] Every module decision traces to requirement (FR/NFR or prior phase)
- [ ] No orphaned modules (COVERAGE MATRIX shows all stories covered)
- [ ] All unresolved items acknowledged (no TBDs)
Status: [PASS / FAIL]
Notes (if FAIL): ________________________________________________

Rule 2C — Flagged Items Resolved
- [ ] All "Flag for Review=YES" modules have domain expert assigned
- [ ] Expert decisions documented (✅ approved / ❌ rejected / 🔄 rework)
- [ ] No flagged items deferred to implementation phase
Status: [PASS / FAIL]
Notes (if FAIL): ________________________________________________

Rule 2E — Bounded Scope Enforcement
- [ ] Rejected scope documented (BOUNDED SCOPE section)
- [ ] No speculative/future features included
- [ ] All modules justified by requirement
Status: [PASS / FAIL]
Notes (if FAIL): ________________________________________________

Rule 2F — Handoff Clarity Test
- [ ] New engineer can understand all module responsibilities
- [ ] Dependencies justified and documented
- [ ] Links to PRD requirements (FR-XXX) present
- [ ] Unexplained acronyms/jargon clarified
Status: [PASS / FAIL]
Notes (if FAIL): ________________________________________________

Rule 2I — Output Completeness
- [ ] All required sections present (DEPENDENCY MAP, COVERAGE MATRIX, etc.)
- [ ] No sections skipped with "N/A" (if N/A, documented why)
- [ ] Module template fully populated for all modules
Status: [PASS / FAIL]
Notes (if FAIL): ________________________________________________

Rule 2J — Acceptance Criteria Traceability
- [ ] Every module has binary, testable acceptance criteria
- [ ] Criteria trace to PRD requirement or prior phase
- [ ] Criteria are measurable (not vague)
Status: [PASS / FAIL]
Notes (if FAIL): ________________________________________________

───────────────────────────────────────────────────────────────────
OVERALL GATE VERDICT:
───────────────────────────────────────────────────────────────────

[✅ APPROVED TO ADVANCE / ❌ BLOCKED — REWORK REQUIRED]

If BLOCKED, list ALL blockers (MUST be resolved before advancing):
1. ________________________________________________________________
2. ________________________________________________________________
3. ________________________________________________________________

───────────────────────────────────────────────────────────────────
NEXT PHASE PREPARATION:
───────────────────────────────────────────────────────────────────

- [ ] All blockers resolved and documented with corrections
- [ ] MDAP output ready for ARCHITECTURE phase input
- [ ] CONTEXT.md updated with THIS Epic's modules
- [ ] Next MDAP Epic prepared (if EPIC-N < total Epics)

───────────────────────────────────────────────────────────────────
SIGN-OFF:
───────────────────────────────────────────────────────────────────

Signature: ________________________     Date: _________________

Reviewer Name (print): _____________________________________________

Next Phase Ready: [YES / NO]
Next Phase: ARCHITECTURE DEFINITION
Next Prompt: PROMPT-4-ARCHITECTURE
Modules Approved: [MODULE-002-01 through MODULE-002-05, etc.]

═══════════════════════════════════════════════════════════════════
Important: This sign-off is FILED with project records. Do NOT discard.

CONTEXT.MD UPDATE BLOCK
After generating all modules for THIS Epic, output this block to be merged into [CONTEXT.md] by human:
[CONTEXT.MD_UPDATE — MDAP PHASE]

## MDAP Module Registry

### EPIC-[ID] Modules ([count] total):

[For each module, add one line:]
- MODULE-[EPIC-ID]-[INDEX]: [Module Name] | Type: [type] | User Stories: [US-IDs] | Risk: [Low/Med/High]

Example:
- MODULE-002-01: Brand Approval Gate | Type: Domain Logic | User Stories: US-1 | Risk: Medium
- MODULE-002-02: Brand Substitution Logger | Type: Domain Logic | User Stories: US-2 | Risk: Low
- MODULE-002-03: Website Trust Classification | Type: Domain Logic | User Stories: US-3 | Risk: High
- MODULE-002-04: Bad-Site Blocker | Type: Domain Logic | User Stories: US-4 | Risk: Medium
- MODULE-002-05: Health Monitor & Auto-Suspend | Type: Infrastructure | User Stories: US-5 | Risk: High

### Cross-Epic Dependencies (NEW):

[For each cross-Epic dependency, add one line:]
- MODULE-[THIS-EPIC]-XX depends on MODULE-[PRIOR-EPIC]-YY (reason)

Example:
- MODULE-002-01 depends on MODULE-003-01 (Search Results Classifier; needed for same-brand count per 5A.4 inter-Epic dependency)

### Total Modules So Far:

- EPIC-001: [X] modules
- EPIC-002: [Y] modules
- EPIC-003: [Z] modules (if processed)
- EPIC-004: [W] modules (if processed)
- **TOTAL: [X+Y+Z+W] modules**

### High-Risk Modules Flagged:

- MODULE-001-XX: [reason] | Expert: [assigned] | Status: [pending/approved/rejected]
- MODULE-003-01: Multi-site Search Query Executor | Expert: [assigned] | Status: [pending]

Example:
- MODULE-001-04: PDF Extraction with Confidence Scoring (complex algorithm) | Expert: [Data Science Lead] | Status: ✅ Approved
- MODULE-003-01: Search Query Executor (performance-critical) | Expert: [Architect] | Status: ✅ Approved

### Unresolved Assumptions Affecting THIS Epic:

- ASSUMPTION-001: [status from 5A.3]
- ASSUMPTION-003: Export formatting unresolved (constraints EPIC-004 modules to be FORMAT-AGNOSTIC)
- ASSUMPTION-004: Brand taxonomy unresolved (constrains EPIC-002 modules to inject taxonomy at runtime)

### Unresolved Thresholds Affecting THIS Epic:

- THRESHOLD-006: Per-site search completion rate unresolved (constrains EPIC-003 modules to allow configurable targets)

### Advancement Gate Sign-Off:

- EPIC-[ID] MDAP Sign-Off: [✅ APPROVED / ⏳ PENDING]
- Sign-Off Date: [date]
- Reviewer: [name]
- Blockers (if any): [list or "None"]

[/CONTEXT.MD_UPDATE]

6A — PHASE TRANSITION NOTE (PRELIMINARY)
Output this section AFTER THIS Epic's MDAP completes. It will be finalized when ALL Epics are processed.
6A (PRELIMINARY): MDAP PHASE FOR EPIC-[ID]

Processing Status: ✅ COMPLETE for EPIC-[ID]

Modules Generated:
- Total modules THIS Epic: [count]
- All modules named MODULE-[EPIC-ID]-[INDEX]: [INDEX ranges from 01 to count]

Module Registry Updated:
- [CONTEXT.md] MDAP MODULE REGISTRY now includes EPIC-[ID] modules
- Cross-Epic dependencies documented (if any)
- High-risk modules flagged and expert assignments recorded

Next Epic Processing:
- IF EPIC-[ID] is final Epic (e.g., EPIC-004): Proceed to FULL 6A (Phase Transition to ARCHITECTURE)
- IF more Epics remain (e.g., EPIC-001, EPIC-002 done; EPIC-003 pending): 
  Generate PRELIMINARY 6A and continue MDAP for next Epic

Advancement Status:
- ✅ THIS Epic ready for ARCHITECTURE phase (ADVANCEMENT GATE SIGN-OFF complete)
- ⏳ Pending Epic(s): [list if any remain]

Expected ARCHITECTURE Phase Start Date: [after all MDAP calls complete + final sign-off]

OPEN QUESTIONS & CONFLICTS (For This Epic Only)
If module decomposition reveals conflicts, unresolved items, or design ambiguities, document them here.
Do NOT resolve conflicts yourself. Escalate to architect or product owner.
Format
## OPEN QUESTIONS & CONFLICTS — EPIC-[ID]

OQ-[N]: [Question Title]
Context: [What triggered this question? What module is affected?]
Options:
  - Option A: [design choice 1]
  - Option B: [design choice 2]
Resolution By: [Person/role] | Phase: [MDAP / ARCHITECTURE / later]
Blocker?: [YES / NO] — If YES, prevents module finalization

[Repeat for each question]

EXAMPLE:

OQ-001: MODULE-003-01 Query Timeout Budget
Context: Search Query Executor (MODULE-003-01) must complete 100+ site queries within 
         NFR-001 (10-minute SLA). Per-site timeout needed, but optimal timeout is unknown.
         Too tight → premature failure. Too loose → SLA breach.
Options:
  - Option A: Aggressive timeout (5 sec/site; retry 2x). Risk: legitimate slow sites timeout.
  - Option B: Moderate timeout (15 sec/site; no retry). Risk: some sites never return.
  - Option C: Adaptive timeout (calibrate in ARCHITECTURE phase based on site performance data).
Resolution By: Architect | Phase: ARCHITECTURE (performance testing will determine)
Blocker?: NO (module design is agnostic to timeout value; timeout injected as config)

OQ-002: ASSUMPTION-004 Brand Taxonomy Injection Point
Context: MODULE-002-02 (Brand Logger) needs to accept reason_code for brand substitution. 
         But ASSUMPTION-004 (taxonomy) is unresolved. Where should taxonomy be defined?
Options:
  - Option A: Hard-code taxonomy in MODULE-002-02 (risky if assumption changes)
  - Option B: Inject taxonomy at module initialization (runtime config; cleaner)
  - Option C: Defer taxonomy to ARCHITECTURE phase (implement as strategy pattern later)
Resolution By: Product Owner | Phase: PRD amendment or ARCHITECTURE decision
Blocker?: NO (module already designed as agnostic; awaiting stakeholder decision on taxonomy)

FINAL CHECKLIST BEFORE SUBMITTING OUTPUT

 EPIC-ID specified and user stories match EPIC_OUTPUT.md
 All gates passed: GATE CHECK section all ✅
 Module template fully populated for every module (no blank rows)
 COVERAGE MATRIX complete — every user story has module(s)
 DEPENDENCY MAP accurate — no circular dependencies within THIS Epic
 No scope creep — BOUNDED SCOPE section explains rejections
 High-risk modules flagged and experts assigned
 Acceptance criteria testable for all modules
 OUTPUT VERIFICATION checklist passed (all items ✅)
 ADVANCEMENT GATE SIGN-OFF completed (✅ APPROVED)
 CONTEXT.md UPDATE block prepared (ready to merge)
 OPEN QUESTIONS documented (if any)
 6A PHASE TRANSITION NOTE generated


INSTRUCTIONS FOR HUMAN EXECUTING THIS PROMPT

Provide INPUT: Paste EPIC_OUTPUT.md (this Epic's section) + PRD_HANDOFF_BLOCK + unresolved items from 5A.3
Execute GATE CHECK: Verify all prerequisites pass before proceeding
Design modules: Follow REQUIRED STRUCTURE template; trace every module to user stories
Check dependencies: Ensure no circular deps; identify critical path and parallel workstreams
Complete COVERAGE MATRIX: Verify every user story is covered
Document BOUNDED SCOPE: Explain what we're NOT creating and why (Rule 7)
Run OUTPUT VERIFICATION: Check all items; fix any ❌ before finalizing
Assign experts to flagged modules (Rule 5): Ensure high-risk modules have domain expert review
Execute ADVANCEMENT GATE SIGN-OFF (Rule 10): Verify all rules 2A-2J; get reviewer signature
Output final modules + CONTEXT.md UPDATE


END OF MDAP v2.0 PROMPT