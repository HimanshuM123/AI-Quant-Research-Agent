from collections.abc import Mapping

from src.models.strategy import ComparisonOperator, RuleCondition, RuleGroup, StrategySpec


class StrategyValidationError(ValueError):
    pass


class RuleEngine:
    """Deterministically validates and evaluates the strategy DSL."""

    ALLOWED_FEATURES = {
        "open",
        "high",
        "low",
        "close",
        "volume",
        "simple_return",
        "log_return",
        "volatility",
        "momentum",
        "sma_20",
        "sma_50",
    }

    @classmethod
    def validate_strategy(cls, strategy: StrategySpec) -> None:
        for group_name, group in (("entry", strategy.entry), ("exit", strategy.exit)):
            for condition in group.conditions:
                if condition.feature not in cls.ALLOWED_FEATURES:
                    raise StrategyValidationError(
                        f"Unsupported {group_name} feature: {condition.feature}"
                    )
                if condition.reference and condition.reference not in cls.ALLOWED_FEATURES:
                    raise StrategyValidationError(
                        f"Unsupported {group_name} reference feature: {condition.reference}"
                    )

    @classmethod
    def evaluate_group(cls, group: RuleGroup, row: Mapping[str, float | int | None]) -> bool:
        results = [cls.evaluate_condition(condition, row) for condition in group.conditions]
        return all(results) if group.logic == "all" else any(results)

    @staticmethod
    def evaluate_condition(condition: RuleCondition, row: Mapping[str, float | int | None]) -> bool:
        lhs = row.get(condition.feature)
        rhs = row.get(condition.reference) if condition.reference else condition.value
        if lhs is None or rhs is None:
            return False

        op = condition.operator
        if op == ComparisonOperator.GT:
            return lhs > rhs
        if op == ComparisonOperator.GTE:
            return lhs >= rhs
        if op == ComparisonOperator.LT:
            return lhs < rhs
        if op == ComparisonOperator.LTE:
            return lhs <= rhs
        if op == ComparisonOperator.EQ:
            return lhs == rhs
        if op == ComparisonOperator.NE:
            return lhs != rhs
        raise StrategyValidationError(f"Unsupported operator: {op}")
