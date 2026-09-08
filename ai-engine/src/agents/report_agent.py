from src.graph.state import ResearchState
from src.models.backtest import BacktestResult
from src.models.evaluation import EvaluationResult
from src.models.report import ResearchReport
from src.models.risk import RiskResult
from src.models.strategy import StrategySpec


class ReportAgent:
    """Build a concise deterministic report from the completed workflow state."""

    def __call__(self, state: ResearchState) -> dict:
        try:
            required = ("strategy", "backtest", "risk", "evaluation")
            missing = [name for name in required if not state.get(name)]
            if missing:
                raise ValueError(f"Missing workflow results before reporting: {', '.join(missing)}")

            strategy = StrategySpec.model_validate(state["strategy"])
            backtest = BacktestResult.model_validate(state["backtest"])
            risk = RiskResult.model_validate(state["risk"])
            evaluation = EvaluationResult.model_validate(state["evaluation"])
            decision = evaluation.decision
            report = ResearchReport(
                title=f"{strategy.name} research report",
                decision=decision,
                executive_summary=(
                    f"The {strategy.name} strategy for {', '.join(strategy.assets)} was "
                    f"{decision.lower()} after backtesting and risk evaluation. "
                    f"It returned {backtest.total_return:.2%} versus "
                    f"{backtest.benchmark_return:.2%} for the benchmark, with a "
                    f"maximum drawdown of {abs(risk.metrics.max_drawdown):.2%}."
                ),
                key_findings=[
                    f"CAGR: {risk.metrics.cagr:.2%}",
                    f"Sharpe ratio: {risk.metrics.sharpe_ratio:.2f}"
                    if risk.metrics.sharpe_ratio is not None
                    else "Sharpe ratio: unavailable",
                    f"Expected shortfall: {risk.metrics.expected_shortfall:.2%}",
                    f"Trades: {len(backtest.trades)}",
                    f"Evaluation score: {evaluation.score:.2f}",
                ],
                strengths=evaluation.strengths,
                weaknesses=evaluation.weaknesses,
                next_steps=(
                    [
                        "Review failed acceptance checks before retaining the strategy.",
                        "Run additional out-of-sample and sensitivity tests.",
                    ]
                    if decision == "REJECT"
                    else [
                        "Run out-of-sample and sensitivity tests before any deployment decision.",
                        "Review assumptions, costs, and data quality with a researcher.",
                    ]
                ),
            )
            return {
                "report": report.model_dump(mode="json"),
                "status": "REPORT_READY",
                "current_agent": "report",
                "errors": [],
            }
        except Exception as exc:
            return {
                "status": "FAILED",
                "current_agent": "report",
                "errors": [f"Report Agent failed: {exc}"],
            }
