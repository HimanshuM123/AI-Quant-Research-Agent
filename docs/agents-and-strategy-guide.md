# Market Data, Research, Strategy, and Backtest Agents

## Quick overview

The research workflow turns a question about assets and a historical date range into a testable strategy, then simulates how that strategy would have behaved on the supplied historical data.

```text
Request (query, symbols, dates, parameters)
        |
        v
Market Data Agent -> historical prices and calculated features
        |
        v
Research Agent -> hypothesis grounded in retrieved research evidence
        |
        v
Strategy Agent -> validated, machine-readable entry and exit rules
        |
        v
Backtest Agent -> historical simulation, costs, trades, and benchmark comparison
        |
        v
Risk -> Evaluation -> Report
```

- **Market Data Agent:** obtains historical price/volume observations and prepares the numeric inputs used downstream.
- **Research Agent:** combines a compact summary of those observations with retrieved knowledge to form a falsifiable research hypothesis. It is not the strategy executor.
- **Strategy Agent:** translates the hypothesis into a constrained `StrategySpec`—the actual rules for entering, exiting, and sizing positions.
- **Backtest Agent:** applies those rules to historical observations and calculates simulated returns, trading costs, trades, and a buy-and-hold comparison using deterministic Python code.

The system is achieving a **repeatable, evidence-informed research and evaluation workflow**: it makes a market idea explicit, tests it against history under stated assumptions, and returns artifacts that can be inspected. It is a research/backtesting system, not a live trading or investment-advice system. A historical result does not establish that a strategy will work in the future.

## Detailed understanding

### 1. The request and shared workflow state

The research request supplies a natural-language `query`, one or more `symbols`, a `start_date` and `end_date`, and parameters such as momentum/volatility windows, number of retrieved evidence items (`top_k`), slippage, and initial capital.

The graph runs the stages in order and passes a shared state between them. Each stage writes its result and a status; if a stage fails, the graph stops rather than passing a successful-looking empty result to later stages.

### 2. Market Data Agent: what data becomes strategy input

The agent delegates to a market data tool and service. The default provider downloads adjusted historical OHLCV data (open, high, low, close, and volume) from Yahoo Finance for each requested symbol. The provider can be replaced, which also allows tests to use controlled data.

The service deterministically adds features to the price history:

| Feature | Meaning |
| --- | --- |
| `simple_return` | `close[t] / close[t-1] - 1` |
| `log_return` | `ln(close[t] / close[t-1])` |
| `momentum` | `close[t] / close[t-N] - 1`, where `N` is the request's momentum window |
| `volatility` | Rolling standard deviation of log returns times `sqrt(252)`, annualized |
| `sma_20`, `sma_50` | 20- and 50-observation simple moving averages of close |

The result contains all dated observations and a compact latest-data summary. The Research Agent uses that compact summary; the Backtest Agent uses the historical observations. Early rows can have missing rolling features until enough history exists. A rule condition with a missing value does not pass.

### 3. Research Agent: turning a question into a hypothesis

The Research Agent retrieves up to `top_k` relevant evidence chunks from the local knowledge directory's research documents. It supplies the query, requested assets, compact market summary, and retrieved evidence to a research synthesizer. The output is a structured hypothesis with a rationale, candidate features, assets, risks, evidence records, and confidence.

If `OPENAI_API_KEY` is configured, the application builds the OpenAI structured-output synthesizer. Otherwise it uses a deterministic offline synthesizer. The deterministic version creates a momentum-plus-volatility-and-trend hypothesis and records evidence returned by retrieval; the OpenAI version is instructed to use supplied evidence for literature claims and not invent performance metrics.

The hypothesis is an idea to test—not proof that the idea works, and not a direct buy/sell decision. It also does not itself specify the actual executable thresholds; that is the Strategy Agent's next step.

### 4. Strategy Agent: how a hypothesis becomes a strategy

The Strategy Agent validates the research hypothesis, asks a strategy synthesizer for a `StrategySpec`, then validates that spec with the `RuleEngine`. The spec is structured data, not generated Python or arbitrary executable code. It includes:

- strategy name, description, assets, and rationale;
- entry and exit rule groups (`all` or `any`);
- allowed market features and comparison operators;
- long-only direction and fixed-fraction position sizing;
- transaction-cost assumption; and
- the research confidence copied into the strategy output.

With `OPENAI_API_KEY`, the strategy synthesizer requests schema-constrained output and provides the allowed features and constraints. Without it, the deterministic synthesizer supplies the reproducible default strategy below. In either case, the Rule Engine rejects unsupported features and evaluates the validated rules against each observation.

#### Deterministic fallback strategy

The offline strategy is named `VolatilityFilteredMomentum`. For each requested asset, it:

**Enters when all conditions are true:**

```text
momentum > 0.05
AND close > sma_50
AND volatility < 0.35
```

That means momentum over the requested window is above 5%, close is above its 50-observation average, and annualized rolling volatility is below 35%.

**Exits when either condition is true:**

```text
momentum < 0
OR close < sma_50
```

The fallback uses a fixed-fraction size of `1.0` (fully invested in the relevant asset sleeve while active), assumes transaction costs of 5 basis points per unit of turnover, and is long-only. These are the fallback's settings, not guarantees that an OpenAI-generated strategy has the same thresholds: inspect the returned `strategy` object for the actual run.

### 5. Backtest Agent: what is simulated

The Backtest Agent validates that both market data and a strategy exist, parses the strategy against the same `StrategySpec` schema, then calls the deterministic `BacktestEngine`. It does not ask an LLM to calculate financial results.

For every strategy asset, the engine walks through observations in date order and evaluates entry/exit conditions to form a target position. A position can be flat (`0`) or long up to the configured sizing fraction. Short positions are not supported by this strategy schema.

#### Signal timing and look-ahead protection

A signal computed from bar `t` is not allowed to earn the return for that same bar. The engine shifts the target position by one observation:

```text
position[t] = target_position[t-1]
```

So the signal at one bar becomes the simulated position on the next available bar. The engine's diagnostics report a one-bar signal/execution lag. This reduces a common backtesting error called look-ahead bias, where a strategy is unrealistically credited with a return using information that was not yet available when it supposedly traded.

#### Return, turnover, and costs

For each symbol and observation, the engine calculates:

```text
gross strategy return[t] = position[t] * simple_return[t]
turnover[t]              = abs(position[t] - position[t-1])
transaction cost[t]      = turnover[t] * transaction_cost_bps / 10,000
slippage cost[t]         = turnover[t] * slippage_bps / 10,000
net strategy return[t]   = gross strategy return[t]
                           - transaction cost[t]
                           - slippage cost[t]
```

One basis point is `0.01%`; dividing by 10,000 converts basis points to a decimal rate. Turnover charges apply when the position changes, including entries and exits. The request's slippage setting defaults to 2 basis points; transaction costs come from the strategy specification (5 basis points in the deterministic fallback).

Returns compound into an equity curve:

```text
equity[t] = equity[t-1] * (1 + net strategy return[t])
```

The result reports initial and final equity, strategy return, benchmark return, excess return (strategy return minus benchmark return), equity-curve points, trade records with signal/execution dates, per-symbol results, and diagnostics.

#### Multiple symbols and benchmark

For multiple assets, the backtester combines per-symbol daily strategy returns by taking their equal-weight average. It does the same for the buy-and-hold benchmark, using the same assets. The benchmark holds the assets rather than applying the strategy's entry/exit rules. This makes the comparison concrete, but it is not a comparison against every possible benchmark or portfolio construction.

The strategy's fixed-fraction position applies within each symbol's strategy sleeve; the portfolio-level return is still formed by the engine's equal-weight averaging across symbols. Review the returned diagnostics and per-symbol results alongside the aggregate.

### 6. What the workflow produces after backtesting

The current graph continues past backtesting:

```text
Market Data -> Research -> Strategy -> Backtest -> Risk -> Evaluation -> Report
```

The Risk stage calculates risk measures from realized simulated returns and portfolio state (for example, CAGR, volatility, Sharpe/Sortino, drawdown, VaR/Expected Shortfall, turnover, and exposure). Evaluation and Report then provide additional assessment and a consolidated output. These stages help make a return number more interpretable; they do not turn a historical simulation into a forecast.

### 7. What to inspect and what to be careful about

For a run, inspect the structured outputs rather than inferring that a generic strategy was always used:

- `market_data`: provider, observation counts, date coverage, and feature values;
- `research`: hypothesis, evidence, stated risks, and confidence;
- `strategy`: the actual generated entry/exit rules, sizing, assets, and assumed costs;
- `backtest`: equity curve, trade ledger, benchmark, excess return, and per-symbol results;
- `risk`, `evaluation`, `report`: subsequent risk and summary outputs; and
- `errors` and `status`: whether each stage completed successfully.

Results depend on the downloaded data, history/date range, feature windows, generated rules, cost assumptions, and simulation conventions. The backtest does not establish that the strategy is profitable out of sample, account for every real-world execution constraint, or execute trades. Treat it as an experimental evaluation; additional validation—such as out-of-sample testing, robustness checks, and realistic trading assumptions—is needed before drawing stronger conclusions.

## Relevant implementation

- Workflow order and failure routing: [`workflow.py`](../ai-engine/src/graph/workflow.py)
- Market data retrieval and features: [`market_data_agent.py`](../ai-engine/src/agents/market_data_agent.py), [`service.py`](../ai-engine/src/market/service.py), [`features.py`](../ai-engine/src/quant/features.py)
- Research synthesis: [`research_agent.py`](../ai-engine/src/agents/research_agent.py), [`research_synthesizer.py`](../ai-engine/src/llm/research_synthesizer.py)
- Strategy generation and validation: [`strategy_agent.py`](../ai-engine/src/agents/strategy_agent.py), [`strategy_synthesizer.py`](../ai-engine/src/llm/strategy_synthesizer.py), [`rule_engine.py`](../ai-engine/src/strategy/rule_engine.py)
- Backtesting: [`backtest_agent.py`](../ai-engine/src/agents/backtest_agent.py), [`engine.py`](../ai-engine/src/backtesting/engine.py)
