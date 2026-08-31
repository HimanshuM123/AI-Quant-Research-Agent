from typing import Any, TypedDict


class ResearchState(TypedDict, total=False):
    research_id: str
    query: str
    symbols: list[str]
    start_date: str
    end_date: str
    volatility_window: int
    momentum_window: int
    top_k: int
    slippage_bps: float
    initial_capital: float

    market_data: dict[str, Any]
    research: dict[str, Any] | None
    strategy: dict[str, Any] | None
    backtest: dict[str, Any] | None
    risk: dict[str, Any] | None
    evaluation: dict[str, Any] | None

    iteration: int
    status: str
    current_agent: str | None
    errors: list[str]
