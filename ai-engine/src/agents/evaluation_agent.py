from src.evaluation.engine import EvaluationEngine
from src.graph.state import ResearchState
from src.models.backtest import BacktestResult
from src.models.evaluation import EvaluationResult
from src.models.risk import RiskResult


class EvaluationAgent:
    """Decide whether a completed strategy meets objective acceptance checks."""

    def __init__(self, engine: EvaluationEngine | None = None):
        self.engine = engine or EvaluationEngine()

    def __call__(self, state: ResearchState) -> dict:
        try:
            if not state.get("backtest"):
                raise ValueError("Backtest result is required before evaluation")
            if not state.get("risk"):
                raise ValueError("Risk result is required before evaluation")

            backtest = BacktestResult.model_validate(state["backtest"])
            risk = RiskResult.model_validate(state["risk"])
            result: EvaluationResult = self.engine.evaluate(backtest, risk)
            return {
                "evaluation": result.model_dump(mode="json"),
                "status": "EVALUATION_READY",
                "current_agent": "evaluation",
                "errors": [],
            }
        except Exception as exc:
            return {
                "status": "FAILED",
                "current_agent": "evaluation",
                "errors": [f"Evaluation Agent failed: {exc}"],
            }
