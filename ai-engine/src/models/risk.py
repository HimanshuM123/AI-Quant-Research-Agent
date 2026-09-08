from pydantic import BaseModel, Field


class RiskMetrics(BaseModel):
    cagr: float
    annualized_volatility: float = Field(ge=0.0)
    sharpe_ratio: float | None = None
    sortino_ratio: float | None = None
    max_drawdown: float = Field(le=0.0)
    var_confidence: float = Field(gt=0.0, lt=1.0)
    historical_var: float = Field(ge=0.0)
    expected_shortfall: float = Field(ge=0.0)
    total_turnover: float = Field(ge=0.0)
    average_daily_turnover: float = Field(ge=0.0)
    average_gross_exposure: float = Field(ge=0.0)
    max_gross_exposure: float = Field(ge=0.0)
    percent_days_in_market: float = Field(ge=0.0, le=1.0)
    observations: int = Field(ge=1)
    periods_per_year: int = Field(gt=0)
    annual_risk_free_rate: float


class RiskResult(BaseModel):
    strategy_name: str
    metrics: RiskMetrics
    benchmark: RiskMetrics
    diagnostics: dict[str, str | float | int]
