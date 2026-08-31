from datetime import date
import math

import pandas as pd

from src.market.provider import MarketDataProvider, YahooFinanceProvider
from src.models.market_data import MarketObservation, SymbolMarketData
from src.quant.features import add_quant_features


class MarketDataService:
    def __init__(self, provider: MarketDataProvider | None = None):
        self.provider = provider or YahooFinanceProvider()

    def get_symbol_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        volatility_window: int = 20,
        momentum_window: int = 20,
    ) -> SymbolMarketData:
        raw = self.provider.download(symbol, start_date, end_date)
        enriched = add_quant_features(
            raw,
            volatility_window=volatility_window,
            momentum_window=momentum_window,
        )
        return SymbolMarketData(
            symbol=symbol,
            observations=self._to_observations(enriched),
        )

    @staticmethod
    def _safe_float(value) -> float | None:
        if value is None or pd.isna(value):
            return None
        number = float(value)
        if not math.isfinite(number):
            return None
        return number

    def _to_observations(self, frame: pd.DataFrame) -> list[MarketObservation]:
        result: list[MarketObservation] = []
        for timestamp, row in frame.iterrows():
            result.append(
                MarketObservation(
                    date=timestamp.date(),
                    open=self._safe_float(row.get("Open")),
                    high=self._safe_float(row.get("High")),
                    low=self._safe_float(row.get("Low")),
                    close=self._safe_float(row.get("Close")),
                    volume=self._safe_float(row.get("Volume")),
                    simple_return=self._safe_float(row.get("simple_return")),
                    log_return=self._safe_float(row.get("log_return")),
                    volatility=self._safe_float(row.get("volatility")),
                    momentum=self._safe_float(row.get("momentum")),
                    sma_20=self._safe_float(row.get("sma_20")),
                    sma_50=self._safe_float(row.get("sma_50")),
                )
            )
        return result
