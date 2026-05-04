"""Shared valuation constants and computation — no heavy dependencies."""
from __future__ import annotations

import math

from models import SignalBundle

SECTOR_PE_BENCHMARK: dict[str, float] = {
    "Technology": 28.0,
    "Communication Services": 22.0,
    "Consumer Cyclical": 20.0,
    "Consumer Defensive": 18.0,
    "Healthcare": 22.0,
    "Financial Services": 14.0,
    "Industrials": 18.0,
    "Basic Materials": 15.0,
    "Energy": 12.0,
    "Real Estate": 35.0,
    "Utilities": 17.0,
}


def compute_undervaluation(bundle: SignalBundle) -> dict:
    f = bundle.fundamentals
    uv: dict = {}

    price = f.current_price
    if price and f.target_mean_price:
        uv["upside_pct"] = round((f.target_mean_price - price) / price * 100, 1)

    lo, hi = f.fifty_two_week_low, f.fifty_two_week_high
    if price and lo and hi and hi > lo:
        uv["week52_position_pct"] = round((price - lo) / (hi - lo) * 100, 1)

    eps, bv = f.trailing_eps, f.book_value
    if eps and bv and eps > 0 and bv > 0:
        graham = math.sqrt(22.5 * eps * bv)
        uv["graham_number"] = round(graham, 2)
        if price:
            uv["price_vs_graham_pct"] = round((price - graham) / graham * 100, 1)

    sector_avg = SECTOR_PE_BENCHMARK.get(f.sector or "")
    if f.pe_ratio and f.pe_ratio > 0 and sector_avg:
        uv["relative_pe"] = round(f.pe_ratio / sector_avg, 2)
        uv["sector_pe_avg"] = sector_avg

    return uv
