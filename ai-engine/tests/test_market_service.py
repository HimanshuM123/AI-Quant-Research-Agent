from datetime import date
import pandas as pd

from src.market.service import MarketDataService


class FakeProvider:
    def download(self, symbol, start_date, end_date):
        idx = pd.date_range("2025-01-01", periods=60, freq="D")
        close = [100.0 + i for i in range(60)]
        return pd.DataFrame(
            {
                "Open": close,
                "High": [v + 1 for v in close],
                "Low": [v - 1 for v in close],
                "Close": close,
                "Volume": [1000] * 60,
            },
            index=idx,
        )


def test_market_service_returns_serializable_observations():
    service = MarketDataService(provider=FakeProvider())
    result = service.get_symbol_data(
        "AAPL",
        date(2025, 1, 1),
        date(2025, 3, 1),
    )

    assert result.symbol == "AAPL"
    assert len(result.observations) == 60
    assert result.observations[-1].close == 159.0
    assert result.observations[-1].momentum is not None
