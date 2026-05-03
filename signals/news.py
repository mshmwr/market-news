from fetch_news import fetch_all
from models import NewsSignal

TICKER_COMPANY: dict[str, str] = {
    "TSLA": "Tesla",
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "NVDA": "NVIDIA",
    "AMZN": "Amazon",
    "GOOGL": "Google",
    "META": "Meta",
    "NFLX": "Netflix",
    "AMD": "AMD",
    "INTC": "Intel",
    "2330": "台積電",
    "2317": "鴻海",
    "2454": "聯發科",
}


def fetch_news_signal(ticker: str) -> NewsSignal:
    tokens = [ticker.lower()]
    company = TICKER_COMPANY.get(ticker)
    if company:
        tokens.append(company.lower())

    articles = fetch_all()
    filtered = [
        a for a in articles
        if any(
            t in a.get("title", "").lower() or
            t in (a.get("description") or "").lower()
            for t in tokens
        )
    ]
    return NewsSignal(articles=filtered, ticker=ticker)
