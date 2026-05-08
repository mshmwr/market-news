# Market News

Daily news aggregator for Taiwan stocks, US stocks, crypto, and macro markets.

## Live URLs

**Production (Current):** https://mshmwr.github.io/market-news/
_(GitHub Pages — static HTML with news + signals display)_

**Pre-release (Next.js):** https://market-news-mshmwr.vercel.app
_(Under development — signals display not yet ported from the production version; see MN-004)_

**Retirement gate:** The pre-release Vercel URL becomes production after MN-004 achieves feature parity (signals display ported to Next.js). The GitHub Pages version will redirect to Vercel at that time.

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

## Local Development

```bash
pip install feedparser
python fetch_news.py > docs/news.json
# serve docs/ with any static server, e.g.:
python -m http.server 8000 --directory docs
```

## Deployment

Push to `main`. GitHub Actions runs `fetch_news.py`, commits `docs/news.json` if changed, and GitHub Pages serves the `docs/` directory automatically.
