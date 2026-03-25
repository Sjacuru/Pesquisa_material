# MDAP_SCRIPT_1_5 — Stage 1: Module Identification

## Goal
Identify the **minimum** set of modules for one Epic, with strict traceability to user stories.

## Inputs (only)
- `EPIC-ID`
- Epic user stories (from `EPIC_OUTPUT.md`)
- Epic acceptance criteria (from `EPIC_OUTPUT.md`)
- Scope ceiling statement (from `CONTEXT.md`)

## Do Not
- Do not create helper/utility modules unless directly required by a user story.
- Do not infer missing requirements.
- Do not resolve unresolved assumptions/thresholds.
- Do not add features outside `FR_IN_SCOPE`.

## Pre-Gate (must pass)
1. `EPIC-ID` is explicit.
2. User stories listed for this Epic match `EPIC_OUTPUT.md`.
3. Acceptance criteria exist for all listed user stories.
4. No mismatch in story count vs `EPIC_OUTPUT.md`.

If any fail: output `BLOCKER` and stop.

## Task
For each user story, propose one or more modules with one domain responsibility each.

## Output Contract (strict)

### A) Module List
- `MODULE-[EPIC_ID]-01: [Name] | Responsibility: [1 sentence] | User Stories: [US-IDs]`
- `MODULE-[EPIC_ID]-02: ...`

### B) Story Coverage Check
- `US-[X] -> [MODULE IDs] | Covered: YES/NO`

### C) Scope Guardrail Check
- `Out-of-scope modules proposed: NONE` (or list + why rejected)

## Validation Checklist
- Every module maps to at least one user story.
- Every user story is covered by at least one module.
- No orphan module.
- No out-of-scope feature.

## Human Gate
- ✅ Approve (all stories covered and modules justified)
- ❌ Rework (missing/extra modules)

## Stage Artifact Name
Save approved output as: `MDAP_STAGE1_[EPIC-ID]_APPROVED.md`
