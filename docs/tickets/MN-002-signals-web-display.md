---
id: MN-002
title: Stock Signals Web Display
status: closed
created: 2026-05-03
closed: 2026-05-03
closed-commit: retroactive-2026-05-09-close-sync
type: feature
priority: high
size: M
visual-delta: none
content-delta: none
design-locked: N/A
qa-early-consultation: "PM proxy tier — 2026-05-03 MN-002 — 6 challenges raised, 4 supplemented to AC, 1 Known Gap, 1 deferred to AC refinement post-BQ resolution"
worktree: .claude/worktrees/MN-002-signals-web-display
branch: MN-002-signals-web-display
---

## Summary

Add `--output-json` flag to `analyze_stock.py` so it writes `docs/signals.json` (list of SignalResult + generated_at timestamp). Add a GitHub Actions daily workflow that runs analysis for all 12 tickers and commits the JSON. Update `docs/index.html` with a Signals section displaying BUY/HOLD/SELL cards per ticker (green/yellow/red, confidence %, rationale text).

## Scope

Files touched:
- `analyze_stock.py` — add `--output-json <path>` flag; write JSON on success
- `docs/signals.json` — generated output (committed by workflow)
- `.github/workflows/update-signals.yml` — new daily cron workflow
- `docs/index.html` — new Signals section with cards

Out of scope:
- Async processing (project rule: no asyncio)
- Schema versioning for signals.json (Known Gap — see §Blocking Questions BQ-002-04)
- Build step for frontend (plain HTML/JS only)

## Acceptance Criteria

### Phase 1 — analyze_stock.py JSON output

**AC-MN002-JSON-01**
- Given: `analyze_stock.py` is invoked with `--output-json docs/signals.json NVDA TSLA`
- When: both tickers complete successfully
- Then: `docs/signals.json` is written with schema `{"generated_at": "<ISO8601>", "signals": [<SignalResult>, ...]}` where each SignalResult contains `ticker`, `signal`, `confidence`, `rationale` fields

**AC-MN002-JSON-02**
- Given: `analyze_stock.py` is invoked with `--output-json docs/signals.json` and one ticker raises an exception
- When: the run completes
- Then: the failing ticker is omitted from the `signals` array (Option A — skip-on-failure); successful tickers are still written; exit code follows existing `main()` logic (non-zero only when ALL tickers fail)

**AC-MN002-JSON-03**
- Given: `analyze_stock.py` is invoked WITHOUT the `--output-json` flag
- When: the run completes
- Then: no `signals.json` file is written; console/Telegram output behavior is unchanged (backward compatible)

**AC-MN002-JSON-04**
- Given: `--output-json` is provided
- When: `python3 -m py_compile analyze_stock.py` is executed after the edit
- Then: exit code is 0 (no syntax error)

### Phase 2 — GitHub Actions workflow

**AC-MN002-WF-01**
- Given: `.github/workflows/update-signals.yml` exists in the repo
- When: the workflow is triggered (scheduled or manual dispatch)
- Then: it runs `python analyze_stock.py --output-json docs/signals.json NVDA TSLA AAPL GOOGL TSM BTC-USD ETH-USD SPY QQQ SOXX "^GSPC" "^VIX"` with all 12 tickers

**AC-MN002-WF-02**
- Given: the workflow has completed the analyze step
- When: `docs/signals.json` differs from the committed version
- Then: the workflow commits `docs/signals.json` with a message `chore: update signals <ISO8601 timestamp>` and pushes to main; if the file is unchanged, no commit is made

**AC-MN002-WF-03**
- Given: both `update-news.yml` and `update-signals.yml` could run concurrently
- When: they attempt to push to main at the same time
- Then: each workflow uses `git pull --rebase` before `git push` to avoid push rejection; alternatively, a `concurrency` group is used to serialize pushes

**AC-MN002-WF-04**
- Given: the workflow runs without `GEMINI_API_KEY` secret set
- When: `analyze_stock.py` executes
- Then: the workflow fails with a clear error (KeyError on env var) rather than silently producing empty output; this is expected behavior — GEMINI_API_KEY must be set as a repo secret (post-deploy manual step for the user, not a code blocker)

### Phase 3 — docs/index.html Signals section

**AC-MN002-HTML-01**
- Given: `docs/signals.json` is present and valid
- When: the page loads
- Then: a "股票訊號" section is visible above the news list, containing one card per ticker returned in `signals.json`

**AC-MN002-HTML-02**
- Given: a signal card for a ticker is rendered
- When: the signal value is `BUY`, `HOLD`, or `SELL`
- Then: the card displays the ticker name, signal label, confidence percentage, and rationale text; the card background or accent color is green for BUY, yellow for HOLD, and red for SELL

**AC-MN002-HTML-03**
- Given: a ticker with null fundamentals data (e.g. SPY, ^VIX)
- When: its card is rendered
- Then: the card renders without JavaScript errors; null/undefined fields are not displayed (graceful omission, not "null" text)

**AC-MN002-HTML-04**
- Given: `docs/signals.json` returns a 404 (file not yet generated)
- When: the page loads
- Then: the Signals section displays a placeholder message ("訊號暫未生成") and the news section continues to load and display normally — no uncaught JS exception

**AC-MN002-HTML-05**
- Given: ticker names including `^GSPC` and `^VIX` are rendered in the DOM
- When: a signal card is inserted into the page
- Then: ticker text is set via `textContent` or equivalent safe assignment — never via raw `innerHTML` string interpolation of the ticker value, preventing XSS

**AC-MN002-HTML-06**
- Given: a rationale string of up to three sentences (~120 characters)
- When: rendered in a signal card on a mobile viewport (375px width)
- Then: the text does not overflow the card boundary; the card is legible without horizontal scrolling; rationale is displayed with a maximum of 3 visible lines (CSS line-clamp or equivalent)

**AC-MN002-HTML-07**
- Given: `generated_at` field is present in `signals.json`
- When: the Signals section renders
- Then: the section displays the last-updated timestamp (e.g. "訊號更新於 YYYY/MM/DD HH:MM") below the section heading

## Blocking Questions

**BQ-002-01 — RESOLVED (PM ruling, 2026-05-03)**
How to handle a failed ticker in signals.json?
Options: (A) skip failed tickers from array; (B) include error record with `signal: null`.
Ruling: **Option A** — omit failed tickers. Failure is typically transient (network); no empty error cards in UI; workflow logs retain the error output for diagnosis.

**BQ-002-02 — RESOLVED (PM ruling, 2026-05-03)**
How to present Signals in the UI: (A) fixed section above news list (single-page scroll); (B) tab toggle between "訊號" and "新聞".
Ruling: **Option A** — fixed section above news. Signals and news are complementary; single-scroll is simpler; tab switching requires additional JS state; index.html is currently single-section.

**BQ-002-03 — RESOLVED supplemented to AC (QA-C5)**
Git push race condition between update-news and update-signals workflows.
Resolution: AC-MN002-WF-03 covers `git pull --rebase` or concurrency group approach; Engineer chooses implementation.

**BQ-002-04 — Known Gap**
signals.json schema versioning: future SignalResult field additions could cause undefined fields in older frontend reads.
Decision: Out of scope for MN-002. Frontend uses defensive optional access (`result?.confidence ?? 'N/A'`). To be addressed if schema changes in a future ticket.

## Phase Gate Status

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1 — JSON output flag | complete | QA-PASS 2026-05-03 |
| Phase 2 — GitHub Actions workflow | complete | QA-PASS 2026-05-03 |
| Phase 3 — HTML Signals section | complete | QA-PASS 2026-05-03 |

## Release Status

Post-deploy manual step (user action required):
1. Go to GitHub repo `mshmwr/market-news` → Settings → Secrets and variables → Actions
2. Add secret `GEMINI_API_KEY` with value from local `.env` file
3. Trigger `.github/workflows/update-signals.yml` manually (workflow_dispatch) to generate initial `docs/signals.json`

---

### Deploy Record

- **Deploy date:** 2026-05-03
- **Git SHA:** retroactive — MN-002-signals-web-display branch merged to main 2026-05-03
- **Hosting URL:** https://mshmwr.github.io/market-news/
- **Verification probe (live evidence at close-sync 2026-05-09):** `docs/signals.json` updated by `update-signals.yml` cron 06:00 UTC daily — multiple `chore: update signals` commits on main confirm live deploy (latest: `1d3e534` 2026-05-07)
- **Status:** Live

_Close-sync note (2026-05-09): MN-002 was functionally deployed on 2026-05-03 but ticket frontmatter was not closed. Retroactively closed during MN-003 intake post-merge scan._

---

_Ticket opened: 2026-05-03 by PM_
