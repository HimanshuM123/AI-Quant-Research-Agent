import math

from src.backtesting.engine import BacktestEngine
from src.models.strategy import StrategySpec


def strategy(cost_bps=5.0):
    return StrategySpec.model_validate({
        "name": "Test Momentum",
        "description": "Simple deterministic strategy used to test the backtesting engine.",
        "assets": ["AAA"],
        "direction": "long_only",
        "entry": {"logic": "all", "conditions": [{"feature": "momentum", "operator": ">", "value": 0.05}]},
        "exit": {"logic": "any", "conditions": [{"feature": "momentum", "operator": "<", "value": 0.0}]},
        "position_sizing": {"method": "fixed_fraction", "fraction": 1.0},
        "transaction_cost_bps": cost_bps,
        "rationale": "Enter after positive momentum and exit after momentum turns negative.",
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


def test_signal_is_shifted_one_bar_to_prevent_lookahead():
    result = BacktestEngine().run(strategy=strategy(cost_bps=0), market_data=market(), slippage_bps=0, initial_capital=1000)
    # Entry signal occurs Jan 2, so Jan 2's +10% cannot be captured. Position begins Jan 3.
    jan2 = next(p for p in result.equity_curve if p.date == "2025-01-02")
    jan3 = next(p for p in result.equity_curve if p.date == "2025-01-03")
    assert jan2.strategy_return == 0.0
    assert math.isclose(jan3.strategy_return, 0.10)
    assert result.trades[0].signal_date == "2025-01-02"
    assert result.trades[0].execution_date == "2025-01-03"


def test_transaction_cost_and_slippage_reduce_return_on_turnover():
    no_cost = BacktestEngine().run(strategy=strategy(cost_bps=0), market_data=market(), slippage_bps=0, initial_capital=1000)
    with_cost = BacktestEngine().run(strategy=strategy(cost_bps=10), market_data=market(), slippage_bps=5, initial_capital=1000)
    assert with_cost.final_equity < no_cost.final_equity
    assert len(with_cost.trades) == 2
    assert with_cost.trades[0].side == "BUY"
    assert with_cost.trades[1].side == "SELL"
    assert with_cost.per_symbol[0].total_cost > 0


def test_benchmark_is_buy_and_hold_and_equity_curve_is_returned():
    result = BacktestEngine().run(strategy=strategy(cost_bps=0), market_data=market(), slippage_bps=0, initial_capital=1000)
    assert len(result.equity_curve) == 5
    assert result.benchmark_final_equity != 1000
    assert math.isclose(result.excess_return, result.total_return - result.benchmark_return)
