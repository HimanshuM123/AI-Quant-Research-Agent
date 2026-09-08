import math

from src.backtesting.engine import BacktestEngine
from src.models.strategy import StrategySpec
from src.risk.engine import RiskEngine


def strategy():
    return StrategySpec.model_validate({
        "name": "Risk Test Momentum",
        "description": "Strategy used to validate Phase 6 risk analytics.",
        "assets": ["AAA"],
        "direction": "long_only",
        "entry": {"logic": "all", "conditions": [{"feature": "momentum", "operator": ">", "value": 0.05}]},
        "exit": {"logic": "any", "conditions": [{"feature": "momentum", "operator": "<", "value": 0.0}]},
        "position_sizing": {"method": "fixed_fraction", "fraction": 1.0},
        "transaction_cost_bps": 0.0,
        "rationale": "Test strategy.",
        "research_confidence": 0.5,
    })


def market():
    rows = [
        {"date":"2025-01-01","open":100,"close":100,"simple_return":0.00,"momentum":0.00,"volatility":0.2,"sma_20":100,"sma_50":100},
        {"date":"2025-01-02","open":100,"close":110,"simple_return":0.10,"momentum":0.10,"volatility":0.2,"sma_20":100,"sma_50":100},
        {"date":"2025-01-03","open":110,"close":121,"simple_return":0.10,"momentum":0.10,"volatility":0.2,"sma_20":105,"sma_50":100},
        {"date":"2025-01-04","open":121,"close":108.9,"simple_return":-0.10,"momentum":-0.05,"volatility":0.2,"sma_20":110,"sma_50":100},
        {"date":"2025-01-05","open":108.9,"close":98.01,"simple_return":-0.10,"momentum":-0.05,"volatility":0.2,"sma_20":105,"sma_50":100},
    ]
    return {"symbols":{"AAA":{"observations":rows}}}


def test_risk_engine_calculates_required_metrics():
    backtest = BacktestEngine().run(strategy=strategy(), market_data=market(), slippage_bps=0, initial_capital=1000)
    risk = RiskEngine().calculate(backtest, annual_risk_free_rate=0.0, var_confidence=0.95)

    m = risk.metrics
    assert m.observations == 5
    assert m.annualized_volatility > 0
    assert m.max_drawdown < 0
    assert m.historical_var >= 0
    assert m.expected_shortfall >= m.historical_var
    assert m.total_turnover == 2.0
    assert math.isclose(m.average_gross_exposure, 0.4)
    assert math.isclose(m.percent_days_in_market, 0.4)
    assert risk.benchmark.average_gross_exposure == 1.0


def test_var_and_expected_shortfall_use_historical_left_tail():
    backtest = BacktestEngine().run(strategy=strategy(), market_data=market(), slippage_bps=0, initial_capital=1000)
    risk = RiskEngine().calculate(backtest, var_confidence=0.80)
    assert risk.metrics.historical_var >= 0
    assert risk.metrics.expected_shortfall >= risk.metrics.historical_var


def test_risk_free_rate_changes_sharpe():
    backtest = BacktestEngine().run(strategy=strategy(), market_data=market(), slippage_bps=0, initial_capital=1000)
    zero_rf = RiskEngine().calculate(backtest, annual_risk_free_rate=0.0)
    high_rf = RiskEngine().calculate(backtest, annual_risk_free_rate=0.20)
    assert zero_rf.metrics.sharpe_ratio != high_rf.metrics.sharpe_ratio
