from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ComparisonOperator(str, Enum):
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    EQ = "=="
    NE = "!="


class RuleCondition(BaseModel):
    feature: str = Field(min_length=1, max_length=100)
    operator: ComparisonOperator
    value: float | None = None
    reference: str | None = Field(default=None, min_length=1, max_length=100)

    @model_validator(mode="after")
    def exactly_one_rhs(self):
        if (self.value is None) == (self.reference is None):
            raise ValueError("Exactly one of value or reference must be supplied")
        return self


class RuleGroup(BaseModel):
    logic: Literal["all", "any"]
    conditions: list[RuleCondition] = Field(min_length=1, max_length=20)


class PositionSizing(BaseModel):
    method: Literal["fixed_fraction"] = "fixed_fraction"
    fraction: float = Field(default=1.0, gt=0.0, le=1.0)


class StrategySpec(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=10, max_length=1000)
    assets: list[str] = Field(min_length=1, max_length=20)
    direction: Literal["long_only"] = "long_only"
    entry: RuleGroup
    exit: RuleGroup
    position_sizing: PositionSizing = Field(default_factory=PositionSizing)
    transaction_cost_bps: float = Field(default=5.0, ge=0.0, le=100.0)
    rationale: str = Field(min_length=10, max_length=1500)
    research_confidence: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def normalize_assets(self):
        self.assets = sorted({asset.strip().upper() for asset in self.assets if asset.strip()})
        if not self.assets:
            raise ValueError("Strategy must contain at least one asset")
        return self
