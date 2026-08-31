from src.backtesting.engine import BacktestEngine
from src.graph.state import ResearchState
from src.models.strategy import StrategySpec


class BacktestAgent:
    """Execute a validated strategy with deterministic market arithmetic."""

    def __init__(self, engine: BacktestEngine | None = None):
        self.engine = engine or BacktestEngine()

    def __call__(self, state: ResearchState) -> dict:
        try:
            if not state.get("strategy"):
                raise ValueError("Strategy is required before backtesting")
            if not state.get("market_data"):
                raise ValueError("Market data is required before backtesting")
            strategy = StrategySpec.model_validate(state["strategy"])
            result = self.engine.run(
                strategy=strategy,
                market_data=state["market_data"],
                slippage_bps=float(state.get("slippage_bps", 2.0)),
                initial_capital=float(state.get("initial_capital", 100_000.0)),
            )
            return {
                "backtest": result.model_dump(mode="json"),
                "status": "BACKTEST_READY",
                "current_agent": "backtest",
                "errors": [],
            }
        except Exception as exc:
            return {
                "status": "FAILED",
                "current_agent": "backtest",
                "errors": [f"Backtest Agent failed: {exc}"],
            }
