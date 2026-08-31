from src.agents.research_agent import ResearchAgent
from src.llm.research_synthesizer import DeterministicResearchSynthesizer
from src.rag.chunking import chunk_document
from src.rag.documents import Document
from src.rag.embeddings import HashEmbeddingProvider
from src.rag.retriever import ResearchRetriever
from src.rag.vector_store import InMemoryVectorStore


def test_research_agent_populates_structured_hypothesis():
    store = InMemoryVectorStore(HashEmbeddingProvider(dimensions=128))
    doc = Document("paper", "Momentum", "Momentum can be tested with trend and volatility filters.")
    store.add(chunk_document(doc, chunk_size=100, overlap=10))
    agent = ResearchAgent(
        retriever=ResearchRetriever(store),
        synthesizer=DeterministicResearchSynthesizer(),
    )
    state = {
        "query": "Find a momentum strategy",
        "symbols": ["AAPL"],
        "top_k": 3,
        "market_data": {
            "symbols": {
                "AAPL": {
                    "observation_count": 100,
                    "first_date": "2024-01-01",
                    "last_date": "2024-06-01",
                    "latest": {"close": 200.0, "volatility": 0.2, "momentum": 0.08},
                }
            }
        },
    }
    result = agent(state)
    assert result["status"] == "RESEARCH_READY"
    assert result["research"]["assets"] == ["AAPL"]
    assert result["research"]["evidence"][0]["title"] == "Momentum"
