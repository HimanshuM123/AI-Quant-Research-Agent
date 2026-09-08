from uuid import uuid4

from src.graph.workflow import build_research_graph
from src.models.research import ResearchHypothesis, ResearchRunRequest, ResearchRunResponse
from src.models.strategy import StrategySpec
from src.models.backtest import BacktestResult
from src.models.evaluation import EvaluationResult
from src.models.report import ResearchReport
from src.models.risk import RiskResult


class ResearchGraphService:
    def __init__(self, graph=None):
        self.graph = graph or build_research_graph()

    def run(self, request: ResearchRunRequest) -> ResearchRunResponse:
        research_id = str(uuid4())
        initial_state = {
            "research_id": research_id,
            "query": request.query,
            "symbols": request.symbols,
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
            "volatility_window": request.volatility_window,
            "momentum_window": request.momentum_window,
            "top_k": request.top_k,
            "slippage_bps": request.slippage_bps,
            "initial_capital": request.initial_capital,
            "annual_risk_free_rate": request.annual_risk_free_rate,
            "var_confidence": request.var_confidence,
            "research": None,
            "strategy": None,
            "backtest": None,
            "risk": None,
            "evaluation": None,
            "report": None,
            "iteration": 0,
            "status": "STARTED",
            "current_agent": None,
            "errors": [],
        }

        result = self.graph.invoke(
            initial_state,
            config={"configurable": {"thread_id": research_id}},
        )
        research = result.get("research")
        strategy = result.get("strategy")
        backtest = result.get("backtest")
        risk = result.get("risk")
        evaluation = result.get("evaluation")
        report = result.get("report")
        return ResearchRunResponse(
            research_id=research_id,
            status=result["status"],
            current_agent=result.get("current_agent"),
            iteration=result.get("iteration", 0),
            market_data=result.get("market_data", {}),
            research=ResearchHypothesis.model_validate(research) if research else None,
            strategy=StrategySpec.model_validate(strategy) if strategy else None,
            backtest=BacktestResult.model_validate(backtest) if backtest else None,
            risk=RiskResult.model_validate(risk) if risk else None,
            evaluation=EvaluationResult.model_validate(evaluation) if evaluation else None,
            report=ResearchReport.model_validate(report) if report else None,
            errors=result.get("errors", []),
        )
