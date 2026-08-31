from pathlib import Path

from src.graph.state import ResearchState
from src.llm.research_synthesizer import ResearchSynthesizer, build_research_synthesizer
from src.rag.retriever import ResearchRetriever


class ResearchAgent:
    def __init__(
        self,
        retriever: ResearchRetriever | None = None,
        synthesizer: ResearchSynthesizer | None = None,
    ):
        knowledge_dir = Path(__file__).resolve().parents[2] / "knowledge"
        self.retriever = retriever or ResearchRetriever.from_directory(knowledge_dir)
        self.synthesizer = synthesizer or build_research_synthesizer()

    def __call__(self, state: ResearchState) -> dict:
        try:
            top_k = state.get("top_k", 5)
            evidence = self.retriever.retrieve(state["query"], top_k=top_k)
            market_summary = self._summarize_market_data(state.get("market_data", {}))
            hypothesis = self.synthesizer.synthesize(
                query=state["query"],
                symbols=state["symbols"],
                market_summary=market_summary,
                evidence=evidence,
            )
            return {
                "research": hypothesis.model_dump(mode="json"),
                "status": "RESEARCH_READY",
                "current_agent": "research",
                "errors": [],
            }
        except Exception as exc:
            return {
                "status": "FAILED",
                "current_agent": "research",
                "errors": [f"Research Agent failed: {exc}"],
            }

    @staticmethod
    def _summarize_market_data(market_data: dict) -> dict:
        summaries: dict = {}
        for symbol, item in market_data.get("symbols", {}).items():
            latest = item.get("latest") or {}
            summaries[symbol] = {
                "observation_count": item.get("observation_count"),
                "first_date": item.get("first_date"),
                "last_date": item.get("last_date"),
                "latest_close": latest.get("close"),
                "latest_volatility": latest.get("volatility"),
                "latest_momentum": latest.get("momentum"),
            }
        return summaries
