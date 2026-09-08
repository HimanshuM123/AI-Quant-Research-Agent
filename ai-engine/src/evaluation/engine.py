from __future__ import annotations

from dataclasses import dataclass
from src.models.backtest import BacktestResult
from src.models.evaluation import EvaluationResult
from src.models.risk import RiskResult


@dataclass(frozen=True)
class EvaluationThresholds:
    minimum_cagr: float = 0.05
    maximum_drawdown: float = 0.20
    maximum_expected_shortfall: float = 0.05
    minimum_trades: int = 3
    maximum_average_daily_turnover: float = 0.25


class EvaluationEngine:
    """Apply deterministic acceptance checks to backtest and risk results."""

    def __init__(self, thresholds: EvaluationThresholds | None = None):
        self.thresholds = thresholds or EvaluationThresholds()

    def evaluate(self, backtest: BacktestResult, risk: RiskResult) -> EvaluationResult:
        strategy = risk.metrics
        benchmark = risk.benchmark
        thresholds = self.thresholds
        checks: list[tuple[str, bool, str, str]] = [
            (
                "sharpe_beats_benchmark",
                strategy.sharpe_ratio is not None
                and benchmark.sharpe_ratio is not None
                and strategy.sharpe_ratio > benchmark.sharpe_ratio,
                "Strategy Sharpe ratio beats the benchmark.",
                "Strategy Sharpe ratio does not beat the benchmark.",
            ),
            (
                "drawdown_within_limit",
                strategy.max_drawdown >= -thresholds.maximum_drawdown,
                f"Maximum drawdown is within {thresholds.maximum_drawdown:.0%}.",
                f"Maximum drawdown exceeds {thresholds.maximum_drawdown:.0%}.",
            ),
            (
                "cagr_above_minimum",
                strategy.cagr > thresholds.minimum_cagr,
                f"CAGR is above the {thresholds.minimum_cagr:.0%} minimum.",
                f"CAGR is not above the {thresholds.minimum_cagr:.0%} minimum.",
            ),
            (
                "expected_shortfall_within_limit",
                strategy.expected_shortfall <= thresholds.maximum_expected_shortfall,
                f"Expected shortfall is within {thresholds.maximum_expected_shortfall:.0%}.",
                f"Expected shortfall exceeds {thresholds.maximum_expected_shortfall:.0%}.",
            ),
            (
                "enough_trades",
                len(backtest.trades) >= thresholds.minimum_trades,
                f"Backtest contains at least {thresholds.minimum_trades} trades.",
                f"Backtest contains fewer than {thresholds.minimum_trades} trades.",
            ),
            (
                "reasonable_turnover",
                strategy.average_daily_turnover <= thresholds.maximum_average_daily_turnover,
                f"Average daily turnover is within {thresholds.maximum_average_daily_turnover:.0%}.",
                f"Average daily turnover exceeds {thresholds.maximum_average_daily_turnover:.0%}.",
            ),
            (
                "risk_adjusted_outperformance",
                backtest.total_return > backtest.benchmark_return
                and (strategy.sharpe_ratio or 0.0) > 0.0,
                "Strategy outperforms the benchmark with positive risk-adjusted return.",
                "Strategy does not demonstrate risk-adjusted outperformance.",
            ),
        ]

        passed = [check for check in checks if check[1]]
        failed = [check[0] for check in checks if not check[1]]
        strengths = [check[2] for check in passed]
        weaknesses = [check[3] for check in checks if not check[1]]
        score = len(passed) / len(checks)

        return EvaluationResult(
            decision="ACCEPT" if not failed else "REJECT",
            score=score,
            strengths=strengths,
            weaknesses=weaknesses,
            failed_checks=failed,
        )
