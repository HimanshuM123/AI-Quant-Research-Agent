from datetime import date
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from src.models.strategy import StrategySpec
from src.models.backtest import BacktestResult
from src.models.evaluation import EvaluationResult
from src.models.risk import RiskResult
from src.models.report import ResearchReport


class ResearchRunRequest(BaseModel):
    query: str = Field(min_length=3, max_length=1000)
    symbols: list[str] = Field(min_length=1, max_length=20)
    start_date: date
    end_date: date
    volatility_window: int = Field(default=20, ge=2, le=252)
    momentum_window: int = Field(default=20, ge=1, le=252)
    top_k: int = Field(default=5, ge=1, le=10)
    slippage_bps: float = Field(default=2.0, ge=0.0, le=100.0)
    initial_capital: float = Field(default=100000.0, gt=0.0, le=1_000_000_000.0)
    annual_risk_free_rate: float = Field(default=0.0, ge=-0.5, le=1.0)
    var_confidence: float = Field(default=0.95, gt=0.5, lt=1.0)

    @field_validator("symbols")
    @classmethod
    def normalize_symbols(cls, symbols: list[str]) -> list[str]:
        cleaned = sorted({symbol.strip().upper() for symbol in symbols if symbol.strip()})
        if not cleaned:
            raise ValueError("At least one non-empty symbol is required")
        return cleaned

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        return self


class Evidence(BaseModel):
    source_id: str
    title: str
    excerpt: str
    score: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResearchHypothesis(BaseModel):
    hypothesis: str
    rationale: str
    features: list[str]
    assets: list[str]
    risks: list[str]
    evidence: list[Evidence]
    confidence: float = Field(ge=0.0, le=1.0)


class ResearchRunResponse(BaseModel):
    research_id: str
    status: str
    current_agent: str | None = None
    iteration: int
    market_data: dict[str, Any]
    research: ResearchHypothesis | None = None
    strategy: StrategySpec | None = None
    backtest: BacktestResult | None = None
    risk: RiskResult | None = None
    evaluation: EvaluationResult | None = None
    report: ResearchReport | None = None
    errors: list[str] = Field(default_factory=list)
