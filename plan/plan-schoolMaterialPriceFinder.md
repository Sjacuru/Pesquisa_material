# PRD Decision Sheet — School Material Price Finder (Brazil MVP)

**Project**: AI-assisted school material price search tool  
**Market**: Brazil (São Paulo region, scalable nationally)  
**Scope**: Personal use, non-commercial  
**Environment**: `matfinder` (Conda, Python 3.12)

---

## Business Objectives
- Extract items from mixed PDFs (typed + image/handwritten).
- Create one canonical item list before any search.
- Search known Brazilian retailers and marketplaces.
- Return cheapest total price per item (item + shipping included).
- Output via dashboard with Excel/CSV export.

---

## Data & Extraction

### Pre-Search Flow
- Ingest all source documents into single deduplicated item catalog.
- Normalize quantities and units.
- Route unresolved duplicates to manual review queue.

### Category Matrix (Authoritative Applicability)

| Attribute | Book | Apostila | Dictionary | Notebook | Art Materials | General Supplies |
| --- | --- | --- | --- | --- | --- | --- |
| name | R | R | R | R | R | R |
| quantity | R | O | O | R | R | R |
| subject | R | R | O | R | O | F |
| isbn | HC | F | HC | F | F | F |
| reuse_allowed | HC | F | HC | F | F | F |
| title | R | O | R | F | F | F |
| authors | R | O | O | F | F | F |
| publisher | R | O | R | F | F | F |
| edition | HC | F | O | F | F | F |
| year | HC | F | O | F | F | F |
| language | HC | F | HC | F | F | F |
| specifications | O | O | O | HC | HC | HC |
| notes | O | O | O | O | O | O |

Legend: R = Required, O = Optional, F = Forbidden, HC = Hard Constraint

### ISBN Rule
- Exact string match after normalization (strip hyphens, spaces, punctuation).
- Required for all Book and Dictionary categories.
- If missing after extraction, request user completion before search.
- Format: ISBN-10 or ISBN-13.

### Reuse Logic
- "já utilizado no [year]" → `reuse_allowed = true`.
- "uso obrigatório" → `reuse_allowed = false`.

### Apostila Special Case
- No ISBN allowed.
- Source tag: "Reprografia".
- Availability: external (non-marketplace only).

### Physical Specifications
- Hard constraints capture forbidden models and required tolerances.
- Example: "modelo barroco (não serve germânico)" → `model: baroque, forbidden: [german]`.

---

## Matching & Ranking

### Brand Substitution Policy
- Default: exact brand match.
- If < 3 same-brand offers found: ask user per item before expanding to other brands.
- Record substitution reason codes.

### Ranking Formula
1. Hard constraints must pass (ISBN match, forbidden specs excluded, mandatory identifiers present).
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
- **Hard constraint rule**: Any HC failure overrides confidence score; item is invalid.

### Low-Confidence Handling
- Route to manual review instead of auto-discard if:
  - Medium-confidence extraction/match band.
  - Missing mandatory fields for category.
  - Brand fallback expansion needed.
  - Conflicts between source text and inferred values.

---

## Sources & Trust

### Website Onboarding (Local MVP Operator)
1. **Add**: operator enters domain, label, category, notes.
2. **Validate**: domain format, HTTPS reachable, product discovery, pricing signals.
3. **Trust**: ReclameAqui status lookup; classify as allowed/review_required/blocked.
4. **Approve**: allowed/review_required sites activate; blocked sites excluded.
5. **Recheck**: periodic validation every 30 days or after repeated failures.
6. **Suspend**: auto-suspend after configurable failure streak; route to review queue.

### Initial Known Sites
- Mercado Livre.
- Americanas.
- Specialized sites by item category (e.g., bookstores for books).

### Trust Rule
- Explicitly bad-rated sites (ReclameAqui): blocked automatically.
- All other sites: searchable unless suspended.

---

## Item Characteristic Editing

- Users can add/edit item fields before search.
- Changes versioned with reason/timestamp.
- Edited values override extraction for downstream matching.

---

## Duplicate Detection

- **Exact duplicate**: same category + name/title + mandatory identifiers + core specs.
- **Probable duplicate**: high text similarity + compatible specs/units → merge review queue.
- **Unit normalization**: canonical set (un, pacote, caixa, g, kg, ml, L, cm, mm). Ambiguous conversions → review queue.

---

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

---

## Validation Gates (Pilot Acceptance)

1. All 8 PDF lists generate canonical item lists with logged merge resolution.
2. Category matrix validation catches missing required/forbidden fields.
3. ISBN logic enforces exact match; rejects mismatches.
4. Apostila items route to external-only sources.
5. Website onboarding correctly blocks bad-rated domains.
6. Low-confidence items route to review; no silent auto-acceptance.
7. Final export includes offer, alternatives, confidence, source metadata.

---

## Out of Scope (MVP)

- Multi-user access control.
- LGPD/commercial compliance.
- Product image matching.
- Shipping address localization (uses marketplace default).
- Price history or predictive analytics.
