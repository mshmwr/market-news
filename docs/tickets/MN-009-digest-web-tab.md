---
id: MN-009
title: Daily Digest — surface as 📨 電子報 tab on the website
status: in-progress
created: 2026-05-09
type: feature
priority: med
size: S
visual-delta: yes
content-delta: yes
qa-early-consultation: skipped — additive new tab; failure mode = empty placeholder; no auth/routing change
supersedes: none (extends MN-004 web shell + MN-008 digest pipeline)
---

## Why

Email digest (MN-008) renders only in inbox. Same content is also useful as a third tab on the website so the user (and future visitors) can browse it without hunting the email — and so the cron failure mode (Resend rejection / NIM down) is less invisible.

## Scope

### Backend / data

- `digest.py` — always write the rendered HTML to `docs/digest-latest.html` before email send (independent of `--preview` flag). Email send still gates on success of compose.
- `.github/workflows/daily-digest.yml` — after `python digest.py`, commit + push `docs/digest-latest.html` so the frontend can fetch it via `raw.githubusercontent.com` like `signals.json` / `news.json`.

### Frontend

- `frontend/lib/data.ts` — add `fetchDigest()` returning `string | null` from the same raw URL pattern.
- `frontend/lib/types.ts` — no schema change (raw HTML string).
- `frontend/app/page.tsx` — fetch digest HTML in parallel with signals + news, pass to `PageClient`.
- `frontend/components/layout/PageClient.tsx` — third tab `digest` rendering the HTML inside a max-width container.
- `frontend/components/layout/TabNav.tsx` — add `📨 電子報` tab (third option).

### Files touched

- `digest.py`
- `.github/workflows/daily-digest.yml`
- `docs/digest-latest.html` (committed by cron, gitignored locally is fine)
- `frontend/lib/data.ts`
- `frontend/app/page.tsx`
- `frontend/components/layout/PageClient.tsx`
- `frontend/components/layout/TabNav.tsx`
- `docs/tickets/MN-009-*.md`

## Acceptance Criteria

1. **HTML persisted.** Every successful `python digest.py` run leaves an updated `docs/digest-latest.html` in the repo.
2. **Cron commits the file.** Daily Digest workflow includes the file in its post-run commit so it lands on `main`.
3. **Tab visible.** Frontend renders three tabs: `📰 新聞`, `📈 股票訊號`, `📨 電子報`.
4. **Newsletter renders.** Selecting `📨 電子報` shows the same content as the email — six sections with bilingual chrome and rationale translations.
5. **Graceful empty state.** If `digest-latest.html` is missing or fetch fails, the tab shows a "尚未產生 / Not generated yet" placeholder; no crash.
6. **Sanitisation.** All news titles already escape via `_html_lib.escape` in `digest.py`; React `dangerouslySetInnerHTML` consumes the trusted-by-construction HTML safely.
7. **No new env vars or secrets.**

## Out of Scope

- Per-day archive of past newsletters (single latest only).
- Subscription / RSS feed surface.
- Dark-mode styling for the embedded HTML (inherits inline styles from email layout).
