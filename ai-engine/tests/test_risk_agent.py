from src.agents.risk_agent import RiskAgent
from src.backtesting.engine import BacktestEngine
from src.models.strategy import StrategySpec


def test_risk_agent_updates_state():
    strategy = StrategySpec.model_validate({
        "name":"Agent Test", "description":"Risk agent test strategy.", "assets":["AAA"], "direction":"long_only",
        "entry":{"logic":"all","conditions":[{"feature":"momentum","operator":">","value":0.05}]},
        "exit":{"logic":"any","conditions":[{"feature":"momentum","operator":"<","value":0.0}]},
        "position_sizing":{"method":"fixed_fraction","fraction":1.0}, "transaction_cost_bps":0,
        "rationale":"Risk agent validation test.", "research_confidence":0.5
    })
    observations = [
        {"date":"2025-01-01","open":100,"close":100,"simple_return":0.0,"momentum":0.0,"volatility":0.2,"sma_20":100,"sma_50":100},
        {"date":"2025-01-02","open":100,"close":102,"simple_return":0.02,"momentum":0.1,"volatility":0.2,"sma_20":100,"sma_50":100},
        {"date":"2025-01-03","open":102,"close":103,"simple_return":0.01,"momentum":0.1,"volatility":0.2,"sma_20":101,"sma_50":100},
    ]
    backtest = BacktestEngine().run(strategy=strategy, market_data={"symbols":{"AAA":{"observations":observations}}}, slippage_bps=0, initial_capital=1000)
    result = RiskAgent()({"backtest": backtest.model_dump(mode="json"), "annual_risk_free_rate":0.0, "var_confidence":0.95})
    assert result["status"] == "RISK_READY"
    assert result["current_agent"] == "risk"
    assert "cagr" in result["risk"]["metrics"]
