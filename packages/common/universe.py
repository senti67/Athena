"""
ATHENA Centralized Asset Universe & Sector Catalogs
Defines an institutional-grade, diversified multi-sector universe of 70+ leading global brands,
growth equities, semiconductors, consumer staples, defense, and hard commodities.
"""

from typing import Dict, List

SECTOR_WATCHLISTS: Dict[str, List[str]] = {
    "Mega-Cap Tech & AI": [
        "NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA",
    ],
    "Semiconductors & AI Hardware": [
        "AVGO", "AMD", "QCOM", "TSM", "ARM", "MU", "ASML", "INTC", "AMAT", "LRCX",
    ],
    "Cloud, SaaS & Cybersecurity": [
        "ORCL", "CRM", "PLTR", "NOW", "PANW", "CRWD", "SNOW", "NET", "DDOG",
    ],
    "Consumer Brands & Global Retail": [
        "COST", "WMT", "PG", "KO", "PEP", "MCD", "NKE", "SBUX", "TGT", "LULU", "HD",
    ],
    "Streaming, Media & Entertainment": [
        "NFLX", "DIS", "SPOT",
    ],
    "Financials, Fintech & Payments": [
        "JPM", "V", "MA", "BAC", "GS", "MS", "AXP", "PYPL", "COIN", "BLK",
    ],
    "Healthcare, Biotech & Pharma": [
        "LLY", "JNJ", "UNH", "ABBV", "MRK", "PFE", "ISRG", "VRTX", "AMGN",
    ],
    "Aerospace, Defense & Space": [
        "LMT", "BA", "RKLB", "RTX", "NOC", "GD",
    ],
    "Energy & Industrials": [
        "XOM", "CVX", "CAT", "GE", "DE", "HON", "SLB",
    ],
    "Mobility & Logistics": [
        "UBER", "FDX", "UPS",
    ],
    "Hard Assets & Crypto": [
        "IBIT", "GLD", "SLV", "USO", "CPER",
    ],
    "Indian Global Bluechips": [
        "RELIANCE", "ICICIBANK", "HDFCBANK", "BHARTIARTL", "TCS", "INFY", "LT", "ITC", "TATAMOTORS",
    ],
}

# Unified Global Watchlist (Deduplicated, preserving categorized ordering)
GLOBAL_WATCHLIST: List[str] = []
for sector_tickers in SECTOR_WATCHLISTS.values():
    for ticker in sector_tickers:
        if ticker not in GLOBAL_WATCHLIST:
            GLOBAL_WATCHLIST.append(ticker)

__all__ = ["SECTOR_WATCHLISTS", "GLOBAL_WATCHLIST"]
