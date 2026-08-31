from src.agents.backtest_agent import BacktestAgent


def test_backtest_agent_fails_closed_without_strategy():
    state = BacktestAgent()({"market_data": {"symbols": {}}, "errors": []})
    assert state["status"] == "FAILED"
    assert state["current_agent"] == "backtest"
