---
title: market-news — System Overview
type: reference
tags: [market-news, Architecture]
updated: 2026-05-09 (MN-003)
---

## Summary

Daily market news aggregator (PWA on GitHub Pages) extended with a local CLI stock
signal analyzer. News fetching runs on a GitHub Actions cron schedule; signal analysis
runs locally on demand.

## Tech Stack

- **News fetch:** Python 3, feedparser
- **Signal analysis:** Python 3, yfinance, pandas, Gemini API (via OpenAI-compat SDK), pydantic, python-dotenv
- **Optional social:** praw (PRAW Reddit API)
- **Optional notify:** requests (Telegram Bot API)
- **Frontend PWA (legacy):** Vanilla HTML/JS/CSS (static, no build step) — `docs/index.html`
- **Frontend (Next.js):** Next.js 14 App Router, React 18, TypeScript strict, Tailwind CSS
- **Hosting:** GitHub Pages (`docs/` directory — current production); Vercel (`frontend/` — pre-release)
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
├── frontend/              # Next.js app (MN-003 scaffold — pre-release on Vercel)
│   ├── app/
│   │   ├── layout.tsx     # Root layout
│   │   ├── page.tsx       # Home page (placeholder shell)
│   │   └── globals.css    # Tailwind directives
│   ├── components/
│   │   └── realtime/
│   │       └── types.ts   # RealtimePrice interface stub
│   ├── package.json
│   ├── tsconfig.json      # TypeScript strict mode
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   └── .gitignore
├── vercel.json            # Vercel config: rootDirectory=frontend
├── .github/workflows/
│   ├── update-news.yml    # cron every 30 min → docs/news.json
│   └── update-signals.yml # cron 06:00 UTC daily → docs/signals.json (MN-002)
├── docs/                  # GitHub Pages PWA (current production)
│   ├── index.html
│   ├── news.json          # updated by update-news.yml
│   ├── signals.json       # updated by update-signals.yml (MN-002)
│   ├── sw.js
│   └── manifest.json
└── ssot/
    ├── system-overview.md  ← this file
    └── PRD.md              ← acceptance criteria
```

## Data Flow

```
GitHub Actions (cron 30 min) — update-news.yml
  └─ fetch_news.py → docs/news.json → GitHub Pages PWA (current production)

GitHub Actions (cron 06:00 UTC daily) — update-signals.yml  [MN-002]
  └─ analyze_stock.py --output-json docs/signals.json <12 tickers>
       └─ synthesizer.py → SignalResult (Gemini API)
            └─ docs/signals.json → GitHub Pages PWA (Signals section)

Vercel (Next.js SSR/ISR — MN-003 scaffold)
  └─ frontend/app/page.tsx → placeholder shell (no data wiring; MN-004 will add signals fetch)

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
| `GEMINI_API_KEY` | Yes (for analysis) | Gemini API auth via OpenAI-compat endpoint (`synthesizer.py`) |
| `TELEGRAM_BOT_TOKEN` | No | Telegram notification |
| `TELEGRAM_CHAT_ID` | No | Telegram notification target |
| `PRAW_CLIENT_ID` | No | Reddit social signal |
| `PRAW_CLIENT_SECRET` | No | Reddit social signal |
| `PRAW_USER_AGENT` | No | Reddit social signal |

## Known Architecture Debt

_None at project init._

## Changelog

**2026-05-09 — MN-003 — Next.js 14 App Router scaffold under frontend/; deploy target Vercel; placeholder shell; realtime stub reserved.**
Design doc: [docs/designs/MN-003-design.md](../docs/designs/MN-003-design.md)

**2026-05-03 — MN-002 — Signals web display: add --output-json flag, daily workflow, HTML Signals section; fix env var drift (ANTHROPIC_API_KEY → GEMINI_API_KEY).**
Design doc: [docs/designs/MN-002-design.md](../docs/designs/MN-002-design.md)

- **2026-05-03** (MN-001 ticket open) — initial system-overview stub; MN-001 adds signal analysis layer.
