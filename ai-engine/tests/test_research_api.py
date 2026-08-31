from datetime import date

import pandas as pd
from fastapi.testclient import TestClient

from src.agents.market_data_agent import MarketDataAgent
from src.agents.research_agent import ResearchAgent
from src.agents.strategy_agent import StrategyAgent
from src.api import main
from src.graph.service import ResearchGraphService
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


def test_research_run_api_executes_phase_5_graph(monkeypatch):
    market_agent = MarketDataAgent(MarketDataTool(MarketDataService(provider=FakeProvider())))
    store = InMemoryVectorStore(HashEmbeddingProvider(dimensions=128))
    store.add(chunk_document(Document("m", "Momentum", "momentum trend volatility filter"), chunk_size=100, overlap=10))
    research_agent = ResearchAgent(ResearchRetriever(store), DeterministicResearchSynthesizer())
    graph = build_research_graph(market_agent, research_agent, StrategyAgent(DeterministicStrategySynthesizer()), with_memory=False)
    monkeypatch.setattr(main, "research_graph_service", ResearchGraphService(graph))

    client = TestClient(main.app)
    response = client.post("/api/v1/research/run", json={
        "query": "Find a momentum strategy for AAPL",
        "symbols": ["AAPL"],
        "start_date": date(2025, 1, 1).isoformat(),
        "end_date": date(2025, 3, 1).isoformat(),
        "volatility_window": 20,
        "momentum_window": 20,
        "top_k": 3,
    })
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "BACKTEST_READY"
    assert body["current_agent"] == "backtest"
    assert body["market_data"]["symbols"]["AAPL"]["observation_count"] == 60
    assert body["research"]["assets"] == ["AAPL"]
    assert body["strategy"]["name"] == "VolatilityFilteredMomentum"
