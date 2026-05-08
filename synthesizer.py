from __future__ import annotations

import json
import os

from openai import OpenAI
from pydantic import ValidationError

from models import SignalBundle, SignalResult
from valuation import compute_undervaluation

SIGNAL_DATA_DESCRIPTION = """Signal layers:
- news: recent news articles mentioning the ticker
- technical: RSI, MACD, MA50, volume ratio (6 months daily price data)
- fundamentals: PE/forward PE/PB, revenue growth, profit margin, debt-to-equity, analyst target, current price, 52-week range, EPS, book value, recommendation_key (strong buy/buy/hold/underperform/sell), opinion count, PEG ratio
- social: Reddit post sentiment (available=false means unavailable)
- undervaluation (computed): upside_pct, week52_position_pct, graham_number, price_vs_graham_pct, relative_pe, peg_ratio"""

BULL_PROMPT = f"""You are a bullish equity analyst. Given four-layer signal data for a stock, argue the strongest case for BUY.

{SIGNAL_DATA_DESCRIPTION}

Find the bullish thread even if signals are mixed. Cite specific numbers (e.g. "RSI 28 oversold", "upside_pct 22%", "PEG 0.7").
Output 2-3 sentences. No hedging words ('but', 'however', 'although', 'while'). No JSON. Plain prose only."""

BEAR_PROMPT = f"""You are a bearish equity analyst. Given four-layer signal data for a stock, argue the strongest case for SELL.

{SIGNAL_DATA_DESCRIPTION}

Find the bearish thread even if signals are mostly positive. Cite specific numbers (e.g. "RSI 75 overbought", "relative_pe 1.4x sector", "week52_position 92%").
Output 2-3 sentences. No hedging words ('but', 'however', 'although', 'while'). No JSON. Plain prose only."""

JUDGE_PROMPT = """You are a senior portfolio manager weighing arguments from a bull and a bear analyst on a stock.
You do NOT see the raw signal data — only the two analyst arguments.

Decision rules:
- Bull case significantly stronger and well-supported with numbers → BUY
- Bear case significantly stronger → SELL
- Both well-supported with similar weight, OR both weak → HOLD
- Confidence reflects argument asymmetry: 80+ when one side dominates, 50-65 when balanced

Respond with ONLY a valid JSON object — no markdown fences, no prose outside JSON:
{"signal": "BUY" | "HOLD" | "SELL", "confidence": <integer 0-100>, "rationale": "<1-2 sentences citing which argument won and why>"}"""


def _make_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["NVIDIA_API_KEY"],
        base_url="https://integrate.api.nvidia.com/v1",
    )


def _call_llm(client: OpenAI, system: str, user: str) -> str:
    response = client.chat.completions.create(
        model="minimaxai/minimax-m2.7",
        max_tokens=8192,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content.strip()


def _strip_fences(raw: str) -> str:
    if raw.startswith("```"):
        lines = raw.split("\n")
        return "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
    return raw


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
    signal_data = json.dumps(bundle_dict, indent=2, ensure_ascii=False)
    debate_input = f"Ticker: {ticker}\n\nSignals:\n{signal_data}"

    bull_case = _call_llm(client, BULL_PROMPT, debate_input)
    bear_case = _call_llm(client, BEAR_PROMPT, debate_input)

    judge_input = (
        f"Ticker: {ticker}\n\n"
        f"Bull analyst argues:\n{bull_case}\n\n"
        f"Bear analyst argues:\n{bear_case}"
    )
    judge_raw = _strip_fences(_call_llm(client, JUDGE_PROMPT, judge_input))

    try:
        data = json.loads(judge_raw)
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
            ticker=ticker, name=bundle.fundamentals.short_name,
            bull_case=bull_case, bear_case=bear_case,
            sources=sources, social_posts=social_posts,
            technical_data=tech, fundamentals_data=fund,
            undervaluation_data=uv or None,
            **data
        )
    except (json.JSONDecodeError, ValueError, KeyError, ValidationError) as exc:
        raise ValueError(
            f"synthesize: malformed NIM judge response for {ticker!r}: {exc!r} | raw={judge_raw!r}"
        ) from exc
