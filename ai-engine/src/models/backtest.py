from typing import Any
from pydantic import BaseModel, Field


class EquityPoint(BaseModel):
    date: str
    strategy_equity: float
    benchmark_equity: float
    strategy_return: float
    benchmark_return: float


class TradeRecord(BaseModel):
    symbol: str
    side: str
    signal_date: str
    execution_date: str
    price: float | None = None
    position_before: float
    position_after: float
    transaction_cost: float
    slippage_cost: float


class SymbolBacktestResult(BaseModel):
    symbol: str
    observations: int
    entries: int
    exits: int
    total_return: float
    benchmark_return: float
    total_cost: float


class BacktestResult(BaseModel):
    strategy_name: str
    symbols: list[str]
    transaction_cost_bps: float = Field(ge=0)
    slippage_bps: float = Field(ge=0)
    initial_capital: float = Field(gt=0)
    final_equity: float
    benchmark_final_equity: float
    total_return: float
    benchmark_return: float
    excess_return: float
    equity_curve: list[EquityPoint]
    trades: list[TradeRecord]
    per_symbol: list[SymbolBacktestResult]
    diagnostics: dict[str, Any] = Field(default_factory=dict)
