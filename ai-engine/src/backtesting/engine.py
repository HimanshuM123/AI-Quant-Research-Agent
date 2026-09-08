from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

import pandas as pd

from src.models.backtest import BacktestResult, EquityPoint, SymbolBacktestResult, TradeRecord
from src.models.strategy import StrategySpec
from src.strategy.rule_engine import RuleEngine


@dataclass
class _SymbolSeries:
    symbol: str
    frame: pd.DataFrame
    trades: list[TradeRecord]
    total_cost: float


class BacktestEngine:
    """Deterministic long-only backtester for the validated Strategy DSL.

    Signal at t is converted to an executable position at t+1. Therefore the
    return at t always uses a position decided strictly before that return.
    """

    def run(
        self,
        *,
        strategy: StrategySpec,
        market_data: dict[str, Any],
        slippage_bps: float = 2.0,
        initial_capital: float = 100_000.0,
    ) -> BacktestResult:
        RuleEngine.validate_strategy(strategy)
        if slippage_bps < 0:
            raise ValueError("slippage_bps must be non-negative")
        if initial_capital <= 0:
            raise ValueError("initial_capital must be positive")

        series: list[_SymbolSeries] = []
        for symbol in strategy.assets:
            raw = market_data.get("symbols", {}).get(symbol)
            if not raw:
                raise ValueError(f"Missing market data for strategy asset {symbol}")
            series.append(self._run_symbol(strategy, symbol, raw["observations"], slippage_bps))

        portfolio = self._combine(series, initial_capital)
        trades = [trade for item in series for trade in item.trades]
        trades.sort(key=lambda t: (t.execution_date, t.symbol))

        per_symbol = []
        for item in series:
            f = item.frame
            strat_equity = float((1.0 + f["strategy_return"]).cumprod().iloc[-1]) if len(f) else 1.0
            bench_equity = float((1.0 + f["benchmark_return"]).cumprod().iloc[-1]) if len(f) else 1.0
            per_symbol.append(SymbolBacktestResult(
                symbol=item.symbol,
                observations=len(f),
                entries=sum(t.side == "BUY" for t in item.trades),
                exits=sum(t.side == "SELL" for t in item.trades),
                total_return=strat_equity - 1.0,
                benchmark_return=bench_equity - 1.0,
                total_cost=item.total_cost,
            ))

        equity_curve = [
            EquityPoint(
                date=index.date().isoformat(),
                strategy_equity=float(row["strategy_equity"] * initial_capital),
                benchmark_equity=float(row["benchmark_equity"] * initial_capital),
                strategy_return=float(row["strategy_return"]),
                benchmark_return=float(row["benchmark_return"]),
                turnover=float(row.get("turnover", 0.0)),
                gross_exposure=float(row.get("gross_exposure", 0.0)),
            )
            for index, row in portfolio.iterrows()
        ]
        final_equity = float(portfolio["strategy_equity"].iloc[-1] * initial_capital) if len(portfolio) else initial_capital
        benchmark_final = float(portfolio["benchmark_equity"].iloc[-1] * initial_capital) if len(portfolio) else initial_capital
        total_return = final_equity / initial_capital - 1.0
        benchmark_return = benchmark_final / initial_capital - 1.0
        return BacktestResult(
            strategy_name=strategy.name,
            symbols=strategy.assets,
            transaction_cost_bps=strategy.transaction_cost_bps,
            slippage_bps=slippage_bps,
            initial_capital=initial_capital,
            final_equity=final_equity,
            benchmark_final_equity=benchmark_final,
            total_return=total_return,
            benchmark_return=benchmark_return,
            excess_return=total_return - benchmark_return,
            equity_curve=equity_curve,
            trades=trades,
            per_symbol=per_symbol,
            diagnostics={
                "signal_execution_lag_bars": 1,
                "position_return_formula": "position[t-1] * return[t] - turnover[t] * costs",
                "portfolio_weighting": "equal_weight_across_strategy_assets",
            },
        )

    def _run_symbol(self, strategy: StrategySpec, symbol: str, observations: list[dict], slippage_bps: float) -> _SymbolSeries:
        frame = pd.DataFrame(observations)
        if frame.empty:
            raise ValueError(f"No observations for {symbol}")
        frame["date"] = pd.to_datetime(frame["date"])
        frame = frame.sort_values("date").set_index("date")

        target = []
        held = 0.0
        fraction = strategy.position_sizing.fraction
        for _, row in frame.iterrows():
            row_map = row.to_dict()
            if held == 0.0 and RuleEngine.evaluate_group(strategy.entry, row_map):
                held = fraction
            elif held > 0.0 and RuleEngine.evaluate_group(strategy.exit, row_map):
                held = 0.0
            target.append(held)
        frame["target_position"] = target

        # The crucial anti-look-ahead operation: today's signal is actionable next bar.
        frame["position"] = frame["target_position"].shift(1).fillna(0.0)
        frame["position_before"] = frame["position"].shift(1).fillna(0.0)
        frame["turnover"] = (frame["position"] - frame["position_before"]).abs()

        tc_rate = strategy.transaction_cost_bps / 10_000.0
        slip_rate = slippage_bps / 10_000.0
        frame["transaction_cost"] = frame["turnover"] * tc_rate
        frame["slippage_cost"] = frame["turnover"] * slip_rate
        frame["gross_strategy_return"] = frame["position"] * frame["simple_return"].fillna(0.0)
        frame["strategy_return"] = frame["gross_strategy_return"] - frame["transaction_cost"] - frame["slippage_cost"]
        frame["benchmark_return"] = frame["simple_return"].fillna(0.0)

        trades: list[TradeRecord] = []
        for i, (execution_date, row) in enumerate(frame.iterrows()):
            before = float(row["position_before"])
            after = float(row["position"])
            if math.isclose(before, after):
                continue
            signal_date = frame.index[i - 1] if i > 0 else execution_date
            trades.append(TradeRecord(
                symbol=symbol,
                side="BUY" if after > before else "SELL",
                signal_date=signal_date.date().isoformat(),
                execution_date=execution_date.date().isoformat(),
                price=None if pd.isna(row.get("open")) else float(row.get("open")),
                position_before=before,
                position_after=after,
                transaction_cost=float(row["transaction_cost"]),
                slippage_cost=float(row["slippage_cost"]),
            ))

        return _SymbolSeries(symbol, frame, trades, float(frame["transaction_cost"].sum() + frame["slippage_cost"].sum()))

    @staticmethod
    def _combine(series: list[_SymbolSeries], initial_capital: float) -> pd.DataFrame:
        returns = []
        benchmarks = []
        for item in series:
            returns.append(item.frame["strategy_return"].rename(item.symbol))
            benchmarks.append(item.frame["benchmark_return"].rename(item.symbol))
        strategy_returns = pd.concat(returns, axis=1).fillna(0.0).mean(axis=1)
        benchmark_returns = pd.concat(benchmarks, axis=1).fillna(0.0).mean(axis=1)
        turnover = pd.concat([item.frame["turnover"].rename(item.symbol) for item in series], axis=1).fillna(0.0).mean(axis=1)
        gross_exposure = pd.concat([item.frame["position"].abs().rename(item.symbol) for item in series], axis=1).fillna(0.0).mean(axis=1)
        frame = pd.DataFrame({
            "strategy_return": strategy_returns,
            "benchmark_return": benchmark_returns,
            "turnover": turnover,
            "gross_exposure": gross_exposure,
        }).sort_index()
        frame["strategy_equity"] = (1.0 + frame["strategy_return"]).cumprod()
        frame["benchmark_equity"] = (1.0 + frame["benchmark_return"]).cumprod()
        return frame
