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
