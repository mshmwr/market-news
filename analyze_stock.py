import argparse
import datetime
import json
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


def _bundle_path(directory: str, ticker: str) -> str:
    safe = ticker.replace("/", "_").replace("^", "_")
    return os.path.join(directory, f"{safe}.json")


def _save_bundle(bundle: SignalBundle, ticker: str, directory: str) -> None:
    os.makedirs(directory, exist_ok=True)
    path = _bundle_path(directory, ticker)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(bundle.model_dump_json(indent=2))
    print(f"[bundle] Saved {ticker} → {path}")


def _load_bundle(ticker: str, directory: str) -> SignalBundle | None:
    path = _bundle_path(directory, ticker)
    try:
        with open(path, encoding="utf-8") as fh:
            return SignalBundle.model_validate_json(fh.read())
    except FileNotFoundError:
        return None


def analyze_ticker(ticker: str, bundle: SignalBundle | None = None) -> SignalResult:
    if bundle is None:
        bundle = SignalBundle(
            news=fetch_news_signal(ticker),
            technical=fetch_technical_signal(ticker),
            fundamentals=fetch_fundamentals_signal(ticker),
            social=fetch_social_signal(ticker),
        )
    return synthesize(ticker, bundle)


def _write_signals_json(path: str, results: list[SignalResult]) -> None:
    """Merge new results into existing signals.json, replacing matching tickers."""
    existing: dict[str, dict] = {}
    try:
        with open(path, encoding="utf-8") as fh:
            existing = {s["ticker"]: s for s in json.load(fh).get("signals", [])}
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        pass

    for r in results:
        existing[r.ticker] = r.model_dump()

    payload = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "signals": list(existing.values()),
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print(f"[signals] Written {len(existing)} signal(s) to {path} ({len(results)} updated)")


def main(
    tickers: list[str],
    output_json: str | None = None,
    save_bundles: str | None = None,
    load_bundles: str | None = None,
) -> int:
    successful_results: list[SignalResult] = []
    failed: list[str] = []
    for ticker in tickers:
        print(f"\n{'=' * 40}")
        print(f"=== {ticker} ===")
        print(f"{'=' * 40}")
        try:
            bundle = _load_bundle(ticker, load_bundles) if load_bundles else None
            if bundle:
                print(f"[bundle] Loaded {ticker} from cache")
            else:
                bundle = SignalBundle(
                    news=fetch_news_signal(ticker),
                    technical=fetch_technical_signal(ticker),
                    fundamentals=fetch_fundamentals_signal(ticker),
                    social=fetch_social_signal(ticker),
                )
                if save_bundles:
                    _save_bundle(bundle, ticker, save_bundles)
            result = analyze_ticker(ticker, bundle=bundle)
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
    parser.add_argument("--save-bundles", metavar="DIR", default=None,
                        help="Save raw signal bundles to DIR/<TICKER>.json after fetching")
    parser.add_argument("--load-bundles", metavar="DIR", default=None,
                        help="Load raw signal bundles from DIR/<TICKER>.json, skip fetching")
    args = parser.parse_args()
    sys.exit(main(args.tickers, output_json=args.output_json,
                  save_bundles=args.save_bundles, load_bundles=args.load_bundles))
