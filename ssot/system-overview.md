---
title: market-news — System Overview
type: reference
tags: [market-news, Architecture]
updated: 2026-05-09 (MN-006)
---

## Summary

Daily market news aggregator (PWA on Vercel) extended with a local CLI stock
signal analyzer. News fetching runs on a GitHub Actions cron schedule; signal analysis
runs locally on demand. The Next.js frontend on Vercel is production; GH Pages serves a legacy redirect.

## Tech Stack

- **News fetch:** Python 3, feedparser
- **Signal analysis:** Python 3, yfinance, pandas, Gemini API (via OpenAI-compat SDK), pydantic, python-dotenv
- **Optional social:** praw (PRAW Reddit API)
- **Optional notify:** requests (Telegram Bot API)
- **Frontend PWA (legacy):** Vanilla HTML/JS/CSS (static, no build step) — `docs/index.html`
- **Frontend (Next.js):** Next.js 14 App Router, React 18, TypeScript strict, Tailwind CSS
- **Hosting:** Vercel (`frontend/` — production, MN-004+); GitHub Pages (`docs/` directory — legacy, retired MN-005; serves meta-refresh redirect to Vercel)
- **CI:** GitHub Actions (cron every 30 min for news fetch)

## Directory Structure

```
market-news/
├── fetch_news.py          # RSS fetch → docs/news.json (8 feeds)
├── analyze_stock.py       # CLI entry: python3 analyze_stock.py [--output-json PATH] TSLA AAPL
├── models.py              # Pydantic signal models
├── synthesizer.py         # Gemini API synthesis (via OpenAI-compat endpoint)
├── notifier.py            # Console ANSI + optional Telegram
├── signals/
│   ├── news.py            # NewsSignal — fetch_all() + ticker filter
│   ├── technical.py       # TechnicalSignal — yfinance OHLCV + RSI/MACD/MA50
│   ├── fundamentals.py    # FundamentalsSignal — yfinance .info
│   └── social.py          # SocialSignal — PRAW Reddit (optional)
├── requirements.txt
├── worker/                # Cloudflare Worker (manual refresh trigger proxy)
├── frontend/              # Next.js app (production on Vercel — MN-004+)
│   ├── app/
│   │   ├── layout.tsx     # Root layout (PWA meta tags + PwaRegister — MN-005)
│   │   ├── page.tsx       # Home page — signals + news ISR
│   │   └── globals.css    # Tailwind directives
│   ├── components/
│   │   ├── pwa/
│   │   │   └── PwaRegister.tsx  # Client component — SW registration (MN-005)
│   │   ├── layout/        # TabNav, Toast, PageClient
│   │   ├── signals/       # SignalCard, SignalFilters, MarketOverview, SignalSort
│   │   └── news/          # NewsItem, NewsFilters
│   ├── lib/
│   │   ├── types.ts       # SignalResult, NewsItem interfaces
│   │   └── data.ts        # fetchSignals(), fetchNews() ISR helpers
│   ├── public/
│   │   ├── manifest.json  # Web App Manifest (MN-005)
│   │   ├── sw.js          # Service worker (MN-005)
│   │   ├── icon-192.png   # PWA icon (MN-005)
│   │   └── icon-512.png   # PWA icon (MN-005)
│   ├── package.json
│   ├── tsconfig.json      # TypeScript strict mode
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   └── .gitignore
├── vercel.json            # Vercel config: rootDirectory=frontend
├── digest.py              # Digest orchestrator — F&G + Fed RSS + geo + signals → Resend email (MN-006)
├── .github/workflows/
│   ├── update-news.yml    # cron every 30 min → docs/news.json
│   ├── update-signals.yml # cron 06:00 UTC daily → docs/signals.json (MN-002)
│   └── daily-digest.yml   # cron 00:00,12:00 UTC (08:00/20:00 TW) → Resend email (MN-006)
├── docs/                  # GitHub Pages (legacy — retired MN-005, serves redirect)
│   ├── index.html         # meta-refresh redirect to Vercel URL (MN-005)
│   ├── news.json          # updated by update-news.yml (data source for Next.js ISR)
│   ├── signals.json       # updated by update-signals.yml (data source for Next.js ISR)
│   ├── sw.js              # legacy SW (served by GH Pages only)
│   └── manifest.json      # legacy manifest (served by GH Pages only)
└── ssot/
    ├── system-overview.md  ← this file
    └── PRD.md              ← acceptance criteria
```

## Data Flow

```
GitHub Actions (cron 30 min) — update-news.yml
  └─ fetch_news.py → docs/news.json (committed to main)

GitHub Actions (cron 06:00 UTC daily) — update-signals.yml  [MN-002]
  └─ analyze_stock.py --output-json docs/signals.json <12 tickers>
       └─ synthesizer.py → SignalResult (Gemini API)
            └─ docs/signals.json (committed to main)

Vercel (Next.js ISR — MN-004 PRODUCTION)
  └─ frontend/app/page.tsx (Server Component, revalidate:300)
       ├─ fetchSignals() → raw.githubusercontent.com/mshmwr/market-news/main/docs/signals.json
       ├─ fetchNews()    → raw.githubusercontent.com/mshmwr/market-news/main/docs/news.json
       └─ → PageClient (ISR-cached; refreshes every 5 min without redeploy)

GitHub Pages (legacy — retired MN-005)
  └─ docs/index.html → meta-refresh redirect to https://market-news-sigma.vercel.app

GitHub Actions (cron 00:00,12:00 UTC) — daily-digest.yml  [MN-006]
  └─ digest.py
       ├─ fetch_news.fetch_all()         → geopolitical filter (Al Jazeera + BBC World)
       ├─ feedparser → Fed RSS           → FOMC filter (latest 2)
       ├─ requests → Alternative.me API  → Crypto Fear & Greed Index
       ├─ docs/signals.json              → top 5 by confidence (BUY-first)
       └─ resend.Emails.send()           → HTML email → rsp93050420@gmail.com

Local CLI
  └─ analyze_stock.py [--output-json PATH] <tickers>
       ├─ signals/news.py      → NewsSignal      (reuses fetch_all())
       ├─ signals/technical.py → TechnicalSignal (yfinance OHLCV)
       ├─ signals/fundamentals.py → FundamentalsSignal (yfinance .info)
       └─ signals/social.py    → SocialSignal    (PRAW, optional)
            └─ synthesizer.py  → SignalResult    (Gemini API)
                 └─ notifier.py → console + Telegram (optional)
```

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `NVIDIA_API_KEY` | Yes (for analysis) | NIM API auth via OpenAI-compat endpoint (`synthesizer.py`) |
| `RESEND_API_KEY` | Yes (for daily digest) | Resend email API auth (`daily-digest.yml`) |
| `TELEGRAM_BOT_TOKEN` | No | Telegram notification |
| `TELEGRAM_CHAT_ID` | No | Telegram notification target |
| `PRAW_CLIENT_ID` | No | Reddit social signal |
| `PRAW_CLIENT_SECRET` | No | Reddit social signal |
| `PRAW_USER_AGENT` | No | Reddit social signal |

## Known Architecture Debt

_None at project init._

## Changelog

**2026-05-09 — MN-006 — Daily Digest Email Scheduler: digest.py orchestrator + Resend + GitHub Actions cron (00:00/12:00 UTC = 08:00/20:00 TW); F&G + Fed RSS + geopolitical pulse + signals shortlist.**
Design doc: [docs/designs/MN-006-design.md](../docs/designs/MN-006-design.md)

**2026-05-09 — MN-005 — Port PWA to Next.js (manifest.json + sw.js + Apple meta tags + PwaRegister); retire GH Pages (meta-refresh redirect); update SSOT.**
Design doc: [docs/designs/MN-005-design.md](../docs/designs/MN-005-design.md)

**2026-05-09 — MN-004 — Port signals + news display to Next.js ISR; Vercel becomes production; GH Pages enters legacy/retiring state.**
Design doc: [docs/designs/MN-004-design.md](../docs/designs/MN-004-design.md)

**2026-05-09 — MN-003 — Next.js 14 App Router scaffold under frontend/; deploy target Vercel; placeholder shell; realtime stub reserved.**
Design doc: [docs/designs/MN-003-design.md](../docs/designs/MN-003-design.md)

**2026-05-03 — MN-002 — Signals web display: add --output-json flag, daily workflow, HTML Signals section; fix env var drift (ANTHROPIC_API_KEY → GEMINI_API_KEY).**
Design doc: [docs/designs/MN-002-design.md](../docs/designs/MN-002-design.md)

- **2026-05-03** (MN-001 ticket open) — initial system-overview stub; MN-001 adds signal analysis layer.
