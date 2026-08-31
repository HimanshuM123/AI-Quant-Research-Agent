import json
import os
from typing import Protocol

from src.models.research import Evidence, ResearchHypothesis


class ResearchSynthesizer(Protocol):
    def synthesize(
        self,
        *,
        query: str,
        symbols: list[str],
        market_summary: dict,
        evidence: list[Evidence],
    ) -> ResearchHypothesis:
        ...


class DeterministicResearchSynthesizer:
    """Offline fallback used for local development and repeatable tests."""

    def synthesize(self, *, query: str, symbols: list[str], market_summary: dict, evidence: list[Evidence]) -> ResearchHypothesis:
        features = ["momentum_20d", "volatility_20d", "sma_50"]
        return ResearchHypothesis(
            hypothesis=(
                f"For {', '.join(symbols)}, medium-term momentum combined with a volatility "
                "filter and trend confirmation should be tested for improved risk-adjusted returns."
            ),
            rationale=(
                "The retrieved research supports testing momentum with volatility/trend controls. "
                "This is a testable hypothesis, not a trading recommendation."
            ),
            features=features,
            assets=symbols,
            risks=[
                "Momentum crashes during abrupt reversals",
                "Parameter sensitivity and overfitting",
                "Transaction costs can erode high-turnover signals",
            ],
            evidence=evidence,
            confidence=0.55 if evidence else 0.3,
        )


class OpenAIResearchSynthesizer:
    """LLM synthesizer with structured JSON output validated by Pydantic."""

    def __init__(self, model: str | None = None):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("openai package is not installed") from exc
        self.client = OpenAI()
        self.model = model or os.getenv("OPENAI_RESEARCH_MODEL", "gpt-5-mini")

    def synthesize(self, *, query: str, symbols: list[str], market_summary: dict, evidence: list[Evidence]) -> ResearchHypothesis:
        schema = ResearchHypothesis.model_json_schema()
        payload = {
            "query": query,
            "symbols": symbols,
            "market_summary": market_summary,
            "retrieved_evidence": [item.model_dump(mode="json") for item in evidence],
        }
        response = self.client.responses.create(
            model=self.model,
            instructions=(
                "You are a quantitative research agent. Form one falsifiable research hypothesis. "
                "Use only supplied evidence for literature claims. Do not invent performance metrics. "
                "Do not recommend live trading. Return JSON matching the provided schema."
            ),
            input=json.dumps(payload),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "research_hypothesis",
                    "strict": True,
                    "schema": schema,
                }
            },
        )
        return ResearchHypothesis.model_validate_json(response.output_text)


def build_research_synthesizer() -> ResearchSynthesizer:
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIResearchSynthesizer()
    return DeterministicResearchSynthesizer()
