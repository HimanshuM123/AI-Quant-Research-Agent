# AI Quant Research Agent - Flow Diagrams

## 1) Overall System Flow

```mermaid
flowchart TD
    A[Client / Postman / PyCharm] --> B[FastAPI app\nsrc/api/main.py]
    B --> C[ResearchGraphService\nsrc/graph/service.py]
    C --> D[LangGraph workflow\nsrc/graph/workflow.py]

    D --> E[MarketDataAgent]
    E --> F[MarketDataService]
    F --> G[YahooFinanceProvider]
    G --> H[Market features\nvolatility, momentum, returns]

    D --> I[ResearchAgent]
    I --> J[ResearchRetriever]
    J --> K[Knowledge docs / RAG\nknowledge/strategy_notes]
    I --> L[ResearchSynthesizer]

    D --> M[StrategyAgent]
    M --> N[StrategySynthesizer]
    N --> O[RuleEngine validation]

    D --> P[BacktestAgent]
    P --> Q[BacktestEngine]
    Q --> R[Portfolio + trade result]

    R --> S[ResearchRunResponse]
    S --> A
```

## 2) REST API Call Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI API
    participant Graph as ResearchGraphService
    participant MD as MarketDataAgent
    participant R as ResearchAgent
    participant S as StrategyAgent
    participant B as BacktestAgent

    Client->>API: POST /api/v1/market-data
    API->>MD: market data request
    MD->>API: Symbol market observations
    API-->>Client: MarketDataResponse

    Client->>API: POST /api/v1/research/run
    API->>Graph: run(request)
    Graph->>MD: fetch market data
    MD-->>Graph: market_data
    Graph->>R: research from query + evidence
    R-->>Graph: research hypothesis
    Graph->>S: build strategy
    S-->>Graph: strategy spec
    Graph->>B: backtest strategy
    B-->>Graph: backtest result
    Graph-->>API: ResearchRunResponse
    API-->>Client: status, strategy, backtest, errors
```

## 3) Simple Text Version

```text
Client
  |
  v
FastAPI API
  |
  v
ResearchGraphService
  |
  +--> MarketDataAgent --> MarketDataService --> YahooFinanceProvider
  |
  +--> ResearchAgent --> RAG Retriever --> knowledge/strategy_notes/*.md
  |
  +--> StrategyAgent --> RuleEngine
  |
  +--> BacktestAgent --> BacktestEngine
  |
  v
ResearchRunResponse
```

## 4) Quick Project Summary

This project is a research-to-backtest pipeline. It fetches market data, retrieves relevant knowledge from the local RAG corpus, synthesizes a research hypothesis, converts it into a strategy DSL, and runs a deterministic backtest before returning the final response.
