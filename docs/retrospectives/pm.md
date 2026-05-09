## 2026-05-09 — MN-006 — Daily digest email scheduler — full pipeline

**Task:** Ship digest.py + Resend + GitHub Actions cron for twice-daily HTML market email.

**What happened:**
- Pre-pipeline git check confirmed MN-006 is next free ID; worktree created; ticket stub committed.
- QA Early Consultation (PM proxy, docs-ticket tier): 3 challenges; 2 supplemented (missing signals.json graceful degradation; send-vs-fetch error distinction); 1 Known Gap (duplicate send on manual re-trigger).
- Architect design doc: 5-dimension challenge sheet all accepted; isolated `_send_email()` for provider swap; Alternative.me-only F&G (CNN scrape out of scope).
- Engineer: `digest.py` (~340 LOC); code review found HTML injection risk (RSS titles unescaped) — fixed same session via `html.escape()` wrapper.
- Smoke test (no `RESEND_API_KEY`): F&G=38, FOMC=2, geo=5, signals=36→5 selected — all fetchers passed; email-send step failed with clear error as expected.

**Root cause of HTML injection finding:** `_render_html()` f-string interpolated RSS entry titles directly; reviewer caught before merge.

**Next time improvement:** When writing any HTML templating function that interpolates external data, add `_esc()` call in the same pass — do not leave it to code review.

## 2026-05-09 — MN-005 — Full pipeline execution

**Task:** PWA port to Next.js + GH Pages retirement.

**What happened:**
- Worktree created; ticket stub committed; QA Early Consultation proxy (5 challenges, 2 supplemented, 3 already-covered).
- Design doc: plain sw.js over next-pwa (fewer config landmines); `PwaRegister` Client Component null-render with useEffect guard.
- Engineer: 6 new files, 5 modified; tsc + build pass first try.
- Phase A: PR #77 squash merged at `b24b7c8`. Vercel auto-deploy not triggered (same pattern as MN-004); manual `vercel --prod` needed.
- GH Pages redirect confirmed live (`curl mshmwr.github.io/market-news/` returns meta-refresh tag).

**Next time improvement:** Before any Vercel-deployed ticket Phase A close, include "verify `vercel ls` shows new deployment after merge; if not, flag user to run `vercel --prod`" in the pre-close checklist.

## 2026-05-09 — MN-004 — Full pipeline execution (Phase B)

**Task:** Run Architect + Engineer + Reviewer + QA + close pipeline for MN-004.

**What happened:**
- QA Early Consultation (PM proxy): 7 challenges, 5 supplemented (matchMedia SSR guard, filter persistence, Invalid Date guard, XSS explicitized, news-default-tab); 1 Known Gap (ISR stale latency).
- Design doc: component tree, TypeScript interfaces, ISR fetch layer (raw.githubusercontent.com), TICKER_CATEGORY constant, 17-file change list.
- Engineer: 14 files created/modified; `fetchNews` return type corrected to `null | NewsItem[]` post-reviewer catch; tsc + build both pass.
- Phase A: PR #73 squash merged at `4401595`. Vercel auto-deploy pending (build queue delay; probe loop running).
- Deploy Record will be appended when Vercel probe confirms "每日市場新聞" in HTML.

**Next time improvement:** For Vercel-deployed tickets, add "Vercel build queue delay is normal; use probe loop rather than blocking Phase B on immediate confirmation" to close checklist.

## 2026-05-09 — MN-004 — Ticket intake + BQ collection

**Task:** Open MN-004 ticket stub; collect BQs before Architect release.

**What happened:**
- Post-merge close-sync: MN-003 status was `accepted` (all three PRs merged) → corrected to `closed` in worktree commit.
- Read `docs/index.html` end-to-end to catalogue exact features: two-tab nav, signals with market overview + signal cards + BUY/HOLD/SELL filter + confidence sort + category filter, news with 4-category filter, manual refresh (Cloudflare Worker), PWA, Google Translate proxy, feedback (Firebase).
- Confirmed `docs/signals.json` and `docs/news.json` field shapes from live files.
- Identified 7 BQs requiring user input before Architect release; formulated PM recommendations for each.
- Ticket stub committed at `6a9cb0a` on `MN-004-signals-port-nextjs` branch.

**Note:** MN-004 has `visual-delta: yes` because it ports a complete production UI. Designer spec and `design-locked: true` required before Architect release — blocked on BQ answers first.

**Next time improvement:** When a ticket ports an existing UI verbatim, note upfront that `visual-delta: yes` is mandatory regardless of whether visual changes are intended; faithful port of complex UI = visual scope.

## 2026-05-09 — MN-003 — Next.js scaffold intake + full pipeline

**Task:** Run full PM intake + pipeline for MN-003 Next.js App Router scaffold.

**What happened:**
- Post-merge close-sync: MN-002 was functionally deployed but ticket had `status: open` — closed retroactively with Deploy Record appended.
- MN-003 worktree created (`MN-003-nextjs-shell` branch); ticket stub committed; PRD updated.
- BQ-003-01~04 collected and resolved by user; all four decisions (coexist, Vercel, pure shell, frontend/ subdir) incorporated into finalized ACs.
- QA Early Consultation (PM proxy): 6 challenges → 5 supplemented to AC (env var dependency, vercel.json rootDirectory, Pre-release label specificity, App Router mandate, TypeScript strict); 1 known gap resolved by adding AC.
- Architect (PM proxy): design doc with 3-decision option analysis, full file change list, boundary contracts, refactorability checklist, all-phase coverage gate. Delivery gate OK.
- Engineer (PM proxy): Next.js 14 scaffold under `frontend/`; found `next.config.ts` not supported in 14.2.x → renamed to `.mjs`; build passes with zero TypeScript errors; all local ACs verified.
- PR #70 squash-merged at `a89367a`.
- AC-SCAFFOLD-05 (Vercel 200 probe) deferred — Vercel project must be connected manually (vercel.json already in repo); ticket set to `status: accepted` pending this user action.

**Root cause of AC-SCAFFOLD-05 deferral:** Vercel project connection requires OAuth + dashboard interaction — not automatable without Vercel CLI tokens. The infrastructure code is shipped; only the project link is missing.

**Next time improvement:** For Vercel-targeted tickets, add an explicit AC for "Vercel project connected" as a prerequisite step; mark it as a user-action gate rather than a code gate, so the ticket can close cleanly without a deferred probe.

## 2026-05-03 — MN-002 — Ticket open + QA Early Consultation

**Task:** Open MN-002 signals web display ticket with full PRD and QA Early Consultation.

**What happened:**
- Worktree created at `.claude/worktrees/MN-002-signals-web-display`; ticket stub + PRD committed
- PM-dashboard updated in Diary repo docs worktree
- QA Early Consultation ran as PM proxy tier (no real QA agent in this session); 6 challenges raised, 4 supplemented to AC (C1 404 graceful fallback, C2 partial-run display, C3 XSS-safe ticker rendering, C5 git push race condition), 1 Known Gap (C4 schema versioning), 1 deferred (C6 rationale line-clamp — AC-MN002-HTML-06 added)
- BQ-002-01 (skip-on-failure) and BQ-002-02 (fixed section vs tab) both self-resolved by PM using priority-source rule; no user escalation needed

**AC vs Sacred cross-check:** no prior Sacred clauses in market-news project — N/A

**Slowest step:** reading PM-dashboard (very long file) and navigating hook block for PM-dashboard edit required creating a second Diary docs worktree

**Next time improvement:** market-news project has no retrospectives directory at project start; create `docs/retrospectives/` + `docs/retrospectives/pending/` as part of project bootstrap (MN-001 ticket setup should have included this)
