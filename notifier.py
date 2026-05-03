import os
import sys

import requests

from models import SignalResult

_COLORS = {
    "BUY": "\033[92m",
    "HOLD": "\033[93m",
    "SELL": "\033[91m",
}
_RESET = "\033[0m"


def notify_console(result: SignalResult) -> None:
    color = _COLORS.get(result.signal, "")
    print(
        f"[{result.ticker}] {color}{result.signal}{_RESET} "
        f"(confidence: {result.confidence}%)\n"
        f"  {result.rationale}"
    )


def notify_telegram(result: SignalResult) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not (token and chat_id):
        return

    text = (
        f"[{result.ticker}] {result.signal} "
        f"(confidence: {result.confidence}%)\n{result.rationale}"
    )
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": text},
            timeout=10,
        )
    except requests.RequestException as exc:
        print(f"WARNING: Telegram notification failed: {exc}", file=sys.stderr)
