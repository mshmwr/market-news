from __future__ import annotations

import json
import os

from openai import OpenAI
from pydantic import ValidationError

from models import SignalBundle, SignalResult

SYSTEM_PROMPT = """You are a quantitative financial analyst. You will be given a JSON object containing four signal layers for a stock ticker:
- news: recent news articles mentioning the ticker
- technical: RSI, MACD, MA50, volume ratio computed from 6 months of daily price data
- fundamentals: PE ratio, revenue growth, profit margin, debt-to-equity (null means unavailable, e.g. for ETFs/indices)
- social: Reddit post sentiment (available=false means data was unavailable)

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

    user_message = bundle.model_dump_json(indent=2)

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
            {"title": a.get("title", ""), "url": a.get("link", "")}
            for a in bundle.news.articles
            if a.get("link")
        ]
        return SignalResult(ticker=ticker, sources=sources, **data)
    except (json.JSONDecodeError, ValueError, KeyError, ValidationError) as exc:
        raise ValueError(
            f"synthesize: malformed NIM response for {ticker!r}: {exc!r} | raw={raw!r}"
        ) from exc
