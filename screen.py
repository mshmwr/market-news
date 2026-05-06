"""Screen S&P 500 / S&P 100 for potentially undervalued stocks using fundamentals only.

Usage:
  python3 screen.py                            # top 20, S&P 500
  python3 screen.py --sp100                    # S&P 100 only (~3 min, daily automation)
  python3 screen.py --top 10 --min-upside 20
  python3 screen.py --limit 50                 # quick test (first 50 tickers)
  python3 screen.py --min-market-cap 50        # only $50B+ companies

Scoring (0–120):
  upside_pct     40 pts max  (analyst target vs current price)
  week52_pos     30 pts max  (lower 52-week position = better)
  relative_pe    30 pts max  (lower P/E vs sector average = better)
  brand          20 pts max  (market cap proxy for brand recognition / industry leadership)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date

import pandas as pd
import yfinance as yf

from valuation import SECTOR_PE_BENCHMARK

_SECTOR_ZH: dict[str, str] = {
    "Technology": "科技",
    "Healthcare": "醫療保健",
    "Consumer Cyclical": "消費循環",
    "Consumer Defensive": "必需消費",
    "Financial Services": "金融服務",
    "Communication Services": "通訊服務",
    "Energy": "能源",
    "Industrials": "工業",
    "Basic Materials": "基礎材料",
    "Real Estate": "房地產",
    "Utilities": "公用事業",
}

_INDUSTRY_ZH: dict[str, str] = {
    # Technology
    "Semiconductors": "半導體",
    "Semiconductor Equipment & Materials": "半導體設備",
    "Software - Application": "軟體應用",
    "Software - Infrastructure": "系統軟體",
    "Consumer Electronics": "消費電子",
    "Computer Hardware": "電腦硬體",
    "Electronic Components": "電子元件",
    "Information Technology Services": "IT服務",
    "Scientific & Technical Instruments": "科技儀器",
    # Communication Services
    "Internet Content & Information": "網路搜尋與內容",
    "Social Media": "社群媒體",
    "Entertainment": "娛樂媒體",
    "Telecom Services": "電信服務",
    "Electronic Gaming & Multimedia": "電玩與多媒體",
    # Healthcare
    "Drug Manufacturers - General": "大型製藥",
    "Drug Manufacturers - Specialty & Generic": "特殊製藥",
    "Biotechnology": "生技",
    "Medical Devices": "醫療設備",
    "Medical Instruments & Supplies": "醫療器材",
    "Diagnostics & Research": "診斷與研究",
    "Healthcare Plans": "健保計畫",
    "Health Information Services": "醫療資訊",
    "Medical Care Facilities": "醫療機構",
    "Pharmaceutical Retailers": "藥局連鎖",
    # Financial Services
    "Banks—Diversified": "大型銀行",
    "Banks—Regional": "地區銀行",
    "Credit Services": "信用卡與支付",
    "Capital Markets": "資本市場",
    "Insurance - Property & Casualty": "財產意外險",
    "Insurance - Life": "壽險",
    "Insurance - Diversified": "多元保險",
    "Asset Management": "資產管理",
    "Financial Data & Stock Exchanges": "金融數據與交易所",
    # Consumer Cyclical
    "Auto Manufacturers": "汽車製造",
    "Specialty Retail": "專賣零售",
    "Internet Retail": "電商",
    "Home Improvement Retail": "家居零售",
    "Lodging": "飯店",
    "Restaurants": "餐飲連鎖",
    "Resorts & Casinos": "博弈度假村",
    # Consumer Defensive
    "Discount Stores": "折扣零售",
    "Grocery Stores": "超市",
    "Household & Personal Products": "家用與個人護理",
    "Beverages - Non-Alcoholic": "非酒精飲料",
    "Beverages - Alcoholic": "酒精飲料",
    "Tobacco": "菸草",
    "Packaged Foods": "包裝食品",
    # Energy
    "Oil & Gas Integrated": "整合石油天然氣",
    "Oil & Gas E&P": "石油天然氣探勘",
    "Oil & Gas Refining & Marketing": "石油煉製",
    "Oil & Gas Equipment & Services": "油服",
    # Industrials
    "Aerospace & Defense": "航太國防",
    "Industrial Conglomerates": "工業集團",
    "Railroads": "鐵路運輸",
    "Air Freight & Logistics": "航空貨運物流",
    "Airlines": "航空公司",
    "Farm & Heavy Construction Machinery": "重型機械",
    "Waste Management": "廢棄物管理",
    # Basic Materials
    "Chemicals": "化工",
    "Specialty Chemicals": "特用化工",
    # Utilities
    "Utilities - Regulated Electric": "電力公用事業",
    "Utilities - Renewable": "再生能源",
}


def _sp500_tickers() -> list[str]:
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    df = pd.read_html(url, storage_options={"User-Agent": "Mozilla/5.0"})[0]
    return df["Symbol"].str.replace(".", "-", regex=False).tolist()


def _sp100_tickers() -> list[str]:
    url = "https://en.wikipedia.org/wiki/S%26P_100"
    tables = pd.read_html(url, storage_options={"User-Agent": "Mozilla/5.0"})
    for df in tables:
        if "Symbol" in df.columns:
            return df["Symbol"].str.replace(".", "-", regex=False).tolist()
    return _sp500_tickers()[:100]


def _generate_reason(r: dict) -> str:
    parts = []
    upside = r.get("upside_pct")
    if upside and upside >= 15:
        parts.append(f"分析師共識漲幅 +{upside:.0f}%")
    w52 = r.get("week52_pos")
    if w52 is not None:
        if w52 <= 10:
            parts.append(f"近52週最低點（{w52:.0f}%）")
        elif w52 <= 25:
            parts.append(f"位於52週低點區（{w52:.0f}%）")
    rpe = r.get("relative_pe")
    if rpe is not None and rpe <= 0.9:
        pct = round((1 - rpe) * 100)
        parts.append(f"本益比低於產業均值 {pct}%")
    mc = r.get("market_cap") or 0
    industry_zh = _INDUSTRY_ZH.get(r.get("industry", ""), "")
    if not industry_zh:
        sector_zh = _SECTOR_ZH.get(r.get("sector", ""), "")
        label = f"{sector_zh}行業" if sector_zh else "行業"
    else:
        label = industry_zh
    if mc >= 100e9:
        parts.append(f"{label}龍頭")
    elif mc >= 20e9:
        parts.append(f"{label}大型股")
    return "；".join(parts) + "。" if parts else "多項量化指標顯示潛在低估。"


def _fetch_row(ticker: str) -> dict | None:
    try:
        info = yf.Ticker(ticker).info
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        if not price:
            return None

        market_cap = info.get("marketCap")
        row: dict = {
            "ticker": ticker,
            "name": info.get("shortName", ticker),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "price": price,
            "market_cap": market_cap,
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
        row["reason"] = _generate_reason(row)
        return row
    except Exception:
        return None


def _brand_score(market_cap: int | None) -> float:
    if not market_cap:
        return 0.0
    b = market_cap / 1e9  # convert to billions
    if b >= 100:
        return 20.0
    if b >= 50:
        return 15.0
    if b >= 20:
        return 10.0
    if b >= 5:
        return 5.0
    return 0.0


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
    s += _brand_score(r.get("market_cap"))
    return round(s, 1)


def screen(
    top_n: int = 20,
    min_upside: float = 10.0,
    max_week52_pos: float = 40.0,
    max_rel_pe: float = 0.9,
    min_market_cap_b: float = 10.0,
    limit: int | None = None,
    use_sp100: bool = False,
) -> list[dict]:
    tickers = _sp100_tickers() if use_sp100 else _sp500_tickers()
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

    min_market_cap = min_market_cap_b * 1e9
    candidates = [
        r for r in results
        if r.get("upside_pct", 0) >= min_upside
        and r.get("week52_pos", 100) <= max_week52_pos
        and r.get("relative_pe", 999) <= max_rel_pe
        and (r.get("market_cap") or 0) >= min_market_cap
    ]
    candidates.sort(key=lambda r: r["score"], reverse=True)
    return candidates[:top_n]


def _print_results(rows: list[dict]) -> None:
    if not rows:
        print("No candidates found — try relaxing filters (--min-upside, --max-52w-pos, --max-rel-pe).")
        return

    header = f"{'#':<3} {'Ticker':<8} {'Name':<28} {'Sector':<22} {'Score':>6} {'Upside':>7} {'52W%':>6} {'RelPE':>6} {'MCap':>7}"
    print(header)
    print("─" * len(header))
    for i, r in enumerate(rows, 1):
        upside = f"+{r['upside_pct']:.1f}%" if "upside_pct" in r else "   N/A"
        w52 = f"{r['week52_pos']:.0f}%" if "week52_pos" in r else "  N/A"
        rpe = f"{r['relative_pe']:.2f}x" if "relative_pe" in r else "  N/A"
        mc = r.get("market_cap")
        mcap = f"{mc/1e9:.0f}B" if mc else "  N/A"
        print(
            f"{i:<3} {r['ticker']:<8} {r['name'][:27]:<28} {r['sector'][:21]:<22}"
            f" {r['score']:>6.1f} {upside:>7} {w52:>6} {rpe:>6} {mcap:>7}"
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
    ap.add_argument("--min-market-cap", type=float, default=10.0, metavar="B",
                    help="Min market cap in billions (default 10 = $10B+; use 0 for no filter)")
    ap.add_argument("--sp100", action="store_true",
                    help="Use S&P 100 instead of S&P 500 (~3 min, for daily automation)")
    ap.add_argument("--limit", type=int, default=None, metavar="N",
                    help="Only check first N tickers (for testing)")
    ap.add_argument("--output", type=str, default=None, metavar="PATH",
                    help="Save results as JSON to PATH (e.g. docs/screen-2026-05-04.json)")
    args = ap.parse_args()

    rows = screen(
        top_n=args.top,
        min_upside=args.min_upside,
        max_week52_pos=args.max_52w_pos,
        max_rel_pe=args.max_rel_pe,
        min_market_cap_b=args.min_market_cap,
        limit=args.limit,
        use_sp100=args.sp100,
    )
    _print_results(rows)

    if args.output:
        payload = {
            "date": str(date.today()),
            "filters": {
                "top_n": args.top,
                "min_upside_pct": args.min_upside,
                "max_week52_pos_pct": args.max_52w_pos,
                "max_rel_pe": args.max_rel_pe,
                "min_market_cap_b": args.min_market_cap,
            },
            "candidates": rows,
        }
        with open(args.output, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        print(f"Saved → {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
