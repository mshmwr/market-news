---
id: MN-005
title: PWA Port to Next.js + Retire GH Pages
status: open
created: 2026-05-09
type: feature
priority: medium
size: M
visual-delta: none
content-delta: yes
design-locked: false
qa-early-consultation: "PM proxy tier — 2026-05-09 MN-005 — see §QA Early Consultation"
worktree: .claude/worktrees/MN-005-pwa-ghpages
branch: MN-005-pwa-ghpages
dependencies: MN-004 (closed 2026-05-09)
---

## Summary

Port the PWA features from `docs/` (legacy GH Pages) into the Next.js frontend on Vercel. Retire GH Pages as production: add a meta-refresh redirect in `docs/index.html`, update README to reflect Vercel as the sole production URL, and update SSOT docs. The GitHub Actions cron workflows that update `docs/news.json` and `docs/signals.json` are kept running (Next.js ISR fetches them via raw.githubusercontent.com).

## Scope

**Files to create:**
- `frontend/public/manifest.json` — updated for Vercel (start_url `/`, scope `/`)
- `frontend/public/sw.js` — service worker (network-first for HTML/JSON, cache-first for icons)
- `frontend/public/icon-192.png` — copied from `docs/icon-192.png`
- `frontend/public/icon-512.png` — copied from `docs/icon-512.png`
- `frontend/components/pwa/PwaRegister.tsx` — client component that registers service worker

**Files to modify:**
- `frontend/app/layout.tsx` — add `<link rel="manifest">`, Apple touch icon meta tags, `<PwaRegister />` component
- `docs/index.html` — add `<meta http-equiv="refresh" content="0; url=https://market-news-sigma.vercel.app">` near top of `<head>` (GH Pages redirect to Vercel)
- `README.md` — remove "Pre-release" label; Vercel = Production only; GH Pages = Legacy (redirects to Vercel)
- `ssot/system-overview.md` — update Hosting line; update Summary paragraph; update Changelog
- `ssot/PRD.md` — move MN-004 AC blocks to §Closed Tickets; add MN-005 AC summary to §Active Tickets

**Files NOT modified:**
- `docs/news.json`, `docs/signals.json`, `.github/workflows/` (cron keeps running — Next.js needs these files)
- All Python files
- `docs/icon-192.png`, `docs/icon-512.png` (kept in docs/ for legacy GH Pages; also copied to frontend/public/)

## Acceptance Criteria

### Phase 1 — PWA assets in Next.js

**AC-MN005-PWA-01**
- Given: `frontend/public/manifest.json` exists
- When: the page HTML is inspected
- Then: a `<link rel="manifest" href="/manifest.json">` tag is present in `<head>`; `manifest.json` contains `name: "每日市場新聞"`, `short_name: "市場新聞"`, `start_url: "/"`, `scope: "/"`, `display: "minimal-ui"`, `theme_color: "#1d1d1f"`

**AC-MN005-PWA-02**
- Given: `frontend/public/sw.js` exists
- When: the page is loaded in a browser context
- Then: a `<script>` in the client component calls `navigator.serviceWorker.register('/sw.js')` only when `'serviceWorker' in navigator`; the `sw.js` script handles `install`, `activate`, and `fetch` events; `npm run build` exits 0

**AC-MN005-PWA-03**
- Given: `frontend/public/icon-192.png` and `frontend/public/icon-512.png` exist
- When: the page HTML is inspected
- Then: `<link rel="apple-touch-icon" href="/icon-192.png">` is present in `<head>`; `<meta name="apple-mobile-web-app-capable" content="yes">` is present; `<meta name="apple-mobile-web-app-status-bar-style" content="black">` is present; `<meta name="apple-mobile-web-app-title" content="市場新聞">` is present

**AC-MN005-PWA-04**
- Given: all PWA assets are present
- When: `npm run build` is executed inside `frontend/`
- Then: exit code 0; no TypeScript errors; `npx tsc --noEmit` exits 0

### Phase 2 — GH Pages retirement

**AC-MN005-RETIRE-01**
- Given: MN-005 changes are merged to main
- When: `docs/index.html` is read
- Then: a `<meta http-equiv="refresh" content="0; url=https://market-news-sigma.vercel.app">` tag is present in `<head>` before any other content; GH Pages visitors are immediately redirected to the Vercel URL; the rest of the original `docs/index.html` content is preserved below the redirect tag

**AC-MN005-RETIRE-02**
- Given: MN-005 changes are merged to main
- When: `README.md` is read
- Then: Vercel URL (`https://market-news-sigma.vercel.app`) appears as the sole production URL; the text "Pre-release" is absent from the README; GH Pages URL appears with label "Legacy" and a note that it redirects to Vercel; no line describes GH Pages as the current production or primary URL

**AC-MN005-RETIRE-03**
- Given: MN-005 changes are merged to main
- When: `ssot/system-overview.md` §Tech Stack "Hosting" line is read
- Then: the line describes Vercel as "production" and GitHub Pages as "legacy (retired MN-005)"; the changelog section contains an entry for MN-005 with date 2026-05-09

## QA Early Consultation

**QA Early Consultation — PM proxy (2026-05-09, MN-005)**

**Challenge 1 — Service worker registration on Vercel edge CDN**
Service workers can only be registered from the same origin. On Vercel, `sw.js` must be served from `https://market-news-sigma.vercel.app/sw.js` (root path). If placed in `frontend/public/`, Next.js serves it at `/sw.js` — correct. Risk: registration scope. Default scope of `/sw.js` registered from root page is `/` — matches `start_url: "/"`. No scope mismatch.
Disposition: **No AC supplement needed** — covered by AC-MN005-PWA-02 (`register('/sw.js')` only when `'serviceWorker' in navigator`).

**Challenge 2 — PwaRegister component causes hydration mismatch**
`navigator.serviceWorker.register()` runs only in browser; if PwaRegister renders any DOM during SSR, it could cause hydration mismatch.
Disposition: **Supplemented to AC-MN005-PWA-02** — PwaRegister must be a Client Component with `useEffect`; the register call must be inside `useEffect(() => { ... }, [])` so it runs only after mount. And: component renders null (no DOM output) — registration is a side-effect only.

**Challenge 3 — meta-refresh redirect on GH Pages breaks existing bookmarks / direct JSON fetches**
`docs/index.html` gets the redirect tag. But `docs/news.json` and `docs/signals.json` are different URLs — they are not affected by HTML meta-refresh (which only applies to the HTML page itself). The Actions workflows that write to `docs/news.json` and `docs/signals.json` are unaffected. Direct fetches from `raw.githubusercontent.com` also unaffected.
Disposition: **No AC supplement needed** — redirect is HTML-only; JSON files are unchanged. Already clear in scope.

**Challenge 4 — icon files differ between docs/ and frontend/public/**
`docs/icon-192.png` exists. The `frontend/public/` copies should be byte-for-byte identical. If Engineer copies via `cp`, the files are identical. If Engineer re-generates, they could differ. Risk: iOS home screen icon mismatch between legacy and new.
Disposition: **Supplemented to AC-MN005-PWA-03** — And: `frontend/public/icon-192.png` and `frontend/public/icon-512.png` must be binary copies of `docs/icon-192.png` and `docs/icon-512.png` respectively (verified by `diff docs/icon-192.png frontend/public/icon-192.png` exit 0).

**Challenge 5 — manifest.json `start_url` / `scope` mismatch between old and new**
Legacy `docs/manifest.json` has `start_url: "/market-news/"` and `scope: "/market-news/"` (GH Pages path prefix). New `frontend/public/manifest.json` must use `start_url: "/"` and `scope: "/"` (Vercel root). If copied verbatim, the PWA would be broken on Vercel.
Disposition: **Supplemented to AC-MN005-PWA-01** — the `start_url` and `scope` fields must be `/` (not `/market-news/`). Already explicit in AC-MN005-PWA-01.

**QA Early Consultation summary:** 5 challenges raised, 2 supplemented to AC (C2: useEffect guard + null render; C4: binary copy diff check), 3 no-supplement-needed (C1, C3, C5 already explicit in AC).

## AC vs Sacred Cross-Check

MN-001/002/003/004 closed Sacred clauses: no visual Sacred conflicts. MN-004 AC-MN004-RETIRE-02 declares `docs/index.html` must NOT be deleted. MN-005 AC-MN005-RETIRE-01 adds a redirect tag to `docs/index.html` but does not delete it — not a conflict (modification of a file that must exist is allowed).
AC vs Sacred cross-check: no conflict.

## Binary-Criterion AC Scan

All Then/And clauses anchored to: file content text match, HTML tag presence, npm build exit code, tsc exit code, `diff` exit 0, README text assertion, ssot text assertion.
Binary-criterion AC scan: 11 clauses checked / 0 subjective.

## Shared Components Expected on This Route (/)

- `frontend/components/pwa/PwaRegister.tsx` — new client component for SW registration (no DOM output; side-effect only)

All other components unchanged from MN-004.

## Blocking Questions

None — all defaults applied per task brief.

## Release Status

_Pending._
