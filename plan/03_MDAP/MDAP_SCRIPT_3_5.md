# MDAP_SCRIPT_3_5 — Stage 3: Module Details

## Goal
Produce full module templates for one Epic using only approved Stage 1+2 artifacts.

## Inputs (only)
- `EPIC-ID`
- Approved module list (`MDAP_STAGE1_[EPIC-ID]_APPROVED.md`)
- Approved dependencies (`MDAP_STAGE2_[EPIC-ID]_APPROVED.md`)
- Unresolved assumptions/thresholds affecting this Epic (from `EPIC_OUTPUT.md` 5A.3 and `CONTEXT.md`)

## Do Not
- Do not resolve unresolved assumptions/thresholds.
- Do not change module names/IDs approved in Stage 1.
- Do not write implementation code or algorithms.

## Required Per-Module Template
`MODULE-[EPIC-ID]-[INDEX]: [Name]`
- Responsibility: [1 sentence]
- User Stories: [US-IDs]
- Module Type: [Domain Logic | Infrastructure | Interface | Utility | Integration]
- Acceptance Criteria: [binary, testable]
- Public Interface: Inputs / Outputs / Side Effects
- Dependencies: [MODULE IDs]
- Consumed By: [MODULE IDs]
- Isolation Level: [YES | NO | PARTIAL]
- Parallel?: [YES | NO]
- Risk Level: [Low | Medium | High]
- Risk Justification: [required if Medium/High]
- Flag for Review: [YES | NO]
- Expert Domain: [if flagged]
- Cross-Epic Dep?: [if any]
- Constraint Notes: [how unresolved items constrain design]

## Output Contract (strict)

### A) Completed Module Templates
(One block per module using all fields)

### B) Coverage Matrix
- `US-[X] -> MODULE-[...] | Covered: YES/NO`

### C) Constraint Ledger
- `ASSUMPTION/THRESHOLD ID -> affected modules -> design constraint`

## Validation Checklist
- All fields populated for every module.
- Acceptance criteria are binary/testable.
- No unresolved item is treated as resolved.
- Coverage matrix has zero uncovered stories.

## Human Gate
- ✅ Approve
- ❌ Rework

## Stage Artifact Name
Save approved output as: `MDAP_STAGE3_[EPIC-ID]_APPROVED.md`
