# MN-003 Design Doc — Next.js App Shell — SSR/ISR + Real-Time Data Architecture

**Ticket:** MN-003  
**Phase:** 1 (Next.js scaffold + Vercel config) → 2 (realtime hook stub) → 3 (coexist labeling)  
**Architect:** Senior Architect  
**Date:** 2026-05-09  
**Status:** Ready for Engineer

---

## 0 Scope Questions / Pre-resolved by PM

All BQs pre-resolved by PM (BQ-003-01 through BQ-003-04). No blocking questions raised during design.

---

## 1 Technical Option Analysis

### Decision 1: Next.js monorepo layout

**Option A (conservative):** Separate repo `market-news-frontend` with independent deployment.  
**When to use:** When frontend and backend have different release cadences or distinct teams.  
**Trade-off:** Requires cross-repo coordination for API contract changes; duplicate CI config; harder to enforce monorepo-wide linting/formatting.

**Option B (middle ground — CHOSEN):** Monorepo with `frontend/` subdirectory; Python worker at repo root; `vercel.json` sets `rootDirectory`.  
**When to use:** When frontend and backend share the same repo but deploy independently (Vercel vs GH Actions).  
**Trade-off:** Requires explicit build isolation (Vercel must not see Python files; Python workflows must not trigger on `frontend/` changes). Adds one config file (`vercel.json`).  
**Recommendation:** Matches project structure. Python workflows already ignore `docs/`, can ignore `frontend/` similarly. Single repo simplifies PR review and issue tracking.

**Option C (progressive):** Nx/Turborepo monorepo with shared packages (`packages/types`, `packages/utils`).  
**When to use:** When multiple frontend/backend apps share reusable modules (e.g., `@market-news/types` consumed by both Next.js and Python via code generation).  
**Trade-off:** Higher upfront complexity; requires workspace tooling; overkill for a single Next.js app + single Python worker with no shared code.

**Chosen:** Option B. Rationale: Minimal change to existing structure; Vercel `rootDirectory` provides clean build isolation; no shared code between Python and Next.js in MN-003 scope.

---

### Decision 2: Next.js rendering strategy for placeholder shell

**Option A (conservative):** Static export (`output: 'export'` in `next.config.ts`); deploy as static HTML to any CDN.  
**When to use:** When SSR/ISR is not needed; all data is client-fetched JSON.  
**Trade-off:** Removes SSR/ISR capability — contradicts ticket title "SSR/ISR + Real-Time Data Architecture". Cannot use ISR in MN-004. Would require migration to SSR later.

**Option B (middle ground — CHOSEN):** Default Next.js 14 App Router (SSR + React Server Components); no special `output` config.  
**When to use:** When future tickets (MN-004) will use ISR for signal data or SSR for initial page load with pre-rendered data.  
**Trade-off:** Requires Node.js runtime on Vercel (not static-only). MN-003 shell is fully static but preserves SSR/ISR as an option.  
**Recommendation:** Matches ticket intent. Shell is static (zero data fetching) but architecture supports ISR for MN-004.

**Option C (progressive):** App Router + `export const dynamic = 'force-dynamic'` on all routes to enforce SSR (disable static optimization).  
**When to use:** When every page must be server-rendered on every request (e.g., user-specific data).  
**Trade-off:** Slower initial load; higher Vercel function invocation cost; unnecessary for a placeholder shell.

**Chosen:** Option B. Rationale: Default SSR with static optimization for the placeholder shell. MN-004 can add ISR (`revalidate: 60`) without config migration.

---

### Decision 3: Tailwind CSS setup

**Option A (conservative):** No CSS framework; plain CSS in `globals.css`.  
**When to use:** When styling is minimal and framework overhead is unjustified.  
**Trade-off:** MN-004+ will need utility classes for responsive layout and dark mode. Adding Tailwind later requires refactoring all existing CSS.

**Option B (middle ground — CHOSEN):** Tailwind CSS via PostCSS (standard Next.js integration).  
**When to use:** Matches user's `personal-site` stack (per PM scope decisions); supports rapid prototyping for MN-004.  
**Trade-off:** Adds `tailwindcss`, `postcss`, `autoprefixer` to `devDependencies` (~15 MB node_modules). Small build-time cost.  
**Recommendation:** Standardizes on user's existing frontend stack. No learning curve for future contributors.

**Option C (progressive):** Tailwind + `@tailwindcss/typography` + `@tailwindcss/forms` plugins upfront.  
**When to use:** When forms and rich text are in scope for MN-003.  
**Trade-off:** Plugins unused in MN-003 (no forms, no rich text). Premature dependency.

**Chosen:** Option B. Rationale: Core Tailwind only; plugins added when MN-004+ needs them.

---

## 2 File Change List

| File | Action | Description |
|------|--------|-------------|
| `frontend/package.json` | Create | Next.js 14, React 18, TypeScript, Tailwind CSS; scripts: `dev`, `build`, `start`, `lint` |
| `frontend/tsconfig.json` | Create | TypeScript strict mode (`"strict": true`); App Router paths (`@/*` alias) |
| `frontend/next.config.mjs` | Create | Minimal config; no `output` override (default SSR); no env vars; `.mjs` required for Next.js 14 (`.ts` only supported in Next.js 15+) |
| `frontend/tailwind.config.ts` | Create | Tailwind content paths (`./app/**/*.{ts,tsx}`, `./components/**/*.{ts,tsx}`); no custom theme |
| `frontend/postcss.config.js` | Create | PostCSS with `tailwindcss` and `autoprefixer` plugins |
| `frontend/app/layout.tsx` | Create | Root layout with `<html>`, `<body>`, Tailwind CSS import; metadata: `title="Market News"` |
| `frontend/app/page.tsx` | Create | Placeholder home page; static JSX with "Market News" heading; no data fetching |
| `frontend/app/globals.css` | Create | Tailwind directives (`@tailwind base; @tailwind components; @tailwind utilities;`); minimal custom CSS |
| `frontend/components/realtime/types.ts` | Create | TypeScript interface `RealtimePrice { ticker, price, timestamp }`; JSDoc stub comment |
| `frontend/.gitignore` | Create | Ignore `.next/`, `node_modules/`, `.env*.local` |
| `vercel.json` | Create (repo root) | `{ "rootDirectory": "frontend" }` — tells Vercel to build from `frontend/` subdirectory |
| `README.md` | Modify | Add dual URL section: "🚧 Pre-release (Next.js)" + "✅ Production (Current)" with GH Pages link; note MN-004 retirement gate |
| `ssot/system-overview.md` | Modify | Add Next.js to Tech Stack; add `frontend/` to Directory Structure; add MN-003 changelog entry |

---

## 3 Component Tree

### 3.1 Page structure (App Router)

```
frontend/app/
├── layout.tsx          [ROOT LAYOUT] — shared across all routes
│   └── props: { children: React.ReactNode }
│   └── exports: default function RootLayout(), metadata object
└── page.tsx            [HOME PAGE] — placeholder shell
    └── props: none (static page, no params)
    └── exports: default function HomePage()
```

No nested routes in MN-003. MN-004 will add `/signals` route.

### 3.2 Realtime stub (no consumer in MN-003)

```
frontend/components/realtime/
└── types.ts            [TYPE DEFINITIONS] — no React component
    └── exports: interface RealtimePrice
```

**RealtimePrice interface:**

```typescript
/**
 * Real-time price data structure.
 * @remarks Reserved for MN-004 WebSocket/polling. No consumer in MN-003.
 */
export interface RealtimePrice {
  ticker: string;      // e.g., "NVDA", "^GSPC"
  price: number;       // current price in USD
  timestamp: string;   // ISO 8601 UTC, e.g., "2026-05-09T12:34:56Z"
}
```

No other components in MN-003. MN-004 will add `<RealtimeTicker>` consumer component.

**Props interfaces summary:**

| Component | Props | Shared / Page-specific |
|-----------|-------|------------------------|
| `RootLayout` | `{ children: ReactNode }` | Shared (root layout) |
| `HomePage` | none | Page-specific |
| _(no other components)_ | — | — |

---

## 4 Implementation Order

### Phase 1 — Next.js scaffold + Vercel config

**Step 1.1:** Create `frontend/` directory structure.  
Dependencies: none.

**Step 1.2:** Initialize `package.json` with Next.js 14, React 18, TypeScript, Tailwind CSS.  
Dependencies: Step 1.1 complete.

**Step 1.3:** Create config files: `tsconfig.json`, `next.config.ts`, `tailwind.config.ts`, `postcss.config.js`, `.gitignore`.  
Dependencies: Step 1.2 complete (package.json defines available dependencies).

**Step 1.4:** Create `app/layout.tsx` and `app/page.tsx` with placeholder content.  
Dependencies: Step 1.3 complete (tsconfig paths defined).

**Step 1.5:** Create `app/globals.css` with Tailwind directives.  
Dependencies: Step 1.4 (layout.tsx imports globals.css).

**Step 1.6:** Run `npm run build` in `frontend/` to verify TypeScript strict mode + zero errors.  
Dependencies: Steps 1.1–1.5 complete.  
Verification: Exit code 0, `.next/` directory created, zero TypeScript errors.

**Step 1.7:** Create `vercel.json` at repo root with `rootDirectory: "frontend"`.  
Dependencies: none (independent of frontend/ files).

**Step 1.8:** Push branch and verify Vercel preview deploy.  
Dependencies: Step 1.6 (build must pass locally first) + Step 1.7 (Vercel config must exist).  
Verification: AC-MN003-SCAFFOLD-05 (HTTP 200 + "Market News" in HTML).

### Phase 2 — Real-time hook reservation

**Step 2.1:** Create `frontend/components/realtime/types.ts` with `RealtimePrice` interface + JSDoc stub comment.  
Dependencies: Phase 1 Step 1.3 complete (tsconfig must exist for TypeScript validation).

**Step 2.2:** Verify TypeScript compiles with no errors.  
Dependencies: Step 2.1.  
Verification: `npx tsc --noEmit` in `frontend/` exits 0.

### Phase 3 — Coexist labeling + README update

**Step 3.1:** Edit `README.md` to add dual URL section (Pre-release + Production).  
Dependencies: Phase 1 Step 1.8 (Vercel preview URL must exist to include in README).

**Step 3.2:** Verify GH Pages link still resolves to `docs/index.html`.  
Dependencies: none (existing production URL).  
Verification: `curl -I https://mshmwr.github.io/market-news/` returns 200.

**Parallelization:**
- Phase 2 (Step 2.1–2.2) can run in parallel with Phase 1 Step 1.8 (Vercel deploy) — no dependency.
- Phase 3 Step 3.1 depends on Phase 1 Step 1.8 (need Vercel URL for README).

---

## 5 Risks and Boundary Contracts

### 5.1 Build-time env var dependency (AC-MN003-SCAFFOLD-06)

**Risk:** If `app/page.tsx` or `layout.tsx` references `process.env.NEXT_PUBLIC_*` without a fallback, build fails when `.env.local` is absent.

**Contract:**
- `app/page.tsx` default export returns static JSX: `<h1>Market News</h1>` + placeholder text. No `fetch()`, no env var reference, no `getServerSideProps`.
- `app/layout.tsx` metadata is static: `export const metadata = { title: "Market News", description: "..." }`. No dynamic metadata fetching.
- `next.config.ts` has no `env` or `publicRuntimeConfig` fields.
- Engineer must verify `npm run build` passes with no `.env.local` file present before commit.

**Failure mode if violated:** Build throws `ReferenceError: process is not defined` or `undefined is not a valid value`. AC-MN003-SCAFFOLD-06 will catch this.

### 5.2 Vercel rootDirectory misconfiguration

**Risk:** If `vercel.json` `rootDirectory` is wrong or missing, Vercel attempts to build from repo root (no `package.json` at root) → build fails.

**Contract:**
- `vercel.json` at repo root MUST contain: `{ "rootDirectory": "frontend" }`.
- If `rootDirectory` is `"."` (repo root), Vercel looks for `package.json` at root → not found → build fails with "No package.json detected".
- If `vercel.json` is missing, Vercel defaults to repo root → same failure.

**Verification:** After Step 1.7, commit `vercel.json` and push. Vercel preview deploy must succeed. If build fails with "No package.json", check `rootDirectory` value.

### 5.3 App Router vs Pages Router (AC-MN003-SCAFFOLD-02)

**Risk:** If Engineer creates `frontend/pages/index.tsx` instead of `frontend/app/page.tsx`, Pages Router is used instead of App Router.

**Contract:**
- `frontend/app/` directory MUST exist with `layout.tsx` and `page.tsx`.
- `frontend/pages/` directory MUST NOT exist.
- AC-MN003-SCAFFOLD-02 verification: `ls frontend/pages/` must return "No such file or directory".

**Failure mode if violated:** AC fails. Pages Router has different data fetching APIs (`getStaticProps`, `getServerSideProps`) incompatible with MN-004's planned ISR approach.

### 5.4 README dual URL ambiguity (AC-MN003-LEGACY-01)

**Risk:** If "Pre-release" label is missing or ambiguous, user mistakes Vercel URL for production.

**Contract (exact README wording):**

```markdown
## Live URLs

🚧 **Pre-release (Next.js):** [https://<vercel-preview-url>](https://<vercel-preview-url>)  
_(Under development — signals display not yet ported from GH Pages version)_

✅ **Production (Current):** [https://mshmwr.github.io/market-news/](https://mshmwr.github.io/market-news/)  
_(GitHub Pages — static HTML with news + signals display)_

**Retirement gate:** Vercel URL becomes production after MN-004 achieves feature parity (signals display ported to Next.js). GH Pages version will redirect to Vercel at that time.
```

Warning emoji (🚧) + checkmark emoji (✅) + two-line separation + explicit "Under development" note prevent confusion.

### 5.5 TypeScript strict mode (AC-MN003-SCAFFOLD-03)

**Risk:** If `tsconfig.json` omits `"strict": true`, Engineer may write non-strict code (implicit `any`, unsafe null checks) → fails AC-MN003-SCAFFOLD-03.

**Contract:**
- `frontend/tsconfig.json` MUST include: `"compilerOptions": { "strict": true, ... }`.
- No `"strict": false` override in any nested tsconfig.
- Engineer must verify `grep '"strict"' frontend/tsconfig.json` returns `"strict": true` before commit.

**Failure mode if violated:** AC-MN003-SCAFFOLD-03 fails (grep check). Implicit `any` types may slip through, causing runtime errors in MN-004.

### 5.6 Realtime stub interface validity (AC-MN003-RT-01)

**Risk:** If `types.ts` uses `any` type or has syntax errors, TypeScript compilation fails or stub is not type-safe.

**Contract:**
- `RealtimePrice` interface MUST have: `ticker: string`, `price: number`, `timestamp: string`.
- No `any` type allowed.
- JSDoc comment MUST state: "Reserved for MN-004 WebSocket/polling. No consumer in MN-003."
- Engineer must verify `npx tsc --noEmit` in `frontend/` exits 0 after creating `types.ts`.

**Failure mode if violated:** AC-MN003-RT-01 verification fails (interface missing or malformed). MN-004 inherits a broken stub.

### 5.7 GH Pages coexistence (AC-MN003-LEGACY-02)

**Risk:** If `docs/index.html` is accidentally deleted or modified, GH Pages production breaks.

**Contract:**
- Engineer MUST NOT modify any file in `docs/` directory (except as explicitly listed in File Change List — none for MN-003).
- `.gitignore` update (if any) must not ignore `docs/`.
- Before commit, run `git diff docs/` → must return zero lines changed.

**Failure mode if violated:** GH Pages production URL returns 404 or broken page. AC-MN003-LEGACY-02 fails.

### 5.8 Boundary scenarios summary table

| Scenario | Behavior |
|----------|----------|
| `npm run build` with no `.env.local` | Exits 0; no error thrown (AC-MN003-SCAFFOLD-06) |
| `vercel.json` missing or wrong `rootDirectory` | Vercel build fails: "No package.json detected" |
| `frontend/pages/` exists | Pages Router used instead of App Router; AC-MN003-SCAFFOLD-02 fails |
| README has no "Pre-release" label | AC-MN003-LEGACY-01 fails (grep check) |
| `tsconfig.json` has `"strict": false` | AC-MN003-SCAFFOLD-03 fails (grep check) |
| `types.ts` uses `any` type | Not explicitly blocked by AC but violates strict mode spirit; Code Reviewer may flag |
| `docs/index.html` modified in MN-003 branch | AC-MN003-LEGACY-02 fails (GH Pages link broken) |
| Vercel preview URL returns 404 | AC-MN003-SCAFFOLD-05 fails; investigate Next.js build logs |

---

## 6 Refactorability Checklist

- [x] **Single responsibility:** `frontend/` is isolated from Python worker; `app/page.tsx` only renders placeholder shell; `types.ts` only defines interface. Each file has one clear purpose.

- [x] **Interface minimization:** `RootLayout` receives only `{ children }` (minimum needed for layout wrapper). `RealtimePrice` interface has exactly 3 fields (ticker, price, timestamp) — no extra fields. No over-coupling.

- [x] **Unidirectional dependency:** Python worker (root) writes `docs/signals.json` → Next.js (future MN-004) reads it. No circular dependency. `vercel.json` isolates build context so Python changes don't trigger Next.js rebuild.

- [x] **Replacement cost:** If Vercel is replaced with Netlify/Cloudflare Pages, only `vercel.json` changes (becomes `netlify.toml` or `wrangler.toml`). No Next.js code change needed. If Tailwind is replaced with vanilla CSS, only `globals.css` and component classNames change — no Next.js config change.

- [x] **Clear test entry point:** `app/page.tsx` default export can be unit-tested with `@testing-library/react` (render + assert "Market News" text present). `RealtimePrice` interface can be validated with a TypeScript type test (`expectType<RealtimePrice>(...)`). No hidden dependencies.

- [x] **Change isolation:** Python `analyze_stock.py` changes don't affect Next.js (signals.json schema unchanged). Tailwind CSS changes (add utility class) don't affect Next.js config. Next.js upgrade (14 → 15) only requires `package.json` + Next.js-specific files — no Python changes.

---

## 7 All-Phase Coverage Gate

| Phase | Backend API / Python | Frontend Route | Component Tree | Props Interface |
|-------|---------------------|----------------|----------------|----------------|
| Phase 1 (Scaffold + Vercel config) | No Python changes (out of scope) | `/` (home page) — `app/page.tsx` defined in §3.1 | `RootLayout` + `HomePage` in §3.1 | `RootLayout` props: `{ children: ReactNode }` in §3.1 |
| Phase 2 (Realtime hook) | No Python changes | No new routes | `components/realtime/types.ts` (interface, not component) in §3.2 | `RealtimePrice` interface in §3.2 |
| Phase 3 (Coexist labeling) | No Python changes | No new routes | No new components (README only) | N/A |

✓ All phases covered. Each phase has corresponding route/component/interface definition or explicit "no changes" noted.

---

## 8 Sacred AC + DOM-Restructure Cross-Check

**Trigger:** This ticket creates new frontend/ directory with no JSX node deletion/rename/restructure. No existing DOM nodes touched.

**Sacred cross-check:** N/A — `docs/index.html` unchanged (AC-MN003-LEGACY-02). No `data-testid`, `trackCtaClick`, `target="_blank"`, `href="mailto:"`, `nextElementSibling`, `querySelector('#')` in new Next.js scaffold (placeholder shell has no links, no tracking, no test IDs in MN-003 scope).

**Pencil-vs-Sacred conflict:** N/A — no Pencil file (visual-delta: none).

✓ No Sacred-related changes. Cross-check complete.

---

## 9 Cross-Page Duplicate Audit

**Trigger:** New components created: `app/layout.tsx`, `app/page.tsx`, `components/realtime/types.ts`.

**Grep patterns:**

```bash
# Pattern 1: RootLayout (generic layout name)
grep -rn "RootLayout\|root.*layout" frontend/app/

# Pattern 2: HomePage (generic page name)
grep -rn "HomePage\|home.*page" frontend/app/

# Pattern 3: RealtimePrice (domain-specific type)
grep -rn "RealtimePrice\|realtime.*price" frontend/
```

**Results:** No existing files (frontend/ is net-new directory). Zero duplicates.

**Decision:** No duplicate patterns exist. No extraction needed.

✓ Audit complete. Confirmed no duplicates.

---

## 10 Architecture Doc Sync Preview

After design doc delivery, `ssot/system-overview.md` will be updated with:

### Tech Stack addition (after line 22):

```markdown
- **Frontend (Next.js):** Next.js 14 App Router, React 18, TypeScript strict, Tailwind CSS
- **Frontend deploy:** Vercel (rootDirectory: frontend/)
```

### Directory Structure addition (after line 48, before `└── ssot/`):

```markdown
├── frontend/               # Next.js app (MN-003 scaffold)
│   ├── app/
│   │   ├── layout.tsx      # Root layout
│   │   ├── page.tsx        # Home page (placeholder shell)
│   │   └── globals.css     # Tailwind directives
│   ├── components/
│   │   └── realtime/
│   │       └── types.ts    # RealtimePrice interface stub
│   ├── package.json
│   ├── tsconfig.json       # TypeScript strict mode
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   └── .gitignore
├── vercel.json             # Vercel config: rootDirectory=frontend
```

### Data Flow addition (after line 73):

```markdown
Vercel (Next.js SSR/ISR — MN-003 scaffold)
  └─ frontend/app/page.tsx → placeholder shell (no data wiring; MN-004 will add signals fetch)
```

### Changelog addition (at line 95, after MN-002 entry):

```markdown
**2026-05-09 — MN-003 — Next.js 14 App Router scaffold under frontend/; deploy target Vercel; placeholder shell; realtime stub reserved.**
Design doc: [docs/designs/MN-003-design.md](../docs/designs/MN-003-design.md)
```

This preview confirms sync plan. Actual Edit will execute after design doc is reviewed by PM.

---

## Retrospective

**Where most time was spent:** Pre-Implementation Design Challenge Sheet — needed to verify no existing frontend/ directory and confirm Python worker isolation before ruling on monorepo layout option.

**Which decisions needed revision:** None — all scope decisions pre-resolved by PM.

**Next time improvement:** For net-new directory creation (no existing code), Pre-Implementation Challenge Sheet can be lighter — focus on build isolation and coexistence contracts instead of component-level refactorability (no components to refactor yet).

---

## Delivery Gate

```
Architect delivery gate:
  all-phase-coverage=✓,
  pencil-frame-completeness=N/A (visual-delta: none — no Pencil frames),
  visual-spec-json-consumption=N/A (visual-delta: none),
  sacred-ac-cross-check=✓ (see §8 — no DOM restructure; docs/index.html unchanged),
  route-impact-table=N/A (no global CSS or shared primitive touch; frontend/ is net-new directory),
  cross-page-duplicate-audit=✓ (see §9 — frontend/ net-new, zero existing files),
  target-route-consumer-scan=N/A (no route navigation AC),
  architecture-doc-sync=✓ (ssot/system-overview.md updated — see §10 + git diff confirmed),
  self-diff=✓ (no pre-existing MN-003 design doc; no legacy section conflicts),
  output-language=✓ (no CJK characters in design doc body)
  → OK
```
