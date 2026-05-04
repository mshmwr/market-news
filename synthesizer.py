from __future__ import annotations

import json
import os

from openai import OpenAI
from pydantic import ValidationError

from models import SignalBundle, SignalResult
from valuation import compute_undervaluation

SYSTEM_PROMPT = """You are a quantitative financial analyst. You will be given a JSON object containing four signal layers for a stock ticker:
- news: recent news articles mentioning the ticker
- technical: RSI, MACD, MA50, volume ratio computed from 6 months of daily price data
- fundamentals: PE ratio, forward PE, P/B ratio, revenue growth, profit margin, debt-to-equity, analyst target price, current price, 52-week range, EPS, book value, analyst recommendation (strong buy/buy/hold/underperform/sell) and opinion count (null means unavailable, e.g. for ETFs/indices)
- social: Reddit post sentiment (available=false means data was unavailable)

Analyst rating guidance:
- recommendation_key "strong buy" or "buy" with number_of_analyst_opinions >= 5: strong bullish institutional consensus — raise confidence by ~10 points when aligned with other signals
- recommendation_key "sell" or "underperform": institutional bearish signal — factor into SELL or lower-confidence HOLD
- recommendation_key alone without corroboration from technical/news: insufficient; do not override other signals

Undervaluation signals to weigh:
- upside_pct > 15%: analyst consensus sees meaningful upside
- week52_position_pct < 30%: price near 52-week low (potential value or distress)
- price_vs_graham_pct < 0%: price below Graham Number (classic value signal)
- forward_pe significantly below trailing_pe: earnings growth expected
- relative_pe < 0.8: trading at a meaningful discount to sector peers — bullish value signal when combined with other positives
- relative_pe > 1.2: premium to sector peers — factor in as headwind for BUY calls; not bearish alone

Analyze all available signals and produce a synthesized recommendation.
Respond with ONLY a valid JSON object — no markdown fences, no prose, no explanation outside the JSON:
{"signal": "BUY" | "HOLD" | "SELL", "confidence": <integer 0-100>, "rationale": "<one to three sentences>"}"""


def _make_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["NVIDIA_API_KEY"],
        base_url="https://integrate.api.nvidia.com/v1",
    )


def synthesize(
    ticker: str,
    bundle: SignalBundle,
    client: OpenAI | None = None,
) -> SignalResult:
    if client is None:
        client = _make_client()

    uv = compute_undervaluation(bundle)
    bundle_dict = bundle.model_dump()
    if uv:
        bundle_dict["undervaluation"] = uv
    user_message = json.dumps(bundle_dict, indent=2, ensure_ascii=False)

    response = client.chat.completions.create(
        model="minimaxai/minimax-m2.7",
        max_tokens=8192,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )

    raw = response.choices[0].message.content.strip()

    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

    try:
        data = json.loads(raw)
        sources = [
            {"title": a.get("title", ""), "url": a.get("link", ""), "published_ts": a.get("published_ts")}
            for a in bundle.news.articles
            if a.get("link")
        ]
        social_posts = [
            {"title": p.get("title", ""), "url": p.get("url", "")}
            for p in (bundle.social.posts[:5] if bundle.social.available else [])
            if p.get("url")
        ]
        tech = {k: v for k, v in bundle.technical.model_dump().items() if k != "ticker"}
        fund = {k: v for k, v in bundle.fundamentals.model_dump().items() if k != "ticker"}
        return SignalResult(
            ticker=ticker, sources=sources, social_posts=social_posts,
            technical_data=tech, fundamentals_data=fund,
            undervaluation_data=uv or None,
            **data
        )
    except (json.JSONDecodeError, ValueError, KeyError, ValidationError) as exc:
        raise ValueError(
            f"synthesize: malformed NIM response for {ticker!r}: {exc!r} | raw={raw!r}"
        ) from exc
