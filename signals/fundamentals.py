import yfinance as yf

from models import FundamentalsSignal


def fetch_fundamentals_signal(ticker: str) -> FundamentalsSignal:
    try:
        info = yf.Ticker(ticker).info
        return FundamentalsSignal(
            pe_ratio=info.get("trailingPE"),
            forward_pe=info.get("forwardPE"),
            price_to_book=info.get("priceToBook"),
            revenue_growth=info.get("revenueGrowth"),
            profit_margin=info.get("profitMargins"),
            debt_to_equity=info.get("debtToEquity"),
            target_mean_price=info.get("targetMeanPrice"),
            current_price=info.get("currentPrice") or info.get("regularMarketPrice"),
            fifty_two_week_low=info.get("fiftyTwoWeekLow"),
            fifty_two_week_high=info.get("fiftyTwoWeekHigh"),
            trailing_eps=info.get("trailingEps"),
            book_value=info.get("bookValue"),
            ticker=ticker,
        )
    except Exception:
        return FundamentalsSignal(
            pe_ratio=None,
            revenue_growth=None,
            profit_margin=None,
            debt_to_equity=None,
            ticker=ticker,
        )
