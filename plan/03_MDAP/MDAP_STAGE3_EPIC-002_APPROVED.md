# MDAP Stage 3 — EPIC-002 (Module Details)

## Stage Status
- Execution Status: COMPLETE
- Human Gate Status: APPROVED
- Epic: EPIC-002
- Input Artifacts:
  - `MDAP_STAGE1_EPIC-002_APPROVED.md` (approved)
  - `MDAP_STAGE2_EPIC-002_APPROVED.md` (approved)

## Pre-Gate Validation (must pass)
1. Stage 1 approved module list available ✅
2. Stage 2 approved dependency map available ✅
3. Unresolved items affecting EPIC-002 identified from handoff/context ✅ (`ASSUMPTION-004`)

Gate Decision: PASS (proceed with Stage 3 output)
---

## A) Completed Module Templates

- User Stories: US-1
- Module Type: Domain Logic
  - AC1: If same-brand offer count >= 3, no expansion prompt is shown. (PASS/FAIL)
  - AC2: If same-brand offer count < 3, per-item approval is required before cross-brand expansion. (PASS/FAIL)
- Public Interface:
  - Inputs: item_id, same_brand_offer_count, candidate_brand_pool
---

**Approved — Stage 3 complete. Proceeded to Stage 4 (Scope & Risk Review).**
  - Side Effects: writes approval/denial decision event to audit logs
- Dependencies: none
- Consumed By: MODULE-002-02
- Isolation Level: YES
- Parallel?: YES
- Risk Level: MEDIUM
- Risk Justification: User-decision gate errors can bias relevance or violate brand policy intent.
- Flag for Review: YES
- Expert Domain: Architect / Product
- Cross-Epic Dep?: NO
- Constraint Notes: ASSUMPTION-004 unresolved; gate consumes runtime-injected reason taxonomy references instead of hard-coded taxonomy.

### MODULE-002-02: Brand Substitution Audit Logger
- Responsibility: Persist reason-coded audit records for approved cross-brand substitutions with timestamped traceability.
- User Stories: US-2
- Module Type: Domain Logic
- Acceptance Criteria:
  - AC1: Every approved expansion persists reason_code and timestamp. (PASS/FAIL)
  - AC2: Items without expansion approval have no substitution reason-code record. (PASS/FAIL)
  - AC3: Multiple expansions for the same item create distinct immutable audit entries. (PASS/FAIL)
- Public Interface:
  - Inputs: expansion_approval_decision, reason_code, event_timestamp
  - Outputs: substitution_audit_record
  - Side Effects: appends records to structured audit log store
- Dependencies: MODULE-002-01
- Consumed By: audit/reporting consumers in later phases
- Isolation Level: YES
- Parallel?: NO
- Risk Level: MEDIUM
- Risk Justification: Incorrect logging breaks auditability and governance traceability.
- Flag for Review: YES
- Expert Domain: QA / Architect
- Cross-Epic Dep?: NO
- Constraint Notes: ASSUMPTION-004 unresolved; reason_code must be accepted as external/configured value, not fixed by module.

### MODULE-002-03: Website Onboarding & Trust Classifier
- Responsibility: Validate domain/HTTPS and classify site trust state (allowed/review_required/blocked) before activation.
- User Stories: US-3
- Module Type: Integration
- Acceptance Criteria:
  - AC1: Domain format and HTTPS checks execute for each onboarding request. (PASS/FAIL)
  - AC2: Trust classification returns one of allowed/review_required/blocked. (PASS/FAIL)
  - AC3: Failed onboarding prevents activation into searchable source set. (PASS/FAIL)
- Public Interface:
  - Inputs: onboarding_request(domain, label, metadata)
  - Outputs: site_validation_result, trust_classification_status, activation_eligibility
  - Side Effects: writes onboarding/trust decisions to audit logs
- Dependencies: none
- Consumed By: MODULE-002-04, MODULE-002-05
- Isolation Level: PARTIAL
- Parallel?: YES
- Risk Level: HIGH
- Risk Justification: External validation and trust-source integration can incorrectly admit or exclude sites.
- Flag for Review: YES
- Expert Domain: Architect / Security
- Cross-Epic Dep?: NO
- Constraint Notes: No unresolved threshold required to classify trust states; implementation details remain external-service agnostic.

### MODULE-002-04: Search Eligibility Site Filter
- Responsibility: Build the active searchable site set by excluding blocked and suspended sources.
- User Stories: US-4
- Module Type: Domain Logic
- Acceptance Criteria:
  - AC1: Blocked sites are always excluded from searchable set. (PASS/FAIL)
  - AC2: Allowed/review_required and non-suspended sites are included as eligible. (PASS/FAIL)
  - AC3: Eligibility output reflects latest trust and suspension states at filter time. (PASS/FAIL)
- Public Interface:
  - Inputs: site_trust_classifications, suspension_status_registry
  - Outputs: searchable_site_set
  - Side Effects: writes eligibility filtering decisions to audit logs
- Dependencies: MODULE-002-03, MODULE-002-05
- Consumed By: EPIC-003 search fan-out entry (FR-015 prerequisite)
- Isolation Level: PARTIAL
- Parallel?: NO
- Risk Level: HIGH
- Risk Justification: Incorrect filtering undermines trust policy and search completeness.
- Flag for Review: YES
- Expert Domain: Architect / QA
- Cross-Epic Dep?: NO
- Constraint Notes: THRESHOLD-006 target tracking is downstream to search completeness monitoring; this module enforces eligibility state only.

### MODULE-002-05: Site Failure Monitor & Auto-Suspension
- Responsibility: Track query failures with retry policy and suspend unstable sites according to configured threshold rules.
- User Stories: US-5
- Module Type: Infrastructure
- Acceptance Criteria:
  - AC1: Failure streak increments only after 3 retry attempts fail for a site query cycle. (PASS/FAIL)
  - AC2: Site status switches to suspended when configured failure threshold is reached. (PASS/FAIL)
  - AC3: Suspended sites remain excluded until explicit revalidation event occurs. (PASS/FAIL)
- Public Interface:
  - Inputs: per_site_query_attempt_events, retry_outcomes, suspension_threshold_config
  - Outputs: updated_suspension_status, failure_streak_state
  - Side Effects: writes suspension transitions and streak counters to audit logs
- Dependencies: MODULE-002-03, [external event stream for site query outcomes]
- Consumed By: MODULE-002-04
- Isolation Level: PARTIAL
- Parallel?: NO
- Risk Level: HIGH
- Risk Justification: Faulty suspension logic can either degrade coverage (false suspension) or degrade reliability (missed suspension).
- Flag for Review: YES
- Expert Domain: Architect / SRE
- Cross-Epic Dep?: NO
- Constraint Notes: Uses configured threshold value (THRESHOLD-004 resolved in context) and must keep policy configurable.

---

## B) Coverage Matrix

- `US-1 -> MODULE-002-01 | Covered: YES`
- `US-2 -> MODULE-002-02 | Covered: YES`
- `US-3 -> MODULE-002-03 | Covered: YES`
- `US-4 -> MODULE-002-04 | Covered: YES`
- `US-5 -> MODULE-002-05 | Covered: YES`

Coverage Result: `5/5 user stories covered`

---

## C) Constraint Ledger

- `ASSUMPTION-004 -> MODULE-002-01, MODULE-002-02 -> reason-code taxonomy unresolved; modules must accept runtime-configured taxonomy values and avoid hard-coded taxonomy schema.`
- `THRESHOLD-004 -> MODULE-002-05 -> auto-suspension threshold enforced via configuration (context decision: 5 failures in 1 hour); no static embedding in module contract.`
- `THRESHOLD-006 -> MODULE-002-04, MODULE-002-05 -> per-site completion-rate target tracking impacts observability and tuning; do not hard-code completion assumptions in eligibility contract.`

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
