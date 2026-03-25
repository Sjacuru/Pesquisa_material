# PROMPT 6 — Implementation (Step 1, Beginner Pace)

## Goal
Implement **one module only** and its **one unit test file**:
- `intake_canonicalization/isbn_normalization_validation.py`
- `tests/unit/intake_canonicalization/test_isbn_normalization_validation.py`

This prompt is intentionally slow-paced and scoped for learning.

---

## Scope Lock

### In Scope (only)
1. `MODULE-001-06 — ISBN Normalization & Validation`
2. Unit tests for this module
3. Small, pure helper functions inside this same file if needed

### Out of Scope (for this step)
- Any other module implementation
- Database models/migrations
- Background jobs
- API/scraping integration
- UI or route wiring changes
- PostgreSQL migration/setup

---

## Environment Lock (important)

- Keep **SQLite** as current runtime backend.
- Do **not** switch to PostgreSQL in this step.
- PostgreSQL move is deferred until this module and tests are approved.

---

## Authoritative Requirements (from approved MDAP)

For `MODULE-001-06`, implement these acceptance criteria:
1. Input ISBN is normalized by removing separators/punctuation.
2. Only ISBN-10 or ISBN-13 format is accepted as valid.
3. Matching uses normalized exact string equality only.

Do not infer extra business rules beyond these criteria.

---

## Coding Contract

Respect file headers already present in the scaffold as contract metadata.

### File A: `intake_canonicalization/isbn_normalization_validation.py`
Implement minimal signatures and behavior:
- `normalize_isbn(raw_value: str) -> str`
- `is_valid_isbn10(value: str) -> bool`
- `is_valid_isbn13(value: str) -> bool`
- `classify_isbn(raw_value: str) -> dict`
  - recommended keys: `raw`, `normalized`, `is_valid`, `format`
- `is_exact_isbn_match(left: str, right: str) -> bool`

Behavior constraints:
- Remove non-alphanumeric separators from input before validation.
- Accept only normalized lengths of 10 or 13.
- No fuzzy matching, no similarity thresholds.
- No external dependencies required for this module.

### File B: `tests/unit/intake_canonicalization/test_isbn_normalization_validation.py`
Implement unit tests that verify:
- normalization removes hyphens/spaces/punctuation
- valid ISBN-10 accepted
- valid ISBN-13 accepted
- invalid lengths rejected
- exact normalized equality match works
- non-exact values do not match

Use clear test names and simple Arrange/Act/Assert style.

---

## Strict Constraints

1. Keep implementation local to these two files only.
2. Do not modify unrelated files.
3. Keep functions small and readable.
4. Avoid framework coupling (no Django imports needed here).
5. No placeholders after implementation: functions must be executable.
6. No speculative features.

---

## Verification Commands

Run these after implementation:
1. `c:/Users/sjacu/GitHub/Pesquisa_material/.venv/Scripts/python.exe -m pytest tests/unit/intake_canonicalization/test_isbn_normalization_validation.py`
2. `c:/Users/sjacu/GitHub/Pesquisa_material/.venv/Scripts/python.exe manage.py check`

Expected:
- unit tests pass
- Django check remains clean

---

## Completion Checklist

- [ ] Only the two target files changed
- [ ] All 3 MDAP acceptance criteria are implemented
- [ ] Unit tests cover normalization, validity, and exact-match behavior
- [ ] Tests pass
- [ ] SQLite-first setup preserved
- [ ] No PostgreSQL migration/setup introduced

---

## Human Review Focus

Before moving to next module, confirm:
1. The logic is easy to read for a non-developer.
2. Tests are understandable and map directly to acceptance criteria.
3. No hidden assumptions were introduced.

If approved, move to the next low-risk module in EPIC-001.
