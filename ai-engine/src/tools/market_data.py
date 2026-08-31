from datetime import date
from typing import Any

from src.market.service import MarketDataService


class MarketDataTool:
    """Deterministic tool exposed to the Market Data Agent.

    The agent/orchestrator never performs financial calculations itself. It
    delegates retrieval and feature generation to ``MarketDataService``.
    """

    def __init__(self, service: MarketDataService | None = None):
        self.service = service or MarketDataService()

    def run(
        self,
        *,
        symbols: list[str],
        start_date: str,
        end_date: str,
        volatility_window: int,
        momentum_window: int,
    ) -> dict[str, Any]:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)

        symbol_results: dict[str, Any] = {}
        for symbol in symbols:
            result = self.service.get_symbol_data(
                symbol=symbol,
                start_date=start,
                end_date=end,
                volatility_window=volatility_window,
                momentum_window=momentum_window,
            )
            symbol_results[symbol] = self._serialize_symbol(result)

        return {
            "provider": type(self.service.provider).__name__,
            "symbols": symbol_results,
        }

    @staticmethod
    def _serialize_symbol(result) -> dict[str, Any]:
        observations = [item.model_dump(mode="json") for item in result.observations]
        latest = result.observations[-1] if result.observations else None

        return {
            "symbol": result.symbol,
            "observation_count": len(result.observations),
            "first_date": result.observations[0].date.isoformat() if result.observations else None,
            "last_date": latest.date.isoformat() if latest else None,
            "latest": latest.model_dump(mode="json") if latest else None,
            "observations": observations,
        }
