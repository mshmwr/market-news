"""Daily digest email — composes and sends a twice-daily HTML market summary.

Sections (each gets an LLM-generated narrative):
  1. TW + US Stock Shortlist  (reads docs/signals.json)
  2. Fear & Greed Index       (Alternative.me free API)
  3. Geopolitical Risk Pulse  (Al Jazeera + BBC World RSS via fetch_news)
  4. FOMC / Fed Updates       (Federal Reserve RSS)

Narratives are produced via NVIDIA NIM (MiniMax M2.7); on failure the section
falls back to raw list rendering only.

Usage:
  python digest.py

Required env vars:
  RESEND_API_KEY   — Resend email API key
  NVIDIA_API_KEY   — NVIDIA NIM API key for narrative generation (optional;
                     missing → narrative skipped, raw lists still render)

Exit codes:
  0  success (email sent)
  1  email send failed (Resend error)
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone, timedelta

import html as _html_lib
import feedparser
import requests
import resend

from fetch_news import fetch_all as fetch_all_news


def _esc(text: str) -> str:
    """HTML-escape a string for safe inline rendering."""
    return _html_lib.escape(str(text))

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RECIPIENT = "mshmwr20@gmail.com"
SENDER = "onboarding@resend.dev"
SIGNALS_PATH = os.path.join(os.path.dirname(__file__), "docs", "signals.json")

FG_URL = "https://api.alternative.me/fng/?limit=1"
FED_RSS_URL = "https://www.federalreserve.gov/feeds/press_all.xml"

GEOPOLITICAL_SOURCES = {"Al Jazeera", "BBC World"}
GEOPOLITICAL_KEYWORDS = {"war", "sanctions", "tariff", "conflict", "geopolitic", "military"}

NIM_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NIM_MODEL = "minimaxai/minimax-m2.7"
NIM_TIMEOUT = 180

# Taiwan is UTC+8
TW_OFFSET = timezone(timedelta(hours=8))


# ---------------------------------------------------------------------------
# LLM narrative (NVIDIA NIM)
# ---------------------------------------------------------------------------

def _call_nim(prompt: str) -> str:
    """Call NVIDIA NIM with prompt; return narrative text. Empty string on any failure."""
    api_key = os.environ.get("NVIDIA_API_KEY", "")
    if not api_key:
        return ""
    try:
        resp = requests.post(
            NIM_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": NIM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4096,
            },
            timeout=NIM_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"].get("content", "").strip()
    except Exception as exc:
        print(f"[digest] NIM call failed: {exc}", file=sys.stderr)
        return ""


def _narrative_fg(fg: dict | None) -> str:
    if not fg:
        return ""
    prompt = (
        f"以下是今日加密貨幣 Fear & Greed Index：數值 {fg['value']}（{fg['classification']}）。"
        "請用繁體中文寫一段約 80–120 字的解讀，說明這個數值代表的市場情緒、"
        "對風險資產（股票、加密貨幣）的潛在含意，以及短線交易者可注意的方向。"
        "直接給出段落文字，不要前綴標題或編號。"
    )
    return _call_nim(prompt)


def _narrative_fomc(entries: list[dict]) -> str:
    if not entries:
        return ""
    bullets = "\n".join(f"- {e['title']} ({e.get('published','')})" for e in entries)
    prompt = (
        "以下是最近的 FOMC / Fed 公告標題：\n"
        f"{bullets}\n\n"
        "請用繁體中文寫一段約 100–150 字的解讀，說明這些公告對利率走向、"
        "美股與全球風險資產的可能影響。直接給出段落文字，不要編號標題。"
    )
    return _call_nim(prompt)


def _narrative_geo(items: list[dict]) -> str:
    if not items:
        return ""
    bullets = "\n".join(f"- {a['title']} ({a.get('source','')})" for a in items)
    prompt = (
        "以下是今日地緣政治風險新聞標題：\n"
        f"{bullets}\n\n"
        "請用繁體中文寫一段約 100–150 字的綜合解讀，歸納本批新聞的主要風險主題，"
        "以及對能源、原物料、避險資產（黃金、美元、美債）的潛在影響。"
        "直接給出段落文字，不要編號標題。"
    )
    return _call_nim(prompt)


def _narrative_stocks(top: list[dict]) -> str:
    if not top:
        return ""
    bullets = "\n".join(
        f"- {s.get('ticker','—')} ({s.get('name','—')}): {s.get('signal','—')} "
        f"conf={s.get('confidence','—')} | {s.get('rationale','')}"
        for s in top
    )
    prompt = (
        "以下是今日 Top 5 個股訊號（來自本系統 analyze_stock 多因子模型）：\n"
        f"{bullets}\n\n"
        "請用繁體中文寫一段約 120–180 字的觀察，說明本批清單反映的板塊或主題、"
        "整體偏多或偏空傾向、以及讀者可關注的後續催化劑。直接給出段落文字。"
    )
    return _call_nim(prompt)


# ---------------------------------------------------------------------------
# Data fetchers
# ---------------------------------------------------------------------------

def _fetch_fg() -> dict | None:
    """Fetch crypto Fear & Greed Index from Alternative.me. Returns None on failure."""
    try:
        resp = requests.get(FG_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        entry = data["data"][0]
        return {
            "value": int(entry["value"]),
            "classification": entry["value_classification"],
        }
    except Exception:
        return None


def _fetch_fomc() -> list[dict]:
    """Fetch Federal Reserve press releases RSS, return latest ≤2 FOMC entries."""
    try:
        feed = feedparser.parse(FED_RSS_URL)
        results = []
        for entry in feed.entries:
            title = entry.get("title", "")
            if "fomc" in title.lower() or "federal open market committee" in title.lower():
                results.append({
                    "title": title,
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                })
                if len(results) >= 2:
                    break
        return results
    except Exception:
        return []


def _fetch_geopolitical() -> list[dict]:
    """Return ≤5 geopolitical risk articles from Al Jazeera / BBC World."""
    try:
        articles = fetch_all_news()
    except Exception:
        return []

    hits = []
    for article in articles:
        if article.get("source") not in GEOPOLITICAL_SOURCES:
            continue
        text = f"{article.get('title', '')} {article.get('description', '')}".lower()
        if any(kw in text for kw in GEOPOLITICAL_KEYWORDS):
            hits.append({
                "title": article.get("title", "(no title)"),
                "link": article.get("link", ""),
                "source": article.get("source", ""),
            })
            if len(hits) >= 5:
                break
    return hits


def _load_signals() -> list[dict]:
    """Load docs/signals.json. Returns empty list if file absent or malformed."""
    try:
        with open(SIGNALS_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
        return data.get("signals", [])
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return []


def _top_signals(signals: list[dict], n: int = 5) -> list[dict]:
    """Return top-n signals: BUY first, then by confidence descending, ties by ticker alpha."""
    def sort_key(s: dict):
        signal_rank = 0 if s.get("signal") == "BUY" else 1
        confidence = -(s.get("confidence") or 0)
        return (signal_rank, confidence, s.get("ticker", ""))

    return sorted(signals, key=sort_key)[:n]


# ---------------------------------------------------------------------------
# HTML renderer
# ---------------------------------------------------------------------------

def _render_html(
    timestamp_tw: str,
    timestamp_utc: str,
    top_stocks: list[dict],
    fg: dict | None,
    geo: list[dict],
    fomc: list[dict],
    narratives: dict[str, str] | None = None,
) -> str:
    narratives = narratives or {}

    def _narr_block(key: str) -> str:
        text = (narratives.get(key) or "").strip()
        if not text:
            return ""
        return (
            '<p style="background:#f7f9fc;border-left:3px solid #2980b9;'
            'padding:8px 12px;margin:8px 0;color:#222;font-size:14px;'
            f'line-height:1.6;">{_esc(text)}</p>'
        )
    # Signal colour map
    sig_colours = {"BUY": "#27ae60", "SELL": "#e74c3c", "HOLD": "#7f8c8d"}

    # Stock table rows
    if top_stocks:
        rows = ""
        for s in top_stocks:
            colour = sig_colours.get(s.get("signal", "HOLD"), "#7f8c8d")
            ticker = _esc(s.get("ticker", "—"))
            name = _esc(s.get("name") or s.get("ticker", "—"))
            signal = _esc(s.get("signal", "—"))
            confidence = _esc(str(s.get("confidence", "—")))
            rationale = _esc(s.get("rationale", ""))
            rows += (
                f'<tr>'
                f'<td style="padding:6px 8px;font-weight:bold;">{ticker}</td>'
                f'<td style="padding:6px 8px;color:#555;">{name}</td>'
                f'<td style="padding:6px 8px;color:{colour};font-weight:bold;">{signal}</td>'
                f'<td style="padding:6px 8px;text-align:center;">{confidence}</td>'
                f'<td style="padding:6px 8px;color:#333;">{rationale}</td>'
                f'</tr>\n'
            )
        stock_section = (
            '<table style="width:100%;border-collapse:collapse;font-size:14px;">'
            '<tr style="background:#f4f4f4;">'
            '<th style="padding:6px 8px;text-align:left;">Ticker</th>'
            '<th style="padding:6px 8px;text-align:left;">Name</th>'
            '<th style="padding:6px 8px;text-align:left;">Signal</th>'
            '<th style="padding:6px 8px;text-align:center;">Conf.</th>'
            '<th style="padding:6px 8px;text-align:left;">Rationale</th>'
            '</tr>\n'
            + rows
            + '</table>'
        )
    else:
        stock_section = '<p style="color:#888;">Signals not yet available — run update-signals workflow first.</p>'

    # F&G section
    if fg is not None:
        v = fg["value"]
        cl = fg["classification"]
        if v <= 25:
            fg_colour = "#e74c3c"
        elif v <= 45:
            fg_colour = "#e67e22"
        elif v <= 55:
            fg_colour = "#f1c40f"
        elif v <= 75:
            fg_colour = "#27ae60"
        else:
            fg_colour = "#1abc9c"
        fg_section = (
            f'<p>Crypto Fear &amp; Greed Index (Alternative.me): '
            f'<strong style="color:{fg_colour};font-size:1.2em;">{v}</strong> — {cl}</p>'
        )
    else:
        fg_section = '<p style="color:#888;">F&amp;G data unavailable this run.</p>'

    # Geopolitical section
    if geo:
        items = "".join(
            f'<li><a href="{_esc(a["link"])}" style="color:#2980b9;">{_esc(a["title"])}</a>'
            f' <span style="color:#999;font-size:12px;">({_esc(a["source"])})</span></li>\n'
            for a in geo
        )
        geo_section = f'<ul style="padding-left:20px;">{items}</ul>'
    else:
        geo_section = '<p style="color:#888;">No geopolitical risk items detected this run.</p>'

    # FOMC section
    if fomc:
        items = "".join(
            f'<li><a href="{_esc(e["link"])}" style="color:#2980b9;">{_esc(e["title"])}</a>'
            f'<span style="color:#999;font-size:12px;"> ({_esc(e["published"])})</span></li>\n'
            for e in fomc
        )
        fomc_section = f'<ul style="padding-left:20px;">{items}</ul>'
    else:
        fomc_section = '<p style="color:#888;">No recent FOMC releases.</p>'

    return f"""<html>
<body style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:16px;color:#1a1a2e;line-height:1.5;">
  <h1 style="font-size:20px;border-bottom:2px solid #e0e0e0;padding-bottom:8px;">
    Market Digest &mdash; {timestamp_tw}
  </h1>

  <h2 style="font-size:16px;color:#1a1a2e;border-bottom:1px solid #e0e0e0;padding-bottom:4px;">
    TW + US Stock Shortlist
  </h2>
  {_narr_block("stocks")}
  {stock_section}

  <h2 style="font-size:16px;color:#1a1a2e;border-bottom:1px solid #e0e0e0;padding-bottom:4px;margin-top:24px;">
    Fear &amp; Greed Index
  </h2>
  {fg_section}
  {_narr_block("fg")}

  <h2 style="font-size:16px;color:#1a1a2e;border-bottom:1px solid #e0e0e0;padding-bottom:4px;margin-top:24px;">
    Geopolitical Risk Pulse
  </h2>
  {_narr_block("geo")}
  {geo_section}

  <h2 style="font-size:16px;color:#1a1a2e;border-bottom:1px solid #e0e0e0;padding-bottom:4px;margin-top:24px;">
    FOMC / Fed Updates
  </h2>
  {_narr_block("fomc")}
  {fomc_section}

  <hr style="border:none;border-top:1px solid #e0e0e0;margin-top:24px;"/>
  <p style="font-size:11px;color:#aaa;">
    Generated by market-news digest.py &mdash; {timestamp_utc} UTC
  </p>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Email sender
# ---------------------------------------------------------------------------

def _send_email(html: str, subject: str) -> None:
    """Send email via Resend. Raises on API error."""
    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key:
        raise ValueError("RESEND_API_KEY environment variable is not set")
    resend.api_key = api_key
    resp = resend.Emails.send({
        "from": SENDER,
        "to": [RECIPIENT],
        "subject": subject,
        "html": html,
    })
    # resend SDK raises ResendError on 4xx/5xx; if we reach here it succeeded
    print(f"[digest] Email sent — id={resp.get('id', '?')}")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main() -> int:
    now_utc = datetime.now(timezone.utc)
    now_tw = now_utc.astimezone(TW_OFFSET)
    timestamp_tw = now_tw.strftime("%Y-%m-%d %H:%M TW")
    timestamp_utc = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"[digest] Starting — {timestamp_tw}")

    # Fetch all data (failures are per-section; only email send failure = non-zero exit)
    print("[digest] Fetching Fear & Greed Index...")
    fg = _fetch_fg()
    print(f"[digest] F&G: {fg}")

    print("[digest] Fetching FOMC RSS...")
    fomc = _fetch_fomc()
    print(f"[digest] FOMC entries: {len(fomc)}")

    print("[digest] Fetching geopolitical news...")
    geo = _fetch_geopolitical()
    print(f"[digest] Geopolitical items: {len(geo)}")

    print("[digest] Loading signals...")
    signals = _load_signals()
    top_stocks = _top_signals(signals)
    print(f"[digest] Signals loaded: {len(signals)} total, {len(top_stocks)} selected")

    # Generate narratives via NIM (best-effort; empty string on failure or missing key)
    print("[digest] Generating narratives via NIM...")
    narratives = {
        "stocks": _narrative_stocks(top_stocks),
        "fg": _narrative_fg(fg),
        "geo": _narrative_geo(geo),
        "fomc": _narrative_fomc(fomc),
    }
    for k, v in narratives.items():
        print(f"[digest] Narrative[{k}]: {len(v)} chars")

    # Compose HTML
    html = _render_html(timestamp_tw, timestamp_utc, top_stocks, fg, geo, fomc, narratives)
    print(f"[digest] HTML composed — {len(html)} chars")

    # Send
    subject = f"Market Digest — {timestamp_tw}"
    try:
        _send_email(html, subject)
    except Exception as exc:
        print(f"[digest] ERROR sending email: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
