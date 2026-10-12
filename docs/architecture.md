# Architecture — Phase 3

```text
React (future)
   |
Java 21 / Spring Boot
   |
REST / Kafka (future)
   |
FastAPI
   |
ResearchGraphService
   |
LangGraph
   |
START
   |
MarketDataAgent
   |-- MarketDataTool -> Provider -> Quant Feature Engine
   |
   +-- failure ----------------------------> END
   |
ResearchAgent
   |-- compact market summary
   |-- ResearchRetriever
   |      |-- Markdown/PDF loaders
   |      |-- chunking
   |      |-- embedding provider
   |      +-- InMemoryVectorStore / PgVectorStore
   |
   +-- ResearchSynthesizer
          |-- OpenAI structured output (production)
          +-- deterministic offline implementation (tests)
   |
Structured ResearchHypothesis
   |
END
```

## Design principles

1. Agent nodes orchestrate; deterministic services calculate financial quantities.
2. RAG literature claims are tied to retrieved evidence records.
3. Raw market observations are not sent wholesale to the LLM; the Research Agent builds a compact summary.
4. LLM output is validated with Pydantic before entering graph state.
5. LLM providers, embedding providers, vector stores and market-data providers are replaceable behind interfaces.
6. Graph routing stops immediately on upstream market-data failure.
7. Test paths are offline and deterministic.




Research a 20-day momentum strategy for the selected stocks. Use a 20-day volatility filter to avoid unusually volatile assets, then evaluate the strategy against buy-and-hold, including transaction costs and risk metrics.