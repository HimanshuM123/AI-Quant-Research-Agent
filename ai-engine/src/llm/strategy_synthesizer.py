import json
import os
from typing import Protocol

from src.models.research import ResearchHypothesis
from src.models.strategy import (
    ComparisonOperator,
    PositionSizing,
    RuleCondition,
    RuleGroup,
    StrategySpec,
)


class StrategySynthesizer(Protocol):
    def synthesize(self, *, research: ResearchHypothesis, symbols: list[str]) -> StrategySpec:
        ...


class DeterministicStrategySynthesizer:
    """Offline, reproducible strategy generator used by tests and local development."""

    def synthesize(self, *, research: ResearchHypothesis, symbols: list[str]) -> StrategySpec:
        return StrategySpec(
            name="VolatilityFilteredMomentum",
            description="Long-only momentum strategy with trend confirmation and a volatility guardrail.",
            assets=symbols,
            direction="long_only",
            entry=RuleGroup(
                logic="all",
                conditions=[
                    RuleCondition(feature="momentum", operator=ComparisonOperator.GT, value=0.05),
                    RuleCondition(feature="close", operator=ComparisonOperator.GT, reference="sma_50"),
                    RuleCondition(feature="volatility", operator=ComparisonOperator.LT, value=0.35),
                ],
            ),
            exit=RuleGroup(
                logic="any",
                conditions=[
                    RuleCondition(feature="momentum", operator=ComparisonOperator.LT, value=0.0),
                    RuleCondition(feature="close", operator=ComparisonOperator.LT, reference="sma_50"),
                ],
            ),
            position_sizing=PositionSizing(method="fixed_fraction", fraction=1.0),
            transaction_cost_bps=5.0,
            rationale=(
                "Translate the research hypothesis into a falsifiable rule set: require positive "
                "momentum, price above the medium-term trend, and avoid unusually high volatility."
            ),
            research_confidence=research.confidence,
        )


class OpenAIStrategySynthesizer:
    """Generate only the constrained StrategySpec JSON schema; never executable code."""

    def __init__(self, model: str | None = None):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("openai package is not installed") from exc
        self.client = OpenAI()
        self.model = model or os.getenv("OPENAI_STRATEGY_MODEL", "gpt-5-mini")

    def synthesize(self, *, research: ResearchHypothesis, symbols: list[str]) -> StrategySpec:
        schema = StrategySpec.model_json_schema()
        payload = {
            "research": research.model_dump(mode="json"),
            "symbols": symbols,
            "allowed_features": [
                "open", "high", "low", "close", "volume", "simple_return", "log_return",
                "volatility", "momentum", "sma_20", "sma_50",
            ],
            "constraints": {
                "direction": "long_only",
                "position_sizing": "fixed_fraction",
                "no_code": True,
            },
        }
        response = self.client.responses.create(
            model=self.model,
            instructions=(
                "You are the Strategy Generation Agent in a quantitative research workflow. "
                "Convert the supplied research hypothesis into one falsifiable StrategySpec. "
                "Use only allowed features and operators represented in the JSON schema. "
                "Do not generate Python, SQL, shell commands, formulas to execute, or invented "
                "performance metrics. The strategy is for backtesting research only, not live trading."
            ),
            input=json.dumps(payload),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "strategy_spec",
                    "strict": True,
                    "schema": schema,
                }
            },
        )
        return StrategySpec.model_validate_json(response.output_text)


def build_strategy_synthesizer() -> StrategySynthesizer:
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIStrategySynthesizer()
    return DeterministicStrategySynthesizer()
