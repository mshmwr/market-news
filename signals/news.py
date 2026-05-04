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
    "ASML": "ASML",
    "MU": "Micron",
    "SNDK": "SanDisk",
    "LWLG": "Lightwave Logic",
    "LITE": "Lumentum",
    "PLTR": "Palantir",
    "CRWD": "CrowdStrike",
    "ONDS": "Ondas",
    "NOK": "Nokia",
    "TSM": "TSMC",
    "2308.TW": "台達電",
    "2454.TW": "聯發科",
    "2330": "台積電",
    "2317": "鴻海",
    "2454": "聯發科",
}


def _allowed_feed_cats(ticker: str) -> set[str]:
    """Restrict which RSS feed categories a ticker may pull from."""
    if ticker.endswith(".TW") or ticker in {"2330", "2317", "2454"}:
        return {"台股", "宏觀"}
    if "-USD" in ticker:
        return {"加密貨幣"}
    return {"美股", "宏觀"}


def fetch_news_signal(ticker: str) -> NewsSignal:
    tokens = [ticker.lower()]
    company = TICKER_COMPANY.get(ticker)
    if company:
        tokens.append(company.lower())

    allowed_cats = _allowed_feed_cats(ticker)
    articles = fetch_all()
    filtered = [
        a for a in articles
        if a.get("category") in allowed_cats
        and any(
            t in a.get("title", "").lower() or
            t in (a.get("description") or "").lower()
            for t in tokens
        )
    ]
    return NewsSignal(articles=filtered, ticker=ticker)
