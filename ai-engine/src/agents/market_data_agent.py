from src.graph.state import ResearchState
from src.tools.market_data import MarketDataTool


class MarketDataAgent:
    """LangGraph node responsible for obtaining and validating market context."""

    def __init__(self, tool: MarketDataTool | None = None):
        self.tool = tool or MarketDataTool()

    def __call__(self, state: ResearchState) -> dict:
        try:
            market_data = self.tool.run(
                symbols=state["symbols"],
                start_date=state["start_date"],
                end_date=state["end_date"],
                volatility_window=state.get("volatility_window", 20),
                momentum_window=state.get("momentum_window", 20),
            )
            return {
                "market_data": market_data,
                "status": "MARKET_DATA_READY",
                "current_agent": "market_data",
                "errors": [],
            }
        except Exception as exc:
            return {
                "status": "FAILED",
                "current_agent": "market_data",
                "errors": [f"Market Data Agent failed: {exc}"],
            }
