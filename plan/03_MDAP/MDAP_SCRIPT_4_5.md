# MDAP_SCRIPT_4_5 — Stage 4: Scope & Risk Review

## Goal
Finalize bounded scope and high-risk flagging before advancement sign-off.

## Inputs (only)
- `EPIC-ID`
- Approved module details (`MDAP_STAGE3_[EPIC-ID]_APPROVED.md`)
- MDAP bounded-scope and rule constraints from `MDAP.md`

## Do Not
- Do not add new modules here.
- Do not silently remove approved modules.
- Do not keep Medium/High risk modules unflagged.

## Task 1 — Rejected Scope Register
For each rejected module/pattern:
- Name
- Reason (requirement-based)
- Alternative
- Future trigger
- Traceability (FR or `None` if preventive)

## Task 2 — High-Risk Flagging
For each module with Risk `MEDIUM` or `HIGH`:
- Ensure `Flag for Review = YES`
- Assign expert domain
- Record justification

## Output Contract (strict)

### A) Rejected Scope
- `REJECTED: [name] | Reason: ... | Alternative: ... | Future: ... | Traceability: ...`

### B) High-Risk Modules Flagged
- `MODULE-... | Risk: ... | Flag: YES | Expert Domain: ... | Justification: ...`

## Validation Checklist
- Rejections are justified and requirement-driven.
- No speculative scope included.
- All Medium/High risks flagged with expert domain.

## Human Gate
- ✅ Approve
- ❌ Adjust

## Stage Artifact Name
Save approved output as: `MDAP_STAGE4_[EPIC-ID]_APPROVED.md`
