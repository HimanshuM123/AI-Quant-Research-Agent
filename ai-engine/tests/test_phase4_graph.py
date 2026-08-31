from datetime import date

import pandas as pd

from src.agents.market_data_agent import MarketDataAgent
from src.agents.research_agent import ResearchAgent
from src.agents.strategy_agent import StrategyAgent
from src.graph.workflow import build_research_graph
from src.llm.research_synthesizer import DeterministicResearchSynthesizer
from src.llm.strategy_synthesizer import DeterministicStrategySynthesizer
from src.market.service import MarketDataService
from src.rag.chunking import chunk_document
from src.rag.documents import Document
from src.rag.embeddings import HashEmbeddingProvider
from src.rag.retriever import ResearchRetriever
from src.rag.vector_store import InMemoryVectorStore
from src.tools.market_data import MarketDataTool


class FakeProvider:
    def download(self, symbol, start_date, end_date):
        idx = pd.date_range("2025-01-01", periods=60, freq="D")
        close = [100.0 + i for i in range(60)]
        return pd.DataFrame(
            {"Open": close, "High": [v + 1 for v in close], "Low": [v - 1 for v in close],
             "Close": close, "Volume": [1000] * 60},
            index=idx,
        )


def test_phase_5_graph_runs_through_strategy_generation():
    store = InMemoryVectorStore(HashEmbeddingProvider(dimensions=128))
    store.add(chunk_document(Document("m", "Momentum", "momentum trend volatility filter"), chunk_size=100, overlap=10))
    research_agent = ResearchAgent(ResearchRetriever(store), DeterministicResearchSynthesizer())
    market_agent = MarketDataAgent(MarketDataTool(MarketDataService(provider=FakeProvider())))
    strategy_agent = StrategyAgent(DeterministicStrategySynthesizer())

    graph = build_research_graph(market_agent, research_agent, strategy_agent, with_memory=False)
    state = graph.invoke({
        "research_id": "R-P4",
        "query": "Research momentum in AAPL",
        "symbols": ["AAPL"],
        "start_date": date(2025, 1, 1).isoformat(),
        "end_date": date(2025, 3, 1).isoformat(),
        "volatility_window": 20,
        "momentum_window": 20,
        "top_k": 3,
        "iteration": 0,
        "status": "STARTED",
        "errors": [],
    })
    assert state["status"] == "BACKTEST_READY"
    assert state["current_agent"] == "backtest"
    assert state["strategy"]["entry"]["logic"] == "all"
