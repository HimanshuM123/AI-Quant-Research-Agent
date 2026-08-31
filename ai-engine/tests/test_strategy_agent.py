from src.agents.strategy_agent import StrategyAgent
from src.llm.strategy_synthesizer import DeterministicStrategySynthesizer


def test_strategy_agent_converts_research_to_validated_dsl():
    state = {
        "symbols": ["AAPL", "MSFT"],
        "research": {
            "hypothesis": "Test momentum with volatility filtering.",
            "rationale": "Retrieved evidence motivates a falsifiable momentum test.",
            "features": ["momentum_20d", "volatility_20d", "sma_50"],
            "assets": ["AAPL", "MSFT"],
            "risks": ["overfitting"],
            "evidence": [],
            "confidence": 0.6,
        },
        "errors": [],
    }
    result = StrategyAgent(DeterministicStrategySynthesizer())(state)
    assert result["status"] == "STRATEGY_READY"
    assert result["current_agent"] == "strategy"
    assert result["strategy"]["name"] == "VolatilityFilteredMomentum"
    assert result["strategy"]["entry"]["conditions"][0]["feature"] == "momentum"
