from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class NewsSignal(BaseModel):
    articles: list[dict]
    ticker: str


class TechnicalSignal(BaseModel):
    rsi: Optional[float]
    macd_line: Optional[float]
    macd_signal: Optional[float]
    macd_histogram: Optional[float]
    ma50: Optional[float]
    volume_ratio: Optional[float]
    ticker: str


class FundamentalsSignal(BaseModel):
    pe_ratio: Optional[float]
    revenue_growth: Optional[float]
    profit_margin: Optional[float]
    debt_to_equity: Optional[float]
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
