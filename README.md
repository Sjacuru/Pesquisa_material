# PRD Creation Workflow — Three-Phase GitHub Copilot Guide

## Overview

This guide explains how to use **three separate prompts** with GitHub Copilot to create a complete, structured PRD that feeds into the EPIC phase. The three-phase approach reduces hallucination risk by breaking the work into reviewable chunks with cross-phase dependencies.

## Project Bootstrap (Environment + Prompt Path)

### Main Python Environment

This project uses the Conda environment `matfinder` as the primary runtime.

1. Activate: `conda activate matfinder`
2. Install dependencies: `python -m pip install -r requirements.txt`
3. Django health check: `python manage.py check`
4. Migration state check: `python manage.py makemigrations --check --dry-run`
5. Full test run: `python -m pytest`

VS Code workspace default interpreter is set to:
`C:\Users\sjacu\anaconda3\envs\matfinder\python.exe`

### GitHub Prompt Folder Path

Canonical path is `.github/prompts/`.

If you see `.github/promps` in a local note/tooling message, treat it as a typo and use `.github/prompts/`.

---

## Timeline & Dependencies

```
PHASE 1 (Foundational)
    ↓ [Phase 1 Output → Input to Phase 2]
PHASE 2 (Requirements)
    ↓ [Phases 1-2 Output → Input to Phase 3]
PHASE 3 (Governance + Handoff)
    ↓ [All 3 outputs assembled into final PRD]
FINAL PRD READY FOR EPIC PHASE
```

---

## Files in This Package

### Prompt Files
1. **PROMPT-1-FOUNDATIONAL.md** — Creates Sections 1-3
2. **PROMPT-2-REQUIREMENTS.md** — Creates Sections 4-6 (uses Phase 1 output)
3. **PROMPT-3-GOVERNANCE.md** — Creates Sections 7-10 + handoff (uses Phases 1-2 output)

### Data Source
- **PRD Decision Sheet** (embedded in each prompt for reference)

### Output Files (You Will Create)
- **Phase-1-Output.md** — Sections 1-3 from Phase 1
- **Phase-2-Output.md** — Sections 4-6 from Phase 2
- **Phase-3-Output.md** — Sections 7-10 + [PRD_HANDOFF_BLOCK] from Phase 3
- **CONTEXT.md** — Traveling context file (created in Phase 3, read-only for all downstream phases)

---

## Step-by-Step Workflow

### PHASE 1: Foundational Sections

**Duration**: ~15-20 minutes

**What You Do**:
1. Open GitHub Copilot (or Claude in your IDE)
2. Copy the entire content of **PROMPT-1-FOUNDATIONAL.md**
3. Paste it as your input to Copilot
4. Copilot generates Sections 1-3 output

**Expected Output**:
- Executive Summary (1 paragraph)
- Problem Statement (4 subsections)
- PERSONA-001 (Role, Goal, Pain Point)

**Validation Before Proceeding**:
- [ ] Section 1 is one paragraph with product description + user + measurable outcome
- [ ] Section 2 has all four subsections with NO solution language
- [ ] Section 3 defines PERSONA-001 with all required fields
- [ ] No technical jargon (APIs, databases, Python)
- [ ] All statements traceable to PRD Decision Sheet

**If Output is Good**: 
- Copy the Phase 1 output to a file called **Phase-1-Output.md**
- Proceed to Phase 2

**If Output Needs Rework**:
- Comment in GitHub Copilot asking for corrections
- Use natural language feedback: "Section 2 includes solution language; remove it and restate problem space only"
- Re-validate before proceeding

---

### PHASE 2: Requirements (FR/NFR)

**Duration**: ~25-35 minutes

**What You Do**:
1. Open a NEW GitHub Copilot conversation (or clear context)
2. Copy the entire content of **PROMPT-2-REQUIREMENTS.md**
3. **IMPORTANT**: Include your Phase 1 output as context:
   ```
   [Paste PROMPT-2-REQUIREMENTS.md content]
   
   ---
   
   CONTEXT FROM PHASE 1:
   [Paste your Phase-1-Output.md]
   ```
4. Copilot generates Sections 4-6 output

**Expected Output**:
- FR-001 through FR-N (Functional Requirements with format: ID, statement, acceptance criteria, source, dependency, priority)
- NFR-001 through NFR-M (Non-Functional Requirements — Performance + Maintainability only)
- Section 6: MoSCoW Priority Summary (table)
- [ASSUMPTION] and [THRESHOLD NEEDED] flags throughout

**Validation Before Proceeding**:
- [ ] All FR/NFR IDs are sequential (FR-001...FR-N, NFR-001...NFR-M) with no gaps
- [ ] Every FR/NFR has: statement, acceptance criteria, source, priority + justification
- [ ] All acceptance criteria are binary (pass/fail, automatable)
- [ ] All requirements traceable to Decision Sheet, [ASSUMPTION], or [THRESHOLD NEEDED]
- [ ] Confidence thresholds (0.90, 0.70, 0.75, 0.92) are embedded
- [ ] Section 5 covers ONLY Performance + Maintainability (no other NFR categories)
- [ ] No duplicate IDs
- [ ] No contradictions between requirements (flag any as [CONFLICT])

**If Output is Good**:
- Copy the Phase 2 output to a file called **Phase-2-Output.md**
- Proceed to Phase 3

**If Output Needs Rework**:
- Comment asking for specific corrections: "FR-015 lacks acceptance criteria; make it a binary pass/fail condition"
- Re-validate before proceeding

---

### PHASE 3: Governance & Handoff

**Duration**: ~30-40 minutes

**What You Do**:
1. Open a NEW GitHub Copilot conversation (or clear context)
2. Copy the entire content of **PROMPT-3-GOVERNANCE.md**
3. **IMPORTANT**: Include both Phase 1 and Phase 2 outputs as context:
   ```
   [Paste PROMPT-3-GOVERNANCE.md content]
   
   ---
   
   CONTEXT FROM PHASE 1:
   [Paste your Phase-1-Output.md]
   
   ---
   
   CONTEXT FROM PHASE 2:
   [Paste your Phase-2-Output.md]
   ```
4. Copilot generates Sections 7-10, [PRD_HANDOFF_BLOCK], and CONTEXT.md

**Expected Output**:
- Section 7: Out of Scope (extracted from Decision Sheet)
- Section 8: Open Questions (OQ-001 through OQ-N with impact analysis)
- Section 9: Success Metrics (SM-001 through SM-M linked to FR/NFR)
- Section 10: Granularity Rule & Epic Recommendation (3-10 Epics)
- [PRD_HANDOFF_BLOCK] (machine-readable payload for EPIC)
- **CONTEXT.md** (standalone file, read-only for all downstream phases)

**Validation Before Proceeding**:
- [ ] Section 7 includes all Decision Sheet out-of-scope items
- [ ] Section 8 lists ALL [ASSUMPTION], [THRESHOLD NEEDED], [CONFLICT] items with OQ-XXX numbering
- [ ] Section 9 success metrics are SM-001 through SM-M with no gaps
- [ ] Section 10 proposes 3-10 Epics with rationale
- [ ] [PRD_HANDOFF_BLOCK] is in exact format (no conversational text)
- [ ] CONTEXT.md is standalone with READ-ONLY notice
- [ ] All Phase 1-2 elements preserved unchanged
- [ ] FR/NFR IDs confirmed CANONICAL

**If Output is Good**:
- Save Phase 3 output to **Phase-3-Output.md**
- Save CONTEXT.md as **CONTEXT.md** (standalone)
- Proceed to final assembly

**If Output Needs Rework**:
- Comment with specific feedback: "OQ-005 is missing; [THRESHOLD NEEDED] items should have one Open Question per missing threshold"
- Re-validate before proceeding

---

## Final Assembly

Once all three phases are approved:

1. **Create a single PRD document** in your preferred format (Markdown or Word):
   - Include Sections 1-3 (Phase 1 output)
   - Include Sections 4-6 (Phase 2 output)
   - Include Sections 7-10 + [PRD_HANDOFF_BLOCK] (Phase 3 output)

2. **Save CONTEXT.md separately** (in the same directory as the PRD)

3. **PRD is complete** and ready for the EPIC phase

---

## GitHub Workflow Integration

### Option A: GitHub Issues (Recommended for Feedback)

1. Create a GitHub Issue: "PRD Creation — Phase 1: Foundational Sections"
2. Paste PROMPT-1-FOUNDATIONAL.md into the issue
3. Copilot auto-completes the issue with Phase 1 output
4. Review in issue thread; request changes via comments
5. Once approved, close issue and move to Phase 2 issue
6. Repeat for Phases 2-3

### Option B: Separate Branches

1. Create branch: `feature/prd-phase-1`
2. Create file: `PRD/Phase-1-Output.md`
3. Use Copilot inline in the file to generate content
4. Commit & create PR for review
5. Merge after approval
6. Create branch: `feature/prd-phase-2` → reference Phase 1 in context
7. Repeat for Phase 3

### Option C: Direct Copilot Conversation (Fastest)

1. Open GitHub Copilot in your IDE
2. Paste each prompt sequentially in separate conversations
3. Save outputs manually to three files
4. Assemble manually once all three phases complete

---

## Risk Mitigation Checklist

### Hallucination Prevention

- ✅ **Separate prompts by phase** — each prompt is focused, not massive
- ✅ **Cross-phase dependencies** — Prompt 2 requires Phase 1 output; Prompt 3 requires Phases 1-2
- ✅ **Explicit boundary markers** — each prompt says "DON'T" (what to avoid in THIS phase)
- ✅ **Validation criteria in each prompt** — you have a checklist to verify output before proceeding
- ✅ **Source traceability** — every requirement tagged with source (Decision Sheet, PERSONA, [ASSUMPTION], [THRESHOLD NEEDED])
- ✅ **Review gates between phases** — you review and approve before moving forward

### If Copilot Drifts

**Problem**: Output doesn't match validation checklist

**Solution**: 
1. Comment in Copilot with SPECIFIC correction
2. Reference the validation criterion that failed
3. Ask for rework on THAT SECTION ONLY
4. Do NOT proceed to next phase until validation passes

Example:
```
Section 4 (Functional Requirements):
- Issue: FR-008 acceptance criteria is not binary (it's a narrative)
- Fix: Rewrite FR-008 acceptance criteria as: "PASS if [condition], FAIL if [condition]"
- Then regenerate entire Section 4 with corrected FR-008
```

---

## Timeline Estimate

| Phase | Duration | Activity |
|-------|----------|----------|
| **Phase 1** | 15-20 min | Generate + validate Sections 1-3 |
| **Phase 2** | 25-35 min | Generate + validate Sections 4-6 (use Phase 1 as context) |
| **Phase 3** | 30-40 min | Generate + validate Sections 7-10 + handoff (use Phases 1-2 as context) |
| **Assembly** | 10 min | Combine all sections + CONTEXT.md into final PRD |
| **TOTAL** | ~90-130 min | Complete PRD ready for EPIC phase |

---

## Key Points for GitHub Copilot Success

1. **Use full prompts** — Do NOT edit or truncate the prompts; use them verbatim
2. **Provide context explicitly** — When moving to next phase, paste previous output as context (don't assume Copilot remembers)
3. **Validate before moving** — Do NOT skip validation checklist between phases
4. **Flag [ASSUMPTION] items** — If Copilot creates assumptions, that's OK; just ensure they're tagged and listed in Section 8
5. **No invented thresholds** — If Copilot invents numeric targets (error rate, availability %), ask it to remark [THRESHOLD NEEDED] instead
6. **Use specific feedback** — When requesting changes, cite the validation criterion that failed (e.g., "GC-2 acceptance criteria not automatable")

---

## Example: Phase 2 Context Block

When starting Phase 2, your input to Copilot should look like:

```
[Full content of PROMPT-2-REQUIREMENTS.md]

---

CONTEXT FROM PHASE 1:
# PRD: School Material Price Finder (Brazil MVP)
## PHASE 1 OUTPUT — Sections 1–3

### Section 1: Executive Summary
[Your Phase 1 output here]

### Section 2: Problem Statement
[Your Phase 1 output here]

### Section 3: User Personas
[Your Phase 1 output here]
```

This signals to Copilot: "You have the Phase 1 output; now generate Phase 2 based on it."

---

## When to Use Human Judgment

- ✅ **Phase transitions**: You decide if output is good enough to proceed
- ✅ **Ambiguous feedback**: If Copilot output seems reasonable but doesn't match a validation criterion, ask for clarification
- ✅ **Conflicts in output**: If Copilot identifies a [CONFLICT] between two requirements, YOU decide which takes precedence (and note in Section 8)
- ✅ **Assumptions**: If Copilot flags [ASSUMPTION] items, review them and decide if they're reasonable or need to be resolved before EPIC

---

## Quick Reference: Prompt Files

| Prompt | Creates | Dependencies | Key Governance Rule |
|--------|---------|--------------|-------------------|
| PROMPT-1-FOUNDATIONAL.md | Sections 1-3 | None (starts pipeline) | GC-1, GC-5, GC-7 (traceability, no invention) |
| PROMPT-2-REQUIREMENTS.md | Sections 4-6 | Requires Phase 1 output | GC-2, GC-3, GC-6, GC-8 (binary criteria, no invented thresholds, permanent IDs) |
| PROMPT-3-GOVERNANCE.md | Sections 7-10 + handoff | Requires Phases 1-2 output | GC-5, GC-6, GC-8, GC-9 (conflict flagging, threshold transparency, downstream handoff) |

---

## Need Help?

- **Phase-specific issues**: Refer to the "VALIDATION CHECKLIST" section in each prompt
- **Governance rules**: Consult PRD.pdf template (GC-1 through GC-9)
- **Decision Sheet ambiguities**: Mark as [ASSUMPTION] in Section 8; resolve at EPIC sign-off
- **Copilot drift**: Use specific validation criteria to redirect (e.g., "GC-6: Do not invent numeric thresholds")

---

## Next Steps After PRD Completion

1. **Assemble final PRD** (Sections 1-10 + [PRD_HANDOFF_BLOCK])
2. **Preserve CONTEXT.md** (read-only, travels with PRD)
3. **Prepare for EPIC phase**:
   - Extract [PRD_HANDOFF_BLOCK] (data payload for EPIC)
   - Extract FR/NFR IDs (canonical through all phases)
   - Resolve [ASSUMPTION] and [THRESHOLD NEEDED] items (or defer to EPIC phase)
4. **Start EPIC phase** with PROMPT-4-EPIC (reference: [PRD_HANDOFF_BLOCK] + CONTEXT.md)

---

**You are now ready to use these three prompts to create a rigorous, traceable PRD.**

Good luck! 🚀