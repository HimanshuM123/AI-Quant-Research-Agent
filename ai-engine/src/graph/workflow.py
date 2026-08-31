from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from src.agents.backtest_agent import BacktestAgent
from src.agents.market_data_agent import MarketDataAgent
from src.agents.research_agent import ResearchAgent
from src.agents.strategy_agent import StrategyAgent
from src.graph.state import ResearchState


def _route_after_stage(state: ResearchState, success_node: str) -> str:
    return "end" if state.get("status") == "FAILED" else success_node


def build_research_graph(
    market_data_agent: MarketDataAgent | None = None,
    research_agent: ResearchAgent | None = None,
    strategy_agent: StrategyAgent | None = None,
    backtest_agent: BacktestAgent | None = None,
    *,
    with_memory: bool = True,
):
    """Phase 5: market data -> research -> strategy -> deterministic backtest."""
    builder = StateGraph(ResearchState)
    builder.add_node("market_data", market_data_agent or MarketDataAgent())
    builder.add_node("research", research_agent or ResearchAgent())
    builder.add_node("strategy", strategy_agent or StrategyAgent())
    builder.add_node("backtest", backtest_agent or BacktestAgent())

    builder.add_edge(START, "market_data")
    builder.add_conditional_edges("market_data", lambda s: _route_after_stage(s, "research"), {"research": "research", "end": END})
    builder.add_conditional_edges("research", lambda s: _route_after_stage(s, "strategy"), {"strategy": "strategy", "end": END})
    builder.add_conditional_edges("strategy", lambda s: _route_after_stage(s, "backtest"), {"backtest": "backtest", "end": END})
    builder.add_edge("backtest", END)
    return builder.compile(checkpointer=InMemorySaver()) if with_memory else builder.compile()
