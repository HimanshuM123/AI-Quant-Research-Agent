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


def build_test_research_agent():
    store = InMemoryVectorStore(HashEmbeddingProvider(dimensions=128))
    store.add(chunk_document(Document("m", "Momentum", "momentum trend volatility filter"), chunk_size=100, overlap=10))
    return ResearchAgent(ResearchRetriever(store), DeterministicResearchSynthesizer())


def test_phase_6_graph_runs_market_data_research_then_strategy():
    market_agent = MarketDataAgent(MarketDataTool(MarketDataService(provider=FakeProvider())))
    graph = build_research_graph(market_agent, build_test_research_agent(), StrategyAgent(DeterministicStrategySynthesizer()), with_memory=False)
    state = graph.invoke({
        "research_id": "R-TEST",
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
    assert state["research_id"] == "R-TEST"
    assert state["status"] == "REPORT_READY"
    assert state["current_agent"] == "report"
    assert state["market_data"]["symbols"]["AAPL"]["latest"]["close"] == 159.0
    assert state["research"]["assets"] == ["AAPL"]
    assert state["strategy"]["name"] == "VolatilityFilteredMomentum"
