"""
ATHENA Pure Quantitative Indicators & Math Engine
Provides vectorized, high-performance technical and statistical calculations.
"""

import math
from typing import List, Tuple
from packages.schemas.market import Candle


def calculate_sma(prices: List[float], window: int) -> float:
    """Computes Simple Moving Average for the most recent bar."""
    if not prices or len(prices) < window:
        return prices[-1] if prices else 0.0
    return sum(prices[-window:]) / window


def calculate_ema(prices: List[float], window: int, smoothing: float = 2.0) -> float:
    """Computes Exponential Moving Average."""
    if not prices:
        return 0.0
    if len(prices) < window:
        return calculate_sma(prices, len(prices))

    alpha = smoothing / (window + 1.0)
    ema = sum(prices[:window]) / window
    for price in prices[window:]:
        ema = (price * alpha) + (ema * (1.0 - alpha))
    return ema


def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """Computes Relative Strength Index (RSI)."""
    if len(prices) < period + 1:
        return 50.0

    gains: List[float] = []
    losses: List[float] = []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]
        if change >= 0:
            gains.append(change)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(change))

    # Wilder's Smoothing
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def calculate_macd(
    prices: List[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> Tuple[float, float, float]:
    """Computes MACD line, Signal line, and Histogram."""
    if len(prices) < slow_period + signal_period:
        return 0.0, 0.0, 0.0

    # Calculate fast & slow EMAs series
    fast_alpha = 2.0 / (fast_period + 1.0)
    slow_alpha = 2.0 / (slow_period + 1.0)

    fast_ema = prices[0]
    slow_ema = prices[0]
    macd_series: List[float] = []

    for price in prices:
        fast_ema = (price * fast_alpha) + (fast_ema * (1.0 - fast_alpha))
        slow_ema = (price * slow_alpha) + (slow_ema * (1.0 - slow_alpha))
        macd_series.append(fast_ema - slow_ema)

    macd_val = macd_series[-1]
    signal_val = calculate_ema(macd_series[-signal_period * 2 :], signal_period)
    hist_val = macd_val - signal_val
    return macd_val, signal_val, hist_val


def calculate_bollinger_bands(
    prices: List[float], window: int = 20, num_std: float = 2.0
) -> Tuple[float, float, float, float]:
    """Computes Bollinger Bands: (Upper, Middle, Lower, Bandwidth)."""
    if len(prices) < window:
        current = prices[-1] if prices else 0.0
        return current, current, current, 0.0

    recent = prices[-window:]
    mean = sum(recent) / window
    variance = sum((p - mean) ** 2 for p in recent) / window
    std = math.sqrt(variance)

    upper = mean + (num_std * std)
    lower = mean - (num_std * std)
    bandwidth = (upper - lower) / mean if mean != 0 else 0.0
    return upper, mean, lower, bandwidth


def calculate_atr(candles: List[Candle], period: int = 14) -> float:
    """Computes Average True Range (ATR)."""
    if len(candles) < period + 1:
        return 1.5

    tr_list: List[float] = []
    for i in range(1, len(candles)):
        h = candles[i].high
        l = candles[i].low
        prev_c = candles[i - 1].close
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        tr_list.append(tr)

    atr = sum(tr_list[:period]) / period
    for tr in tr_list[period:]:
        atr = (atr * (period - 1) + tr) / period
    return atr


def calculate_vwap(candles: List[Candle]) -> float:
    """Computes Volume-Weighted Average Price (VWAP)."""
    if not candles:
        return 0.0
    cum_vol_price = sum(((c.high + c.low + c.close) / 3.0) * c.volume for c in candles)
    cum_vol = sum(c.volume for c in candles)
    if cum_vol == 0:
        return candles[-1].close
    return cum_vol_price / cum_vol


def calculate_stochastic(
    candles: List[Candle], period: int = 14, smooth_k: int = 3, smooth_d: int = 3
) -> Tuple[float, float]:
    """Computes Stochastic Oscillator (%K and %D)."""
    if len(candles) < period:
        return 50.0, 50.0

    recent = candles[-period:]
    highest_high = max(c.high for c in recent)
    lowest_low = min(c.low for c in recent)
    current_close = candles[-1].close

    if highest_high == lowest_low:
        return 50.0, 50.0

    k = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100.0
    d = k  # simplified smoothing for point calculation
    return k, d


def calculate_support_resistance(candles: List[Candle], lookback: int = 50) -> Tuple[float, float]:
    """Computes local pivot support and resistance levels."""
    if not candles:
        return 0.0, 0.0
    recent = candles[-lookback:] if len(candles) >= lookback else candles
    support = min(c.low for c in recent)
    resistance = max(c.high for c in recent)
    return support, resistance
