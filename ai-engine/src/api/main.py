from fastapi import FastAPI, HTTPException

from src.graph.service import ResearchGraphService
from src.market.service import MarketDataService
from src.models.market_data import MarketDataRequest, MarketDataResponse
from src.models.research import ResearchRunRequest, ResearchRunResponse

app = FastAPI(
    title="AI Quant Research Agent - AI Engine",
    version="0.5.0",
    description="Python AI/quant service for the AI Quant Research Agent platform.",
)

market_service = MarketDataService()
research_graph_service = ResearchGraphService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "phase": "5", "langgraph": "enabled", "rag": "enabled", "strategy_dsl": "enabled", "backtesting": "enabled"}


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


@app.post("/api/v1/research/run", response_model=ResearchRunResponse)
def run_research(request: ResearchRunRequest) -> ResearchRunResponse:
    """Run Market Data -> RAG Research -> Strategy Generation -> Backtest workflow."""

    response = research_graph_service.run(request)
    if response.status == "FAILED":
        raise HTTPException(status_code=502, detail=response.errors)
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
