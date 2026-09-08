from io import BytesIO

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from matplotlib.figure import Figure

from src.graph.service import ResearchGraphService
from src.market.service import MarketDataService
from src.models.market_data import MarketDataRequest, MarketDataResponse
from src.models.research import ResearchRunRequest, ResearchRunResponse

app = FastAPI(
    title="AI Quant Research Agent - AI Engine",
    version="0.6.0",
    description="Python AI/quant service for the AI Quant Research Agent platform.",
)

market_service = MarketDataService()
research_graph_service = ResearchGraphService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "phase": "8", "langgraph": "enabled", "rag": "enabled", "strategy_dsl": "enabled", "backtesting": "enabled", "risk": "enabled", "evaluation": "enabled", "report": "enabled"}


@app.post("/api/v1/market-data", response_model=MarketDataResponse)
def get_market_data(request: MarketDataRequest) -> MarketDataResponse:
    try:
        data = [
            market_service.get_symbol_data(
                symbol=symbol,
                start_date=request.start_date,
                end_date=request.end_date,
                volatility_window=request.volatility_window,
                momentum_window=request.momentum_window,
            )
            for symbol in request.symbols
        ]
        return MarketDataResponse(data=data)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Market data provider failure: {exc}") from exc


@app.post("/api/v1/market-data/plot", response_class=Response)
def plot_market_data(request: MarketDataRequest) -> Response:
    """Return market data features as a PNG chart using the same request contract."""
    try:
        market_data = get_market_data(request)
        figure = Figure(figsize=(12, 8), constrained_layout=True)
        axes = figure.subplots(3, 1, sharex=True)

        for item in market_data.data:
            dates = [observation.date for observation in item.observations]
            closes = [observation.close for observation in item.observations]
            sma_20 = [observation.sma_20 for observation in item.observations]
            sma_50 = [observation.sma_50 for observation in item.observations]
            momentum = [observation.momentum for observation in item.observations]
            volatility = [observation.volatility for observation in item.observations]

            axes[0].plot(dates, closes, label=f"{item.symbol} close")
            axes[0].plot(dates, sma_20, linestyle="--", label=f"{item.symbol} SMA 20")
            axes[0].plot(dates, sma_50, linestyle=":", label=f"{item.symbol} SMA 50")
            axes[1].plot(dates, momentum, label=item.symbol)
            axes[2].plot(dates, volatility, label=item.symbol)

        axes[0].set_title("Market Data Overview")
        axes[0].set_ylabel("Price")
        axes[1].set_ylabel("Momentum")
        axes[2].set_ylabel("Annualized volatility")
        axes[2].set_xlabel("Date")
        for axis in axes:
            axis.grid(alpha=0.25)
            axis.legend()

        output = BytesIO()
        figure.savefig(output, format="png", dpi=140)
        return Response(content=output.getvalue(), media_type="image/png")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Market data plotting failure: {exc}") from exc


@app.post("/api/v1/research/run", response_model=ResearchRunResponse)
def run_research(request: ResearchRunRequest) -> ResearchRunResponse:
    """Run Market Data -> RAG Research -> Strategy -> Backtest -> Risk workflow."""

    response = research_graph_service.run(request)
    if response.status == "FAILED":
        raise HTTPException(status_code=502, detail=response.errors)
    return response
