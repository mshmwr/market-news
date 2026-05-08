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
