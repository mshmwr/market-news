---
id: MN-003
title: Next.js App Shell — SSR/ISR + Real-Time Data Architecture
status: open
created: 2026-05-09
type: architecture
priority: high
size: L
visual-delta: none
content-delta: none
design-locked: N/A
qa-early-consultation: pending
worktree: .claude/worktrees/MN-003-nextjs-shell
branch: MN-003-nextjs-shell
---

## Summary

Rebuild the market-news frontend by replacing the current static `docs/index.html` (GitHub Pages) with a Next.js application. The Next.js app will render the page shell and static/periodic signal data via SSR or ISR, while reserving client-side hooks (WebSocket or polling) for future real-time price feeds. No live data source is wired in this ticket — this is a forward-looking architecture scaffold.

## Scope

Pending BQ resolution — see §Blocking Questions below.

Expected files touched (draft, subject to BQ answers):
- `frontend/` — new Next.js app directory (layout TBD per BQ-003-04)
- `docs/` — possibly retired or reduced to redirect (per BQ-003-01)
- `.github/workflows/` — CI/deploy workflow changes (per BQ-003-02)
- `ssot/system-overview.md` — update tech stack + directory structure
- `ssot/PRD.md` — add MN-003 AC row

Out of scope (MN-003):
- Live data source / WebSocket connection to real market feed
- Auth or paywall (SP-prefix scope)
- Migration of Python worker / signal analysis CLI (unchanged)

## Blocking Questions

**BQ-003-01 — OPEN (awaiting user)**
Replace vs coexist: does `docs/index.html` (and GitHub Pages deploy) get retired when MN-003 ships, or does it coexist as a fallback?

Implication: if retired, AC must include removing/archiving `docs/index.html` and changing GH Pages source or disabling Pages. If coexist, both are maintained during the transition period.

**BQ-003-02 — OPEN (awaiting user)**
Deploy target for Next.js app: Vercel (enables ISR natively) or GitHub Pages with `next export` (SSG only, ISR impossible)?

Implication: this is the highest-impact architectural decision — it determines whether ISR is achievable or whether all "periodic refresh" must be handled via client-side polling. Vercel requires connecting the repo to Vercel dashboard; GH Pages requires `output: 'export'` in `next.config.js` which disables API routes and ISR.

**BQ-003-03 — OPEN (awaiting user)**
Data to show NOW: should the MN-003 Next.js shell display the existing `docs/signals.json` (produced by the daily GitHub Actions workflow), or is it acceptable to show a blank/placeholder shell until a future ticket wires real data?

Implication: if signals.json is fetched, Architect must decide between ISR (fetch at build time with revalidate) vs client-side fetch at page load. If placeholder, MN-003 AC is simpler.

**BQ-003-04 — OPEN (awaiting user)**
Repo layout: Next.js app under `frontend/` subdirectory inside this market-news repo (monorepo), or in a separate package.json root at repo root?

Implication: monorepo (`frontend/`) keeps Python + Next.js co-located; separate root simplifies tooling but complicates paths for GH Actions CI.

## Acceptance Criteria

_To be authored after BQ-003-01 through BQ-003-04 are resolved. Draft skeleton below._

### Phase 1 — Next.js project scaffold

AC-MN003-SCAFFOLD-01 (draft)
- Given: the repo contains a Next.js app directory (path TBD per BQ-003-04)
- When: `npm run build` executes in that directory
- Then: build exits 0 with no TypeScript errors; output includes at least one pre-rendered page (SSR or SSG)

AC-MN003-SCAFFOLD-02 (draft)
- Given: the Next.js app is deployed (target TBD per BQ-003-02)
- When: a browser requests the root URL
- Then: the page shell loads with a document `<title>` including "Market News" and a visible heading; response includes server-rendered HTML (not a blank `<div id="root">`)

### Phase 2 — Real-time data hook reservation

AC-MN003-RT-01 (draft)
- Given: the Next.js app scaffold exists
- When: a developer adds a WebSocket or polling client component
- Then: there is a designated `components/realtime/` directory and a documented stub interface (TypeScript interface or comment) indicating the expected data shape from a future price feed; no live connection is established

### Phase 3 — Legacy docs/index.html transition

AC-MN003-LEGACY-01 (draft, conditional on BQ-003-01 = retire)
- Given: MN-003 ships and Next.js app is live
- When: `docs/index.html` is accessed at the old GitHub Pages URL
- Then: either the page redirects to the new Next.js URL, or `docs/index.html` is removed and GitHub Pages source is changed to the new deploy target

---

_Ticket opened: 2026-05-09 by PM. ACs are draft skeletons; full AC authoring blocked on BQ-003-01 through BQ-003-04 user responses._
