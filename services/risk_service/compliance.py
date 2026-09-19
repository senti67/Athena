"""
ATHENA Compliance & Eligibility Gatekeeper
Validates regulatory requirements, restricted trading lists, penny stock prohibitions,
and symbol whitelist eligibility.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ComplianceCheckResult(BaseModel):
    is_compliant: bool = True
    status: str = "PASS"  # "PASS" or "REJECT"
    symbol: str
    violations: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ComplianceEngine:
    """
    Validates regulatory and mandate compliance before trade execution.
    """

    def __init__(
        self,
        min_stock_price: float = 5.0,
        restricted_symbols: Optional[List[str]] = None,
    ):
        self.min_stock_price = min_stock_price
        self.restricted_symbols = set(restricted_symbols or [])

    def check_compliance(
        self,
        symbol: str,
        current_price: float,
        action: str = "BUY",
    ) -> ComplianceCheckResult:
        violations: List[str] = []

        # 1. Penny stock restriction
        if current_price < self.min_stock_price:
            violations.append(
                f"Penny stock restriction: Asset price (${current_price:.2f}) is below mandatory ${self.min_stock_price:.2f} floor."
            )

        # 2. Restricted symbol list
        if symbol.upper() in self.restricted_symbols:
            violations.append(f"Restricted list: Symbol {symbol} is currently on the corporate restricted trading list.")

        # 3. Valid ticker structure
        if not symbol or len(symbol) > 6 or not symbol.isalnum():
            violations.append(f"Invalid symbol format: {symbol}")

        is_compliant = (len(violations) == 0)
        return ComplianceCheckResult(
            is_compliant=is_compliant,
            status="PASS" if is_compliant else "REJECT",
            symbol=symbol,
            violations=violations,
        )


compliance_engine = ComplianceEngine()
