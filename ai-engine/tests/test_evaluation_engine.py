from src.evaluation.engine import EvaluationEngine, EvaluationThresholds
from src.models.backtest import BacktestResult, EquityPoint, TradeRecord
from src.models.risk import RiskMetrics, RiskResult


def backtest(total_return: float = 0.20, benchmark_return: float = 0.05) -> BacktestResult:
    return BacktestResult(
        strategy_name="Evaluation Test",
        symbols=["AAA"],
        transaction_cost_bps=5.0,
        slippage_bps=2.0,
        initial_capital=100_000.0,
        final_equity=120_000.0,
        benchmark_final_equity=105_000.0,
        total_return=total_return,
        benchmark_return=benchmark_return,
        excess_return=total_return - benchmark_return,
        equity_curve=[
            EquityPoint(
                date=f"2025-01-{index:02d}",
                strategy_equity=100_000.0 + index * 100.0,
                benchmark_equity=100_000.0 + index * 25.0,
                strategy_return=0.001,
                benchmark_return=0.0005,
                turnover=0.02,
                gross_exposure=1.0,
            )
            for index in range(1, 11)
        ],
        trades=[
            TradeRecord(
                symbol="AAA",
                side="BUY" if index % 2 else "SELL",
                signal_date="2025-01-01",
                execution_date="2025-01-02",
                position_before=0.0,
                position_after=1.0,
                transaction_cost=0.0,
                slippage_cost=0.0,
            )
            for index in range(4)
        ],
        per_symbol=[],
        diagnostics={},
    )


def risk() -> RiskResult:
    metrics = RiskMetrics(
        cagr=0.10,
        annualized_volatility=0.15,
        sharpe_ratio=1.2,
        sortino_ratio=1.5,
        max_drawdown=-0.10,
        var_confidence=0.95,
        historical_var=0.02,
        expected_shortfall=0.03,
        total_turnover=0.20,
        average_daily_turnover=0.02,
        average_gross_exposure=0.8,
        max_gross_exposure=1.0,
        percent_days_in_market=0.8,
        observations=10,
        periods_per_year=252,
        annual_risk_free_rate=0.0,
    )
    benchmark = metrics.model_copy(update={"sharpe_ratio": 0.8})
    return RiskResult(strategy_name="Evaluation Test", metrics=metrics, benchmark=benchmark, diagnostics={})


def test_evaluation_accepts_strategy_passing_all_checks():
    result = EvaluationEngine().evaluate(backtest(), risk())

    assert result.decision == "ACCEPT"
    assert result.score == 1.0
    assert result.failed_checks == []


def test_evaluation_reports_failed_checks_and_score():
    failing_risk = risk().model_copy(update={
        "metrics": risk().metrics.model_copy(update={
            "cagr": 0.01,
            "max_drawdown": -0.30,
            "expected_shortfall": 0.08,
            "average_daily_turnover": 0.50,
            "sharpe_ratio": 0.2,
        }),
    })
    result = EvaluationEngine(EvaluationThresholds(minimum_trades=5)).evaluate(
        backtest(total_return=0.01, benchmark_return=0.05),
        failing_risk,
    )

    assert result.decision == "REJECT"
    assert result.score < 1.0
    assert "cagr_above_minimum" in result.failed_checks
    assert "drawdown_within_limit" in result.failed_checks
    assert "expected_shortfall_within_limit" in result.failed_checks
    assert "enough_trades" in result.failed_checks
    assert "reasonable_turnover" in result.failed_checks
