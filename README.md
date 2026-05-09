# Market News

Daily news aggregator for Taiwan stocks, US stocks, crypto, and macro markets.

## Live URLs

**Production:** https://market-news-sigma.vercel.app
_(Next.js + ISR — news + signals display; auto-refreshes every 5 min from GitHub-Actions-updated JSON)_

**Legacy (retired — redirects to Vercel):** https://mshmwr.github.io/market-news/
_(GitHub Pages — now serves a meta-refresh redirect to the Vercel URL; `docs/news.json` and `docs/signals.json` continue to be updated by GitHub Actions as the data source for the Next.js ISR fetch)_

## Features

- **Category filter** — Taiwan stocks / US stocks / Crypto / Macro
- **Manual refresh** — triggers a live RSS fetch via GitHub Actions; button spins until new data arrives
- **PWA** — installable on mobile home screen (`manifest.json` + Service Worker)
- **Translate** — opens the page through Google Translate proxy

## Architecture

```
GitHub Actions (cron every 30 min)
  └─ fetch_news.py  →  docs/news.json  →  GitHub Pages
                                              └─ index.html reads news.json
```

The frontend is a static HTML page. All data fetching happens server-side in GitHub Actions.

## News Sources

| Source | Category |
|--------|----------|
| 經濟日報 | 台股 |
| ETtoday 財經 | 台股 |
| CNBC | 美股 |
| MarketWatch | 美股 |
| CoinDesk | 加密貨幣 |
| CoinTelegraph | 加密貨幣 |
| Al Jazeera | 宏觀 |
| BBC World | 宏觀 |

## Manual Refresh Setup (one-time)

The 🔄 button triggers a live fetch when the last update is over 1 hour old. It requires a GitHub Fine-grained PAT with `Actions: Read and write` permission on this repo.

1. Go to [GitHub → Settings → Fine-grained tokens](https://github.com/settings/personal-access-tokens/new)
2. Repository access: `mshmwr/market-news`
3. Permissions → **Actions: Read and write**
4. Generate and copy the token
5. Click 🔄 on the page — paste the token in the modal that appears

The token is stored in `localStorage` and reused on subsequent refreshes. A 401/403 response clears it automatically.

## Daily Digest

Twice-daily HTML email (08:00 and 20:00 Taiwan time) covering:

- **TW + US Stock Shortlist** — top 5 signals from the latest `docs/signals.json` (confidence-ranked, BUY-first)
- **Fear & Greed Index** — Crypto F&G via Alternative.me free API
- **Geopolitical Risk Pulse** — Al Jazeera + BBC World RSS filtered for risk keywords
- **FOMC / Fed Updates** — Federal Reserve press release RSS, FOMC entries only

Sent via [Resend](https://resend.com) (free tier, 3000 emails/month — we use 60/month).

### Secret setup (one-time)

The workflow requires a Resend API key stored as a GitHub Actions secret:

```bash
gh secret set RESEND_API_KEY --repo mshmwr/market-news
```

Or via GitHub web UI: **Settings → Secrets and variables → Actions → New repository secret** — Name: `RESEND_API_KEY`.

Get your API key at https://resend.com/api-keys (free account).

### Smoke-test (before secret is added)

Trigger the workflow manually from the Actions tab. It will succeed through the fetcher steps and fail only at the email-send step with a clear `RESEND_API_KEY not set` error — this confirms the pipeline is healthy.

```bash
gh workflow run daily-digest.yml --repo mshmwr/market-news
```

---

## Local Development

### Python worker (news + signals)

```bash
pip install feedparser
python fetch_news.py > docs/news.json
# serve docs/ with any static server, e.g.:
python -m http.server 8000 --directory docs
```

### Next.js frontend (production)

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000
```

## Deployment

### Vercel (production — MN-004+)

Project linked: `mshmwrs-projects/market-news` (root directory: `frontend`). Pushes to `main` trigger automatic Vercel deploys. The Next.js page uses ISR `revalidate: 300` to pick up JSON updates from GitHub Actions without a redeploy.

```bash
cd frontend
vercel --prod  # manual redeploy if needed
```

### GitHub Pages (legacy — retired MN-005)

GitHub Pages continues to serve the `docs/` directory. `docs/index.html` now contains a meta-refresh redirect to the Vercel URL. The GitHub Actions cron workflows continue to update `docs/news.json` and `docs/signals.json` — these files remain the data source for the Next.js ISR fetch via `raw.githubusercontent.com`.
