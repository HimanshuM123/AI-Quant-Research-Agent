import pytest
from pydantic import ValidationError

from src.models.strategy import ComparisonOperator, RuleCondition, RuleGroup, StrategySpec
from src.strategy.rule_engine import RuleEngine, StrategyValidationError


def test_condition_requires_exactly_one_rhs():
    with pytest.raises(ValidationError):
        RuleCondition(feature="momentum", operator=ComparisonOperator.GT)
    with pytest.raises(ValidationError):
        RuleCondition(feature="momentum", operator=ComparisonOperator.GT, value=0.1, reference="sma_50")


def test_rule_engine_evaluates_entry_and_exit_deterministically():
    entry = RuleGroup(logic="all", conditions=[
        RuleCondition(feature="momentum", operator=ComparisonOperator.GT, value=0.05),
        RuleCondition(feature="close", operator=ComparisonOperator.GT, reference="sma_50"),
        RuleCondition(feature="volatility", operator=ComparisonOperator.LT, value=0.35),
    ])
    row = {"momentum": 0.08, "close": 120.0, "sma_50": 110.0, "volatility": 0.21}
    assert RuleEngine.evaluate_group(entry, row) is True


def test_rule_engine_rejects_unknown_features():
    strategy = StrategySpec.model_validate({
        "name": "BadFeatureStrategy",
        "description": "Contains an unsupported feature and must be rejected.",
        "assets": ["AAPL"],
        "direction": "long_only",
        "entry": {"logic": "all", "conditions": [{"feature": "future_return", "operator": ">", "value": 0.1}]},
        "exit": {"logic": "any", "conditions": [{"feature": "momentum", "operator": "<", "value": 0.0}]},
        "transaction_cost_bps": 5,
        "rationale": "This strategy intentionally references a forbidden future feature.",
        "research_confidence": 0.5,
    })
    with pytest.raises(StrategyValidationError):
        RuleEngine.validate_strategy(strategy)
