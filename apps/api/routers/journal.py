"""
ATHENA Trade Journal Router
"""

from typing import List
from fastapi import APIRouter, HTTPException
from packages.schemas.journal import TradeJournalEntry
from services.journal_service.journal import journal_service

router = APIRouter(prefix="/journal", tags=["Trade Journal"])


@router.get("", response_model=List[TradeJournalEntry])
async def list_trade_journal():
    return list(journal_service.journal.values())


@router.get("/{trade_id}", response_model=TradeJournalEntry)
async def get_trade_entry(trade_id: str):
    if trade_id not in journal_service.journal:
        raise HTTPException(status_code=404, detail="Trade journal entry not found")
    return journal_service.journal[trade_id]


@router.get("/{trade_id}/explainability")
async def get_trade_explainability(trade_id: str):
    if trade_id not in journal_service.journal:
        raise HTTPException(status_code=404, detail="Trade journal entry not found")
    entry = journal_service.journal[trade_id]
    return {
        "trade_id": trade_id,
        "symbol": entry.symbol,
        "markdown": entry.explainability_report_markdown,
    }
