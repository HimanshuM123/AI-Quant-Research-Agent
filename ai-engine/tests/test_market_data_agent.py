from datetime import date

import pandas as pd

from src.agents.market_data_agent import MarketDataAgent
from src.market.service import MarketDataService
from src.tools.market_data import MarketDataTool


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


def test_market_data_agent_updates_research_state():
    service = MarketDataService(provider=FakeProvider())
    agent = MarketDataAgent(MarketDataTool(service))

    update = agent(
        {
            "symbols": ["AAPL", "MSFT"],
            "start_date": date(2025, 1, 1).isoformat(),
            "end_date": date(2025, 3, 1).isoformat(),
            "volatility_window": 20,
            "momentum_window": 20,
        }
    )

    assert update["status"] == "MARKET_DATA_READY"
    assert update["errors"] == []
    assert update["market_data"]["symbols"]["AAPL"]["observation_count"] == 60
    assert update["market_data"]["symbols"]["MSFT"]["latest"]["close"] == 159.0
