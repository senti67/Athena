"""
ATHENA Custom Institutional Exceptions
"""


class AthenaException(Exception):
    """Base exception for all ATHENA platform errors."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class RiskVetoException(AthenaException):
    """Raised when an order is vetoed by the independent Risk Engine."""


class DataQualityException(AthenaException):
    """Raised when incoming market data fails quality validation."""


class LiveTradingDisabledException(AthenaException):
    """Raised when an attempt is made to place a live trade while LIVE_TRADING_ENABLED=false."""


class InsufficientFundsException(AthenaException):
    """Raised when account buying power is insufficient for order."""


class InvalidOrderException(AthenaException):
    """Raised when order parameters are malformed or invalid."""


class LLMInferenceException(AthenaException):
    """Raised when LLM returns invalid JSON or fails schema validation."""


class BrokerConnectionException(AthenaException):
    """Raised when broker API connection or heartbeat fails."""


class RegimeMismatchException(AthenaException):
    """Raised when strategy execution is incompatible with detected market regime."""
