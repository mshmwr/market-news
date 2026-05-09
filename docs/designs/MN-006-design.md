# MN-006 Design Doc — Daily Digest Email Scheduler

**Ticket:** MN-006  
**Phases:** 1 (digest.py + workflow) → 2 (docs)  
**Architect:** Senior Architect  
**Date:** 2026-05-09  
**Status:** Ready for Engineer

---

## 0 Pre-Implementation Design Challenge Sheet

| Dimension | Challenge | Verdict |
|-----------|-----------|---------|
| Interface contracts | `digest.py` imports `fetch_news.fetch_all()` and reads `docs/signals.json` directly — no function signature changes to existing files | Accept — imports are read-only; no modification to `fetch_news.py` or `analyze_stock.py` |
| Refactorability | If email provider changes from Resend to SMTP, only `_send_email()` function in `digest.py` needs changing; HTML composition is provider-agnostic | Accept — `_send_email()` is isolated; composition functions return plain strings |
| Test seam | `RESEND_API_KEY` missing at test time is a real scenario; script must detect and exit non-zero rather than crash at import | Accept — AC-MN006-DIGEST-06 and WF-02 cover this; `resend` SDK raises on missing key at send time, not import time |
| Blast radius | New `digest.py` and new workflow file; zero changes to existing `.py` files or workflows | Accept — additive only; no regression surface |
| Spec vs codebase drift | `docs/signals.json` schema: `{"generated_at": "...", "signals": [...]}` where each signal has `ticker`, `signal`, `confidence`, `rationale`; confirmed from `models.SignalResult` | Accept — `digest.py` reads the JSON with these exact keys; graceful degradation if file absent |

All 5 dimensions: accept.

---

## 1 Technical Decisions

### Decision 1: Email SDK — resend Python package

**Chosen:** `resend` PyPI package (official Resend Python SDK).  
**Interface:** `resend.Emails.send({"from": ..., "to": [...], "subject": ..., "html": ...})` — returns a dict with `"id"` on success; raises `resend.exceptions.ResendError` on 4xx/5xx.  
**Reason:** Official SDK; single-line send; explicit error raising makes non-zero exit straightforward.

### Decision 2: signals.json path — relative to cwd

`digest.py` reads `docs/signals.json` relative to the process working directory.  
In the workflow, the job `cd`s to repo root (default checkout), so `docs/signals.json` resolves correctly.  
No path injection needed.

### Decision 3: F&G — Alternative.me only (no CNN scrape)

CNN equity F&G requires JavaScript rendering; scraping it reliably is out of scope.  
`digest.py` calls only `https://api.alternative.me/fng/?limit=1` and degrades gracefully.  
Label added: "Crypto Fear & Greed Index (Alternative.me)".

### Decision 4: HTML format — inline-CSS table layout

Max 600px width; no external CSS; Gmail-safe inline styles.  
Section headers as `<h2>` with `color:#1a1a2e; border-bottom:2px solid #e0e0e0`.  
Signal table: `<table>` with inline `style` on each `<td>`.  
BUY = green `#27ae60`, SELL = red `#e74c3c`, HOLD = gray `#7f8c8d`.

---

## 2 File Change List

| File | Action | Notes |
|------|--------|-------|
| `digest.py` | Create | Orchestrator; ~150 LOC |
| `requirements.txt` | Edit | Add `resend>=2.0` |
| `.github/workflows/daily-digest.yml` | Create | Cron 0 0,12 * * * |
| `README.md` | Edit | Add "Daily Digest" section |
| `ssot/PRD.md` | Edit | Move MN-005 to Closed; add MN-006 as Active |
| `ssot/system-overview.md` | Edit | Add digest data flow + env var row |

---

## 3 `digest.py` Module Structure

```
digest.py
├── _fetch_fg()            → dict | None          # Alternative.me F&G
├── _fetch_fomc()          → list[dict]            # Fed RSS, filtered
├── _fetch_geopolitical()  → list[dict]            # fetch_news.fetch_all() filtered
├── _load_signals()        → list[dict]            # reads docs/signals.json
├── _top_signals()         → list[dict]            # sort by confidence, BUY first, top 5
├── _render_html()         → str                   # composes full HTML
├── _send_email(html: str) → None                  # calls resend SDK; raises on error
└── main()                 → int (exit code)       # orchestrates; returns 0 or 1
```

---

## 4 Environment Variables Required

| Variable | Required | Source |
|----------|----------|--------|
| `RESEND_API_KEY` | Yes | GitHub secret `RESEND_API_KEY` |
| `NVIDIA_API_KEY` | No (digest.py does not call analyzer) | Inherited from workflow env for potential future use |

Note: `digest.py` does NOT call `synthesizer.py` or any LLM. It reads the pre-computed `docs/signals.json`. `NVIDIA_API_KEY` is included in the workflow env block for consistency with `update-signals.yml` but is not used by `digest.py`.

---

## 5 Workflow YAML Structure

```yaml
name: Daily Digest Email
on:
  schedule:
    - cron: '0 0,12 * * *'
  workflow_dispatch: {}
jobs:
  digest:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    env:
      RESEND_API_KEY: ${{ secrets.RESEND_API_KEY }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Send daily digest
        run: python digest.py
```

Key choices:
- `permissions: contents: read` — workflow only reads repo files, no push
- `workflow_dispatch: {}` — allows manual trigger (smoke-test gate, AC-MN006-WF-02)
- No `concurrency` block — duplicate-send risk is accepted Known Gap per QA consultation

---

## 6 Alternative.me F&G Response Shape

```json
{
  "name": "Fear and Greed Index",
  "data": [
    {
      "value": "68",
      "value_classification": "Greed",
      "timestamp": "1715212800",
      "time_until_update": "12345"
    }
  ]
}
```

`digest.py` reads `data[0]["value"]` (string, cast to int) and `data[0]["value_classification"]`.

---

## 7 Federal Reserve RSS Parse Logic

Feed URL: `https://www.federalreserve.gov/feeds/press_all.xml`  
Parsed with `feedparser`. Filter: `entry.title` contains (case-insensitive) `"fomc"` or `"federal open market committee"`.  
Fields used: `entry.title`, `entry.link`, `entry.published`.  
Maximum 2 entries shown (most recent first, feedparser returns newest-first by default).

---

## 8 Resend Payload Schema

```python
resend.Emails.send({
    "from": "onboarding@resend.dev",
    "to": ["rsp93050420@gmail.com"],
    "subject": f"Market Digest — {timestamp_tw}",
    "html": html_body,
})
```

`timestamp_tw`: formatted as `YYYY-MM-DD HH:MM TW` using `datetime.now(ZoneInfo("Asia/Taipei"))`.  
Fallback if `zoneinfo` unavailable (Python < 3.9): use UTC+8 manual offset.

---

## 9 HTML Template Structure

```html
<html>
<body style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:16px;color:#1a1a2e;">
  <h1>Market Digest — {timestamp_tw}</h1>

  <h2>TW + US Stock Shortlist</h2>
  <table>...</table>   <!-- top 5 signals -->

  <h2>Fear & Greed Index</h2>
  <p>Crypto F&G: <strong>{value}</strong> — {classification}</p>

  <h2>Geopolitical Risk Pulse</h2>
  <ul>
    <li><a href="{link}">{title}</a> — {source}</li>
    ...
  </ul>

  <h2>FOMC / Fed Updates</h2>
  <ul>
    <li><a href="{link}">{title}</a> ({published})</li>
    ...
  </ul>

  <hr/>
  <p style="font-size:11px;color:#aaa;">Generated by market-news digest.py — {timestamp_utc} UTC</p>
</body>
</html>
```
