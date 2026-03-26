# PRD Addendum: School-Defined Seller Exclusivity (FR-022)

**Status**: PENDING STAKEHOLDER SIGN-OFF  
**Date**: March 26, 2026  
**References**: PRD.md (FR-001..FR-021) [BASELINE — NOT MODIFIED]  
**Approver**: _________________ Date: _________  
**Architecture Lead**: _________________ Date: _________

---

## 1. Executive Summary

Schools often mandate that specific materials be purchased from specific suppliers (e.g., "uniforms from Uniforme São Paulo only"). Current system (FR-001..FR-021) does not capture or enforce these constraints.

This addendum extends the extraction and search logic to recognize, validate, and respect school-defined seller restrictions while maintaining operator override capability and audit traceability.

**In Scope**:
- Extract school-defined exclusivity markers from documents
- Validate required sellers against active source set
- Route conditional search based on exclusivity state
- Log conflicts and operator overrides
- Rank with soft preference for preferred sellers (tie-break only)

**Out of Scope**:
- Dynamic seller contract negotiation
- Multi-school marketplace (single school context per MVP)
- Seller-defined restrictions (only school-defined constraints)
- Advanced conflict resolution UI (operator sees log; manual override sufficient for MVP)

---

## 2. FR-001 Extension: Extracted Field Additions

**Original FR-001**: Extract mixed-PDF item fields with confidence scores.

**Extension**: Add school-defined seller constraints to extracted fields.

### New Fields Extracted (per item)
```
school_exclusive (bool)
  - true: item restricted to required_sellers only
  - false (default): item searchable from any active source
  - confidence: derived from extraction; inherited from marker detection confidence

required_sellers (list[str])
  - List of seller names where item MUST be purchased
  - Empty if school_exclusive=false
  - Example: ["Uniforme São Paulo", "Livraria Contrato"]
  - All names normalized to canonical representation (via MODULE-002-04)

preferred_sellers (list[str])
  - List of sellers to prioritize in ranking (soft hint, not mandatory)
  - Applies only when school_exclusive=false
  - Used as secondary sort key in ranking, not search filter
  - Example: ["Amazon", "Saraiva"]

exclusive_source (string)
   - How exclusivity was determined: "document_notation" | "user_annotation" | None
   - Tracks source of information for conflict resolution (source-precedence policy applied)
```

### Extraction Detection Logic (Proposed; MDAP will formalize)

1. **Document pre-pass**: Scan for legends, footnotes, metadata
   - Example: "* = school exclusive" or "Items marked [S] = Uniforme São Paulo only"
   - Result: notation_rules dict applied to subsequent items

2. **Line-level matching**: For each extracted item, apply notation rules
   - Example: Item name contains "*" → school_exclusive=true
   - Example: Item tagged with [S] → required_sellers=["Uniforme São Paulo"]

3. **User annotation override** (post-extraction): Operator can amend exclusivity
   - Handled by FR-018 (user edits), not extraction itself

### Acceptance Criteria (Extended from FR-001)

- AC1: Extracted items include school_exclusive, required_sellers, preferred_sellers fields
- AC2: If no exclusivity markers present → school_exclusive=false, required_sellers=[]
- AC3: If document notation rule present → school_exclusive=true, required_sellers populated
- AC4: Seller names extracted match configured seller list (via MODULE-002-04 canonical representation)
- AC5: confidence scores for exclusivity fields are present and valid [0.0, 1.0]
- AC6: original values AND extracted/normalized values stored for traceability

---

## 3. FR-015 Extension: Conditional Search Routing

**Original FR-015**: Query all activated eligible websites for each search-eligible item.

**Extension**: Respect school-defined seller restrictions in search scope.

### New Routing Logic
```
IF school_exclusive=true:
  - Query ONLY sellers in required_sellers list
  - Filter active sellers via MODULE-002-04 eligibility
  - If required_sellers=[S1, S2] but only S1 is active:
    - Query S1 only
  - If required_sellers=[S1, S2] but BOTH are blocked/inactive:
    - Route to review_required (conflict: school says mandatory, system says unavailable)

ELSE (school_exclusive=false):
  - Query all active eligible sellers (original behavior)
  - Use preferred_sellers as ranking hint ONLY (not filter)
  - If preferred_sellers contains a seller not in active set:
    - Ignore that seller in ranking; still search all active sources
    - Do NOT route to review_required (preferred is optional)
```

### Acceptance Criteria (Extended from FR-015)

- AC1: If school_exclusive=true, search queries only required_sellers that are active/eligible
- AC2: If school_exclusive=true and no required sellers are active, route to review_required with reason="no_active_required_sellers"
- AC3: If school_exclusive=false, search queries all active sellers (original behavior)
- AC4: preferred_sellers does NOT filter search; used in ranking only
- AC5: Fallback semantics: if preferred seller not in active set, drop from ranking hint; still search other sources
- AC6: Routing decision logged with: item_id, school_exclusive state, required_sellers, active_sellers_queried

---

## 4. FR-022 (New): School-Defined Seller Exclusivity Resolution

**User Story**: As a system operator, I want to resolve school-defined seller constraints and validate them against active sources, so that items are searched correctly without manual intervention for every case.

### Responsibility

- Determine whether an extracted item is school-exclusive
- Validate required sellers exist and are active
- Log conflicts when required sellers are blocked
- Route ambiguous cases for operator review
- Provide operator override capability
- Track all decisions in audit trail

### Acceptance Criteria

1. **AC1 — Exclusive Item with Active Required Seller**
   - Given: school_exclusive=true, required_sellers=["Seller A"], Seller A is active/eligible
   - When: resolution runs
   - Then: Status=eligible, reason="exclusive_with_active_sellers", item proceeds to search

2. **AC2 — Exclusive Item with No Active Required Sellers**
   - Given: school_exclusive=true, required_sellers=["Seller A", "Seller B"], both blocked/inactive
   - When: resolution runs
   - Then: Status=review_required, reason="no_active_required_sellers", conflict logged

3. **AC3 — Exclusive Item with Some Active Required Sellers**
   - Given: school_exclusive=true, required_sellers=["Seller A", "Seller B"], Seller A active, Seller B blocked
   - When: resolution runs
   - Then: Status=eligible, active_sellers_to_query=["Seller A"], conflict logged (for operator awareness)

4. **AC4 — Non-Exclusive Item**
   - Given: school_exclusive=false (or default), preferred_sellers=["Seller X"]
   - When: resolution runs
   - Then: Status=eligible, search_scope=all_active_sellers, preferred_sellers passed to ranking only

5. **AC5 — Conflict Logging**
   - Given: Any conflict (blocked required seller, document vs. user mismatch)
   - When: resolution runs
   - Then: Conflict logged with: item_id, conflict_type, source_of_information, timestamp, operator_action_if_override

6. **AC6 — Source-of-Information Precedence**
   - Given: Document says exclusive; user annotation says non-exclusive
   - When: conflict resolution runs
   - Then: Document state wins; user override requires operator acknowledgment logged as "operator_override_reason"

7. **AC7 — Operator Override**
   - Given: Item routed to review_required due to no active sellers
   - When: operator edits school_exclusive flag (exclusive→non-exclusive)
   - Then: Override logged with reason; item re-evaluated; decision logged to audit trail

8. **AC8 — Deterministic Decisions**
   - Given: Same item state
   - When: resolution runs multiple times
   - Then: Same decision every time (no non-deterministic behavior)

---

## 5. Design Clarifications (Formal Record)

### Source-of-Information Precedence
- The system applies a **source-precedence policy** to resolve conflicts between document-derived and user-provided exclusivity
- Default policy for MVP: document-derived value has precedence when both sources are present
- Within the same source, **more specific annotation wins** (e.g., line note beats legend)
- **Operator override** is explicit; logged as conflict resolution, not silent change

### Required vs. Preferred Semantics
- **required_sellers**: Mandatory purchase source. If school says exclusive to Seller A, and Seller A is inactive, item must be reviewed.
- **preferred_sellers**: Soft priority hint. If preferred seller is inactive, item is still searched elsewhere; no conflict.
- In ranking: preferred_sellers is a **secondary sort key** only (tie-break after main delivered-price signal). Never injected into composite score.

### Blocked Required Seller Behavior
- If school requires Seller X, but Seller X is currently blocked → **Show conflict + allow operator override**
- Operator can choose: (a) Keep exclusive (wait for seller reactivation), or (b) Make non-exclusive (search elsewhere)
- Decision logged to audit trail

### Fallback Semantics (websearch_enabled=false)
- If preferred_sellers contains a seller not in configured sources, **route item to existing configured sources** (search proceeds; seller hint dropped)
- Do **NOT** route to review_required (preferred is optional)
- Item is still searched; just without the seller preference hint

### Ranking Effect of Preferred Sellers
- Preferred sellers used as **deterministic secondary sort key**:
  1. Primary sort: delivered_price (ascending)
  2. Secondary sort: is_preferred_seller (true > false)
  3. Tertiary sort: trust_signal (descending)
- **Never** inject into composite score (avoids normalization breaks, re-sorting issues, low-confidence flag changes)

---

## 6. Impact on Other FRs

| FR | Impact | Type |
|----|--------|------|
| FR-001 | Extended with school_exclusive, required_sellers, preferred_sellers fields | Extension |
| FR-015 | Extended with conditional routing based on exclusivity state | Extension |
| FR-018 | Operator can edit school_exclusive field (user_edit_handler handles as normal field edit) | Extension |
| FR-019 | Conflicts logged to audit trail alongside other item versioning | Integration |
| FR-020 | Export includes school_exclusive state in output metadata (informational, not filtered by it) | Extension |
| All other FRs | No change | None |

---

## 7. Dependencies & Scheduling

### Governance Approval Required Before MDAP
- [ ] Stakeholder: This addendum is approved for implementation
- [ ] Stakeholder: Option B (add MODULE-003-05) is chosen
- [ ] Architecture Lead: Addendum scope aligns with existing structure

### MDAP Re-Gate Trigger
- Once approved, EPIC-003 MDAP Stage 5 must be re-run as MDAP CIR-001 (MODULE-003-05 addition)

### Implementation Sequencing
1. MDAP CIR-001 approved
2. MODULE-003-05 implemented (search_ranking/school_exclusivity_resolver.py)
3. Extensions to pdf_ingestion_field_extraction.py, query_orchestrator.py, ranking_engine.py, user_edit_handler.py
4. Tests + integration

---

## 8. Sign-Off

**Addendum Status**: Ready for stakeholder review

**Stakeholder Approval**:
- Product Owner: _________________ Date: _________
- Architecture Lead: _________________ Date: _________

**MDAP Next Step**: Upon approval, trigger MDAP CIR-001 for EPIC-003 (MODULE-003-05 addition)