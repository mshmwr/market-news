# MN-005 Design Doc — PWA Port to Next.js + GH Pages Retirement

**Ticket:** MN-005  
**Phases:** 1 (PWA assets in Next.js) → 2 (GH Pages retirement)  
**Architect:** Senior Architect  
**Date:** 2026-05-09  
**Status:** Ready for Engineer

---

## 0 Pre-Implementation Design Challenge Sheet

| Dimension | Challenge | Verdict |
|-----------|-----------|---------|
| Interface contracts | `PwaRegister` must be a Client Component (`'use client'`) with `useEffect`; no props required; no DOM output; pure side-effect | Accept — Client Component renders `null`; SW registration is fire-and-forget inside `useEffect` |
| Refactorability | If SW strategy changes (e.g., Workbox), only `frontend/public/sw.js` and the register call in `PwaRegister.tsx` need changing | Accept — SW logic is isolated to two files; layout.tsx only imports `<PwaRegister />` |
| Test seam | SW registration is async and side-effect only; Playwright cannot easily assert SW state in unit mode; build + tsc are the primary gates | Accept — AC-MN005-PWA-02 tests build exit code and source-level `useEffect` guard; E2E SW registration left to browser DevTools / manual verify |
| Blast radius | Changes to `layout.tsx` affect all pages. Adding `<link rel="manifest">` and Apple meta tags are non-breaking additive changes. `<PwaRegister />` renders null — no visual regression. | Accept — additive-only layout changes; zero visual delta |
| Spec vs codebase drift | `docs/manifest.json` has wrong `start_url`/`scope` for Vercel; new `frontend/public/manifest.json` must use `/` root paths | Accept — new file; no copy-paste risk; AC-MN005-PWA-01 explicitly calls out start_url `/` and scope `/` |

All 5 dimensions: accept.

---

## 1 Technical Decisions

### Decision 1: Service Worker implementation approach

**Option A (next-pwa package):** Install `next-pwa`; configure in `next.config.ts`; auto-generates SW.  
**Trade-off:** Adds a build dependency; generates a precache manifest automatically; more config overhead for a simple network-first + cache-first strategy.

**Option B (plain public/sw.js — CHOSEN):** Copy `docs/sw.js` verbatim (already tested in production); register via a `PwaRegister` Client Component.  
**When to use:** When the existing SW logic is minimal, already tested, and no build-step integration is required.  
**Trade-off:** Manual SW; no auto-precaching of Next.js chunks. For a news aggregator where content is always fetched fresh, network-first is the right strategy anyway.  
**Recommendation:** Plain `public/sw.js` — avoids next-pwa dependency; zero config landmines; existing SW code is already battle-tested on GH Pages.

**Chosen:** Option B. Rationale: Simpler; fewer dependencies; existing SW is already correct for this app's network-first data pattern.

---

### Decision 2: manifest.json approach

**Approach:** New file at `frontend/public/manifest.json` with updated `start_url: "/"` and `scope: "/"` for Vercel root deployment. All other fields ported from `docs/manifest.json` (name, short_name, description, display, background_color, theme_color, lang, icons).

Icons reference `/icon-192.png` and `/icon-512.png` — served from `frontend/public/` by Next.js at root.

---

### Decision 3: Icon file strategy

Copy `docs/icon-192.png` → `frontend/public/icon-192.png` and `docs/icon-512.png` → `frontend/public/icon-512.png` using binary copy (`cp`). The `docs/` originals remain for GH Pages legacy serve.

---

### Decision 4: GH Pages redirect

Add `<meta http-equiv="refresh" content="0; url=https://market-news-sigma.vercel.app">` as the very first tag inside `<head>` in `docs/index.html`. This is the simplest redirect with no JavaScript dependency. The rest of the file is preserved unchanged so GH Pages users who bookmark sub-anchors still get a valid redirect.

---

## 2 File Change List

### New files

| File | Description |
|------|-------------|
| `frontend/public/manifest.json` | Web App Manifest for Vercel deployment |
| `frontend/public/sw.js` | Service worker (copy of docs/sw.js with updated CACHE name) |
| `frontend/public/icon-192.png` | Binary copy of docs/icon-192.png |
| `frontend/public/icon-512.png` | Binary copy of docs/icon-512.png |
| `frontend/components/pwa/PwaRegister.tsx` | Client Component: registers SW in useEffect, renders null |

### Modified files

| File | Change |
|------|--------|
| `frontend/app/layout.tsx` | Add manifest link, Apple meta tags, import PwaRegister |
| `docs/index.html` | Add meta-refresh redirect at top of `<head>` |
| `README.md` | Remove "Pre-release" label; Vercel = Production; GH Pages = Legacy (redirects to Vercel) |
| `ssot/system-overview.md` | Update Hosting description + Changelog |
| `ssot/PRD.md` | Add MN-005 to §Active Tickets |

---

## 3 Component Spec

### `frontend/components/pwa/PwaRegister.tsx`

```typescript
'use client';

import { useEffect } from 'react';

export default function PwaRegister() {
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(() => {
        // SW registration failure is non-fatal — app works without it
      });
    }
  }, []);

  return null;
}
```

### `frontend/app/layout.tsx` additions

```typescript
import PwaRegister from '@/components/pwa/PwaRegister';

// In <head>:
<link rel="manifest" href="/manifest.json" />
<link rel="apple-touch-icon" href="/icon-192.png" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="black" />
<meta name="apple-mobile-web-app-title" content="市場新聞" />

// In <body> (before {children}):
<PwaRegister />
```

---

## 4 Route Impact Table

| Route | Change | Visual Impact |
|-------|--------|--------------|
| `/` (Next.js home) | Additive meta tags + PwaRegister (null render) | None |
| All Next.js routes | manifest + apple tags in root layout | None (head-only changes) |
| GH Pages `/market-news/` | meta-refresh added to docs/index.html | Redirect (not visual) |

---

## 5 Shared Component Blast Radius

`PwaRegister` is imported only in `frontend/app/layout.tsx`. It renders null. No existing component is modified. No risk of blast to other components.
