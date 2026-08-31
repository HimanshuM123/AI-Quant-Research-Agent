from src.rag.chunking import chunk_document
from src.rag.documents import Document
from src.rag.embeddings import HashEmbeddingProvider
from src.rag.vector_store import InMemoryVectorStore


def test_vector_retrieval_prefers_momentum_text():
    docs = [
        Document("m", "Momentum", "momentum trailing returns trend moving average"),
        Document("v", "Volatility", "volatility clustering risk variance turbulence"),
    ]
    store = InMemoryVectorStore(HashEmbeddingProvider(dimensions=128))
    chunks = [chunk_document(doc, chunk_size=100, overlap=10)[0] for doc in docs]
    store.add(chunks)
    results = store.search("momentum trend strategy", top_k=1)
    assert results[0].chunk.title == "Momentum"
