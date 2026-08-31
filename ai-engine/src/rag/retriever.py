import os
from pathlib import Path

from src.models.research import Evidence
from src.rag.chunking import chunk_document
from src.rag.documents import load_documents
from src.rag.embeddings import HashEmbeddingProvider
from src.rag.vector_store import InMemoryVectorStore, PgVectorStore, VectorStore


class ResearchRetriever:
    def __init__(self, store: VectorStore):
        self.store = store

    @classmethod
    def from_directory(cls, root: str | Path):
        embedding_provider = HashEmbeddingProvider(dimensions=384)
        store_kind = os.getenv("RAG_STORE", "memory").lower()
        if store_kind == "pgvector":
            dsn = os.getenv("POSTGRES_DSN", "postgresql://quantagent:quantagent@postgres:5432/quantagent")
            store: VectorStore = PgVectorStore(dsn, embedding_provider, dimensions=384)
        else:
            store = InMemoryVectorStore(embedding_provider)

        chunks = []
        for document in load_documents(root):
            chunks.extend(chunk_document(document))
        store.add(chunks)
        return cls(store)

    @classmethod
    def from_markdown_directory(cls, root: str | Path):
        # Backwards-compatible helper retained for tests and Phase-2 callers.
        return cls.from_directory(root)

    def retrieve(self, query: str, *, top_k: int = 5) -> list[Evidence]:
        results = self.store.search(query, top_k=top_k)
        return [
            Evidence(
                source_id=item.chunk.chunk_id,
                title=item.chunk.title,
                excerpt=item.chunk.text[:700],
                score=round(item.score, 6),
                metadata=item.chunk.metadata,
            )
            for item in results
        ]
