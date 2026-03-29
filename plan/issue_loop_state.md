# Website Access Issue Loop State

Status values:
- not_started
- in_progress
- solved
- partial
- blocked_external
- blocked_internal

## Current Focus

- Current site: Loop checkpoint (all listed sites classified)
- Loop status: partial
- Objective: prioritize next unblock candidate or quality pass.

## Site Board

- Kalunga (kalunga_br)
  - Status: solved
  - Classification: access_ok + parsing_ok
  - Evidence: HTTP 200, offers parsed, retrieval accurate for supply items.
  - Last note: access and extraction confirmed with debug snapshots.

- Mercado Livre (ml_br)
  - Status: partial
  - Classification: api_access_blocked + web_fallback_ok
  - Evidence: API returned 403, while web-first adapter returned status=ok with 10 offers in live tests.
  - Next check: monitor relevance quality drift for ambiguous queries.

- Estante Virtual (ev_br)
  - Status: partial
  - Classification: browser_retrieval_ok + challenge_detector_refined
  - Evidence: Selenium-only controlled run returned status=ok with 10 offers. Prior failures were caused by challenge detector false-positive on weak markers (cdn.perfdrive.com/aperture.js) present on normal result pages.
  - Next check: monitor for strong challenge markers (validate.perfdrive.com/radware title) and keep Selenium as last-resort fallback.

- Amazon Brasil (amazon_br)
  - Status: partial
  - Classification: access_ok + parser_fixed + isbn_precision_hardened
  - Evidence: controlled runs returned status=ok for title/supply queries after link-selector fix; sponsored ad redirects (/sspa/click) are filtered. ISBN-mode now enforces strict ISBN signal in title/url, preventing unrelated keyword-only matches.
  - Next check: monitor ISBN-13 direct misses and rely on upstream name fallback where ISBN-specific results are absent.

- Magalu (magalu_br)
  - Status: blocked_external
  - Classification: access_wall_shieldsquare_perfdrive
  - Evidence: adapter now runs Selenium first (HTTP fallback off by default); controlled validation still lands on validate.perfdrive.com with strong challenge markers.
  - Next check: retry only from trusted residential egress or deprioritize site in current network.

## Update Rules (Mandatory)

When a site loop closes:
1. Update Current Focus to next site.
2. Update site status and classification.
3. Add one-line evidence summary.
4. Keep notes factual (no speculation).
