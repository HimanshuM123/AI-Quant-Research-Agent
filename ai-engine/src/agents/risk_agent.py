from src.graph.state import ResearchState
from src.models.backtest import BacktestResult
from src.risk.engine import RiskEngine


class RiskAgent:
    """Calculate deterministic risk metrics from completed backtest results."""

    def __init__(self, engine: RiskEngine | None = None):
        self.engine = engine or RiskEngine()

    def __call__(self, state: ResearchState) -> dict:
        try:
            if not state.get("backtest"):
                raise ValueError("Backtest result is required before risk analysis")
            backtest = BacktestResult.model_validate(state["backtest"])
            result = self.engine.calculate(
                backtest,
                annual_risk_free_rate=float(state.get("annual_risk_free_rate", 0.0)),
                var_confidence=float(state.get("var_confidence", 0.95)),
            )
            return {
                "risk": result.model_dump(mode="json"),
                "status": "RISK_READY",
                "current_agent": "risk",
                "errors": [],
            }
        except Exception as exc:
            return {
                "status": "FAILED",
                "current_agent": "risk",
                "errors": [f"Risk Agent failed: {exc}"],
            }
