# RAG and Vector Database Architecture

This document explains how retrieval-augmented generation (RAG) works in the AI Quant Research Agent and how the vector store supports research evidence retrieval.

## 1. Purpose

The RAG layer gives the Research Agent access to strategy knowledge before it creates a research hypothesis. It retrieves relevant passages from the local research corpus and passes those passages to the research synthesizer as structured evidence.

The RAG layer is separate from market data processing:

- Market data is fetched and summarized by deterministic Python services.
- Research documents provide contextual evidence about strategy ideas, risks, and methodology.
- The LLM synthesizes a hypothesis from the user query, compact market data, and retrieved evidence.

## 2. Repository Components

| Responsibility | Implementation |
|---|---|
| Document loading | `ai-engine/src/rag/documents.py` |
| Chunking | `ai-engine/src/rag/chunking.py` |
| Embedding interface | `ai-engine/src/rag/embeddings.py` |
| In-memory vector store | `InMemoryVectorStore` |
| PostgreSQL vector store | `PgVectorStore` in `ai-engine/src/rag/vector_store.py` |
| Retrieval orchestration | `ai-engine/src/rag/retriever.py` |
| Research integration | `ai-engine/src/agents/research_agent.py` |
| Knowledge corpus | `ai-engine/knowledge/` |
| RAG tests | `ai-engine/tests/test_rag.py` |

## 3. High-Level Architecture

```mermaid
flowchart TD
    UI[React UI] --> API[FastAPI research API]
    API --> GRAPH[ResearchGraphService]
    GRAPH --> AGENT[ResearchAgent]

    AGENT --> QUERY[User research query]
    AGENT --> MARKET[Compact market summary]
    AGENT --> RETRIEVER[ResearchRetriever]

    RETRIEVER --> STORE{Configured vector store}
    STORE --> MEMORY[InMemoryVectorStore]
    STORE --> PG[PostgreSQL + pgvector]

    RETRIEVER --> EVIDENCE[Evidence records]
    QUERY --> SYNTH[ResearchSynthesizer]
    MARKET --> SYNTH
    EVIDENCE --> SYNTH
    SYNTH --> HYPOTHESIS[Validated ResearchHypothesis]
```

## 4. Document Ingestion Flow

Documents are loaded from the knowledge directory when `ResearchRetriever.from_directory()` is created.

The loader currently supports Markdown and PDF files:

- Markdown files are discovered recursively with `*.md`.
- PDF files are discovered recursively with `*.pdf`.
- Empty documents are ignored.
- The first Markdown heading becomes the document title when available.
- File type and path are retained as metadata.

Each document is normalized and split into overlapping chunks. The default chunk size is 900 characters with a 120-character overlap. Each chunk receives a stable ID such as:

```text
strategy_notes/momentum.md#chunk-0
```

```mermaid
flowchart LR
    FILES[Markdown and PDF files] --> LOAD[load_documents]
    LOAD --> DOC[Document objects]
    DOC --> NORMALIZE[Normalize whitespace]
    NORMALIZE --> CHUNK[chunk_document]
    CHUNK --> ITEMS[Chunk objects]
    ITEMS --> EMBED[EmbeddingProvider.embed]
    EMBED --> VECTORS[Embedding vectors]
    ITEMS --> STORE[Vector store]
    VECTORS --> STORE
```

A chunk contains:

```text
chunk_id
 document_id
 title
 text
 metadata
```

Metadata includes values such as source path, document type, page count for PDFs, and chunk index.

## 5. Embeddings

The embedding layer is defined by the `EmbeddingProvider` protocol:

```python
class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        ...
```

The current default is `HashEmbeddingProvider` with 384 dimensions. It is dependency-free and deterministic:

1. Tokenize the text.
2. Hash each token into a vector bucket.
3. Count bucket occurrences.
4. Normalize the vector.

This provider is useful for offline development and tests. It is not a semantic model comparable to OpenAI or transformer embeddings. A production provider can replace it behind the same interface without changing the retriever or Research Agent.

## 6. Vector Store Options

### 6.1 In-memory mode

In-memory mode is the default:

```text
RAG_STORE=memory
```

`InMemoryVectorStore` stores pairs of chunks and vectors in the Python process. Queries are embedded, compared with cosine similarity, sorted by score, and truncated to `top_k` results.

Advantages:

- No database dependency.
- Fast startup for tests and local development.
- Fully deterministic with the hash embedding provider.

Limitations:

- Data disappears when the process restarts.
- Every process builds its own index.
- It is not suitable for a multi-instance production deployment.

### 6.2 PostgreSQL and pgvector mode

The production-oriented option is PostgreSQL with the `pgvector` extension:

```text
RAG_STORE=pgvector
POSTGRES_DSN=postgresql://quantagent:quantagent@postgres:5432/quantagent
```

`PgVectorStore` creates the `research_chunks` table if needed and stores:

```text
chunk_id       TEXT primary key
document_id    TEXT
title          TEXT
content        TEXT
metadata       JSONB
embedding      vector(384)
```

The store searches with pgvector cosine distance using the `<=>` operator. Metadata filters are translated to a JSONB containment condition.

```mermaid
flowchart TD
    CHUNK[Chunk text and metadata] --> EMBED[384-dimensional embedding]
    EMBED --> INSERT[INSERT or upsert]
    CHUNK --> INSERT
    INSERT --> TABLE[(research_chunks)]

    QUERY[User query] --> QEMBED[Query embedding]
    QEMBED --> SEARCH[pgvector cosine search]
    TABLE --> SEARCH
    FILTER[Optional metadata filter] --> SEARCH
    SEARCH --> TOPK[Top-k SearchResult objects]
```

The project already includes a `pgvector/pgvector:pg16` PostgreSQL image in `docker-compose.yml`. The same PostgreSQL service is also used by the Java platform for research-run persistence.

## 7. Query-Time Retrieval Flow

When a research request reaches the Research Agent:

1. The agent reads `top_k` from graph state, defaulting to 5.
2. `ResearchRetriever.retrieve()` embeds the query.
3. The configured vector store calculates similarity against stored chunks.
4. Results are sorted from highest to lowest score.
5. Each result is converted to an `Evidence` model.
6. Evidence excerpts are limited to 700 characters.
7. The ResearchSynthesizer receives the query, market summary, and evidence.
8. The synthesizer returns a validated `ResearchHypothesis`.

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant Graph as ResearchGraphService
    participant Agent as ResearchAgent
    participant Retriever as ResearchRetriever
    participant Store as VectorStore
    participant LLM as ResearchSynthesizer

    Client->>API: POST /api/v1/research/run
    API->>Graph: ResearchRunRequest
    Graph->>Agent: Query + market data state
    Agent->>Retriever: retrieve(query, top_k)
    Retriever->>Store: search(query, top_k)
    Store-->>Retriever: Ranked chunks and scores
    Retriever-->>Agent: Evidence records
    Agent->>LLM: Query + market summary + evidence
    LLM-->>Agent: ResearchHypothesis
    Agent-->>Graph: RESEARCH_READY
    Graph-->>API: Structured research response
```

## 8. Evidence Contract

Retrieved passages are returned as structured evidence rather than untracked text:

```json
{
  "source_id": "strategy_notes/momentum.md#chunk-0",
  "title": "Momentum Strategy",
  "excerpt": "Relevant source passage...",
  "score": 0.82,
  "metadata": {
    "type": "markdown",
    "chunk_index": 0
  }
}
```

The evidence records become part of `ResearchHypothesis.evidence`. This makes the generated research report auditable: the user can inspect which source chunks influenced the hypothesis.

## 9. End-to-End Research Flow

```mermaid
flowchart TD
    START([Research request]) --> MD[MarketDataAgent]
    MD --> SUMMARY[Compact market summary]
    START --> RQ[Research query]

    RQ --> RETRIEVE[Retrieve top-k evidence]
    RETRIEVE --> SOURCES[Ranked source chunks]
    SOURCES --> EVIDENCE[Evidence model]
    SUMMARY --> SYNTH[ResearchSynthesizer]
    EVIDENCE --> SYNTH
    RQ --> SYNTH

    SYNTH --> VALIDATE[Pydantic validation]
    VALIDATE --> HYPOTHESIS[ResearchHypothesis]
    HYPOTHESIS --> STRATEGY[StrategyAgent]
    STRATEGY --> BACKTEST[Deterministic BacktestAgent]
    BACKTEST --> RISK[RiskAgent]
    RISK --> REPORT[ReportAgent]
    REPORT --> END([Research report])
```

RAG supports the qualitative research stage. It does not calculate returns, risk, positions, or portfolio performance. Those quantities are calculated later by deterministic quant services.

## 10. Configuration and Deployment Modes

### Offline development and tests

```text
RAG_STORE=memory
```

This mode requires no PostgreSQL connection and is used by the dependency-light RAG tests.

### PostgreSQL vector mode

```text
RAG_STORE=pgvector
POSTGRES_DSN=postgresql://quantagent:quantagent@localhost:5432/quantagent
```

This mode requires:

- PostgreSQL
- The `vector` extension
- `psycopg`
- An embedding provider whose dimension matches the configured vector column

### Future production improvements

The current architecture leaves clear replacement points for:

- OpenAI or transformer-based semantic embeddings.
- A dedicated vector database such as Qdrant.
- Batch ingestion and incremental document updates.
- Embedding versioning and re-indexing.
- Vector indexes such as IVFFlat or HNSW for larger corpora.
- Document-level access control and tenant filtering.
- Reranking after initial vector retrieval.

## 11. Design Boundaries

1. The Research Agent orchestrates retrieval; it does not implement vector math.
2. The embedding provider is replaceable through an interface.
3. The vector store is replaceable through the `VectorStore` protocol.
4. Market data is summarized before reaching the synthesizer.
5. Evidence is structured and retained in the research response.
6. The deterministic backtest and risk stages do not depend on the vector database.
7. In-memory mode keeps tests offline; pgvector mode provides persistence for deployment.
