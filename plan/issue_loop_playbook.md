# Website Access Issue Loop Playbook

Purpose: Keep troubleshooting focused on the current website and avoid unrelated deep dives.

## Scope Contract

Larger problem:
- Fail in accessing selected websites for offer retrieval.

Specific problem (current loop unit):
- For one chosen website, determine whether failure is due to:
  - Access problem (blocked, timeout, anti-bot, redirect/login wall, HTTP error), or
  - Parsing problem (access works but extraction fails/returns wrong data).

Out of scope during a loop unit:
- Ranking tuning and threshold changes (unless user explicitly asks).
- Cross-site architecture redesign.
- New features not required to classify access vs parsing for the chosen site.

## Loop Definition

1. Choose one website.
2. Run access diagnostics (request URL, status, redirects, response shape).
3. Run retrieval diagnostics (offers found, extraction path, sample titles/prices).
4. Classify root cause: access or parsing (or both).
5. Apply minimal fix only for current site.
6. Re-run and confirm expected behavior.
7. Mark site as solved/partial/blocked.
8. Move to next website.

End condition:
- All target websites classified and resolved (or marked externally blocked with evidence).

## Required Evidence Per Site

- Request evidence:
  - Query used
  - Final URL
  - HTTP status and redirect chain
  - Timeout/error details if any
- Parsing evidence:
  - Parse strategy hit (JSON-LD/CSS/other)
  - Parsed offer count
  - 3-5 sample offers (title + price + URL)
- Outcome label:
  - solved
  - partial
  - blocked_external
  - blocked_internal

## Guardrails For Assistant (Anti-Drift)

- Always state current site before changes/runs.
- Use smallest possible change set.
- Prefer existing project dependencies before introducing new tooling (e.g., Playwright if already installed instead of adding Selenium).
- Do not switch to a different site mid-loop unless user asks.
- If hypothesis is uncertain, collect evidence first and avoid speculative fixes.
- Stop after classification + minimal fix validation; then ask for next site.
- Only keep scripts/helpers if the solution they implement was confirmed working. Delete them if the approach failed.

## Detector Policy (Required)

- Do not treat weak markers alone as a definitive challenge.
- Strong markers (definitive):
  - `radware bot manager captcha`
  - `validate.perfdrive.com`
  - `window.ssjsinternal`
  - provider-specific hard block URLs
- Weak markers (contextual):
  - `cdn.perfdrive.com`
  - `aperture.js`
- Challenge decision rule:
  - If any strong marker is present => challenge.
  - If only weak markers are present => challenge only when there is no result evidence in DOM/HTML.

## Selenium Fallback Policy (Future-Proofing)

- Every adapter should have an optional Selenium last-resort fallback path behind env flags.
- Apply Selenium fallback first to adapters that currently return no products in the active network.
- Keep fallback lazy-imported and disabled by env when needed.
- Reuse persistent profile directories per site.
- Keep anti-detection options configurable but minimal.

## Known Unresolved Blocks

### Estante Virtual (ev_br) — historical block note
- Previous state: access challenged by Radware/ShieldSquare during earlier runs.
- Current state: hardened browser fallback returned status=ok in controlled validation (2026-03-29).
- Residual risk: challenge may recur intermittently; keep diagnostics enabled when regressions appear.

## Commands Baseline

- First command in new terminal:
  - conda activate matfinder
- Debug setup helper:
  - . .\scripts\enable_search_debug.ps1

## Reporting Format

For each loop completion, report only:
- Site
- Root cause category
- Evidence summary (access + parsing)
- Fix applied (if any)
- Validation result
- Next suggested site
