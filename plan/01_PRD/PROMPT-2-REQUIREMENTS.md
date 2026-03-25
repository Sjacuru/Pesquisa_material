# PROMPT-2-REQUIREMENTS
## PRD Phase 2: Sections 4–5 (Functional & Non-Functional Requirements)

**Status**: Depends on Phase 1 completion (requires Phase 1 output as input)  
**Previous Phase**: PROMPT-1-FOUNDATIONAL (will be provided as context)  
**Next Phase**: PROMPT-3-GOVERNANCE (will consume this output)  
**Governance**: PRD.pdf template (sections 4-5 + GC-1, GC-2, GC-3, GC-4, GC-6, GC-8)  
**Data Source**: PRD Decision Sheet + Phase 1 output (Persona PERSONA-001)  

---

## INSTRUCTIONS FOR GITHUB COPILOT

You are creating **all functional and non-functional requirements** for the PRD. This is Phase 2 of 3.

### CRITICAL: WHAT YOU MUST HAVE BEFORE STARTING

**Input 1: Phase 1 Output** — The user will provide Sections 1-3 (Executive Summary, Problem Statement, PERSONA-001) from Phase 1.  
**Input 2: PRD Decision Sheet** — (Provided below)  
**Input 3: This Prompt** — You are reading it now.

Do NOT proceed until you have all three inputs. If Phase 1 output is missing or incomplete, ask the user for it.

---

## SECTION 4: FUNCTIONAL REQUIREMENTS

### NAMING CONVENTION
- **ID Format**: FR-001, FR-002, FR-003, ... (sequential, no gaps)
- **Statement Format**: "The system shall [verb] [object] [condition]"
- Example: "The system shall extract item names from typed and handwritten text in PDF documents."

### REQUIRED FIELDS FOR EACH FR

```
FR-XXX [PRIORITY]: [Requirement statement in "The system shall..." format]

Acceptance Criteria:
[1-3 binary, human-verifiable AND automatable criteria. Format: "Given [context], when [action], then [outcome]" or simple pass/fail condition.]

Source: [One of: "PRD Decision Sheet section [name]" OR "PERSONA-001 goal/pain point" OR "[ASSUMPTION]"]

Depends On: [FR-XXX, FR-YYY] (omit if no dependency)

Priority Tags (MoSCoW + one-line justification):
- [MUST] — reason: [one sentence why it's critical]
OR
- [SHOULD] — reason: [one sentence why it's important]
OR
- [COULD] — reason: [one sentence why it's desirable]
OR
- [WONT] — reason: [one sentence why it's deferred]
```

### EXTRACTION RULES FROM DECISION SHEET

From the Decision Sheet, extract functional requirements for these process flows:

1. **PDF Extraction & Canonicalization**
   - Extract item names, quantities, subjects, ISBN (where applicable)
   - Handle typed text AND handwritten/image content
   - Normalize units (un, pacote, caixa, g, kg, ml, L, cm, mm)
   - Route confidence < 0.70 to user correction
   - Deduplicate items (exact match + probable duplicates to review queue)

2. **Category-Based Validation**
   - Enforce Required (R) fields per category (Books, Apostilas, Dictionaries, Notebooks, Art Materials, General Supplies)
   - Reject Forbidden (F) field values per category
   - Enforce Hard Constraints (HC) — e.g., ISBN for Books/Dictionaries, no ISBN for Apostilas
   - Route HC failures to review queue (do NOT auto-accept)

3. **ISBN Validation**
   - Accept ISBN-10 or ISBN-13 format
   - Normalize: strip hyphens, spaces, punctuation
   - Exact string match post-normalization
   - If missing: request user completion before search

4. **Brand Substitution**
   - Default: exact brand match
   - If < 3 same-brand offers found: ask user before expanding to other brands
   - Record substitution reason codes

5. **Website & Trust Management**
   - Validate domain format, HTTPS reachability
   - Check ReclameAqui classification
   - Block explicitly bad-rated sites
   - Allow/review_required sites to activate for search
   - Auto-suspend after configurable failure streak

6. **Search & Ranking**
   - Query all activated websites for each item
   - Rank results by lowest total delivered price (item price + shipping)
   - Filter out results that fail HC (wrong ISBN, forbidden specs)
   - Rank candidates by trust (marketplace reputation + ReclameAqui)

7. **Item Editing & Versioning**
   - Allow user to edit item fields before search
   - Version changes with reason + timestamp
   - Override extraction values with edited values

8. **Export**
   - Export results as Excel + CSV
   - Include: item, selected offer, price, alternatives, confidence, source URL

### CONFIDENCE THRESHOLDS (From Decision Sheet)

These are NOT changeable; they define acceptance criteria:

**Extraction confidence**:
- ≥ 0.90: auto-accept
- 0.70–0.89: manual review before canon
- < 0.70: reject, request correction

**Matching confidence**:
- ≥ 0.92 + HC satisfied: candidate
- 0.75–0.91: review_required
- < 0.75: invalid, exclude

---

### HANDLING [ASSUMPTION] & AMBIGUITIES

If you cannot extract a clear FR from the Decision Sheet:
- DO NOT invent the requirement
- Instead, tag it [ASSUMPTION], explain what is ambiguous
- This will be resolved in Phase 3 (Section 8: Open Questions)

Example:
```
FR-022 [MUST]: The system shall [ASSUMPTION: need clarification on export format detail]...
Source: [ASSUMPTION — Decision Sheet says "Excel + CSV" but does not specify column ordering, decimal places, date format]
```

---

## SECTION 5: NON-FUNCTIONAL REQUIREMENTS

### SCOPE LIMITATION (Per Your Decision)

You will define NFRs ONLY in these categories:
- **Performance** (only: the 10-min target from Decision Sheet)
- **Maintainability** (code quality, logging, observability — only what Decision Sheet implies)

You will NOT define NFRs for: Security, Availability, Accessibility, Scalability, Compliance.

If numeric thresholds are missing (e.g., error rate, concurrency, file size limits), mark them:
```
[THRESHOLD NEEDED — no source provided]
```

### NAMING CONVENTION

- **ID Format**: NFR-001, NFR-002, NFR-003, ... (sequential, no gaps)
- **Statement Format**: Same as FR: "The system shall [quality attribute statement]"

### REQUIRED FIELDS FOR EACH NFR

```
NFR-XXX [PRIORITY]: [Requirement statement]

Acceptance Criteria:
[Binary, human-verifiable AND automatable condition]

Source: [One of: "PRD Decision Sheet section [name]" OR "[ASSUMPTION]" OR "[THRESHOLD NEEDED — specify what is missing]"]

Priority Tags (MoSCoW + one-line justification):
- [MUST] — reason: [one sentence]
- [SHOULD] — reason: [one sentence]
- [COULD] — reason: [one sentence]
- [WONT] — reason: [one sentence]
```

### PERFORMANCE NFRs (From Decision Sheet)

Decision Sheet states: **"Up to 10 minutes per list (MVP)"**

Extract this as one or more Performance NFRs. Example:

```
NFR-001 [MUST]: The system shall process a school material list (up to [THRESHOLD NEEDED — max items per list]) end-to-end (extract + deduplicate + search + rank + export) within 10 minutes on [THRESHOLD NEEDED — reference environment].

Acceptance Criteria:
- Given a school material PDF list with [THRESHOLD NEEDED] items, when the user initiates processing, the system shall complete all phases (extraction, deduplication, website search, ranking, export) and present results within 10 minutes (measured from list upload to dashboard display).
- Measurement: automated timer on production environment; baseline established at MVP launch.

Source: "PRD Decision Sheet — Performance Target: Up to 10 minutes per list (MVP)"

Priority: [MUST] — reason: MVP viability depends on acceptable user wait time; beyond 10 min, user experience breaks.
```

### MAINTAINABILITY NFRs (Infer from Decision Sheet)

Decision Sheet mentions:
- Item versioning (reason + timestamp)
- Logging of merge resolution
- Manual review queues for ambiguous cases
- Confidence scores tracked
- Failure streak tracking for websites

These imply logging, observability, and auditability requirements. Create NFRs that reflect these.

Example:

```
NFR-XXX [SHOULD]: The system shall maintain an audit log of all item extraction, deduplication, and user edit actions with timestamp, user action, and reason.

Acceptance Criteria:
- Every extraction result includes confidence score (stored).
- Every deduplication decision (auto or manual) is logged with merge criteria + user decision (if manual).
- Every item edit includes reason + timestamp.
- Logs are queryable by item ID, action type, date range.

Source: "PRD Decision Sheet — Item Characteristic Editing, Duplicate Detection, Validation Gates"

Priority: [SHOULD] — reason: Enables debugging, compliance, and user transparency; not blocking MVP but essential for pilot validation.
```

---

## SECTION 6: MoSCoW PRIORITY SUMMARY

### FORMAT

Provide a table:

```
| Priority | Requirement IDs |
|----------|-----------------|
| MUST | FR-001, FR-002, FR-003, ... NFR-001, NFR-002, ... |
| SHOULD | FR-XXX, FR-YYY, ... NFR-XXX, ... |
| COULD | FR-ZZZ, ... |
| WONT | [List any WONT items, if any] |
```

This section is auto-generated from your FR/NFR priority tags. Do not add explanations here — those remain in Sections 4-5.

---

## ACCEPTANCE CRITERIA FOR PHASE 2 OUTPUT

Your output is acceptable if:

- ✅ All FR/NFR IDs are sequential with no gaps (FR-001 through FR-N, NFR-001 through NFR-M)
- ✅ Every FR/NFR follows the required format (ID, statement, acceptance criteria, source, priority + justification)
- ✅ Every acceptance criterion is binary (pass/fail, human + automatable)
- ✅ Every requirement is traceable to Decision Sheet OR tagged [ASSUMPTION] OR marked [THRESHOLD NEEDED]
- ✅ All confidence thresholds from Decision Sheet are embedded in acceptance criteria (not invented)
- ✅ Section 5 covers ONLY Performance + Maintainability; other NFR categories are omitted
- ✅ Section 6 is a clean table (auto-generated from FR/NFR tags)
- ✅ No duplicate requirement IDs
- ✅ No statements that contradict each other (if you find a conflict, flag it in a [CONFLICT] note)

---

## OUTPUT FORMAT

Provide your response as a single markdown file with this structure:

```markdown
# PRD: School Material Price Finder (Brazil MVP)
## PHASE 2 OUTPUT — Sections 4–6

### Section 4: Functional Requirements

#### FR-001 [MUST]: [Requirement statement]
**Acceptance Criteria:**
- [Criterion 1]
- [Criterion 2]
- [Criterion 3]

**Source**: [Source reference]

**Depends On**: [FR-XXX list or "None"]

**Priority**: [MUST] — reason: [one sentence]

---

#### FR-002 [SHOULD]: [Requirement statement]
[Same structure as above]

---

[Continue for all FR through FR-N]

### Section 5: Non-Functional Requirements

#### NFR-001 [MUST]: [Performance requirement statement]
**Acceptance Criteria:**
- [Criterion 1]
- [Criterion 2]

**Source**: [Source reference]

**Priority**: [MUST] — reason: [one sentence]

---

#### NFR-002 [SHOULD]: [Maintainability requirement statement]
[Same structure]

---

[Continue for all NFR through NFR-M]

### Section 6: MoSCoW Priority Summary

| Priority | Requirement IDs |
|----------|-----------------|
| MUST | [List] |
| SHOULD | [List] |
| COULD | [List] |
| WONT | [List or "None"] |

---
## HANDOFF NOTE
This Phase 2 output will be consumed by Phase 3 (PROMPT-3-GOVERNANCE).
All FR/NFR IDs assigned here are CANONICAL and will not change in downstream phases.
Do NOT modify this output after Phase 2 completion.
```

---

## PRD DECISION SHEET (DATA SOURCE — SAME AS PHASE 1)

[Same full Decision Sheet as provided in PROMPT-1-FOUNDATIONAL — use it to extract all FR/NFR requirements]

---

## VALIDATION CHECKLIST (BEFORE SUBMISSION)

- [ ] Are all FR/NFR IDs sequential with no gaps?
- [ ] Does every FR/NFR have: statement, acceptance criteria, source, priority + justification?
- [ ] Are all acceptance criteria binary and automatable?
- [ ] Is every requirement traceable to Decision Sheet, [ASSUMPTION], or [THRESHOLD NEEDED]?
- [ ] Are confidence thresholds (0.90, 0.70, 0.75, 0.92) embedded in acceptance criteria?
- [ ] Section 5 covers ONLY Performance + Maintainability (no other NFR categories)?
- [ ] Section 6 is a clean, readable table?
- [ ] Are there any duplicate IDs? (There should NOT be)
- [ ] Are there any contradictions between FR/NFR? (If yes, flag them as [CONFLICT])

---

## NEXT STEPS

Once this Phase 2 output is approved by the user:

1. User will provide your Phase 2 output + Phase 1 output to GitHub Copilot with PROMPT-3-GOVERNANCE
2. PROMPT-3 will create Sections 7-10 + [PRD_HANDOFF_BLOCK] + CONTEXT.md
3. User can then assemble all three outputs into a final PRD document

---

**Generate Phase 2 Output now. Use the format specified in the OUTPUT FORMAT section above.**