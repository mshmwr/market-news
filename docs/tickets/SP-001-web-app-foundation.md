---
id: SP-001
title: StockPulse Web App — Foundation
status: open
created: 2026-05-03
type: feature
priority: high
size: L
visual-delta: none
content-delta: yes
design-locked: N/A
qa-early-consultation: "✗"
worktree: TBD
branch: SP-001-web-app-foundation
---

## Summary

Extend `market-news` with a FastAPI backend + Supabase (auth + PostgreSQL) to transform the existing signal CLI into a multi-user web application. Users can create accounts, manage a ticker watchlist, and view personalized BUY/HOLD/SELL signal cards via a React + Vite frontend.

This ticket covers the **foundation layer only** — no alerts, no paywall, no B2B API.

## PRD Reference

- Product: [StockPulse PRD v0.1](../../Life/black-cat-lesson-week01-stockpulse-prd.md) (Diary notes repo)
- Schema: [Database Schema](../../Life/black-cat-lesson-week01-stockpulse-schema.md) (Diary notes repo)
- Features covered: F-001 (Watchlist), F-002 (Signal Card), F-005 (User Auth)

## Scope

### New files
```
backend/
    main.py              # FastAPI app entry point
    db.py                # Supabase client + connection
    routers/
        auth.py          # POST /api/v1/auth/signup, /login (proxy to Supabase Auth)
        watchlist.py     # GET/POST/DELETE /api/v1/watchlist
        signals.py       # GET /api/v1/signals
    migrations/
        001_initial.sql  # Full schema from DB Schema doc
requirements.txt         # + fastapi, uvicorn, supabase-py
```

### Modified files
```
analyze_stock.py         # Add --output-db flag → INSERT into signals table
frontend/                # Scaffold React + Vite (replaces docs/index.html PWA)
    src/
        App.tsx
        pages/Dashboard.tsx   # Watchlist + Signal cards
        components/SignalCard.tsx
```

### Out of scope
- Push alerts (SP-002)
- Freemium paywall / Stripe (SP-003)
- B2B API keys (SP-004)
- Mobile app

## Phases

### Phase 1 — Backend + DB
1. Scaffold `backend/` with FastAPI
2. Connect Supabase (env: `SUPABASE_URL`, `SUPABASE_KEY`)
3. Run `migrations/001_initial.sql` to create 6 tables
4. Implement watchlist CRUD endpoints
5. Implement signals read endpoint (latest signal per watchlist ticker)

### Phase 2 — analyze_stock.py DB output
6. Add `--output-db` flag: after successful synthesis, INSERT into `signals` table
7. Keep `--output-json` path unchanged (backward compatible with GitHub Pages PWA)

### Phase 3 — React frontend
8. Scaffold React + Vite in `frontend/`
9. Auth flow: signup / login via Supabase Auth
10. Dashboard: watchlist management + signal cards (reuse MN-002 CSS tokens)
11. Wire to backend API

## Acceptance Criteria

*(To be completed by Architect before Engineer release)*

### Phase 1 — Backend skeleton

**AC-SP001-BACKEND-01**
- Given: `uvicorn backend.main:app` is run
- When: `GET /api/v1/health` is called
- Then: returns `{"status": "ok"}` with HTTP 200

**AC-SP001-WATCHLIST-01**
- Given: authenticated user sends `POST /api/v1/watchlist {"ticker": "AAPL"}`
- When: ticker is not already in the user's watchlist
- Then: row is inserted into `watchlist_items`; response is `{"ticker": "AAPL", "added_at": "<ISO8601>"}`

**AC-SP001-WATCHLIST-02**
- Given: authenticated user sends `GET /api/v1/watchlist`
- When: user has 3 watchlist items
- Then: response is array of 3 `{ticker, added_at}` objects

**AC-SP001-SIGNALS-01**
- Given: `signals` table has at least one row for `AAPL`
- When: authenticated user sends `GET /api/v1/signals`
- Then: returns latest signal per ticker in user's watchlist; each row has `{ticker, signal, confidence, rationale, generated_at}`

### Phase 2 — analyze_stock.py DB output

**AC-SP001-DB-01**
- Given: `analyze_stock.py --output-db AAPL` is run with valid `SUPABASE_URL` + `SUPABASE_KEY` in env
- When: synthesis succeeds
- Then: one row inserted into `signals` table with correct `{ticker, signal, confidence, rationale, generated_at}`

**AC-SP001-DB-02**
- Given: `analyze_stock.py` is run WITHOUT `--output-db`
- When: synthesis completes
- Then: no DB writes occur; existing behavior unchanged

### Phase 3 — React frontend

**AC-SP001-FE-01**
- Given: user visits `/` while unauthenticated
- When: page loads
- Then: login/signup form is displayed

**AC-SP001-FE-02**
- Given: authenticated user has 3 watchlist tickers with signals
- When: Dashboard loads
- Then: 3 SignalCard components render with correct signal color (BUY=green, HOLD=yellow, SELL=red)

## Blocking Questions

**BQ-SP001-01:** Supabase free tier limit is 500MB DB + 50k monthly active users. Sufficient for MVP?
→ Ruling: ✅ Yes — MVP traffic will be well under both limits.

**BQ-SP001-02:** Keep GitHub Pages PWA (`docs/index.html`) alongside new React frontend, or replace?
→ Ruling: Keep both initially. `--output-json` still writes `docs/signals.json` for PWA; React frontend is served separately (Vercel). Replace PWA once React frontend is stable.

**BQ-SP001-03:** Authentication provider — Supabase Auth (built-in) or separate (Auth0)?
→ Ruling: Supabase Auth — already using Supabase for DB; one less service to configure.

## Deferred Features

**DF-SP001-01: User-provided Gemini API key**
- Phase 3 User Settings page: authenticated user can enter their own `GEMINI_API_KEY`
- Backend stores key (encrypted) per user; signal generation uses that key instead of server-side env var
- Rationale: lets each user bring their own quota; avoids single shared key bottleneck at scale
