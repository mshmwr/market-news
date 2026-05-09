"""Daily digest email — composes and sends a twice-daily HTML market summary.

Sections (each gets an LLM-generated narrative):
  1. US Stock Shortlist            (reads docs/signals.json)
  2. TW Stock Shortlist            (reads docs/signals.json)
  3. Fear & Greed Index            (Alternative.me free API)
  4. 影響股票市場的新聞              (CNBC + MarketWatch + 經濟日報 + ETtoday)
  5. Geopolitical Risk Pulse       (Al Jazeera + BBC World RSS via fetch_news)
  6. FOMC / Fed Updates            (Federal Reserve RSS)

Narratives are produced via NVIDIA NIM (MiniMax M2.7); on failure the section
falls back to raw list rendering only.

Usage:
  python digest.py              # fetch + narrate + email
  python digest.py --preview    # fetch + narrate + write digest-preview.html (no email)

Required env vars:
  RESEND_API_KEY   — Resend email API key (not needed in --preview mode)
  NVIDIA_API_KEY   — NVIDIA NIM API key for narrative generation (optional;
                     missing → narrative skipped, raw lists still render)

Exit codes:
  0  success (email sent or preview file written)
  1  email send failed (Resend error)
"""

from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta

import html as _html_lib
import feedparser
import requests
import resend

from fetch_news import fetch_all as fetch_all_news


def _esc(text: str) -> str:
    """HTML-escape a string for safe inline rendering."""
    return _html_lib.escape(str(text))


def _fmt_ts(ts: int) -> str:
    """Format unix epoch (seconds) as 'MM/DD HH:MM' in Taiwan time. Empty if ts falsy."""
    if not ts:
        return ""
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(TW_OFFSET).strftime("%m/%d %H:%M")
    except (OSError, ValueError):
        return ""

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
NIM_TIMEOUT = 300

# Taiwan is UTC+8
TW_OFFSET = timezone(timedelta(hours=8))


# ---------------------------------------------------------------------------
# LLM narrative (NVIDIA NIM)
# ---------------------------------------------------------------------------

def _call_nim(prompt: str, label: str = "", attempts: int = 3) -> str:
    """Call NVIDIA NIM with retry. Returns content on success, empty string after final failure."""
    import time
    api_key = os.environ.get("NVIDIA_API_KEY", "")
    if not api_key:
        return ""
    last_err = None
    for attempt in range(1, attempts + 1):
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
                    "max_tokens": 8192,
                },
                timeout=NIM_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            choice = data["choices"][0]
            msg = choice.get("message", {})
            content = (msg.get("content") or "").strip()
            if content:
                return content
            finish = choice.get("finish_reason", "?")
            comp = (data.get("usage", {}) or {}).get("completion_tokens", "?")
            print(
                f"[digest] NIM[{label}] attempt {attempt}/{attempts} empty — "
                f"finish={finish} completion_tokens={comp}",
                flush=True,
            )
        except Exception as exc:
            last_err = exc
            print(
                f"[digest] NIM[{label}] attempt {attempt}/{attempts} failed: {exc}",
                flush=True,
            )
        if attempt < attempts:
            time.sleep(2 ** (attempt - 1))  # 1s, 2s exponential backoff
    if last_err is not None:
        print(f"[digest] NIM[{label}] gave up after {attempts} attempts; last error: {last_err}", flush=True)
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
    return _call_nim(prompt, "fg")


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
    return _call_nim(prompt, "fomc")


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
    return _call_nim(prompt, "geo")


def _narrative_stocks(top: list[dict], region_label: str) -> str:
    if not top:
        return ""
    bullets = "\n".join(
        f"- {s.get('ticker','—')} ({s.get('name','—')}): {s.get('signal','—')} "
        f"conf={s.get('confidence','—')} | {s.get('rationale','')}"
        for s in top
    )
    prompt = (
        f"以下是今日{region_label}個股 Top 訊號（來自本系統 analyze_stock 多因子模型）：\n"
        f"{bullets}\n\n"
        f"請用繁體中文寫一段約 120–180 字的觀察，說明本批{region_label}清單反映的板塊或主題、"
        "整體偏多或偏空傾向、以及讀者可關注的後續催化劑。直接給出段落文字。"
    )
    return _call_nim(prompt, f"stocks_{region_label}")


def _translate_rationales(stocks: list[dict]) -> dict[str, str]:
    """Batch-translate per-stock rationale to zh-TW. Returns {ticker: zh}.

    On any failure (NIM down, parse error) returns {} — caller falls back to original.
    """
    pairs = [(s.get("ticker", ""), s.get("rationale", "")) for s in stocks if s.get("rationale")]
    if not pairs:
        return {}
    numbered = "\n".join(f"{i+1}. [{tk}] {r}" for i, (tk, r) in enumerate(pairs))
    prompt = (
        "以下是個股的多因子訊號 rationale（英文）。請翻譯成自然的繁體中文，"
        "保留所有具體數字與比率，不要意譯關鍵指標名稱（PE、PEG、Graham number、forward P/E 等可保留英文）。\n\n"
        f"{numbered}\n\n"
        "輸出格式：嚴格按照「N. [TICKER] 中文翻譯」逐行對應，不要新增段落或註解，"
        "不要省略任何一條。"
    )
    raw = _call_nim(prompt, "rationale_translate")
    if not raw:
        return {}

    out: dict[str, str] = {}
    import re
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^\d+\.\s*\[([^\]]+)\]\s*(.+)$", line)
        if m:
            out[m.group(1).strip()] = m.group(2).strip()
    return out


def _narrative_market_news(items: list[dict]) -> str:
    if not items:
        return ""
    bullets = "\n".join(
        f"- [{a.get('category','')}] {a.get('title','')} ({a.get('source','')})"
        for a in items
    )
    prompt = (
        "以下是今日影響股票市場的財經新聞標題（涵蓋台股 + 美股媒體）：\n"
        f"{bullets}\n\n"
        "請用繁體中文寫一段約 150–200 字的綜合解讀，說明本批新聞反映的"
        "(1) 市場主題（產業輪動、利率、業績、政策、AI 等）、"
        "(2) 對台股與美股的潛在影響、"
        "(3) 短線交易者可關注的方向。直接給出段落文字，不要編號標題。"
    )
    return _call_nim(prompt, "market_news")


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


def _fetch_geopolitical(articles: list[dict] | None = None, limit: int = 8) -> list[dict]:
    """Return up to `limit` geopolitical risk articles from Al Jazeera / BBC World."""
    if articles is None:
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
                "description": article.get("description", ""),
                "published_ts": article.get("published_ts", 0),
            })
            if len(hits) >= limit:
                break
    return hits


def _fetch_market_news(articles: list[dict] | None = None, per_category: int = 4) -> list[dict]:
    """Return market-moving news balanced across 美股 + 台股 (≤per_category each).

    Source feeds: CNBC + MarketWatch (美股) + 經濟日報 + ETtoday財經 (台股).
    Result is interleaved so US and TW alternate when both have items.
    """
    if articles is None:
        try:
            articles = fetch_all_news()
        except Exception:
            return []

    def _pick(cat: str) -> list[dict]:
        out = []
        for article in articles:
            if article.get("category") != cat:
                continue
            out.append({
                "title": article.get("title", "(no title)"),
                "link": article.get("link", ""),
                "source": article.get("source", ""),
                "category": article.get("category", ""),
                "description": article.get("description", ""),
                "published_ts": article.get("published_ts", 0),
            })
            if len(out) >= per_category:
                break
        return out

    us = _pick("美股")
    tw = _pick("台股")
    interleaved = []
    for u, t in zip(us, tw):
        interleaved.extend([u, t])
    interleaved.extend(us[len(tw):])
    interleaved.extend(tw[len(us):])
    return interleaved


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


def _split_signals_by_region(signals: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split signals into (us_top5, tw_topN). TW = ticker ends with .TW; US = everything else."""
    tw = [s for s in signals if s.get("ticker", "").upper().endswith(".TW")]
    us = [s for s in signals if not s.get("ticker", "").upper().endswith(".TW")]
    return _top_signals(us, 5), _top_signals(tw, 4)


# ---------------------------------------------------------------------------
# HTML renderer
# ---------------------------------------------------------------------------

def _render_html(
    timestamp_tw: str,
    timestamp_utc: str,
    us_stocks: list[dict],
    tw_stocks: list[dict],
    fg: dict | None,
    market_news: list[dict],
    geo: list[dict],
    fomc: list[dict],
    narratives: dict[str, str] | None = None,
    rationale_zh: dict[str, str] | None = None,
) -> str:
    narratives = narratives or {}
    rationale_zh = rationale_zh or {}

    def _narr_block(key: str) -> str:
        text = (narratives.get(key) or "").strip()
        if not text:
            return ""
        return (
            '<p style="background:#f7f9fc;border-left:3px solid #2980b9;'
            'padding:8px 12px;margin:8px 0;color:#222;font-size:14px;'
            f'line-height:1.6;">{_esc(text)}</p>'
        )
    # Signal colour + label map
    sig_colours = {"BUY": "#27ae60", "SELL": "#e74c3c", "HOLD": "#7f8c8d"}
    sig_labels = {"BUY": "BUY / 買進", "SELL": "SELL / 賣出", "HOLD": "HOLD / 觀望"}

    def _stock_table(stocks: list[dict], empty_msg: str) -> str:
        if not stocks:
            return f'<p style="color:#888;">{empty_msg}</p>'
        rows = ""
        for s in stocks:
            sig_key = s.get("signal", "HOLD")
            colour = sig_colours.get(sig_key, "#7f8c8d")
            ticker_raw = s.get("ticker", "—")
            ticker = _esc(ticker_raw)
            name = _esc(s.get("name") or ticker_raw)
            signal = _esc(sig_labels.get(sig_key, sig_key))
            confidence = _esc(str(s.get("confidence", "—")))
            rationale_en = _esc(s.get("rationale", ""))
            zh = rationale_zh.get(ticker_raw, "")
            if zh:
                rationale_html = (
                    f'{rationale_en}'
                    f'<br><span style="color:#555;">{_esc(zh)}</span>'
                )
            else:
                rationale_html = rationale_en
            rows += (
                f'<tr>'
                f'<td style="padding:6px 8px;font-weight:bold;">{ticker}</td>'
                f'<td style="padding:6px 8px;color:#555;">{name}</td>'
                f'<td style="padding:6px 8px;color:{colour};font-weight:bold;">{signal}</td>'
                f'<td style="padding:6px 8px;text-align:center;">{confidence}</td>'
                f'<td style="padding:6px 8px;color:#333;">{rationale_html}</td>'
                f'</tr>\n'
            )
        return (
            '<table style="width:100%;border-collapse:collapse;font-size:14px;">'
            '<tr style="background:#f4f4f4;">'
            '<th style="padding:6px 8px;text-align:left;">Ticker / 代號</th>'
            '<th style="padding:6px 8px;text-align:left;">Name / 名稱</th>'
            '<th style="padding:6px 8px;text-align:left;">Signal / 訊號</th>'
            '<th style="padding:6px 8px;text-align:center;">Conf. / 信心</th>'
            '<th style="padding:6px 8px;text-align:left;">Rationale / 理由</th>'
            '</tr>\n'
            + rows
            + '</table>'
        )

    us_section = _stock_table(us_stocks, "US signals not yet available — run update-signals workflow first. / 美股訊號尚未產生。")
    tw_section = _stock_table(tw_stocks, "TW signals not yet available — run update-signals workflow first. / 台股訊號尚未產生。")

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
            f'<p>Crypto Fear &amp; Greed Index / 加密貨幣恐懼貪婪指數 (Alternative.me): '
            f'<strong style="color:{fg_colour};font-size:1.2em;">{v}</strong> — {cl}</p>'
        )
    else:
        fg_section = '<p style="color:#888;">F&amp;G data unavailable this run. / 本次取不到指數資料。</p>'

    def _meta(parts: list[str]) -> str:
        joined = " · ".join(p for p in parts if p)
        return f' <span style="color:#999;font-size:12px;">({joined})</span>' if joined else ""

    # Market-moving news section
    if market_news:
        items = "".join(
            f'<li><a href="{_esc(a["link"])}" style="color:#2980b9;">{_esc(a["title"])}</a>'
            f'{_meta([_esc(a["category"]), _esc(a["source"]), _esc(_fmt_ts(a.get("published_ts", 0)))])}</li>\n'
            for a in market_news
        )
        market_section = f'<ul style="padding-left:20px;">{items}</ul>'
    else:
        market_section = '<p style="color:#888;">No market-moving headlines fetched this run. / 本次未抓到影響市場的新聞。</p>'

    # Geopolitical section
    if geo:
        items = "".join(
            f'<li><a href="{_esc(a["link"])}" style="color:#2980b9;">{_esc(a["title"])}</a>'
            f'{_meta([_esc(a["source"]), _esc(_fmt_ts(a.get("published_ts", 0)))])}</li>\n'
            for a in geo
        )
        geo_section = f'<ul style="padding-left:20px;">{items}</ul>'
    else:
        geo_section = '<p style="color:#888;">No geopolitical risk items detected this run. / 本次未偵測到地緣政治風險新聞。</p>'

    # FOMC section
    if fomc:
        items = "".join(
            f'<li><a href="{_esc(e["link"])}" style="color:#2980b9;">{_esc(e["title"])}</a>'
            f'<span style="color:#999;font-size:12px;"> ({_esc(e["published"])})</span></li>\n'
            for e in fomc
        )
        fomc_section = f'<ul style="padding-left:20px;">{items}</ul>'
    else:
        fomc_section = '<p style="color:#888;">No recent FOMC releases. / 近期無 FOMC 公告。</p>'

    return f"""<html>
<body style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:16px;color:#1a1a2e;line-height:1.5;">
  <h1 style="font-size:20px;border-bottom:2px solid #e0e0e0;padding-bottom:8px;">
    Market Digest / 每日市場摘要 &mdash; {timestamp_tw}
  </h1>

  <h2 style="font-size:16px;color:#1a1a2e;border-bottom:1px solid #e0e0e0;padding-bottom:4px;">
    US Stock Shortlist / 美股精選清單
  </h2>
  {_narr_block("stocks_US")}
  {us_section}

  <h2 style="font-size:16px;color:#1a1a2e;border-bottom:1px solid #e0e0e0;padding-bottom:4px;margin-top:24px;">
    TW Stock Shortlist / 台股精選清單
  </h2>
  {_narr_block("stocks_TW")}
  {tw_section}

  <h2 style="font-size:16px;color:#1a1a2e;border-bottom:1px solid #e0e0e0;padding-bottom:4px;margin-top:24px;">
    Fear &amp; Greed Index / 恐懼貪婪指數
  </h2>
  {fg_section}
  {_narr_block("fg")}

  <h2 style="font-size:16px;color:#1a1a2e;border-bottom:1px solid #e0e0e0;padding-bottom:4px;margin-top:24px;">
    Market-Moving News / 影響股票市場的新聞
  </h2>
  {_narr_block("market_news")}
  {market_section}

  <h2 style="font-size:16px;color:#1a1a2e;border-bottom:1px solid #e0e0e0;padding-bottom:4px;margin-top:24px;">
    Geopolitical Risk Pulse / 地緣政治風險脈動
  </h2>
  {_narr_block("geo")}
  {geo_section}

  <h2 style="font-size:16px;color:#1a1a2e;border-bottom:1px solid #e0e0e0;padding-bottom:4px;margin-top:24px;">
    FOMC / Fed Updates / 聯準會動態
  </h2>
  {_narr_block("fomc")}
  {fomc_section}

  <hr style="border:none;border-top:1px solid #e0e0e0;margin-top:24px;"/>
  <p style="font-size:11px;color:#aaa;">
    Generated by market-news digest.py / 由 market-news digest.py 產生 &mdash; {timestamp_utc} UTC
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
    preview_mode = "--preview" in sys.argv[1:]

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

    print("[digest] Fetching all news once (geo + market-moving share the result)...")
    try:
        all_articles = fetch_all_news()
    except Exception as exc:
        print(f"[digest] fetch_all_news failed: {exc}", flush=True)
        all_articles = []
    print(f"[digest] News articles fetched: {len(all_articles)}")

    geo = _fetch_geopolitical(all_articles)
    print(f"[digest] Geopolitical items: {len(geo)}")

    market_news = _fetch_market_news(all_articles)
    print(f"[digest] Market-moving items: {len(market_news)}")

    print("[digest] Loading signals...")
    signals = _load_signals()
    us_stocks, tw_stocks = _split_signals_by_region(signals)
    print(f"[digest] Signals loaded: {len(signals)} total | US top {len(us_stocks)} | TW top {len(tw_stocks)}")

    # Generate narratives via NIM in parallel (best-effort; empty string on failure)
    # max_workers=2 keeps NIM server load light — 6 simultaneous reasoning calls
    # caused RemoteDisconnected on 3/6 slots in earlier runs.
    print("[digest] Generating narratives via NIM (parallel x2)...")
    all_stocks = us_stocks + tw_stocks
    narrative_jobs = {
        "stocks_US":           (lambda: _narrative_stocks(us_stocks, "美股")),
        "stocks_TW":           (lambda: _narrative_stocks(tw_stocks, "台股")),
        "fg":                  (lambda: _narrative_fg(fg)),
        "market_news":         (lambda: _narrative_market_news(market_news)),
        "geo":                 (lambda: _narrative_geo(geo)),
        "fomc":                (lambda: _narrative_fomc(fomc)),
        "rationale_translate": (lambda: _translate_rationales(all_stocks)),
    }
    narratives: dict[str, str] = {}
    rationale_zh: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {key: pool.submit(fn) for key, fn in narrative_jobs.items()}
        for key, fut in futures.items():
            try:
                result = fut.result()
            except Exception as exc:
                print(f"[digest] Narrative[{key}] threw: {exc}", flush=True)
                result = "" if key != "rationale_translate" else {}
            if key == "rationale_translate":
                rationale_zh = result or {}
                print(f"[digest] Rationale translations: {len(rationale_zh)} entries")
            else:
                narratives[key] = result
                print(f"[digest] Narrative[{key}]: {len(result)} chars")

    # Compose HTML
    html = _render_html(
        timestamp_tw, timestamp_utc,
        us_stocks, tw_stocks, fg, market_news, geo, fomc,
        narratives,
        rationale_zh,
    )
    print(f"[digest] HTML composed — {len(html)} chars")

    subject = f"Market Digest / 每日市場摘要 — {timestamp_tw}"

    if preview_mode:
        out_path = os.path.join(os.path.dirname(__file__), "digest-preview.html")
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(html)
        print(f"[digest] Preview written — {out_path} ({len(html)} chars, no email sent)")
        return 0

    try:
        _send_email(html, subject)
    except Exception as exc:
        print(f"[digest] ERROR sending email: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
