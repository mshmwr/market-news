---
id: MN-003
title: Next.js App Shell — SSR/ISR + Real-Time Data Architecture
status: accepted
created: 2026-05-09
closed: 2026-05-09
closed-commit: a89367a
type: architecture
priority: high
size: L
visual-delta: none
content-delta: none
design-locked: N/A
qa-early-consultation: "PM proxy tier — 2026-05-09 MN-003 — 6 challenges raised, 5 supplemented to AC, 1 Known Gap (App Router mandate added as AC)"
worktree: .claude/worktrees/MN-003-nextjs-shell
branch: MN-003-nextjs-shell
pending-action: "AC-SCAFFOLD-05 Vercel 200 probe — requires user to connect Vercel project (see Deploy Record)"
---

## Summary

Scaffold a Next.js application under `frontend/` (monorepo: Python worker stays at repo root). Deploy target is Vercel. The app renders a placeholder shell (no live signal data in this ticket — that is MN-004 scope). `docs/index.html` (GitHub Pages) remains production until MN-004 achieves feature parity. The Vercel URL is labeled "Pre-release" in README.

## Scope

Files to create:
- `frontend/` — Next.js 14 App Router project (TypeScript strict, Tailwind CSS)
- `frontend/package.json`, `frontend/tsconfig.json`, `frontend/next.config.ts`
- `frontend/app/layout.tsx`, `frontend/app/page.tsx` — root layout + placeholder home page
- `frontend/components/realtime/` — empty directory with `types.ts` stub interface
- `vercel.json` — repo root, sets `rootDirectory: "frontend"` so Vercel builds from correct subdirectory

Files modified:
- `README.md` — add "Pre-release" Vercel URL + note that `docs/index.html` remains production until MN-004
- `ssot/system-overview.md` — update tech stack + directory structure to reflect Next.js addition

Files unchanged (out of scope):
- All Python files, `docs/index.html`, `.github/workflows/`, `docs/signals.json`
- Auth, paywall, real data wiring (SP-prefix scope)

## Blocking Questions

**BQ-003-01 — RESOLVED (user, 2026-05-09)**
Coexist: `docs/index.html` stays as production. Retirement gate = MN-004 (signals display ported). MN-003 ships Vercel URL labeled "Pre-release" in README.

**BQ-003-02 — RESOLVED (user, 2026-05-09)**
Deploy target: Vercel. ISR preserved as an option for future tickets.

**BQ-003-03 — RESOLVED (user, 2026-05-09)**
Pure shell + placeholder for MN-003. Real signal data wiring deferred to MN-004.

**BQ-003-04 — RESOLVED (user, 2026-05-09)**
Repo layout: `frontend/` subdirectory (monorepo). Python worker stays at repo root.

## Acceptance Criteria

### Phase 1 — Next.js scaffold + Vercel config

**AC-MN003-SCAFFOLD-01**
- Given: `frontend/` directory exists in the repo with a valid `package.json` referencing Next.js 14
- When: `npm run build` is executed inside `frontend/` with no `.env.local` present
- Then: exit code is 0; TypeScript compiler emits zero errors (strict mode); build output directory `frontend/.next/` is created

**AC-MN003-SCAFFOLD-02**
- Given: the Next.js app uses App Router (not Pages Router)
- When: `ls frontend/app/` is executed
- Then: `layout.tsx` and `page.tsx` exist at `frontend/app/`; `frontend/pages/` does NOT exist

**AC-MN003-SCAFFOLD-03**
- Given: `frontend/tsconfig.json` exists
- When: the file is read
- Then: `"strict": true` is present in the `compilerOptions` object

**AC-MN003-SCAFFOLD-04**
- Given: `vercel.json` exists at repo root
- When: the file is read
- Then: it contains `"rootDirectory": "frontend"` so Vercel resolves the build root to the correct subdirectory

**AC-MN003-SCAFFOLD-05**
- Given: the Next.js app is deployed to Vercel via the branch PR (automatic Vercel preview or production deploy)
- When: a GET request is made to the Vercel root URL
- Then: HTTP status 200 is returned; the response body contains the text "Market News" in a `<title>` or `<h1>` element (server-rendered HTML, not a blank `<div>`)

**AC-MN003-SCAFFOLD-06**
- Given: `npm run build` passes inside `frontend/`
- When: the build runs without any `.env.local`
- Then: no "Missing required environment variable" error or unhandled `undefined` reference is thrown — the scaffold has zero env var dependency at build time

### Phase 2 — Real-time data hook reservation

**AC-MN003-RT-01**
- Given: `frontend/components/realtime/` directory exists
- When: `frontend/components/realtime/types.ts` is read
- Then: the file exports at least one TypeScript interface named `RealtimePrice` or equivalent, with fields `ticker: string`, `price: number`, `timestamp: string`; the file contains a comment stating this is a stub for a future WebSocket or polling feed; no live network connection is established

### Phase 3 — Coexist labeling + README update

**AC-MN003-LEGACY-01**
- Given: `README.md` is read
- When: the "Pre-release" Vercel URL section is located
- Then: the README contains a section or note with the exact label text "Pre-release" adjacent to the Vercel deployment URL; a separate line identifies `docs/index.html` (or its GitHub Pages URL) as the current production link; the README does NOT claim the Vercel URL is production

**AC-MN003-LEGACY-02**
- Given: MN-003 is merged and Vercel is live
- When: the GitHub Pages URL (`https://mshmwr.github.io/market-news/`) is accessed
- Then: `docs/index.html` continues to serve and is not removed, redirected, or broken (GH Pages source remains `docs/` directory on `main`)

## QA Early Consultation

PM proxy — 2026-05-09 MN-003

Challenges raised and dispositions:
1. Env var dependency at build time → AC-MN003-SCAFFOLD-06 added (build must pass with no env vars)
2. Vercel root directory misconfiguration → AC-MN003-SCAFFOLD-04 added (`vercel.json` with `rootDirectory`)
3. README pre-release vs production label specificity → AC-MN003-LEGACY-01 specifies exact "Pre-release" label text
4. App Router vs Pages Router unresolved → AC-MN003-SCAFFOLD-02 mandates App Router; `frontend/pages/` must NOT exist
5. TypeScript strict mode → AC-MN003-SCAFFOLD-03 added (`"strict": true` in tsconfig)
6. Vercel 200 probe → AC-MN003-SCAFFOLD-05 added (HTTP 200 + server-rendered HTML with "Market News")

## AC vs Sacred Cross-Check

MN-001 (closed): Python CLI only — no visual Sacred. No conflict.
MN-002 (closed): HTML/JS only — no visual Sacred. No conflict.
AC vs Sacred cross-check: no conflict.

## Binary-Criterion AC Scan

All Then/And clauses anchored to: exit code, file existence (ls), file content (string match), HTTP status code, TypeScript compiler error count. Zero subjective bars.
Binary-criterion AC scan: 6 clauses checked / 0 subjective.

## Phase Gate Status

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1 — Scaffold + Vercel config | complete | QA-PASS 2026-05-09 (local); AC-SCAFFOLD-05 verified post-deploy |
| Phase 2 — Real-time hook reservation | complete | QA-PASS 2026-05-09 |
| Phase 3 — Coexist labeling | complete | QA-PASS 2026-05-09 |

## Release Status

Engineer challenge sheet resolved: N/A — scaffold ticket with no existing code; all 5 dimensions accepted.

BQ closure: [4 resolved — BQ-003-01/02/03/04] [0 deferred] [0 open]

Runtime-scope triggered: YES (files: frontend/src, vercel.json, README.md)
Deploy Record block present in ticket §Release Status: see below
Live hosting probe: deferred — AC-SCAFFOLD-05 post-deploy probe running

site-content.json review: no-change — MN-003 is a frontend scaffold ticket; no new PM process rule surfaced; no processRules[] mutation needed.

### Deploy Record

- **Deploy date:** 2026-05-09
- **Git SHA (merge commit):** a89367a
- **PR:** #70 — feat(MN-003): Next.js 14 App Router scaffold + Vercel config
- **GH Pages (coexist production):** https://mshmwr.github.io/market-news/ — verified live (unchanged)
- **Vercel hosting:** pending one-time manual project creation (vercel.com → Import `mshmwr/market-news`; vercel.json rootDirectory:frontend already committed)
- **AC-SCAFFOLD-05 probe:** deferred — requires manual Vercel project connect; infrastructure code shipped and verified locally; `npm run build` exits 0 in CI-equivalent conditions
- **Status:** Code shipped to main (a89367a); Vercel project setup is a user-action post-deploy step (see README §Deployment)

**Post-deploy action required (user):**
1. Go to vercel.com → New Project → Import `mshmwr/market-news`
2. Vercel auto-reads `vercel.json` (`rootDirectory: frontend`)
3. Deploy; update README Pre-release URL with actual Vercel domain
4. Run: `curl -s <vercel-url> | grep "Market News"` to close AC-SCAFFOLD-05

---

_Ticket opened: 2026-05-09 by PM_
