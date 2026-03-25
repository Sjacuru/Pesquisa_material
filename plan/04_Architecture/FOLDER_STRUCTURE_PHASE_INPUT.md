# Folder Structure Phase Input

**Project:** School Material Price Finder (Brazil MVP)  
**Input From:** Architecture Phase  
**Date:** March 25, 2026

---

## Goal

This file is the direct handoff from Architecture into the Folder/File Structure phase.
It translates architecture decisions into constraints for how the repository should be organized before implementation begins.

---

## 1. Canonical Inputs

Use these as authoritative inputs:
- CONTEXT.md
- ARCHITECTURE_DECISION_RECORD.md
- ARCHITECTURE_DEFINITION.md
- ARCHITECTURE_COMPONENT_VIEW.md

---

## 2. Structural Rules

- Preserve the modular-monolith architecture.
- Preserve the four architecture components as primary domain boundaries.
- Keep web/UI concerns separate from domain logic.
- Keep shared platform/infrastructure code separate from business-domain code.
- Keep source adapters isolated from core ranking and governance logic.
- Keep audit/versioning storage concerns explicit, not hidden inside generic utilities.
- Keep file/object storage concerns explicit, not mixed into unrelated domain modules.

---

## 3. Expected Top-Level Application Folders

Recommended top-level structure for the future implementation workspace:
- /web
- /intake_canonicalization
- /source_governance
- /search_ranking
- /workflow_export
- /platform
- /tests

### Intent of Each Folder
- /web: routes, views, forms, templates, UI interaction endpoints
- /intake_canonicalization: upload intake, extraction pipeline, normalization, duplicates, category/ISBN rules
- /source_governance: site onboarding, trust classification, site eligibility, suspension lifecycle, brand governance
- /search_ranking: query orchestration, adapters, matching, ranking, Apostila routing
- /workflow_export: edit workflow, version history, export generation, artifact delivery
- /platform: configuration, storage abstractions, job execution, logging, shared technical primitives
- /tests: test suites organized by component and cross-component contracts

---

## 4. Module-to-Folder Traceability

- MODULE-001-01 through MODULE-001-07 -> /intake_canonicalization
- MODULE-002-01 through MODULE-002-05 -> /source_governance
- MODULE-003-01 through MODULE-003-04 -> /search_ranking
- MODULE-004-01 through MODULE-004-03 -> /workflow_export

Cross-cutting delivery layer:
- all user-facing page and interaction entry points -> /web

Cross-cutting technical layer:
- storage, configuration, background execution, and structured logging -> /platform

---

## 5. Folder-Phase Questions to Answer Next

These are the kinds of concrete questions the next phase will answer:
- Should each domain folder contain its own models/services/repositories subfolders?
- Should adapters live inside /search_ranking/adapters or under a broader /platform/integrations boundary?
- Should templates be colocated by feature or centralized under /web/templates?
- How should tests mirror the domain folders?
- Where should shared schemas/contracts live so they do not dissolve component boundaries?

---

## 6. Guardrails

- Do not introduce service splits or microservice folder layouts.
- Do not add an auth subsystem as a first-class domain unless scope changes.
- Do not centralize everything under a generic /common folder.
- Do not let source-specific adapter code leak into ranking logic.
- Do not let export-format-specific details leak backward into edit/versioning flows.

---

## 7. Ready State

Folder/File Structure phase can begin from this point.
The purpose of that phase is not to redesign architecture, but to express the approved architecture cleanly in repository structure.
