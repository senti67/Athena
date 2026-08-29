"""
ATHENA Data Quality Agent & Validation Engine
Calculates DATA_QUALITY_SCORE (0.0 to 1.0) and blocks bad feeds from entering trading pipelines.
"""

from datetime import datetime
from typing import List, Tuple
from packages.common.config import settings
from packages.logging.logger import get_logger
from packages.monitoring.metrics import metrics
from packages.schemas.market import Candle, DataQualityReport, Tick

logger = get_logger("athena.data_quality")


class DataQualityAgent:
    """
    Independent Data Quality Agent inspecting market, fundamental, and alternative feeds.
    Blocks execution if data quality falls below threshold (e.g. 0.80).
    """

    def __init__(self, min_quality_score: float = None):
        self.min_score = min_quality_score or settings.MIN_DATA_QUALITY_SCORE

    def evaluate_candles(self, symbol: str, candles: List[Candle]) -> DataQualityReport:
        warnings: List[str] = []
        rejections: List[str] = []
        score = 1.0

        if not candles:
            return DataQualityReport(
                symbol=symbol,
                data_quality_score=0.0,
                is_valid=False,
                rejections_reasons=["Empty candle stream provided."],
            )

        # 1. Check minimum bar length
        if len(candles) < 30:
            score -= 0.15
            warnings.append(f"Short history: only {len(candles)} bars available.")

        # 2. Check for impossible prices (negative or zero)
        for i, c in enumerate(candles):
            if c.open <= 0 or c.high <= 0 or c.low <= 0 or c.close <= 0:
                score -= 0.50
                rejections.append(f"Impossible non-positive price detected at bar {i}.")
                break
            if c.low > c.high or c.open > c.high or c.close < c.low:
                score -= 0.30
                rejections.append(f"Inconsistent OHLC bar geometry at bar {i}.")
                break

        # 3. Check for extreme price spikes (>40% single-day change without split)
        for i in range(1, len(candles)):
            prev_close = candles[i - 1].close
            curr_close = candles[i].close
            pct_change = abs(curr_close - prev_close) / prev_close
            if pct_change > 0.40:
                score -= 0.25
                warnings.append(f"Extreme single-bar price jump ({pct_change*100:.1f}%) at bar {i}.")

        # 4. Check for timestamp monotonicity
        timestamp_errors = 0
        now = datetime.utcnow()
        for i in range(1, len(candles)):
            if candles[i].timestamp <= candles[i - 1].timestamp:
                timestamp_errors += 1
            if candles[i].timestamp > now:
                timestamp_errors += 1

        if timestamp_errors > 0:
            score -= min(0.30, timestamp_errors * 0.05)
            warnings.append(f"Found {timestamp_errors} timestamp sequencing anomalies.")

        final_score = max(0.0, min(1.0, round(score, 3)))
        is_valid = final_score >= self.min_score and len(rejections) == 0

        # Record prometheus metric
        metrics.update_data_quality(symbol, final_score)

        return DataQualityReport(
            symbol=symbol,
            timestamp=datetime.utcnow(),
            data_quality_score=final_score,
            is_valid=is_valid,
            timestamp_errors=timestamp_errors,
            warnings=warnings,
            rejection_reasons=rejections,
        )

    def evaluate_tick(self, tick: Tick) -> Tuple[bool, float, List[str]]:
        """Quick validation for real-time streaming ticks."""
        reasons = []
        if tick.price <= 0:
            reasons.append("Non-positive tick price.")
            return False, 0.0, reasons

        if tick.bid is not None and tick.ask is not None:
            if tick.ask < tick.bid:
                reasons.append("Crossed market: ask < bid.")
                return False, 0.2, reasons
            spread = tick.ask - tick.bid
            if spread > (tick.price * 0.05):  # 5% spread
                reasons.append("Abnormal spread > 5% of price.")
                return True, 0.75, reasons

        return True, 1.0, reasons
