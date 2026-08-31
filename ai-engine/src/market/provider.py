from datetime import date
from typing import Protocol

import pandas as pd


class MarketDataProvider(Protocol):
    def download(self, symbol: str, start_date: date, end_date: date) -> pd.DataFrame:
        ...


class YahooFinanceProvider:
    def download(self, symbol: str, start_date: date, end_date: date) -> pd.DataFrame:
        # Lazy import keeps the domain/service layer testable without requiring
        # an external market-data dependency during unit-test collection.
        try:
            import yfinance as yf
        except ImportError as exc:
            raise RuntimeError(
                "yfinance is not installed. Run: pip install -r requirements.txt"
            ) from exc

        frame = yf.download(
            symbol,
            start=start_date.isoformat(),
            end=end_date.isoformat(),
            auto_adjust=True,
            progress=False,
            threads=False,
        )

        if frame.empty:
            raise ValueError(f"No market data returned for symbol={symbol}")

        if isinstance(frame.columns, pd.MultiIndex):
            frame.columns = frame.columns.get_level_values(0)

        return frame
