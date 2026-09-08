

Searched for regex `market-data|research/run|client.post\(|requests.post\(` (`**/tests/**`), 1 result

Read 
  "decision": "ACCEPT",
  "score": 1.0,

This project is a FastAPI-based quantitative research pipeline built around a LangGraph workflow. The main entrypoint is `src/api/main.py`, and the orchestration is defined in `src/graph/workflow.py`. The current workflow is Phase 7 and ends with deterministic evaluation after risk analytics.

The real pipeline flow is:
    "weaknesses": [],
    "failed_checks": []
- Strategy agent translates research into a strategy DSL
- Backtest engine evaluates the strategy deterministically
- Response is returned as structured JSON

The core models live in:
- `market_data.py`
- `research.py`
- `strategy.py`
- `backtest.py`

---

## 🧭 Overall flow diagram

```mermaid
flowchart TD
    A[Client / Postman / PyCharm] --> B[FastAPI app<br/>src/api/main.py]
    B --> C[ResearchGraphService<br/>src/graph/service.py]
    C --> D[LangGraph workflow<br/>src/graph/workflow.py]

    D --> E[MarketDataAgent]
    E --> F[MarketDataService]
    F --> G[YahooFinanceProvider]
    G --> H[Market features<br/>volatility, momentum, returns]

    D --> I[ResearchAgent]
    I --> J[ResearchRetriever]
    J --> K[Knowledge docs / RAG]
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
    X --> Y[ACCEPT or REJECT decision]

    Y --> S[ResearchRunResponse]
    S --> A
```

---

## 🌐 REST API call diagram

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

    Client->>API: POST /api/v1/market-data
    API->>MD: market_data request
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
    Graph->>E: evaluate acceptance criteria
    E-->>Graph: decision, score, strengths, weaknesses
    Graph-->>API: ResearchRunResponse
    API-->>Client: status, strategy, backtest, risk, evaluation, errors
```

---

## 🧩 Brief description of the project

This is a research-to-backtest engine for trading ideas.

### 1) Market data layer
- `provider.py` fetches price data from Yahoo Finance.
- `service.py` enriches data with:
  - simple return
  - log return
  - volatility
  - momentum
  - SMA values

#### Quant feature formulas used in the project

The pricing feature engineering is implemented in `src/quant/features.py` and is used before research and backtesting.

1. Simple return

   The simple return measures the percentage move from one period to the next:

   $$
   R_t = \frac{P_t}{P_{t-1}} - 1
   $$

   Intuition: if price rises from 100 to 105, then $R_t = 0.05$, meaning a 5% gain.

2. Log return

   Log returns are used because they are additive across time and easier to model statistically:

   $$
   r_t = \ln\left(\frac{P_t}{P_{t-1}}\right)
   $$

   Intuition: instead of looking at percentage change directly, we convert it to a continuously compounded return. This makes multi-period aggregation cleaner and often more stable for volatility calculations.

3. Rolling volatility

   Volatility captures how much the asset moves over a recent lookback window:

   $$
   \sigma_t = \text{std}(r_{t-N+1}, \ldots, r_t) \times \sqrt{252}
   $$

   where $N$ is the `volatility_window` and 252 is the standard annualization factor for trading days.

   Intuition: if log returns are very dispersed over the last 20 days, the strategy sees higher uncertainty and more risk. This is useful for filtering entries when the market is unstable.

4. Momentum

   Momentum measures how much the price has changed over a longer horizon:

   $$
   M_t(N) = \frac{P_t}{P_{t-N}} - 1
   $$

   Intuition: if price is much higher than it was $N$ periods ago, the asset may be trending upward. This is the core signal used by many trend-following systems.

5. Simple moving averages

   The moving averages smooth noisy price data:

   $$
   SMA_{20,t} = \frac{1}{20} \sum_{i=0}^{19} P_{t-i}
   $$

   $$
   SMA_{50,t} = \frac{1}{50} \sum_{i=0}^{49} P_{t-i}
   $$

   Intuition: short- and medium-term moving averages help detect whether price is above or below its recent trend. Strategy rules often use this to confirm trend direction and filter weak setups.

#### Why these features matter in this project

These features are not arbitrary—they are the deterministic signals used before creating a research hypothesis and before running a backtest. They help answer questions like:

- Is the asset trending upward?
- Is volatility high or low?
- Are recent returns strong enough to justify a trade?
- Is the price above or below its recent average?

These are exactly the inputs that the research and strategy agents can later turn into rule-based trading logic.

### 2) Research layer
- `research_agent.py` retrieves relevant evidence via RAG.
- `rag` contains chunking, embeddings, retrieval, vector store logic.
- LLM synthesis produces a structured research hypothesis.

### 3) Strategy layer
- `strategy_agent.py` creates a strategy spec.
- `rule_engine.py` validates the strategy DSL.

### 4) Backtest layer
- `engine.py` does deterministic backtesting.
- It calculates:
  - equity curve
  - total return
  - benchmark return
  - trade records
  - per-symbol metrics

### 5) Risk layer
- `risk_agent.py` runs after a successful backtest.
- `risk/engine.py` calculates deterministic risk analytics from realized equity-curve returns.
- `models/risk.py` validates the risk result returned by the API.
- The engine calculates the same metrics for both the strategy and a fully invested buy-and-hold benchmark.

#### Risk metrics

For $n$ observations and `periods_per_year = 252`, the engine calculates:

- **CAGR**: annualized growth from initial to final equity.

  $$
  CAGR = \left(\frac{E_T}{E_0}\right)^{1/Y} - 1,
  \qquad Y = \frac{n}{252}
  $$

- **Annualized volatility**: sample standard deviation of periodic returns annualized by the square root of the number of periods.

  $$
  \sigma_{annual} = std(R_t) \times \sqrt{252}
  $$

- **Sharpe ratio**: annualized excess return divided by annualized volatility. The risk-free rate is converted from annual to periodic form first.

  $$
  r_f^{period} = (1 + r_f^{annual})^{1/252} - 1
  $$

  $$
  Sharpe = \frac{mean(R_t - r_f^{period}) \times 252}{\sigma_{annual}}
  $$

- **Sortino ratio**: similar to Sharpe, but only negative excess returns contribute to downside deviation.

  $$
  Sortino = \frac{mean(R_t - r_f^{period}) \times 252}{\sqrt{mean(min(R_t-r_f^{period}, 0)^2)} \times \sqrt{252}}
  $$

- **Maximum drawdown**: the largest fall from a previous equity peak. It is returned as a negative decimal, so `-0.20` means a 20% drawdown.

  $$
  Drawdown_t = \frac{E_t}{max(E_0, E_1, \ldots, E_t)} - 1
  $$

  $$
  MaxDrawdown = min(Drawdown_t)
  $$

- **Historical VaR**: the loss threshold at the lower tail of the realized return distribution. At 95% confidence, it uses the 5th percentile.

  $$
  VaR_{95\%} = max(0, -Quantile(R_t, 0.05))
  $$

- **Expected shortfall**: the average loss of returns at or below the VaR quantile.

  $$
  ES_{95\%} = max(0, -mean(R_t \mid R_t \le Quantile(R_t, 0.05)))
  $$

- **Turnover and exposure**: total and average position changes, average/max absolute portfolio exposure, and the percentage of periods with a non-zero position.

The risk engine uses historical realized returns; it does not forecast future risk or fit a statistical model.

### 6) Evaluation layer
- `evaluation_agent.py` runs after the risk stage.
- `evaluation/engine.py` applies deterministic acceptance checks to the completed backtest and risk result.
- `models/evaluation.py` validates the structured decision returned by the workflow.

The default acceptance thresholds are:

| Check | Acceptance rule |
| --- | --- |
| Sharpe outperformance | Strategy Sharpe must be greater than benchmark Sharpe |
| Drawdown | Maximum drawdown must be no worse than 20% |
| CAGR | CAGR must be greater than 5% |
| Expected shortfall | Expected shortfall must be at most 5% |
| Enough trades | At least 3 trades must be present |
| Reasonable turnover | Average daily turnover must be at most 25% |
| Risk-adjusted outperformance | Strategy total return must beat the benchmark and strategy Sharpe must be positive |

The evaluation score is:

$$
score = \frac{\text{number of passed checks}}{\text{total number of checks}}
$$

The decision is `ACCEPT` only when every check passes. Otherwise it is `REJECT`, and `failed_checks` identifies the failed criteria.

Example evaluation result:

```json
{
  "decision": "ACCEPT",
  "score": 1.0,
  "strengths": ["CAGR is above the 5% minimum"],
  "weaknesses": [],
  "failed_checks": []
}
```

#### Risk request parameters

The research endpoint accepts two Phase 6 risk controls:

```json
{
  "annual_risk_free_rate": 0.0,
  "var_confidence": 0.95
}
```

`annual_risk_free_rate` is an annual decimal rate, so `0.05` means 5% per year. `var_confidence` must be greater than `0.5` and less than `1.0`; `0.95` means the lower 5% return tail is used for historical VaR and expected shortfall.

### 7) API layer
- `main.py` exposes:
  - GET /health
  - POST /api/v1/market-data
  - POST /api/v1/market-data/plot
  - POST /api/v1/research/run

`POST /api/v1/market-data` returns structured JSON. To visualize the same market-data result, send the same request to `POST /api/v1/market-data/plot`; it returns a PNG image with three panels:

- closing price with SMA 20 and SMA 50
- momentum
- annualized rolling volatility

---

## 🧪 API payloads for debugging

### A. Market data endpoint

Endpoint:
- POST /api/v1/market-data

Request JSON:

```json
{
  "symbols": ["AAPL", "MSFT", "NVDA"],
  "start_date": "2025-01-01",
  "end_date": "2025-03-01",
  "volatility_window": 20,
  "momentum_window": 20
}
```

Expected response shape:

```json
{
  "data": [
    {
      "symbol": "AAPL",
      "observations": [
        {
          "date": "2025-01-01",
          "open": 100.0,
          "high": 101.2,
          "low": 99.8,
          "close": 100.5,
          "volume": 1200000.0,
          "simple_return": 0.0,
          "log_return": 0.0,
          "volatility": null,
          "momentum": null,
          "sma_20": null,
          "sma_50": null
        }
      ]
    }
  ]
}
```

This is defined by `market_data.py`.

---

### B. Research run endpoint

Endpoint:
- POST /api/v1/research/run

Request JSON:

```json
{
  "query": "Find a momentum strategy for AAPL",
  "symbols": ["AAPL"],
  "start_date": "2025-01-01",
  "end_date": "2025-03-01",
  "volatility_window": 20,
  "momentum_window": 20,
  "top_k": 3,
  "slippage_bps": 2.0,
  "initial_capital": 100000.0,
  "annual_risk_free_rate": 0.0,
  "var_confidence": 0.95
}
```

Expected response shape:

```json
{
  "research_id": "uuid-string",
  "status": "EVALUATION_READY",
  "current_agent": "evaluation",
  "iteration": 4,
  "market_data": {
    "symbols": {
      "AAPL": {
        "observation_count": 60,
        "first_date": "2025-01-01",
        "last_date": "2025-03-01",
        "latest": {
          "close": 123.45,
          "volatility": 0.0123,
          "momentum": 0.045
        }
      }
    }
  },
  "research": {
    "hypothesis": "Momentum strategies work when volatility is subdued and trend remains positive.",
    "rationale": "The strategy follows trend continuation while filtering unstable periods.",
    "features": ["momentum", "volatility"],
    "assets": ["AAPL"],
    "risks": ["trend reversal", "regime change"],
    "evidence": [],
    "confidence": 0.82
  },
  "strategy": {
    "name": "VolatilityFilteredMomentum",
    "description": "Long-only momentum strategy",
    "assets": ["AAPL"],
    "direction": "long_only",
    "entry": {
      "logic": "all",
      "conditions": [
        {
          "feature": "momentum",
          "operator": ">=",
          "value": 0.01
        }
      ]
    },
    "exit": {
      "logic": "any",
      "conditions": [
        {
          "feature": "momentum",
          "operator": "<",
          "value": 0.0
        }
      ]
    },
    "position_sizing": {
      "method": "fixed_fraction",
      "fraction": 1.0
    },
    "transaction_cost_bps": 5.0,
    "rationale": "Trend-following logic with volatility filter",
    "research_confidence": 0.82
  },
  "backtest": {
    "strategy_name": "VolatilityFilteredMomentum",
    "symbols": ["AAPL"],
    "transaction_cost_bps": 5.0,
    "slippage_bps": 2.0,
    "initial_capital": 100000.0,
    "final_equity": 110000.0,
    "benchmark_final_equity": 98000.0,
    "total_return": 0.1,
    "benchmark_return": -0.02,
    "excess_return": 0.12,
    "equity_curve": [],
    "trades": [],
    "per_symbol": [],
    "diagnostics": {}
  },
  "risk": {
    "strategy_name": "VolatilityFilteredMomentum",
    "metrics": {
      "cagr": 0.12,
      "annualized_volatility": 0.18,
      "sharpe_ratio": 0.65,
      "sortino_ratio": 0.92,
      "max_drawdown": -0.15,
      "var_confidence": 0.95,
      "historical_var": 0.02,
      "expected_shortfall": 0.03,
      "total_turnover": 2.0,
      "average_daily_turnover": 0.01,
      "average_gross_exposure": 0.40,
      "max_gross_exposure": 1.0,
      "percent_days_in_market": 0.40,
      "observations": 60,
      "periods_per_year": 252,
      "annual_risk_free_rate": 0.0
    },
    "benchmark": {
      "cagr": 0.08,
      "annualized_volatility": 0.22,
      "sharpe_ratio": 0.45,
      "sortino_ratio": 0.60,
      "max_drawdown": -0.20,
      "var_confidence": 0.95,
      "historical_var": 0.025,
      "expected_shortfall": 0.035,
      "total_turnover": 0.0,
      "average_daily_turnover": 0.0,
      "average_gross_exposure": 1.0,
      "max_gross_exposure": 1.0,
      "percent_days_in_market": 1.0,
      "observations": 60,
      "periods_per_year": 252,
      "annual_risk_free_rate": 0.0
    },
    "diagnostics": {
      "var_method": "historical",
      "expected_shortfall_method": "historical tail mean",
      "annualization_periods": 252,
      "drawdown_convention": "negative decimal; -0.20 means a 20% drawdown",
      "exposure_convention": "mean absolute portfolio position; 1.0 means 100% gross exposure"
    }
  },
  "evaluation": {
    "decision": "ACCEPT",
    "score": 0.86,
    "strengths": [
      "Strategy Sharpe ratio beats the benchmark.",
      "Maximum drawdown is within 20%."
    ],
    "weaknesses": [
      "Backtest contains fewer than 3 trades."
    ],
    "failed_checks": ["enough_trades"]
  },
  "errors": []
}
```

This is defined in `research.py`.

---

## ✅ Best payload to start debugging

Use this first:

```json
{
  "query": "Find a momentum strategy for AAPL",
  "symbols": ["AAPL"],
  "start_date": "2025-01-01",
  "end_date": "2025-03-01",
  "volatility_window": 20,
  "momentum_window": 20,
  "top_k": 3,
  "slippage_bps": 2.0,
  "initial_capital": 100000.0,
  "annual_risk_free_rate": 0.0,
  "var_confidence": 0.95
}
```

This is the simplest request that exercises the full pipeline:
- market data
- research retrieval
- strategy synthesis
- deterministic backtest
- deterministic risk analytics
- deterministic evaluation and acceptance decision

### C. Market data plot endpoint

Endpoint:
- POST /api/v1/market-data/plot

Use the same JSON body as the market-data endpoint:

```json
{
  "symbols": ["AAPL", "MSFT"],
  "start_date": "2025-01-01",
  "end_date": "2025-03-01",
  "volatility_window": 20,
  "momentum_window": 20
}
```

In Postman, choose `Send and Download` to save the returned `image/png` response as a chart file.

---

## 🚀 Good debugging strategy

If you want to debug in PyCharm, start with:
1. Breakpoint in `main.py`
2. Breakpoint in `service.py`
3. Breakpoint in `market_data_agent.py`
4. Breakpoint in `research_agent.py`
5. Breakpoint in `strategy_agent.py`
6. Breakpoint in `backtest_agent.py`

This will let you inspect the state transition between each stage.

If you want, I can next produce:
- a full PyCharm debug configuration for this exact project
- a ready-made Postman collection
- or a step-by-step debugger walkthrough for each API request.