# PROMPT-1-FOUNDATIONAL
## PRD Phase 1: Sections 1–3 (Executive Summary, Problem Statement, User Personas)

**Status**: Entry point — starts the three-phase PRD creation pipeline  
**Next Phase**: PROMPT-2-REQUIREMENTS (will consume this output)  
**Governance**: PRD.pdf template (sections 1-3 + GC-1 through GC-7)  
**Data Source**: PRD Decision Sheet (provided at end of this prompt)  

---

## INSTRUCTIONS FOR GITHUB COPILOT

You are creating the **foundational sections** of a Product Requirements Document (PRD) for a school material price finder tool. This is Phase 1 of 3. Your output will be used by Phase 2 to construct all functional and non-functional requirements.

### YOUR ROLE
- Extract product intent from the Decision Sheet
- Structure it according to PRD.pdf template sections 1-3
- Avoid technical depth (save that for later phases)
- Flag ANY assumptions you make as [ASSUMPTION] — do NOT invent details
- Maintain traceability: every statement should map back to the Decision Sheet

### SECTION 1: EXECUTIVE SUMMARY
**Template**: One paragraph describing the product, primary user, core need, and single measurable success outcome.

**Rules**:
- DO: State the product in plain language
- DO: Name the primary user type
- DO: Define ONE measurable outcome (e.g., "users find cheapest option 80% faster")
- DON'T: Discuss technical implementation, architecture, or deployment
- DON'T: Over-promise outcomes not derivable from the Decision Sheet

**Input basis**: "Extract items from mixed PDFs, search Brazilian retailers, return cheapest with trusted ranking."

---

### SECTION 2: PROBLEM STATEMENT
**Template**: 4 subsections: (a) specific problem/gap, (b) who experiences it, (c) why existing solutions insufficient, (d) consequence of not solving.

**Rules**:
- DO: Be concrete — reference the school material context
- DO: Explain why price comparison is manual today (gap identification)
- DON'T: Propose solutions; only state the problem space
- DON'T: Invent pain points not grounded in the product idea

**Input basis**: Decision Sheet mentions "personal use, non-commercial, Brazil" + retail search automation.

---

### SECTION 3: USER PERSONAS
**Template**: Single persona (per your decision to avoid over-assumption).

**Exact format**:
```
PERSONA-001: School List User
- Role: Parent, school administrator, or budget-conscious shopper
- Primary Goal: [derive from Decision Sheet: find complete school material list at lowest total cost]
- Primary Pain Point: [derive from Decision Sheet: currently manual searching, time-consuming, no price comparison]
```

**Rules**:
- DO: Create ONE persona only (as you specified)
- DO: Use "PERSONA-001" identifier (this will be canonical in Phase 2)
- DO: Ground goal + pain point in the Decision Sheet
- DON'T: Invent demographic details (age, location, income)
- DON'T: Create secondary personas

---

## ACCEPTANCE CRITERIA FOR PHASE 1 OUTPUT

Your output is acceptable if:
- ✅ Section 1 is exactly one paragraph (50-100 words) with product description + user + measurable outcome
- ✅ Section 2 has all four subsections (problem, who, why insufficient, consequence) with no solution language
- ✅ Section 3 defines PERSONA-001 with role, goal, and pain point derived from Decision Sheet
- ✅ NO technical jargon (APIs, databases, algorithms, UI frameworks)
- ✅ NO invented details — every statement traces to Decision Sheet or is tagged [ASSUMPTION]
- ✅ NO scope creep — focus only on problem/user space, not features or roadmap

---

## OUTPUT FORMAT

Provide your response as a single markdown file with this structure:

```markdown
# PRD: School Material Price Finder (Brazil MVP)
## PHASE 1 OUTPUT — Sections 1–3

### Section 1: Executive Summary
[Your paragraph here]

### Section 2: Problem Statement
#### 2.1 The Problem/Gap
[Your text]
#### 2.2 Who Experiences This Problem
[Your text]
#### 2.3 Why Existing Solutions Are Insufficient
[Your text]
#### 2.4 Consequence of Not Solving
[Your text]

### Section 3: User Personas
#### PERSONA-001: School List User
- **Role**: [Your text]
- **Primary Goal**: [Your text]
- **Primary Pain Point**: [Your text]

---
## HANDOFF NOTE
This Phase 1 output will be consumed by Phase 2 (PROMPT-2-REQUIREMENTS).
No modifications to this section after Phase 1 completion.
```

---

## PRD DECISION SHEET (DATA SOURCE)

Below is the complete product model. Extract ALL foundational information from here:

```
# PRD Decision Sheet — School Material Price Finder (Brazil MVP)

**Project**: AI-assisted school material price search tool  
**Market**: Brazil (São Paulo region, scalable nationally)  
**Scope**: Personal use, non-commercial  
**Environment**: `matfinder` (Conda, Python 3.12)

## Business Objectives
- Extract items from mixed PDFs (typed + image/handwritten).
- Create one canonical item list before any search.
- Search known Brazilian retailers and marketplaces.
- Return cheapest total price per item (item + shipping included).
- Output via dashboard with Excel/CSV export.

## Category Matrix
Covers 6 item types: Books, Apostilas, Dictionaries, Notebooks, Art Materials, General Supplies
Each with applicability rules (R=Required, O=Optional, F=Forbidden, HC=Hard Constraint)

## ISBN Rule
- Exact string match after normalization (strip hyphens, spaces, punctuation).
- Required for all Book and Dictionary categories.
- If missing after extraction, request user completion before search.
- Format: ISBN-10 or ISBN-13.

## Reuse Logic
- "já utilizado no [year]" → `reuse_allowed = true`.
- "uso obrigatório" → `reuse_allowed = false`.

## Apostila Special Case
- No ISBN allowed.
- Source tag: "Reprografia".
- Availability: external (non-marketplace only).

## Matching & Ranking

### Brand Substitution Policy
- Default: exact brand match.
- If < 3 same-brand offers found: ask user per item before expanding to other brands.

### Ranking Formula
1. Hard constraints must pass (ISBN match, forbidden specs excluded).
2. If HC satisfied, rank by lowest total delivered price = item price + shipping.
3. Seller trust: interpret via marketplace native reputation + ReclameAqui classification.

### Confidence Thresholds
- **Extraction**:
  - ≥ 0.90: auto-accept.
  - 0.70–0.89: keep but manual review before canonicalization.
  - < 0.70: reject, request user correction.
- **Matching**:
  - ≥ 0.92 + HC satisfied: candidate.
  - 0.75–0.91: review_required candidate.
  - < 0.75: invalid, exclude from results.

## Sources & Trust

### Website Onboarding (Local MVP Operator)
1. **Add**: operator enters domain, label, category, notes.
2. **Validate**: domain format, HTTPS reachable, product discovery, pricing signals.
3. **Trust**: ReclameAqui status lookup; classify as allowed/review_required/blocked.
4. **Approve**: allowed/review_required sites activate; blocked sites excluded.

### Initial Known Sites
- Mercado Livre.
- Americanas.
- Specialized sites by item category.

## Item Characteristic Editing
- Users can add/edit item fields before search.
- Changes versioned with reason/timestamp.
- Edited values override extraction for downstream matching.

## Duplicate Detection
- **Exact duplicate**: same category + name/title + mandatory identifiers + core specs.
- **Probable duplicate**: high text similarity + compatible specs → merge review queue.
- **Unit normalization**: canonical set (un, pacote, caixa, g, kg, ml, L, cm, mm).

## User Interface & Output
### Dashboard
- Simple web app.
- Show extracted item list with per-item edit capability.
- Show search results with selected offer, alternatives, confidence flags, source.
- Per-item confirmation for brand fallback.

### Export
- Excel format with all selected fields, offer details, alternatives, confidence, source URL.
- CSV format equivalent.

### Performance Target
- Up to 10 minutes per list (MVP).

## Validation Gates (Pilot Acceptance)
1. All 8 PDF lists generate canonical item lists with logged merge resolution.
2. Category matrix validation catches missing required/forbidden fields.
3. ISBN logic enforces exact match; rejects mismatches.
4. Apostila items route to external-only sources.
5. Website onboarding correctly blocks bad-rated domains.
6. Low-confidence items route to review; no silent auto-acceptance.
7. Final export includes offer, alternatives, confidence, source metadata.

## Out of Scope (MVP)
- Multi-user access control.
- LGPD/commercial compliance.
- Product image matching.
- Shipping address localization (uses marketplace default).
- Price history or predictive analytics.
```

---

## VALIDATION CHECKLIST (BEFORE SUBMISSION)

Run through these checks before finalizing Phase 1 output:

- [ ] Section 1: Is it exactly one paragraph? Does it name the user and success outcome?
- [ ] Section 2: Are there four subsections with no solution language?
- [ ] Section 3: Does PERSONA-001 have role + goal + pain point derived from Decision Sheet?
- [ ] All three sections: Do they avoid technical jargon (APIs, databases, Python, etc.)?
- [ ] Traceability: Can you trace every statement back to the Decision Sheet?
- [ ] No invented details: Are there any assumptions that should be tagged [ASSUMPTION]?

---

## NEXT STEPS

Once this Phase 1 output is approved by the user (via GitHub review/comment):

1. User will provide your Phase 1 output to GitHub Copilot with PROMPT-2-REQUIREMENTS
2. PROMPT-2 will consume Phase 1 output and create Sections 4-5 (all FR/NFR)
3. PROMPT-3 will consume Phases 1-2 and create Sections 6-10 + handoff blocks

---

**Generate Phase 1 Output now. Use the format specified in the OUTPUT FORMAT section above.**