# MDAP Stage 3: Module Details & Acceptance Criteria
## EPIC-004: User Editing, Versioned Traceability, and Export Delivery

**Status**: APPROVED  
**Date**: March 24, 2026  
**Reviewer**: User  
**Epic ID**: EPIC-004  
**Module Count**: 3 modules  
**Coverage**: All 3 user stories (US-014, US-015, US-016)

---

## A. MODULE TEMPLATES & ACCEPTANCE CRITERIA

### MODULE-004-01: User Edit Handler
**Domain**: User-initiated material metadata editing with schema enforcement  
**User Stories Covered**: US-014  
**FRs Covered**: FR-018  
**Risk Level**: LOW  
**Expert Domains Required**: [User Input Validation, Domain Schema Enforcement]  
**Blocked By**: EPIC-003 ranked result output, MODULE-001-05 category validation contract

**Responsibility Chain**:
- Consumes selected material item from EPIC-003 ranked results
- Accepts edit request containing field name, previous value, proposed value, and optional user note
- Validates edit against allowed editable fields and schema constraints
- Delegates category validation to EPIC-001 category contract instead of duplicating logic
- Rejects edits to immutable source fields
- Persists accepted edit as a structured edit record for downstream audit logging
- Returns deterministic success/failure response with reason code

**Binary Acceptance Criteria**:
- ✓ Only editable fields are accepted: title, category, subtitle, notes, and local metadata tags
- ✓ Immutable fields are rejected: source ID, extraction timestamp, original source URL, provenance token
- ✓ Category edits validate against EPIC-001 category enum before persistence
- ✓ Title edits longer than 500 characters are rejected
- ✓ Empty-string edits are rejected unless target field explicitly allows blank values
- ✓ All accepted edits produce an edit record containing user ID, timestamp, field name, old value, new value, and reason note
- ✓ All rejected edits return explicit reason code (immutable_field, schema_violation, invalid_category, missing_value)
- ✓ Same valid input produces the same validation result every execution
- ✓ No source system is mutated; persistence is local-only and append-based

**Public Interface**:
```text
INPUT:
  - materialItem: RankedMaterialRecord
  - editRequest: EditRequest { fieldName, oldValue, newValue, reasonNote }
  - userContext: UserContext { userId, sessionId, role }
  - categoryContract: CategoryEnumContract (from EPIC-001)

OUTPUT:
  - editResult: EditResult { status, reasonCode, persistedEditId, acceptedAt }
  - editRecord: EditRecord { materialId, userId, fieldName, oldValue, newValue, reasonNote, timestamp }

SIDE EFFECTS:
  - Persists accepted edit record to local edit store
  - Emits validation failure event for rejected edits
```

**Constraint Ledger**:
- Validation authority for category values belongs to EPIC-001; this module must not create local category variants
- No direct dependency on export-format assumptions
- Inherited thresholds THRESHOLD-002 and THRESHOLD-005 do not materially change module contract at MDAP phase

---

### MODULE-004-02: Versioned Audit Trail Logger
**Domain**: Immutable version history and diff retrieval for user edits  
**User Stories Covered**: US-015  
**FRs Covered**: FR-019  
**Risk Level**: MEDIUM  
**Expert Domains Required**: [Audit Logging, Versioning, Compliance Traceability]  
**Blocked By**: MODULE-004-01

**Responsibility Chain**:
- Consumes accepted edit records from MODULE-004-01
- Appends each accepted edit to immutable version ledger
- Generates monotonic version number per material entity
- Stores structured diff between prior state and new state
- Exposes retrieval of full history, specific version snapshots, and pairwise diff views
- Preserves user attribution and timestamp for every version event
- Applies configured retention policy without breaking version traceability contract

**Binary Acceptance Criteria**:
- ✓ Every accepted edit from MODULE-004-01 produces exactly one appended version entry
- ✓ Version numbers are gapless and strictly increasing per material ID
- ✓ Each version entry contains user ID, timestamp, changed field, old value, new value, and version number
- ✓ Historical entries cannot be overwritten or deleted through the public interface
- ✓ Diff output for the same version pair is deterministic and repeatable
- ✓ Full history retrieval returns entries in version order
- ✓ Query by material ID returns complete version chain for retained records
- ✓ Retention policy is configurable and does not alter surviving version payloads
- ✓ Rejected edits from MODULE-004-01 do not generate version entries

**Public Interface**:
```text
INPUT:
  - editRecord: EditRecord (from MODULE-004-01)
  - retentionPolicy: RetentionPolicy { mode, duration, archiveBehavior }

OUTPUT:
  - versionEntry: VersionEntry { materialId, versionNumber, userId, fieldName, oldValue, newValue, timestamp }
  - auditQueryResult: AuditHistory { entries[], latestVersion, retentionState }
  - diffResult: VersionDiff { fromVersion, toVersion, changedFields[] }

SIDE EFFECTS:
  - Appends immutable record to version ledger
  - Updates version index for material ID
  - Emits archival eligibility event when retention threshold is met
```

**Constraint Ledger**:
- THRESHOLD-003 (log retention duration) remains unresolved; module accepts runtime-configured retention policy instead of hardcoding duration
- Module must preserve audit semantics even if archival strategy changes in ARCHITECTURE phase
- No export-format logic allowed here; this module owns traceability only

---

### MODULE-004-03: Export Formatter & Delivery
**Domain**: Format-agnostic export assembly and user delivery  
**User Stories Covered**: US-016  
**FRs Covered**: FR-020  
**Risk Level**: MEDIUM  
**Expert Domains Required**: [Document Rendering, File Export, Delivery Workflows]  
**Blocked By**: MODULE-004-02

**Responsibility Chain**:
- Consumes curated material set together with latest editable state and version context
- Accepts requested export format (PDF, CSV, JSON)
- Builds format-neutral export payload from material and audit data
- Delegates rendering to format adapter selected by requested format
- Generates export artifact and delivery metadata
- Returns delivery handle or file payload to user-facing layer
- Logs export event with user, format, timestamp, and exported item count

**Binary Acceptance Criteria**:
- ✓ Only supported formats are accepted: PDF, CSV, JSON
- ✓ Unsupported format requests are rejected with explicit reason code
- ✓ Export payload includes latest material values and associated version metadata for every exported record
- ✓ Export operation does not mutate material state or audit history
- ✓ Same input dataset and same format request produce structurally identical export payload
- ✓ Export event log contains user ID, timestamp, format, material count, and artifact identifier
- ✓ Empty export requests are rejected with explicit reason code
- ✓ Module can execute with format-specific rendering delegated behind a single adapter boundary
- ✓ Delivery result distinguishes success, validation failure, and rendering failure states

**Public Interface**:
```text
INPUT:
  - curatedSet: CuratedMaterialSet { materialIds[], selectedFields[], filters[] }
  - versionContext: AuditHistoryBundle (from MODULE-004-02)
  - exportRequest: ExportRequest { format, includeHistory, deliveryMode }
  - userContext: UserContext { userId, sessionId, role }

OUTPUT:
  - exportArtifact: ExportArtifact { artifactId, format, contentRef, generatedAt }
  - deliveryResult: DeliveryResult { status, reasonCode, artifactId, deliveredAt }
  - exportEvent: ExportEvent { userId, format, itemCount, timestamp, artifactId }

SIDE EFFECTS:
  - Invokes chosen format adapter
  - Persists export event log entry
  - Stores generated artifact or delivery reference
```

**Constraint Ledger**:
- ASSUMPTION-003 (export format specifications) remains unresolved; rendering adapters must remain format-agnostic at MDAP phase and defer styling/schema specifics to ARCHITECTURE
- Module may support multiple delivery modes later, but current contract only guarantees artifact generation and delivery result reporting
- THRESHOLD-002 does not change structure here; performance tuning deferred

---

## B. COVERAGE MATRIX

| User Story | Module(s) | Coverage Status |
|-----------|-----------|-----------------|
| US-014: User edits material metadata | MODULE-004-01 | ✓ Primary responsible |
| US-015: Versioned audit trail with attribution | MODULE-004-02 | ✓ Primary responsible |
| US-016: Export curated set in multiple formats | MODULE-004-03 | ✓ Primary responsible |

**Total User Stories**: 3  
**Stories Covered**: 3  
**Coverage Percentage**: 100%

---

## C. FUNCTIONAL REQUIREMENT TRACEABILITY

| FR ID | FR Title | Module(s) | Traceability Note |
|-------|----------|-----------|-------------------|
| FR-018 | User editing of material metadata | MODULE-004-01 | Accepts and validates user edits |
| FR-019 | Versioned audit trail with attribution | MODULE-004-02 | Maintains immutable version history and diff retrieval |
| FR-020 | Export delivery in multiple formats | MODULE-004-03 | Builds export payload and delivers formatted artifact |

---

## D. CONSTRAINT LEDGER (Unresolved Items Carried Forward)

### Unresolved Assumptions / Thresholds
- **ASSUMPTION-003**: Export formatting specifications unresolved; deferred to ARCHITECTURE via adapter-level design
- **THRESHOLD-003**: Log retention duration unresolved; handled as runtime policy input in MODULE-004-02
- **THRESHOLD-002**: Performance reference environment unresolved; no module contract change at MDAP phase
- **THRESHOLD-005**: Peak concurrent users unresolved; no module contract change at MDAP phase

### Cross-Epic Contract Dependencies
- MODULE-004-01 depends on EPIC-003 ranked material output as source-of-edit truth
- MODULE-004-01 depends on EPIC-001 category validation contract for category edits
- No EPIC-004 module mutates upstream Epic outputs; all changes are local overlays with traceability

---

## E. MODULE INTERDEPENDENCIES (Within EPIC-004)

```text
MODULE-004-01 (User Edit Handler)
    ↓
MODULE-004-02 (Versioned Audit Trail Logger)
    ↓
MODULE-004-03 (Export Formatter & Delivery)
    ↓
[User Delivery Layer]
```

**Dependency Chain**:
- Sequential only; each module consumes prior module output
- No parallel runtime branch inside EPIC-004
- Export module depends on audit context, not directly on edit handler

---

## F. RISK ASSESSMENT & EXPERT FLAGGING

| Module | Risk Level | Expert Domains | Risk Justification |
|--------|-----------|----------------|--------------------|
| MODULE-004-01 | LOW | User Input Validation, Domain Schema Enforcement | Straightforward validation boundary with explicit immutable/editable field split |
| MODULE-004-02 | MEDIUM | Audit Logging, Versioning, Compliance Traceability | Gapless versions, immutable history, retention-policy interaction |
| MODULE-004-03 | MEDIUM | Document Rendering, File Export, Delivery Workflows | Format-adapter boundary exposed to unresolved export-spec assumption |

---

## G. PUBLIC INTERFACE BOUNDARY CONTRACTS

**MODULE-004-01 Output → MODULE-004-02 Input Contract**:
- Accepted edits only
- Edit record must include old and new value, actor, time, and material ID
- Rejected edit attempts are not versioned

**MODULE-004-02 Output → MODULE-004-03 Input Contract**:
- Audit history bundle must include latest version and retrievable chain for exported records
- Version numbering is authoritative and immutable
- Export module consumes read-only version context

---

## H. MODULE SUMMARY

| Module ID | Name | Primary Output | Next Consumer |
|-----------|------|----------------|---------------|
| MODULE-004-01 | User Edit Handler | EditRecord | MODULE-004-02 |
| MODULE-004-02 | Versioned Audit Trail Logger | VersionEntry / AuditHistory | MODULE-004-03 |
| MODULE-004-03 | Export Formatter & Delivery | ExportArtifact / DeliveryResult | User-facing delivery layer |

**Approved — Stage 3 complete. Proceeded to Stage 4 (Scope & Risk Review).**
