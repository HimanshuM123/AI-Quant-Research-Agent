from typing import Literal

from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    decision: Literal["ACCEPT", "REJECT"]
    score: float = Field(ge=0.0, le=1.0)
    strengths: list[str]
    weaknesses: list[str]
    failed_checks: list[str]
