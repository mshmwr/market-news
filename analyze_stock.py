import os
import sys
from dotenv import load_dotenv

load_dotenv()

from models import SignalBundle, SignalResult
from synthesizer import synthesize
from notifier import notify_console, notify_telegram
from signals.news import fetch_news_signal
from signals.technical import fetch_technical_signal
from signals.fundamentals import fetch_fundamentals_signal
from signals.social import fetch_social_signal


def analyze_ticker(ticker: str) -> SignalResult:
    news = fetch_news_signal(ticker)
    technical = fetch_technical_signal(ticker)
    fundamentals = fetch_fundamentals_signal(ticker)
    social = fetch_social_signal(ticker)
    bundle = SignalBundle(
        news=news,
        technical=technical,
        fundamentals=fundamentals,
        social=social,
    )
    return synthesize(ticker, bundle)


def main(tickers: list[str]) -> int:
    failed: list[str] = []
    for ticker in tickers:
        print(f"\n{'=' * 40}")
        print(f"=== {ticker} ===")
        print(f"{'=' * 40}")
        try:
            result = analyze_ticker(ticker)
            notify_console(result)
            notify_telegram(result)
        except Exception as exc:
            print(f"ERROR [{ticker}]: {exc}")
            failed.append(ticker)

    return 1 if len(failed) == len(tickers) else 0


if __name__ == "__main__":
    tickers = sys.argv[1:]
    if not tickers:
        print("Usage: python3 analyze_stock.py <TICKER> [<TICKER> ...]", file=sys.stderr)
        sys.exit(1)
    sys.exit(main(tickers))
