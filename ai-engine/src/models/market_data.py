from datetime import date
from pydantic import BaseModel, Field, field_validator


class MarketDataRequest(BaseModel):
    symbols: list[str] = Field(min_length=1, max_length=20)
    start_date: date
    end_date: date
    volatility_window: int = Field(default=20, ge=2, le=252)
    momentum_window: int = Field(default=20, ge=1, le=252)

    @field_validator("symbols")
    @classmethod
    def normalize_symbols(cls, symbols: list[str]) -> list[str]:
        cleaned = sorted({symbol.strip().upper() for symbol in symbols if symbol.strip()})
        if not cleaned:
            raise ValueError("At least one non-empty symbol is required")
        return cleaned

    def model_post_init(self, __context) -> None:
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")


class MarketObservation(BaseModel):
    date: date
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: float | None = None
    simple_return: float | None = None
    log_return: float | None = None
    volatility: float | None = None
    momentum: float | None = None
    sma_20: float | None = None
    sma_50: float | None = None


class SymbolMarketData(BaseModel):
    symbol: str
    observations: list[MarketObservation]


class MarketDataResponse(BaseModel):
    data: list[SymbolMarketData]
