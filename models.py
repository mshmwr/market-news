from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class NewsSignal(BaseModel):
    articles: list[dict]
    ticker: str


class TechnicalSignal(BaseModel):
    rsi: float | None
    macd_line: float | None
    macd_signal: float | None
    macd_histogram: float | None
    ma50: float | None
    volume_ratio: float | None
    ticker: str


class FundamentalsSignal(BaseModel):
    pe_ratio: float | None
    revenue_growth: float | None
    profit_margin: float | None
    debt_to_equity: float | None
    ticker: str


class SocialSignal(BaseModel):
    posts: list[dict]
    ticker: str
    available: bool


class SignalBundle(BaseModel):
    news: NewsSignal
    technical: TechnicalSignal
    fundamentals: FundamentalsSignal
    social: SocialSignal


class SignalResult(BaseModel):
    signal: Literal["BUY", "HOLD", "SELL"]
    confidence: int = Field(ge=0, le=100)
    rationale: str
    ticker: str
    sources: list[dict] = []
    social_posts: list[dict] = []
    technical_data: dict | None = None
    fundamentals_data: dict | None = None
