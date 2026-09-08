from __future__ import annotations

import math

import numpy as np

from src.models.backtest import BacktestResult
from src.models.risk import RiskMetrics, RiskResult


class RiskEngine:
    """Deterministic risk analytics computed from realized backtest returns."""

    def calculate(
        self,
        backtest: BacktestResult,
        *,
        annual_risk_free_rate: float = 0.0,
        var_confidence: float = 0.95,
        periods_per_year: int = 252,
    ) -> RiskResult:
        if not 0.0 < var_confidence < 1.0:
            raise ValueError("var_confidence must be between 0 and 1")
        if periods_per_year <= 0:
            raise ValueError("periods_per_year must be positive")
        if not backtest.equity_curve:
            raise ValueError("Backtest equity curve is empty")

        strategy_returns = np.asarray([p.strategy_return for p in backtest.equity_curve], dtype=float)
        benchmark_returns = np.asarray([p.benchmark_return for p in backtest.equity_curve], dtype=float)
        strategy_equity = np.asarray([p.strategy_equity for p in backtest.equity_curve], dtype=float)
        benchmark_equity = np.asarray([p.benchmark_equity for p in backtest.equity_curve], dtype=float)

        strategy_turnover = np.asarray([getattr(p, "turnover", 0.0) for p in backtest.equity_curve], dtype=float)
        strategy_exposure = np.asarray([getattr(p, "gross_exposure", 0.0) for p in backtest.equity_curve], dtype=float)

        # Buy-and-hold benchmark is always fully invested after initialization.
        benchmark_turnover = np.zeros_like(benchmark_returns)
        benchmark_exposure = np.ones_like(benchmark_returns)

        strategy = self._metrics(
            returns=strategy_returns,
            equity=strategy_equity,
            turnover=strategy_turnover,
            exposure=strategy_exposure,
            initial_equity=backtest.initial_capital,
            annual_risk_free_rate=annual_risk_free_rate,
            var_confidence=var_confidence,
            periods_per_year=periods_per_year,
        )
        benchmark = self._metrics(
            returns=benchmark_returns,
            equity=benchmark_equity,
            turnover=benchmark_turnover,
            exposure=benchmark_exposure,
            initial_equity=backtest.initial_capital,
            annual_risk_free_rate=annual_risk_free_rate,
            var_confidence=var_confidence,
            periods_per_year=periods_per_year,
        )

        return RiskResult(
            strategy_name=backtest.strategy_name,
            metrics=strategy,
            benchmark=benchmark,
            diagnostics={
                "var_method": "historical",
                "expected_shortfall_method": "historical tail mean",
                "annualization_periods": periods_per_year,
                "drawdown_convention": "negative decimal; -0.20 means a 20% drawdown",
                "exposure_convention": "mean absolute portfolio position; 1.0 means 100% gross exposure",
            },
        )

    @staticmethod
    def _metrics(
        *,
        returns: np.ndarray,
        equity: np.ndarray,
        turnover: np.ndarray,
        exposure: np.ndarray,
        initial_equity: float,
        annual_risk_free_rate: float,
        var_confidence: float,
        periods_per_year: int,
    ) -> RiskMetrics:
        n = int(len(returns))
        if n == 0:
            raise ValueError("At least one return observation is required")

        years = n / periods_per_year
        final_equity = float(equity[-1])
        cagr = (final_equity / initial_equity) ** (1.0 / years) - 1.0 if years > 0 and final_equity > 0 else -1.0

        annualized_vol = float(np.std(returns, ddof=1) * math.sqrt(periods_per_year)) if n > 1 else 0.0
        daily_rf = (1.0 + annual_risk_free_rate) ** (1.0 / periods_per_year) - 1.0
        excess = returns - daily_rf
        annualized_excess_return = float(np.mean(excess) * periods_per_year)
        sharpe = annualized_excess_return / annualized_vol if annualized_vol > 0 else None

        downside = np.minimum(excess, 0.0)
        downside_deviation = float(math.sqrt(np.mean(np.square(downside))) * math.sqrt(periods_per_year))
        sortino = annualized_excess_return / downside_deviation if downside_deviation > 0 else None

        running_peak = np.maximum.accumulate(np.concatenate(([initial_equity], equity)))
        full_equity = np.concatenate(([initial_equity], equity))
        drawdowns = full_equity / running_peak - 1.0
        max_drawdown = float(np.min(drawdowns))

        tail_probability = 1.0 - var_confidence
        quantile = float(np.quantile(returns, tail_probability))
        historical_var = max(0.0, -quantile)
        tail = returns[returns <= quantile]
        expected_shortfall = max(0.0, -float(np.mean(tail))) if len(tail) else historical_var

        total_turnover = float(np.sum(turnover))
        average_daily_turnover = float(np.mean(turnover))
        average_exposure = float(np.mean(np.abs(exposure)))
        max_exposure = float(np.max(np.abs(exposure)))
        percent_days_in_market = float(np.mean(np.abs(exposure) > 1e-12))

        return RiskMetrics(
            cagr=float(cagr),
            annualized_volatility=annualized_vol,
            sharpe_ratio=None if sharpe is None else float(sharpe),
            sortino_ratio=None if sortino is None else float(sortino),
            max_drawdown=max_drawdown,
            var_confidence=var_confidence,
            historical_var=historical_var,
            expected_shortfall=expected_shortfall,
            total_turnover=total_turnover,
            average_daily_turnover=average_daily_turnover,
            average_gross_exposure=average_exposure,
            max_gross_exposure=max_exposure,
            percent_days_in_market=percent_days_in_market,
            observations=n,
            periods_per_year=periods_per_year,
            annual_risk_free_rate=annual_risk_free_rate,
        )
