from src.graph.state import ResearchState
from src.llm.strategy_synthesizer import StrategySynthesizer, build_strategy_synthesizer
from src.models.research import ResearchHypothesis
from src.strategy.rule_engine import RuleEngine


class StrategyAgent:
    """Translate validated research into a constrained, executable-by-rule-engine DSL."""

    def __init__(self, synthesizer: StrategySynthesizer | None = None):
        self.synthesizer = synthesizer or build_strategy_synthesizer()

    def __call__(self, state: ResearchState) -> dict:
        try:
            if not state.get("research"):
                raise ValueError("Research hypothesis is required before strategy generation")

            research = ResearchHypothesis.model_validate(state["research"])
            strategy = self.synthesizer.synthesize(
                research=research,
                symbols=state["symbols"],
            )
            RuleEngine.validate_strategy(strategy)
            return {
                "strategy": strategy.model_dump(mode="json"),
                "status": "STRATEGY_READY",
                "current_agent": "strategy",
                "errors": [],
            }
        except Exception as exc:
            return {
                "status": "FAILED",
                "current_agent": "strategy",
                "errors": [f"Strategy Agent failed: {exc}"],
            }
