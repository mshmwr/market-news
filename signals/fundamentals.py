import yfinance as yf

from models import FundamentalsSignal


def fetch_fundamentals_signal(ticker: str) -> FundamentalsSignal:
    try:
        info = yf.Ticker(ticker).info
        return FundamentalsSignal(
            pe_ratio=info.get("trailingPE"),
            revenue_growth=info.get("revenueGrowth"),
            profit_margin=info.get("profitMargins"),
            debt_to_equity=info.get("debtToEquity"),
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
