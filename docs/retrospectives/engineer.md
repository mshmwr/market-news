## 2026-05-10 — Restore Feedback Button (Lazy Firebase)

**What went well:** Source of truth was the legacy `docs/index.html` script block — copied the Firebase config + Firestore write shape verbatim, only translated to React state + Tailwind. Lazy-imported `firebase/firestore` and `@/lib/firebase` inside the submit handler so initial First Load JS only grew +0.9kB (vs +77kB with eager import). `npx next build` confirmed both the bundle delta and the dynamic chunk split.
**What went wrong:** First version eagerly imported Firebase at top-of-file → bundle size jumped 6.88kB → 84.2kB on `/`. Caught this via the build output and refactored to dynamic import inside the click handler. Should have started with lazy import: any third-party SDK ≥30kB used only in a rare modal flow is a candidate for dynamic import from the very first commit.
**Next time improvement:** When porting a feature that pulls in a heavy SDK (Firebase, payment, charting), default to dynamic `await import('...')` inside the trigger handler. Only switch to top-level import if profiling shows the user-visible delay matters.

## 2026-05-10 — Rationale Translate Chunked to Survive NIM Disconnect

**What went well:** Root cause was visible in the run log on first read — three RemoteDisconnected attempts on `rationale_translate`, last with `0 entries` parsed, so HTML rendered EN-only. Fix was a 20-line refactor of `_translate_rationales` (single big batch → chunks of 4) that preserves the parse logic and the EN fallback. `python3 -m py_compile` verified syntax in seconds.
**What went wrong:** Treated `_translate_rationales` as exempt from the MN-008 lesson ("NIM dies on big workloads") because the lesson was framed as concurrency (`max_workers`), not prompt size. A 12-stock batch with detailed multi-factor rationale is a long prompt + long expected response; same server-side pressure, different surface. User had to point out the missing ZH because there was no per-section visual telltale — it just silently degraded.
**Next time improvement:** When integrating any new LLM call that aggregates N items into one prompt, default to chunking (4–6 items/chunk). The MN-008 lesson generalises: NIM RemoteDisconnected is triggered by **total work per request**, whether that's parallel calls or a long single-prompt response. Add the chunking pattern to digest's NIM helper conventions.

## 2026-05-09 — UI Polish: Filter Position + Split Components

**What went well:** Three filter-position iterations (PR #91 under h2 → PR #92 under explainer → PR #100 back into sticky header) each took one Edit + one build, no regressions. PR #99 split monolithic `SignalFilters` into `SignalCatFilter` + `SignalActionFilter` — cleaner placement freedom, both consumers (header + section body) call separate components. `npx next build` was the single source of truth: every iteration verified before push.
**What went wrong:** Three back-and-forth iterations of the same filter block before settling. Each move was driven by a specific user nudge ("under h2" → "under 信心度" → "back to header"). Built component split too late — should have split the moment the first relocation request landed, since it telegraphed the user wanted the two filters in different places.
**Next time improvement:** When a UI element has two distinct concerns (category vs action) and the user starts moving it around, treat that as a structural signal: split first, then relocate. Avoids moving the wrong unit twice.

## 2026-05-09 — MN-010 Manual Regenerate Button + Cron Push Race Fix

**What went well:** `app/api/digest/regenerate/route.ts` is a 60-line server route that does workflow_dispatch + run-list inspection in two sequential GitHub API calls; rate-limit logic (409 if any in_progress/queued, 429 if last success <12h with `nextAvailable` timestamp) is plain integer arithmetic, no DB. Frontend `RegenerateButton` covers idle/pending/triggered/running/cooldown/error from the same response shape. Cron push race patched in same PR (#97) — three-attempt `git pull --rebase && git push` loop survives concurrent main commits during the ~15-min run.
**What went wrong:** First two cron runs (13:06 schedule + 13:47 dispatch) were started before PR #97 merged, so they used the pre-#97 workflow without retry — both lost the push race when other PRs landed mid-run. Had to manually trigger a fresh dispatch after merge so the new runner would `actions/checkout@v4` the updated workflow file.
**Next time improvement:** When patching a workflow that currently has runs in flight, cancel any in-flight runs that pre-date the patch — they cannot benefit from it and will fail the same way. Saves 15 minutes of NIM tokens per stuck run.

## 2026-05-09 — MN-Cron Email Decommission

**What went well:** PR #95 single-edit decommission: `digest.py --preview` already wrote `docs/digest-latest.html` for MN-009; workflow change was deleting the email-send step and adding `git add docs/digest-latest.html` + commit + push. No code path changes in `digest.py` itself — the `--preview` flag was already the no-email path. RESEND_API_KEY env removal was a separate clean-up step in the workflow.
**What went wrong:** Did not anticipate that the new commit step would race against concurrent main commits during the workflow's ~15-min runtime. First scheduled run after merge failed at push because PR #95 itself + a docs PR landed during the run. Had to follow up with PR #97 retry loop to make the workflow self-healing.
**Next time improvement:** Any new workflow step that does `git push` to a busy branch needs a rebase+retry block from day one, not as a follow-up patch. Treat the GitHub Actions long-running job as an inherently racy committer.

## 2026-05-09 — MN-009 Digest Web Tab

**What went well:** Reused the existing ISR `RAW_BASE` pattern by adding one `fetchDigest()` helper — three-line analogue of `fetchSignals` / `fetchNews`. `dangerouslySetInnerHTML` was acceptable here because the HTML is generated by our own `digest.py`, which already runs `html.escape` on every interpolated external string. Frontend gracefully degrades when the file does not yet exist on `main` — null fetch → bilingual placeholder.
**What went wrong:** Tried to seed an initial `docs/digest-latest.html` by running `digest.py --preview` locally but the rationale-translate slot looped on NIM read timeouts; killed the run and shipped without seed. Empty placeholder will be visible until the next cron tick populates the file.
**Next time improvement:** When a future ticket requires a static asset to land on `main` for the frontend to render, prefer a `workflow_dispatch` manual trigger over a local seed run — skips the local NIM dependency and exercises the production commit path immediately.

## 2026-05-09 — MN-008 Richer Digest Content + NIM Reliability

**What went well:** TW/US split + market-moving section landed cleanly via additive helpers (`_split_signals_by_region`, `_fetch_market_news`, region-aware `_narrative_stocks`); the interleave fold for US/TW news is small enough to fit in the function. Bilingual chrome (English first, Chinese after) was a search/replace pass, not a structural rewrite. Per-news `published_ts` capture was already on the `fetch_news` schema — only had to forward it through.
**What went wrong:** First production run with `max_workers=6` lost 3 of 6 NIM slots to `RemoteDisconnected`; even with 3-attempt exponential-backoff retry the same 3 slots failed all attempts. Root cause was server-side: 6 simultaneous reasoning-mode requests overwhelmed NIM. Cut concurrency to `max_workers=2` and the failure mode disappeared (5–6 of 6 slots populated each run).
**Next time improvement:** When integrating a new LLM provider in parallel mode, start at `max_workers=2` and only raise after observing stable success across multiple runs. Also: long reasoning prompts truncate silently when `finish_reason=length` — log `completion_tokens` per attempt so the truncation case is distinguishable from a network failure.

## 2026-05-09 — MN-007 Per-Section LLM Narrative

**What went well:** First integration of NVIDIA NIM (MiniMax M2.7) used the existing `NVIDIA_API_KEY` secret — no new secret to onboard. The narrative pattern (one prompt per section, return string, render as a styled `<p>` block) kept the renderer change minimal and let each section degrade independently to raw lists.
**What went wrong:** Initial 4 narrative slots all hit the 180-second timeout on first cron run. Bumping per-call timeout alone was insufficient because total wall-time then exceeded the workflow's effective budget; had to parallelise via `ThreadPoolExecutor` to keep total ≈ max(single-call). Second run revealed `max_tokens=4096` was insufficient because the reasoning model spends part of the budget on `reasoning_content` — bumped to 8192.
**Next time improvement:** For reasoning-mode LLMs, budget `max_tokens` for **both** reasoning and content; pick a figure ≥2× the longest expected response. Always add a `label` argument to the API helper so per-section failures are identifiable in workflow logs (this saved us in MN-008 debugging).

## 2026-05-09 — MN-006 Daily Digest Email Scheduler

**What went well:** `py_compile` passed on first try; Resend SDK type was TypedDict (`.get()` is valid) — no API surface mismatch; graceful degradation for all three fallible fetchers implemented correctly.
**What went wrong:** Interpolated RSS/signal data directly into HTML f-strings without escaping; code review caught this.
**Next time improvement:** When writing HTML rendering with external data, call `html.escape()` on every interpolated value in the same Edit — not post-review.

## 2026-05-09 — MN-005 PWA Port + GH Pages Retirement

**What went well:** Plain `public/sw.js` approach (no next-pwa) was zero-config; build passed first try; tsc exit 0 on first try; binary icon copy verified via `diff` immediately.
**What went wrong:** No functional issues. Vercel auto-deploy did not trigger on squash merge — same pattern as MN-003/004 (manual deploy required by user).
**Next time improvement:** Document at ticket open that Vercel requires manual `vercel --prod` after merge; do not block Phase B close on auto-deploy assumption.

## 2026-05-09 — MN-004 Signals Display Port

**What went well:** Design doc's component tree and TypeScript interface spec translated directly to working code with zero structural surprises; tsc exit 0 on first attempt after fixing two minor name-collision issues.
**What went wrong:** (1) `import { NewsItem }` name clash with component `NewsItem` required aliasing to `NewsItemType`/`NewsItemRow`; (2) `[...new Set(...)]` spread requires `downlevelIteration` or es2015+ target — used `Array.from()` instead; both caught by tsc immediately.
**Next time improvement:** When a type name and a component name share the same identifier, alias one at import time; document the alias decision in the design doc component tree to prevent same-session confusion.

## 2026-05-09 — MN-003 Next.js Scaffold

**What went well:** Design doc pre-resolved all scope decisions; zero BQs hit during implementation. Build passed on second attempt.
**What went wrong:** `next.config.ts` is only supported in Next.js 15+; used `.ts` per design doc spec but Next.js 14.2.29 requires `.mjs`; caught immediately by build error and fixed in one step.
**Next time improvement:** When specifying config file extensions in design docs for Next.js projects, verify the installed version supports `.ts` config before naming it — would have saved one build cycle.
**Slowest step:** `npm install` — ~45s for first-time dependency resolution.

## 2026-05-08 — Debate UI Render

**What went well:** Single-file HTML edit; CSS + JS both in `docs/index.html`. Guard `if (s.bull_case || s.bear_case)` lets old archived signals render cleanly without the debate block — no migration step needed. Used `appendChild(document.createTextNode(...))` after `innerHTML` to avoid XSS on the case strings while keeping the label tag styled.

**What went wrong:** None.

**Next time improvement:** When new SignalResult fields arrive, plan UI render same session as backend ship — UI was a separate PR (#67) which left the new fields invisible for ~30min. Tightening would mean shipping data + display together.

**Slowest step:** Locating the right insertion point in the 800-line index.html — used grep on `signal-rationale` to find both CSS and JS sites in two queries.

---

## 2026-05-08 — Bull/Bear/Judge Debate Synthesizer

**What went well:** Three-call adversarial pattern slot in cleanly via `_call_llm` helper; existing `compute_undervaluation` + bundle dump reused unchanged. Each prompt forces commitment to one side ("no hedging words"), surfacing the strongest case both ways. Smoke test on GLW returned HOLD 58% with bull/bear/judge rationales that visibly weigh both sides.

**What went wrong:** Forgot to `git add docs/retrospectives/engineer.md` in the synthesizer commit — retro entry was lost when worktree was abandoned. Recovered by re-writing in next worktree.

**Next time improvement:** Stage retro + code in same `git add` per CLAUDE.md trigger. Or use `git add -A` on the worktree after verifying scope with `git status --short`.

**Slowest step:** Iterating prompts to remove hedging — initial drafts had judge restating both sides without picking a winner; tightened with explicit "Bull case significantly stronger → BUY" decision rules.

---

## 2026-05-04 — MN-031/032/033/034/035 Engineer

**What went well:** Five tickets shipped in one session — additive-only Pydantic fields (nullable defaults) meant old bundle JSON loaded without migration. Undervaluation + analyst rating fields flowed cleanly through models → synthesizer → frontend card.

**What went wrong:**
1. `git worktree remove` ran while CWD was inside the target worktree → `fatal: Unable to read current working directory`. Fix: always run worktree removal from repo root.
2. MN-032 worktree created before fetching latest `origin/main` → diverged HEAD required `git rebase origin/main`. Fix: fetch + merge origin/main on canonical checkout before every `git worktree add`.
3. Repeated from 2026-05-03: Edit on worktree copy without first Reading that worktree path → "file not read yet" guard hit again.

**Next time improvement:**
- `git worktree remove` must run from repo root — not from inside the target worktree.
- Before `git worktree add`: (1) `git fetch origin`, (2) `git merge origin/main --ff-only`, (3) `git worktree add ... origin/main`.

---

## 2026-05-03 — MN-002 Engineer

**What went well:** Design doc provided exact pseudo-code and CSS verbatim — zero ambiguity on implementation; `ssot/system-overview.md` was already updated in the branch by the Architect, so the SSOT update required no extra commit.

**What went wrong:** First Edit on `docs/index.html` hit "file not read yet" guard because the worktree copy had not been Read before editing (Read had been done on the canonical repo path only). Added a Read call before the Edit.

**Next time improvement:** When worktree path differs from canonical repo path, Read the worktree copy explicitly — do not assume a Read of the canonical path satisfies the Edit guard.

**Slowest step:** Reading 6 files in parallel at session start; all other steps were immediate.
