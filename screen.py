"""Screen S&P 500 for potentially undervalued stocks using fundamentals only.

Usage:
  python3 screen.py                            # top 20 with default filters
  python3 screen.py --top 10 --min-upside 20
  python3 screen.py --limit 50                 # quick test (first 50 tickers)

Scoring (0–100):
  upside_pct     40 pts max  (analyst target vs current price)
  week52_pos     30 pts max  (lower 52-week position = better)
  relative_pe    30 pts max  (lower P/E vs sector average = better)
"""
from __future__ import annotations

import argparse
import sys
import time

import pandas as pd
import yfinance as yf

from valuation import SECTOR_PE_BENCHMARK


def _sp500_tickers() -> list[str]:
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    df = pd.read_html(url, storage_options={"User-Agent": "Mozilla/5.0"})[0]
    return df["Symbol"].str.replace(".", "-", regex=False).tolist()


def _fetch_row(ticker: str) -> dict | None:
    try:
        info = yf.Ticker(ticker).info
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        if not price:
            return None

        row: dict = {
            "ticker": ticker,
            "name": info.get("shortName", ticker),
            "sector": info.get("sector", ""),
            "price": price,
        }

        target = info.get("targetMeanPrice")
        if target:
            row["upside_pct"] = round((target - price) / price * 100, 1)

        lo, hi = info.get("fiftyTwoWeekLow"), info.get("fiftyTwoWeekHigh")
        if lo and hi and hi > lo:
            row["week52_pos"] = round((price - lo) / (hi - lo) * 100, 1)

        pe = info.get("trailingPE")
        sector_avg = SECTOR_PE_BENCHMARK.get(info.get("sector", ""))
        if pe and pe > 0 and sector_avg:
            row["relative_pe"] = round(pe / sector_avg, 2)

        row["score"] = _uv_score(row)
        return row
    except Exception:
        return None


def _uv_score(r: dict) -> float:
    s = 0.0
    upside = r.get("upside_pct", 0)
    if upside > 0:
        s += min(upside / 50, 1.0) * 40
    w52 = r.get("week52_pos")
    if w52 is not None:
        s += max(0.0, (50 - w52) / 50) * 30
    rpe = r.get("relative_pe")
    if rpe is not None:
        s += max(0.0, (1.2 - rpe) / 1.2) * 30
    return round(s, 1)


def screen(
    top_n: int = 20,
    min_upside: float = 10.0,
    max_week52_pos: float = 40.0,
    max_rel_pe: float = 0.9,
    limit: int | None = None,
) -> list[dict]:
    tickers = _sp500_tickers()
    if limit:
        tickers = tickers[:limit]

    print(f"Screening {len(tickers)} tickers…", file=sys.stderr)
    results = []
    for i, t in enumerate(tickers, 1):
        r = _fetch_row(t)
        if r:
            results.append(r)
        if i % 50 == 0:
            print(f"  {i}/{len(tickers)} done", file=sys.stderr)
        time.sleep(0.1)

    candidates = [
        r for r in results
        if r.get("upside_pct", 0) >= min_upside
        and r.get("week52_pos", 100) <= max_week52_pos
        and r.get("relative_pe", 999) <= max_rel_pe
    ]
    candidates.sort(key=lambda r: r["score"], reverse=True)
    return candidates[:top_n]


def _print_results(rows: list[dict]) -> None:
    if not rows:
        print("No candidates found — try relaxing filters (--min-upside, --max-52w-pos, --max-rel-pe).")
        return

    header = f"{'#':<3} {'Ticker':<8} {'Name':<28} {'Sector':<22} {'Score':>5} {'Upside':>7} {'52W%':>6} {'RelPE':>6}"
    print(header)
    print("─" * len(header))
    for i, r in enumerate(rows, 1):
        upside = f"+{r['upside_pct']:.1f}%" if "upside_pct" in r else "   N/A"
        w52 = f"{r['week52_pos']:.0f}%" if "week52_pos" in r else "  N/A"
        rpe = f"{r['relative_pe']:.2f}x" if "relative_pe" in r else "  N/A"
        print(
            f"{i:<3} {r['ticker']:<8} {r['name'][:27]:<28} {r['sector'][:21]:<22}"
            f" {r['score']:>5.1f} {upside:>7} {w52:>6} {rpe:>6}"
        )
    print()
    print("Run `python3 analyze_stock.py <TICKER>` for full BUY/HOLD/SELL signal on any candidate.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Screen S&P 500 for undervalued stock candidates")
    ap.add_argument("--top", type=int, default=20, metavar="N",
                    help="Max results to show (default 20)")
    ap.add_argument("--min-upside", type=float, default=10.0, metavar="PCT",
                    help="Min analyst target upside %% (default 10)")
    ap.add_argument("--max-52w-pos", type=float, default=40.0, metavar="PCT",
                    help="Max 52-week range position %% (default 40)")
    ap.add_argument("--max-rel-pe", type=float, default=0.9, metavar="RATIO",
                    help="Max P/E relative to sector average (default 0.9)")
    ap.add_argument("--limit", type=int, default=None, metavar="N",
                    help="Only check first N tickers (for testing)")
    args = ap.parse_args()

    rows = screen(
        top_n=args.top,
        min_upside=args.min_upside,
        max_week52_pos=args.max_52w_pos,
        max_rel_pe=args.max_rel_pe,
        limit=args.limit,
    )
    _print_results(rows)


if __name__ == "__main__":
    main()
