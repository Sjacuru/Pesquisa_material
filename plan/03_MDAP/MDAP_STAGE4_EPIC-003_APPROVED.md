# MDAP Stage 4: Scope & Risk Review
## EPIC-003: Multi-Source Search, Match Classification, Ranking, and Apostila Routing

**Status**: SCOPE_REVIEW_APPROVED  
**Date**: March 24, 2026  
**Reviewer**: User  
**Epic ID**: EPIC-003  
**Module Count**: 4 modules (all retained)  
**Rejected Scope Patterns**: 2  

---

## A. REJECTED SCOPE PATTERNS (Out of Scope for EPIC-003 MDAP)

### Pattern 1: Real-Time Ranking Optimization (ML-Based Relevance Signals)
**Proposal Summary**:  
Integrate machine learning model for dynamic relevance scoring based on user click patterns, dwell time analytics, and conversion signals. Adaptive ranking weights would re-calibrate per user cohort and session context.

**Why Rejected**:
- ❌ Violates **Minimal Module Principle**: Would require 2+ additional modules (ML pipeline orchestrator, cohort-based feature aggregator, model serving wrapper)
- ❌ Violates **Rule 2A (Scope Creep)**: No functional requirement (FR-015..FR-021) explicitly requires ML-based optimization; FR-017 only requires ranked results delivery, not adaptive ranking
- ❌ Introduces **Unresolved Dependency**: ML model retraining cadence, offline evaluation environment, A/B test harness all unspecified in PRD
- ❌ **Cross-Epic Risk**: EPIC-002 source trust pipeline does not output click-stream or engagement metrics; external data source required (out of bounds)
- ✓ **Deferred to ARCHITECTURE**: ML-based ranking can be overlaid post-MDAP as optimization layer; foundational ranking (MODULE-003-03) supports configurable weights

**Traceability**: Relates to THRESHOLD-005 (peak concurrent user handling); deferred to post-launch optimization

---

### Pattern 2: Query Rewriting & Synonym Expansion
**Proposal Summary**:  
Module to expand user queries via synonym dictionary, handle common typos, and apply linguistic normalization (stemming, lemmatization). Enables better match rates for misspelled or colloquial search terms (e.g., "calc" → "calculus", "calc-based textbook").

**Why Rejected**:
- ❌ Violates **Single Domain Responsibility**: Query rewriting is distinct domain from orchestration (MODULE-003-01); synonym expansion is distinct from classification (MODULE-003-02)
- ❌ Violates **Minimal Module Principle**: Requires dedicated query linguistics module + synonym/typo dictionary management module (2 modules)
- ❌ **User Story Misalignment**: No user story (US-010..US-013) explicitly requires typo tolerance or synonym expansion; US-010 specifies "multi-source search request" without linguistic preprocessing
- ❌ **Hidden Complexity**: Synonym dictionary maintenance, version control, language-specific rules (Portuguese vs. English) introduces operational burden unbudgeted in MDAP
- ✓ **Deferred to ARCHITECTURE**: Query rewriting can be added as pre-processor to MODULE-003-01 if future user stories demand it

**Traceability**: Would add complexity to EPIC-003 without corresponding FR justification; compatible with future enhancement

---

## B. HIGH-RISK MODULE FLAGGING & MITIGATION

### MODULE-003-01: Query Orchestrator — HIGH RISK
**Risk Category**: Infrastructure & Concurrency  
**Expert Domains Required**: [Search Infrastructure, Distributed Query Execution]

**Risk Factors**:
1. **Orchestration Complexity**: Parallel query execution across 5-10 heterogeneous sources with varying latency (100ms to 5s). Timeout cascades, partial failure handling, result buffering all subject to race conditions.
2. **Cross-Epic Dependency Chain**: Depends on MODULE-001-05 + MODULE-001-07 + MODULE-002-04 outputs being materialized and available at query time. If upstream modules fail mid-batch, MODULE-003-01 has no fallback strategy.
3. **Backpressure Handling**: Result queue buffer (max 100K) must prevent downstream blocking. If MODULE-003-02 slows, MODULE-003-01 must gracefully handle buffer saturation without source timeout collision.
4. **Gateway Jitter**: Per-source API rate limits and circuit breakers (if sources go down) must not cascade into dropped queries or user-visible latency spikes.

**Mitigation Strategies**:
- [ ] **Pre-ARCHITECTURE**: Establish test harness with mock heterogeneous sources (varying latency profiles: 100ms, 500ms, 5s)
- [ ] **Pre-ARCHITECTURE**: Define timeout escalation policy: per-source timeout events trigger exponential backoff (1s, 2s, 4s) before source is marked unavailable
- [ ] **Pre-ARCHITECTURE**: Buffer saturation threshold triggers graceful degradation mode (reduce concurrent source queries, not reject incoming searches)
- [ ] **ARCHITECTURE Phase**: Implement circuit breaker pattern per source (3 consecutive timeouts → 60s isolation window, then test recovery)
- [ ] **ARCHITECTURE Phase**: Add observability: log source availability/latency percentiles per query wave; alert on cross-source latency skew > 2x median

**Sign-Off Gate**: Must not proceed to deployment until mitigation strategies prototyped and validated against infrastructure test harness

---

### MODULE-003-02: Match Classifier — MEDIUM RISK (Upgraded to Reviewed)
**Risk Category**: Data Quality & Deduplication Accuracy  
**Expert Domains Required**: [Data Classification, String/Entity Matching]

**Risk Factors**:
1. **Deduplication Accuracy Baseline (95%)**: Fuzzy matching at Levenshtein distance ≤ 3 may miss legitimate duplicates (e.g., "Calculus, 9th Edition" vs. "Calculus 9e") or over-match (e.g., "Statistics" vs. "Stats for Biologists"). 5% error rate in corpus of 100K results = 5K false negatives.
2. **Heterogeneous Source Schemas**: Title/author field naming conventions vary per source. Normalization edge cases: titles with special characters, Unicode handling, author name ordering (First Last vs. Last, First).
3. **Brand Substitution Interaction**: MODULE-002-02 injects brand substitutes; duplicates detected before substitution applied. Risk: same material under different brand names treated as distinct. Ordering in classification pipeline critical.

**Mitigation Strategies**:
- [ ] **Pre-ARCHITECTURE**: Validate 95% accuracy baseline on representative corpus of 10K results from actual sources (not synthetic data)
- [ ] **Pre-ARCHITECTURE**: Document schema normalization rules per source (naming conventions, encoding, field order assumptions)
- [ ] **Test Harness**: Create A/B test dataset with 500 known duplicate pairs + 500 known distinct pairs; measure precision/recall against fuzzy match threshold
- [ ] **ARCHITECTURE Phase**: Add debug mode to log deduplication decisions (why matched, why not) for post-hoc accuracy review
- [ ] **ARCHITECTURE Phase**: If 95% baseline not met, escalate to expert domain review before production deployment

**Sign-Off Gate**: Must validate accuracy baseline against real source data before advancement

---

### MODULE-003-03: Ranking Engine — HIGH RISK
**Risk Category**: Algorithm Stability & User Experience  
**Expert Domains Required**: [Ranking Algorithms, Scoring Strategies, User Relevance Modeling]

**Risk Factors**:
1. **Multi-Factor Score Stability**: Composite score formula (reputation_weight * R + recency_weight * Rec + similarity_weight * Sim + classification_weight * C) assumes independent factors. Interactions between factors (e.g., old highly-reputable source vs. new low-reputation source) may produce unexpected rank inversions.
2. **Weight Calibration Sensitivity**: Alpha parameter values (reputation_weight, recency_weight, etc.) have outsized impact on final ranking. Small weight shifts (0.25 → 0.30) can dramatically reorder top 10 results. No principled tuning methodology defined.
3. **Source Reputation Coupling**: MODULE-003-03 depends on MODULE-002-05 failure rate data. If MODULE-002-05 is stale or contains NaN values (no failures recorded for new source), reputation scores become unreliable.
4. **User Expectation Mismatch**: No user study or A/B test defined to validate that ranked output matches user mental model of "relevance." High risk of user complaints ("Why is this result ranked so high?").

**Mitigation Strategies**:
- [ ] **Pre-ARCHITECTURE**: Define principled weight calibration methodology (linear regression on historical click-through rates, or expert panel consensus scoring with statistical validation)
- [ ] **Test Harness**: Create scoring function test suite with known query-result pairs where expected rank order is validated (10+ scenarios minimum)
- [ ] **ARCHITECTURE Phase**: Implement NaN detection in reputation lookup; fallback to neutral (0.5) score if source has no failure history
- [ ] **ARCHITECTURE Phase**: Add sensitivity analysis tool: log score deltas when weights perturbed ±10%; alert if rank order changes
- [ ] **Post-Launch**: A/B test ranking weights against baseline; measure user engagement (click-through, dwell time) to validate expected behavior
- [ ] **Observability**: Log percentiles of composite scores per query wave; alert if distribution shape changes unexpectedly (e.g., bimodal)

**Sign-Off Gate**: Weight calibration methodology and sensitivity analysis tool must be defined before ARCHITECTURE phase begins

---

### MODULE-003-04: Apostila Routing Guard — MEDIUM RISK
**Risk Category**: Policy Enforcement & Provenance Chain Validation  
**Expert Domains Required**: [Policy Evaluation, Source Attribution Rules]

**Risk Factors**:
1. **Provenance Chain Brittleness**: MODULE-003-04 queries provenance index from MODULE-001-04 dedup output. If dedup cluster IDs are not properly scoped or versioned, Apostila results may reference stale/missing clusters, causing silent rejections.
2. **Immutability Contract Fragility**: Module enforces "no brand substitution override" for Apostila results. If downstream UI layer ignores this contract and applies brand substitution anyway, Apostila attribution is lost. No enforcement mechanism beyond documentation.
3. **Classification Tag Accuracy Dependency**: Apostila identification relies on MODULE-003-02 classification tag. If classifier misses Apostila material (false negative), those results bypass routing guard and enter generic tier, violating source attribution policy.

**Mitigation Strategies**:
- [ ] **Pre-ARCHITECTURE**: Validate provenance index schema matches MODULE-001-04 dedup output schema exactly (cluster ID format, timestamp precision, field presence)
- [ ] **Test Harness**: Create test corpus with 100 known Apostila materials + 100 non-Apostila materials; verify MODULE-003-04 rejection behavior on incomplete/stale provenance index
- [ ] **ARCHITECTURE Phase**: Implement contract enforcement: MODULE-003-04 output includes immutability flag; enforce at API boundary (reject downstream mutations with HTTP 409 Conflict if flag set)
- [ ] **ARCHITECTURE Phase**: Add audit trail: log all Apostila rejections (reason: missing provenance link, classification confidence < threshold, etc.) for compliance review
- [ ] **Cross-Epic Validation**: MODULE-001-04 dedup output must be materialized and stable before MODULE-003-04 starts; no runtime discovery

**Sign-Off Gate**: Provenance index schema validation and immutability enforcement mechanism must be tested before advancement

---

## C. SCOPE CEILING VALIDATION

**In-Scope (Confirmed)**:
- ✓ Multi-source query orchestration (MODULE-003-01)
- ✓ Result deduplication and classification (MODULE-003-02)
- ✓ Multi-factor ranking (MODULE-003-03)
- ✓ Apostila source attribution routing (MODULE-003-04)

**Out-of-Scope (Not Included)**:
- ❌ ML-based ranking optimization (Pattern 1)
- ❌ Query rewriting & synonym expansion (Pattern 2)
- ❌ User feedback loop for relevance recalibration (no user story specified)
- ❌ A/B testing infrastructure (deferred to ARCHITECTURE)
- ❌ Linguistic preprocessing (deferred to post-launch enhancement)

**Scope Boundary Compliance**: ✓ All 4 modules strictly bounded to FR-015..FR-021; no scope creep detected

---

## D. MODULE RETENTION DECISION

| Module | Retention Status | Justification |
|--------|------------------|---------------|
| MODULE-003-01 | ✓ RETAINED | High risk mitigated via orchestration test harness; critical path for US-010 realization |
| MODULE-003-02 | ✓ RETAINED | Medium risk mitigated via accuracy validation on real source corpus |
| MODULE-003-03 | ✓ RETAINED | High risk mitigated via weight calibration methodology + sensitivity analysis |
| MODULE-003-04 | ✓ RETAINED | Medium risk mitigated via provenance chain validation + immutability enforcement |

**Total Modules Retained**: 4/4 (100%)  
**Module Rejection Rate**: 0% (no modules rejected; all passed risk review)

---

## E. CROSS-EPIC RISK ASSESSMENT

### Risk: MODULE-003-01 Depends on Upstream EPIC-001/002 Outputs
**Severity**: HIGH  
**Dependency Chain**: MODULE-001-05 → MODULE-003-01 (category validation gate)  
**Dependency Chain**: MODULE-001-07 → MODULE-003-01 (ISBN search gate)  
**Dependency Chain**: MODULE-002-04 → MODULE-003-01 (site eligibility filter)

**Mitigation**:
- [ ] EPIC-001/002 modules must be tested independently and signed off before EPIC-003 begins
- [ ] Cross-epic integration test harness created to validate MODULE-003-01 behavior with actual upstream outputs (not mocks)
- [ ] If upstream modules unavailable or produce NaN values, MODULE-003-01 must fail-open (accept all queries) or fail-closed (reject all queries) with explicit logging

**Gate Approval**: Deferred to ARCHITECTURE phase (cross-epic integration testing required)

---

## F. ASSUMPTION & THRESHOLD CARRY-FORWARD (Unresolved Items)

### Unresolved Thresholds (MDAP Phase → ARCHITECTURE Phase)
- **THRESHOLD-002**: Performance reference environment unresolved (latency benchmarks, CPU/memory targets for orchestrator)
- **THRESHOLD-005**: Peak concurrent users unresolved (impacts batching policy for MODULE-003-01)

### Resolved Items (No Further Action Required)
- **CONFLICT-001**: Category-eligible interpretation (resolved: defer to MODULE-001-05)
- **OQ-012**: Ranking signal source clarification (resolved: use MODULE-002-05 + internal signals)

### Inherited Unresolved Items (From EPIC-001/002)
- **ASSUMPTION-004**: Brand reason-code taxonomy undefined (EPIC-002 carry-forward)
- **ASSUMPTION-003**: Export formatting undefined (EPIC-004 concern; not impacting EPIC-003)

---

## G. RISK MATRIX SUMMARY

| Dimension | EPIC-003 Status | Benchmark | Variance |
|-----------|-----------------|-----------|----------|
| High-Risk Modules | 2 (MODULE-003-01, MODULE-003-03) | ≤ 2 per Epic | ✓ At limit |
| Medium-Risk Modules | 2 (MODULE-003-02, MODULE-003-04) | ≤ 3 per Epic | ✓ Within limit |
| Rejected Scope Patterns | 2 | ≥ 1 per Epic | ✓ Alignment |
| Unresolved Thresholds | 2 | Minimize | ⚠ 2 carry-forward (acceptable for cross-Epic threshold) |
| Module Retention Rate | 100% (4/4) | ≥ 75% | ✓ Exceeds |

---

## H. ADVANCEMENT DECISION

**Stage 4 Status**: ✓ APPROVED  

**Verification Checklist**:
- ✓ All rejected scope patterns justified with FR traceability
- ✓ High-risk modules flagged with expert domain assignments + mitigation strategies
- ✓ Medium-risk modules reviewed; mitigation strategies documented
- ✓ Cross-epic dependencies assessed (deferred to ARCHITECTURE integration testing)
- ✓ Scope ceiling validated; no scope creep detected
- ✓ Module retention decision: all 4 modules retained
- ✓ Unresolved items (THRESHOLD-002, THRESHOLD-005) carry-forward explicit

**Next Gate**: Stage 5 (Advancement Sign-Off) - Ready for execution upon approval


**Reviewed By**: User (GitHub Copilot)  
**Approval Date**: March 24, 2026  
**Status**: READY FOR STAGE 5 ✓
**Next Gate**: Stage 5 (Advancement Sign-Off) - Ready for execution upon approval

**Approved — Stage 4 complete. Proceeded to Stage 5 (Advancement Sign-Off).**
