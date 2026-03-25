# MDAP_SCRIPT_2_5 — Stage 2: Dependency Mapping

## Goal
Map intra-Epic and cross-Epic dependencies for approved modules, without introducing new modules.

## Inputs (only)
- `EPIC-ID`
- Approved module list (`MDAP_STAGE1_[EPIC-ID]_APPROVED.md`)
- Inter-Epic dependencies from `EPIC_OUTPUT.md` section 5A.4
- Prior module registry from `CONTEXT.md` (if Epic > 1)

## Do Not
- Do not add or rename modules.
- Do not invent dependencies not justified by 5A.4 or module responsibility.
- Do not allow reverse cross-Epic dependency direction.

## Pre-Gate (must pass)
1. Stage 1 approved artifact exists.
2. 5A.4 dependencies for this Epic are explicit.
3. Prior module registry exists if needed.

If any fail: output `BLOCKER` and stop.

## Task
Create dependency graph, detect cycles, identify critical path and parallel workstreams.

## Output Contract (strict)

### A) Dependency Map
- `MODULE-[EPIC]-01 depends on: [none | MODULE-... ]`
- `...`

### B) Circular Dependency Check
- `Cycle detected: YES/NO`
- If YES: list cycle path and stop.

### C) Critical Path
- `Path: MODULE-... -> MODULE-...`

### D) Parallel Workstreams
- `Workstream A: [MODULE IDs]`
- `Workstream B: [MODULE IDs]`

### E) Cross-Epic Dependency Justification
- `MODULE-[THIS]-XX -> MODULE-[PRIOR]-YY | Reason from 5A.4: ...`

## Validation Checklist
- No intra-Epic cycles.
- All dependencies justified.
- Cross-Epic direction valid.
- Parallelizable modules explicitly identified.

## Human Gate
- ✅ Approve
- ❌ Redesign

## Stage Artifact Name
Save approved output as: `MDAP_STAGE2_[EPIC-ID]_APPROVED.md`
