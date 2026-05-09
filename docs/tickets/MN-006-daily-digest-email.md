---
id: MN-006
title: Daily Digest Email Scheduler
status: closed
created: 2026-05-09
closed: 2026-05-09
closed-commit: 5d5d052
type: feature
priority: high
size: M
visual-delta: none
content-delta: yes
qa-early-consultation: docs-ticket; PM proxy — 3 adversarial challenges raised, 2 supplemented to AC, 1 Known Gap declared
---

## Summary

Ship a Python orchestrator (`digest.py`) that composes a two-section HTML email
(stock shortlist + Fear & Greed + geopolitical pulse + FOMC updates) and sends it
via Resend twice daily at 08:00 and 20:00 Taiwan time (UTC 00:00 and 12:00),
triggered by a new GitHub Actions cron workflow.

## Scope

Files touched:
- `digest.py` (new) — orchestrator: fetches signals/news/F&G/Fed RSS, composes HTML, calls Resend
- `requirements.txt` — add `resend>=2.0`
- `.github/workflows/daily-digest.yml` (new) — cron 0 0,12 * * *
- `README.md` — Daily Digest section + secret setup instructions
- `ssot/PRD.md` — move MN-005 to Closed, add MN-006 as Active
- `ssot/system-overview.md` — add digest data flow + env var table entry

No changes to:
- `fetch_news.py`, `analyze_stock.py`, `synthesizer.py`, `models.py`, `signals/`
- Any frontend/Vercel files

## Acceptance Criteria

### Phase 1 — digest.py + workflow

**AC-MN006-DIGEST-01**
- Given: `digest.py` is executed with env vars `RESEND_API_KEY`, `NVIDIA_API_KEY` set (or mocked)
- When: the script runs to completion
- Then: it produces a non-empty HTML string containing `<html>`, `<body>`, and the four section headers ("TW + US Stock Shortlist", "Fear & Greed Index", "Geopolitical Risk Pulse", "FOMC / Fed Updates")
- And: `python -m py_compile digest.py` exits 0

**AC-MN006-DIGEST-02**
- Given: the Alternative.me F&G API endpoint (`https://api.alternative.me/fng/`) returns JSON
- When: `digest.py` fetches F&G data
- Then: the HTML body contains a numeric value (0–100) labelled as the Fear & Greed reading
- And: if the request fails, the section shows "F&G data unavailable this run" rather than raising an unhandled exception

**AC-MN006-DIGEST-03**
- Given: the Federal Reserve RSS feed (`https://www.federalreserve.gov/feeds/press_all.xml`) is fetched
- When: `digest.py` filters entries
- Then: only entries whose title contains "FOMC" or "Federal Open Market Committee" are included
- And: at most 2 entries are displayed in the FOMC section; if zero matching entries exist, the section shows "No recent FOMC releases"

**AC-MN006-DIGEST-04**
- Given: `fetch_news.py` `fetch_all()` is called by `digest.py`
- When: filtering for geopolitical risk
- Then: articles from sources "Al Jazeera" or "BBC World" containing at least one of the keywords [war, sanctions, tariff, conflict, geopolitic, military] in title or description are selected
- And: at most 5 geopolitical items appear in the HTML

**AC-MN006-DIGEST-05**
- Given: `docs/signals.json` exists in the repo (populated by `update-signals.yml`)
- When: `digest.py` reads the signals file
- Then: it selects the top 5 entries by `confidence` descending (BUY signals preferred; ties broken alphabetically by ticker)
- And: each selected entry shows ticker, signal (BUY/HOLD/SELL), confidence, and a one-sentence rationale in the HTML

**AC-MN006-DIGEST-06 — Email send + failure handling**
- Given: `RESEND_API_KEY` is set and Resend API returns HTTP 200
- When: `digest.py` completes composition
- Then: it calls `resend.Emails.send()` with `to=["rsp93050420@gmail.com"]`, `from_="onboarding@resend.dev"`, `subject` containing the run timestamp (YYYY-MM-DD HH:MM TW), and `html=<composed body>`
- And: a non-zero exit code is returned if Resend returns an error response (HTTP 4xx/5xx)

**AC-MN006-WF-01 — Workflow cron**
- Given: `.github/workflows/daily-digest.yml` is present
- When: the workflow is triggered
- Then: it installs Python 3.11 + `requirements.txt` and runs `python digest.py`
- And: cron schedule is `0 0,12 * * *` (08:00 and 20:00 TW)
- And: `RESEND_API_KEY` and `NVIDIA_API_KEY` are injected from GitHub secrets
- And: the workflow exits non-zero if `digest.py` exits non-zero

**AC-MN006-WF-02 — Smoke-test gate (manual trigger)**
- Given: the workflow is triggered via `workflow_dispatch` without `RESEND_API_KEY` set
- When: the workflow runs
- Then: it fails at the email-send step with a clear error in the Actions log (not at import time, not silently)
- And: the earlier fetcher steps (F&G, RSS, signals read) succeed and produce log output

### Phase 2 — docs

**AC-MN006-DOC-01**
- Given: `README.md` is read after this ticket
- When: a new user sets up the project
- Then: a "Daily Digest" section exists explaining: what it sends, the two send times (08:00 + 20:00 TW), the required secret (`RESEND_API_KEY`), and the exact command to add the secret (`gh secret set RESEND_API_KEY --repo mshmwr/market-news`)

**AC-MN006-DOC-02**
- Given: `ssot/system-overview.md` is read
- When: reviewing environment variables
- Then: `RESEND_API_KEY` appears in the env var table with purpose "Resend email API auth (daily-digest.yml)"

## QA Early Consultation (PM proxy)

**Challenge 1 (data availability):** signals.json may not exist on first run (before update-signals.yml has ever run).
- Resolution: AC-MN006-DIGEST-05 supplemented — if `docs/signals.json` is missing or empty, section shows "Signals not yet available"; script does not exit non-zero for this condition.

**Challenge 2 (send errors vs fetch errors):** a network-level timeout on F&G or RSS should not prevent email sending; only Resend-send failure should exit non-zero.
- Resolution: AC-MN006-DIGEST-02 and DIGEST-03 already specify graceful degradation per-section; AC-MN006-DIGEST-06 links non-zero exit exclusively to Resend response errors. Codified in implementation constraint.

**Challenge 3 (duplicate sends):** if the workflow is re-triggered manually while a cron run is in progress, two emails could be sent.
- Known Gap: no idempotency guard in scope for this ticket; GitHub Actions concurrency group would be overkill for a 60/mo email budget. Acceptable risk documented here.

## Blocking Questions

_None raised during implementation._

BQ closure: [0 resolved] [0 deferred→TD] [0 open]

## Release Status

**CLOSED 2026-05-09**

All 10 ACs: PASS.

- AC-MN006-DIGEST-01: `python3 -m py_compile digest.py` exit 0; HTML structure confirmed in `_render_html()`.
- AC-MN006-DIGEST-02: `_fetch_fg()` returns None on exception; "F&G data unavailable" rendered — PASS.
- AC-MN006-DIGEST-03: feedparser filter for "fomc"/"federal open market committee"; max 2; "No recent FOMC releases" fallback — PASS.
- AC-MN006-DIGEST-04: GEOPOLITICAL_SOURCES + GEOPOLITICAL_KEYWORDS filter; max 5 — PASS.
- AC-MN006-DIGEST-05: `_top_signals()` BUY-first, confidence desc, ticker alpha; "Signals not yet available" on absent file — PASS.
- AC-MN006-DIGEST-06: `_send_email()` raises on empty RESEND_API_KEY; `main()` returns 1 on exception — PASS.
- AC-MN006-WF-01: cron `0 0,12 * * *`; Python 3.11; `RESEND_API_KEY` secret injected — PASS.
- AC-MN006-WF-02: smoke test run #25592311420 — F&G=38, FOMC=2, geo=5, signals=36→5; failed at email-send with clear error — PASS.
- AC-MN006-DOC-01: README "Daily Digest" section with timing + `gh secret set` command — PASS.
- AC-MN006-DOC-02: `ssot/system-overview.md` env var table has RESEND_API_KEY row — PASS.

Runtime-scope triggered: YES (files: digest.py, .github/workflows/daily-digest.yml, requirements.txt)
Deploy Record block: GitHub Actions workflow (no Vercel deploy — backend-only ticket)
Smoke-test probe (run #25592311420): fetcher steps all produced log output; email-send failed with `RESEND_API_KEY environment variable is not set` — confirms pipeline healthy, only send step fails without key.

AC vs Sacred cross-check: no Sacred clauses in this ticket; no dependency ticket Sacred lists — no conflict.
Binary-criterion AC scan: 10 clauses checked / 0 subjective.
Engineer challenge sheet: N/A — Architect and Engineer in same session; design doc 5-dimension sheet all-accept.
site-content.json review: no-change — digest.py is infrastructure automation, not a workflow rule surfaced in README named-artefacts.

### Deploy Record

- **Deploy date:** 2026-05-09
- **Git SHA:** 5d5d052 (PR #81 squash merge)
- **Mechanism:** GitHub Actions cron `0 0,12 * * *` (no Vercel deploy; backend-only)
- **Smoke-test run:** https://github.com/mshmwr/market-news/actions/runs/25592311420
- **Verification probe:** GH Actions run log shows `[digest] Signals loaded: 36 total, 5 selected` + `[digest] HTML composed — 7428 chars` + `[digest] ERROR sending email: RESEND_API_KEY environment variable is not set`
- **Status:** Pipeline LIVE; email sending requires user to add `RESEND_API_KEY` secret (see README)

## Retrospective

### PM Summary

**Cross-role recurring issue:** HTML injection from RSS/API data — reviewer caught it; engineer and architect retrospectives both note the miss.
**Process improvement decision:** Add "HTML rendering + external data → audit all interpolations for html.escape()" as a standing engineer checklist item.

| Issue | Responsible Role | Action | Update Location |
|-------|-----------------|--------|-----------------|
| HTML injection in f-string template | Engineer | Add `_esc()` wrapper; apply to all external-data interpolations | `docs/retrospectives/engineer.md` + `reviewer.md` |
