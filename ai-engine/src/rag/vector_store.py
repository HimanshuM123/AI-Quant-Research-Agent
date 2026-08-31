from dataclasses import dataclass
import json
import math
from typing import Any, Protocol

from src.rag.documents import Chunk
from src.rag.embeddings import EmbeddingProvider


@dataclass(frozen=True)
class SearchResult:
    chunk: Chunk
    score: float


class VectorStore(Protocol):
    def add(self, chunks: list[Chunk]) -> None:
        ...

    def search(self, query: str, *, top_k: int = 5, metadata: dict[str, Any] | None = None) -> list[SearchResult]:
        ...


class InMemoryVectorStore:
    def __init__(self, embedding_provider: EmbeddingProvider):
        self.embedding_provider = embedding_provider
        self._items: list[tuple[Chunk, list[float]]] = []

    def add(self, chunks: list[Chunk]) -> None:
        vectors = self.embedding_provider.embed([chunk.text for chunk in chunks])
        self._items.extend(zip(chunks, vectors, strict=True))

    def search(self, query: str, *, top_k: int = 5, metadata: dict[str, Any] | None = None) -> list[SearchResult]:
        query_vector = self.embedding_provider.embed([query])[0]
        scored: list[SearchResult] = []
        for chunk, vector in self._items:
            if metadata and any(chunk.metadata.get(key) != value for key, value in metadata.items()):
                continue
            score = self._cosine(query_vector, vector)
            scored.append(SearchResult(chunk=chunk, score=max(0.0, min(1.0, score))))
        return sorted(scored, key=lambda item: item.score, reverse=True)[:top_k]

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b, strict=True))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        if na == 0.0 or nb == 0.0:
            return 0.0
        return dot / (na * nb)


class PgVectorStore:
    """PostgreSQL/pgvector store used by the production deployment path."""

    def __init__(self, dsn: str, embedding_provider: EmbeddingProvider, dimensions: int = 384):
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError("psycopg is required for PgVectorStore") from exc
        self.psycopg = psycopg
        self.dsn = dsn
        self.embedding_provider = embedding_provider
        self.dimensions = dimensions
        self._ensure_schema()

    @staticmethod
    def _vector_literal(vector: list[float]) -> str:
        return "[" + ",".join(f"{value:.10f}" for value in vector) + "]"

    def _ensure_schema(self) -> None:
        with self.psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS research_chunks (
                        chunk_id TEXT PRIMARY KEY,
                        document_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                        embedding vector({self.dimensions}) NOT NULL
                    )
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS research_chunks_document_idx ON research_chunks(document_id)")
            conn.commit()

    def add(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        vectors = self.embedding_provider.embed([chunk.text for chunk in chunks])
        with self.psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                for chunk, vector in zip(chunks, vectors, strict=True):
                    if len(vector) != self.dimensions:
                        raise ValueError(f"Expected embedding dimension {self.dimensions}, got {len(vector)}")
                    cur.execute(
                        """
                        INSERT INTO research_chunks(chunk_id, document_id, title, content, metadata, embedding)
                        VALUES (%s, %s, %s, %s, %s::jsonb, CAST(%s AS vector))
                        ON CONFLICT (chunk_id) DO UPDATE SET
                            document_id = EXCLUDED.document_id,
                            title = EXCLUDED.title,
                            content = EXCLUDED.content,
                            metadata = EXCLUDED.metadata,
                            embedding = EXCLUDED.embedding
                        """,
                        (
                            chunk.chunk_id,
                            chunk.document_id,
                            chunk.title,
                            chunk.text,
                            json.dumps(chunk.metadata),
                            self._vector_literal(vector),
                        ),
                    )
            conn.commit()

    def search(self, query: str, *, top_k: int = 5, metadata: dict[str, Any] | None = None) -> list[SearchResult]:
        vector = self.embedding_provider.embed([query])[0]
        vector_literal = self._vector_literal(vector)
        clauses = []
        params: list[Any] = [vector_literal]
        if metadata:
            clauses.append("metadata @> %s::jsonb")
            params.append(json.dumps(metadata))
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        params.extend([vector_literal, top_k])
        sql = f"""
            SELECT chunk_id, document_id, title, content, metadata,
                   1 - (embedding <=> CAST(%s AS vector)) AS score
            FROM research_chunks
            {where}
            ORDER BY embedding <=> CAST(%s AS vector)
            LIMIT %s
        """
        results: list[SearchResult] = []
        with self.psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                for chunk_id, document_id, title, content, meta, score in cur.fetchall():
                    results.append(SearchResult(
                        chunk=Chunk(
                            chunk_id=chunk_id,
                            document_id=document_id,
                            title=title,
                            text=content,
                            metadata=meta or {},
                        ),
                        score=max(0.0, min(1.0, float(score))),
                    ))
        return results
