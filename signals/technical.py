from __future__ import annotations

import yfinance as yf
import pandas as pd

from models import TechnicalSignal


def _none_signal(ticker: str) -> TechnicalSignal:
    return TechnicalSignal(
        rsi=None,
        macd_line=None,
        macd_signal=None,
        macd_histogram=None,
        ma50=None,
        volume_ratio=None,
        ticker=ticker,
    )


def _compute_rsi(close: pd.Series, period: int = 14) -> float | None:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    last = rsi.iloc[-1]
    return float(last) if pd.notna(last) else None


def _compute_macd(
    close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple[float | None, float | None, float | None]:
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    macd_signal_series = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - macd_signal_series

    def _last(s: pd.Series) -> float | None:
        v = s.iloc[-1]
        return float(v) if pd.notna(v) else None

    return _last(macd_line), _last(macd_signal_series), _last(histogram)


def fetch_technical_signal(ticker: str) -> TechnicalSignal:
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False, auto_adjust=True)
        if df.empty:
            return _none_signal(ticker)

        close = df["Close"].squeeze()
        volume = df["Volume"].squeeze()

        rsi = _compute_rsi(close)
        macd_line, macd_signal, macd_histogram = _compute_macd(close)

        ma50_raw = close.rolling(50).mean().iloc[-1]
        ma50 = float(ma50_raw) if pd.notna(ma50_raw) else None

        vol_avg_20 = volume.rolling(20).mean().iloc[-1]
        vol_latest = volume.iloc[-1]
        if pd.notna(vol_avg_20) and vol_avg_20 != 0:
            volume_ratio = float(vol_latest / vol_avg_20)
        else:
            volume_ratio = None

        return TechnicalSignal(
            rsi=rsi,
            macd_line=macd_line,
            macd_signal=macd_signal,
            macd_histogram=macd_histogram,
            ma50=ma50,
            volume_ratio=volume_ratio,
            ticker=ticker,
        )
    except Exception:
        return _none_signal(ticker)
