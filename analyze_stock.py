import argparse
import datetime
import json
import sys
import time
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


def _write_signals_json(path: str, results: list[SignalResult]) -> None:
    """Write signals to a JSON file with envelope {generated_at, signals}."""
    payload = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "signals": [r.model_dump() for r in results],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print(f"[signals] Written {len(results)} signal(s) to {path}")


def main(tickers: list[str], output_json: str | None = None) -> int:
    successful_results: list[SignalResult] = []
    failed: list[str] = []
    for i, ticker in enumerate(tickers):
        if i > 0:
            time.sleep(13)  # Gemini free tier: 5 req/min
        print(f"\n{'=' * 40}")
        print(f"=== {ticker} ===")
        print(f"{'=' * 40}")
        try:
            result = analyze_ticker(ticker)
            notify_console(result)
            notify_telegram(result)
            successful_results.append(result)
        except Exception as exc:
            print(f"ERROR [{ticker}]: {exc}")
            failed.append(ticker)

    if output_json is not None and successful_results:
        _write_signals_json(output_json, successful_results)

    return 1 if len(failed) == len(tickers) else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze stock tickers and output signals.")
    parser.add_argument("tickers", nargs="+", metavar="TICKER")
    parser.add_argument("--output-json", metavar="PATH", default=None,
                        help="Write signals.json to this path")
    args = parser.parse_args()
    sys.exit(main(args.tickers, output_json=args.output_json))
