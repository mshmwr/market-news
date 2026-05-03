from __future__ import annotations

import json
from typing import Optional

import anthropic

from models import SignalBundle, SignalResult

SYSTEM_PROMPT = """You are a quantitative financial analyst. You will be given a JSON object containing four signal layers for a stock ticker:
- news: recent news articles mentioning the ticker
- technical: RSI, MACD, MA50, volume ratio computed from 6 months of daily price data
- fundamentals: PE ratio, revenue growth, profit margin, debt-to-equity
- social: Reddit post sentiment (available=false means data was unavailable)

Analyze all available signals and produce a synthesized recommendation.
Respond with ONLY a valid JSON object — no markdown fences, no prose, no explanation outside the JSON:
{"signal": "BUY" | "HOLD" | "SELL", "confidence": <integer 0-100>, "rationale": "<one to three sentences>"}"""


def synthesize(
    ticker: str,
    bundle: SignalBundle,
    client: Optional[anthropic.Anthropic] = None,
) -> SignalResult:
    if client is None:
        client = anthropic.Anthropic()

    user_message = bundle.model_dump_json(indent=2)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip()

    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

    try:
        data = json.loads(raw)
        return SignalResult(ticker=ticker, **data)
    except (json.JSONDecodeError, ValueError, KeyError) as exc:
        raise ValueError(
            f"synthesize: malformed Claude response for {ticker!r}: {exc!r} | raw={raw!r}"
        ) from exc
