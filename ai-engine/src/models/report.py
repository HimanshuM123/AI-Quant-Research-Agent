from typing import Literal

from pydantic import BaseModel, Field


class ResearchReport(BaseModel):
    title: str
    decision: Literal["ACCEPT", "REJECT"]
    executive_summary: str
    key_findings: list[str] = Field(min_length=1)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(min_length=1)
