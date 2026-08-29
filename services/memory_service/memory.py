"""
ATHENA 4-Tier Memory Operating System
Short-term, Long-term, Vector similarity, and Knowledge base memory layers.
"""

import math
from datetime import datetime
from typing import Any, Dict, List, Optional
from packages.logging.logger import get_logger
from packages.schemas.decision import TradingDecision
from packages.schemas.journal import TradeJournalEntry

logger = get_logger("athena.memory")


class MemoryService:
    """Institutional 4-Tier Trading Memory Architecture."""

    def __init__(self):
        # 1. Short-term Memory (Working memory for current session)
        self.short_term_decisions: List[TradingDecision] = []

        # 2. Long-term Memory (Full closed/open trade ledger)
        self.long_term_trades: Dict[str, TradeJournalEntry] = {}

        # 3. Vector Memory (Embeddings & situation fingerprints)
        self.vector_store: List[Dict[str, Any]] = []

        # 4. Knowledge Memory (Research documents, macroeconomic filings)
        self.knowledge_base: Dict[str, str] = {
            "regime_transitions": "When inflation drops below 3% while GDP > 2%, equities experience strong factor re-rating.",
            "volatility_clustering": "Periods of high realized volatility persist for 10-15 trading days on average.",
            "liquidity_dry_up": "Bid-ask spreads widen 3x during opening 15 minutes of non-farm payroll announcements.",
        }

    def record_decision(self, decision: TradingDecision):
        """Appends decision to short-term memory and vector index."""
        self.short_term_decisions.append(decision)
        if len(self.short_term_decisions) > 50:
            self.short_term_decisions.pop(0)

        # Store vector fingerprint (price, return, rsi, vol, conf)
        vector = [
            decision.current_price / 500.0,
            decision.expected_return_pct * 10.0,
            decision.confidence,
            1.0 if decision.action.value == "BUY" else 0.0,
        ]
        self.vector_store.append(
            {
                "id": decision.id,
                "symbol": decision.symbol,
                "timestamp": decision.timestamp,
                "vector": vector,
                "action": decision.action.value,
                "confidence": decision.confidence,
            }
        )

    def record_trade(self, entry: TradeJournalEntry):
        """Persists trade into long-term memory."""
        self.long_term_trades[entry.trade_id] = entry
        logger.info(f"Recorded trade {entry.trade_id} ({entry.symbol} {entry.action}) into long-term memory.")

    def search_similar_market_situations(
        self, query_vector: List[float], top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Semantic vector search using cosine similarity across historical trade situations."""
        if not self.vector_store:
            return []

        def cosine_sim(v1: List[float], v2: List[float]) -> float:
            dot = sum(a * b for a, b in zip(v1, v2))
            norm1 = math.sqrt(sum(a * a for a in v1))
            norm2 = math.sqrt(sum(b * b for b in v2))
            return dot / (norm1 * norm2) if (norm1 * norm2) > 0 else 0.0

        scored = []
        for item in self.vector_store:
            sim = cosine_sim(query_vector, item["vector"])
            scored.append({"item": item, "similarity": round(sim, 4)})

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return [s["item"] for s in scored[:top_k]]


memory_service = MemoryService()
