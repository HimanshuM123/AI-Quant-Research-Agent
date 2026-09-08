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
    R --> T[RiskAgent]
    T --> U[RiskEngine]
    U --> V[Risk metrics vs benchmark]
    V --> W[EvaluationAgent]
    W --> X[EvaluationEngine]
    X --> Y[ACCEPT or REJECT]
    Y --> Z[ReportAgent]
    Z --> AA[Research report]

    AA --> S[ResearchRunResponse]
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
    participant K as RiskAgent
    participant E as EvaluationAgent
    participant P as ReportAgent

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
    Graph->>K: calculate risk metrics
    K-->>Graph: strategy and benchmark risk results
    Graph->>E: apply acceptance checks
    E-->>Graph: decision and score
    Graph->>P: build final report
    P-->>Graph: summary, findings, next steps
    Graph-->>API: ResearchRunResponse
    API-->>Client: status, strategy, backtest, risk, evaluation, report, errors
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
  +--> RiskAgent --> RiskEngine --> Strategy and benchmark metrics
  |
  +--> EvaluationAgent --> ACCEPT or REJECT decision
  |
  +--> ReportAgent --> Final research report
  |
  v
ResearchRunResponse
```

## 4) Quick Project Summary

This project is a research-to-report pipeline. It fetches market data, retrieves relevant knowledge from the local RAG corpus, synthesizes a research hypothesis, converts it into a strategy DSL, runs a deterministic backtest, calculates strategy and benchmark risk metrics, decides whether the strategy passes objective acceptance checks, and produces a final research report.
