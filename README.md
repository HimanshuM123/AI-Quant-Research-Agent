# AI Quant Research Agent

## Current milestone: Phase 5 — Deterministic Backtesting Engine

Phase 5 turns the validated Strategy DSL into an auditable historical simulation. LLMs still do not calculate returns, positions, P&L, costs, or benchmark performance. Those are deterministic Python operations.

### End-to-end workflow

```text
START
  ↓
Market Data Agent
  ↓
Research Agent + RAG
  ↓
Strategy Generation Agent
  ↓
Validated Strategy DSL
  ↓
Backtest Agent
  ├── signal generation
  ├── one-bar position shift
  ├── transaction costs
  ├── slippage
  ├── equity curve
  ├── trade ledger
  └── buy-and-hold benchmark
  ↓
BACKTEST_READY
  ↓
END
```

## Backtesting mathematics

A strategy signal formed using information available at bar `t` is not allowed to earn bar `t`'s return. The executable position is shifted by one bar:

```text
position[t] = target_position[t-1]
```

Gross strategy return:

```text
R_gross,t = w_(t-1) * R_t
```

Turnover:

```text
turnover_t = |w_t - w_(t-1)|
```

Costs:

```text
transaction_cost_t = turnover_t * transaction_cost_bps / 10000
slippage_cost_t    = turnover_t * slippage_bps / 10000
```

Net strategy return:

```text
R_strategy,t = R_gross,t - transaction_cost_t - slippage_cost_t
```

Equity curve:

```text
Equity_t = Equity_(t-1) * (1 + R_strategy,t)
```

For multiple strategy assets, Phase 5 uses an equal-weight portfolio of per-symbol strategy returns. The benchmark is equal-weight buy-and-hold across the same assets.

## New Phase 5 code

```text
ai-engine/src/backtesting/
├── __init__.py
└── engine.py

ai-engine/src/agents/
└── backtest_agent.py

ai-engine/src/models/
└── backtest.py
```

### Outputs

The backtest result contains:

- initial/final equity
- total strategy return
- buy-and-hold benchmark return
- excess return
- daily equity curve
- trade ledger with signal and execution dates
- transaction/slippage costs
- per-symbol results
- diagnostics documenting the one-bar execution lag

## Example API request

```bash
curl -X POST http://localhost:8000/api/v1/research/run \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Research a momentum strategy for AAPL and MSFT with a volatility filter",
    "symbols": ["AAPL", "MSFT"],
    "start_date": "2024-01-01",
    "end_date": "2025-01-01",
    "volatility_window": 20,
    "momentum_window": 20,
    "top_k": 5,
    "slippage_bps": 2.0,
    "initial_capital": 100000
  }'
```

Expected terminal status:

```json
{
  "status": "BACKTEST_READY",
  "current_agent": "backtest",
  "backtest": {
    "strategy_name": "VolatilityFilteredMomentum",
    "initial_capital": 100000.0,
    "final_equity": 0,
    "benchmark_final_equity": 0,
    "total_return": 0,
    "benchmark_return": 0,
    "excess_return": 0,
    "equity_curve": [],
    "trades": []
  }
}
```

Values above are placeholders; the API returns values computed from actual historical observations.

## Testing

The dependency-independent suite currently has 14 passing tests, including explicit checks that:

- the entry signal is shifted one bar before earning returns;
- transaction costs and slippage reduce performance when turnover occurs;
- BUY/SELL events appear in the trade ledger;
- a benchmark equity curve is produced;
- unsupported/future features are rejected before the backtester.

The container used to build this phase does not have `langgraph` installed, so the LangGraph integration/API tests cannot be executed here. Install `ai-engine/requirements.txt` locally to run the full suite.

## Next milestone

Phase 6 adds a deterministic Risk Agent: CAGR, annualized volatility, Sharpe, Sortino, maximum drawdown, VaR, Expected Shortfall, turnover, exposure, and additional risk diagnostics.

## Phase 6 — Risk Agent

The workflow now continues from the deterministic backtest into deterministic risk analytics:

`Market Data -> RAG Research -> Strategy DSL -> Backtest -> Risk`

The Risk Agent calculates from realized backtest returns and portfolio state:

- CAGR
- annualized volatility
- Sharpe ratio
- Sortino ratio
- maximum drawdown
- historical Value at Risk (VaR)
- historical Expected Shortfall (ES)
- total and average daily turnover
- average and maximum gross exposure
- percentage of days in market
- benchmark risk metrics for equal-weight buy-and-hold

The backtest equity curve now carries daily `turnover` and `gross_exposure` so the Risk Agent consumes actual portfolio state rather than inferring exposure from trades.

### Research API Phase 6 parameters

```json
{
  "query": "Research a momentum strategy for AAPL and MSFT with a volatility filter",
  "symbols": ["AAPL", "MSFT"],
  "start_date": "2020-01-01",
  "end_date": "2026-01-01",
  "volatility_window": 20,
  "momentum_window": 20,
  "top_k": 5,
  "slippage_bps": 2,
  "initial_capital": 100000,
  "annual_risk_free_rate": 0.04,
  "var_confidence": 0.95
}
```

Successful terminal state: `RISK_READY`.


1) From the project root:

cd "D:\Workspace\AI_Quant_Research_Agent_Platform\ai-quant-research-agent"

docker compose up -d --build
docker compose ps

2) Start the frontend in a separate terminal:
cd "D:\Workspace\AI_Quant_Research_Agent_Platform\ai-quant-research-agent\frontend"

npm install
npm run dev -- --host 0.0.0.0

Open:

Frontend: http://localhost:5173
AI API docs: http://localhost:8000/docs
Java health: http://localhost:8080/actuator/health

3) Stop the backend:
cd "D:\Workspace\AI_Quant_Research_Agent_Platform\ai-quant-research-agent"
docker compose down


Intellij IDEA--------------------------------------------------
A) Env Variables:
DATABASE_URL=jdbc:postgresql://localhost:5432/quantagent;DATABASE_USERNAME=quantagent;DATABASE_PASSWORD=quantagent;KAFKA_BOOTSTRAP_SERVERS=localhost:9092;REDIS_HOST=localhost;PYTHON_AI_BASE_URL=http://localhost:8000;QUANT_SECURITY_ENABLED=false

com.portfolio.quant.QuantPlatformApplication

Pycharm--------------------------------------------------------
src.api.main:app --reload --host 0.0.0.0 --port 8000

D:\Workspace\AI_Quant_Research_Agent_Platform\ai-quant-research-agent\ai-engine

Env variables: 
PYTHONPATH=D:\Workspace\AI_Quant_Research_Agent_Platform\ai-quant-research-agent\ai-engine