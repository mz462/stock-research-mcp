"""Calculation utilities for technical analysis."""

from typing import Any


def calculate_support_resistance(
    prices: list[dict[str, Any]],
    threshold: float = 0.02
) -> tuple[list[float], list[float]]:
    """Calculate support and resistance levels from price data.

    Uses pivot point analysis to identify significant price levels.

    Args:
        prices: List of price dicts with 'high', 'low', 'close' keys
        threshold: Percentage threshold for grouping nearby levels (default 2%)

    Returns:
        Tuple of (support_levels, resistance_levels), sorted by significance
    """
    if not prices:
        return [], []

    # Find local minima (support) and maxima (resistance)
    highs = [p["high"] for p in prices]
    lows = [p["low"] for p in prices]

    support_candidates = []
    resistance_candidates = []

    # Find pivot lows (support) - points where low is lower than neighbors
    for i in range(2, len(lows) - 2):
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
           lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            support_candidates.append(lows[i])

    # Find pivot highs (resistance) - points where high is higher than neighbors
    for i in range(2, len(highs) - 2):
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
           highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            resistance_candidates.append(highs[i])

    # Cluster nearby levels
    support_levels = _cluster_levels(support_candidates, threshold)
    resistance_levels = _cluster_levels(resistance_candidates, threshold)

    # Sort support descending (closest to price first), resistance ascending
    support_levels.sort(reverse=True)
    resistance_levels.sort()

    return support_levels, resistance_levels


def _cluster_levels(levels: list[float], threshold: float) -> list[float]:
    """Cluster nearby price levels together.

    Groups levels that are within threshold percentage of each other
    and returns the average of each cluster.
    """
    if not levels:
        return []

    sorted_levels = sorted(levels)
    clusters = []
    current_cluster = [sorted_levels[0]]

    for level in sorted_levels[1:]:
        # Check if this level is close to the current cluster
        cluster_avg = sum(current_cluster) / len(current_cluster)
        if abs(level - cluster_avg) / cluster_avg <= threshold:
            current_cluster.append(level)
        else:
            # Start a new cluster
            clusters.append(current_cluster)
            current_cluster = [level]

    # Don't forget the last cluster
    clusters.append(current_cluster)

    # Return the average of each cluster, weighted by cluster size
    result = []
    for cluster in clusters:
        avg = sum(cluster) / len(cluster)
        result.append((round(avg, 2), len(cluster)))

    # Sort by significance (cluster size) and return just the levels
    result.sort(key=lambda x: x[1], reverse=True)
    return [r[0] for r in result]


def calculate_pivot_points(high: float, low: float, close: float) -> dict[str, float]:
    """Calculate classic pivot points.

    Args:
        high: Period high price
        low: Period low price
        close: Period close price

    Returns:
        Dict with pivot, support (s1, s2, s3), and resistance (r1, r2, r3) levels
    """
    pivot = (high + low + close) / 3

    return {
        "pivot": round(pivot, 2),
        "r1": round(2 * pivot - low, 2),
        "r2": round(pivot + (high - low), 2),
        "r3": round(high + 2 * (pivot - low), 2),
        "s1": round(2 * pivot - high, 2),
        "s2": round(pivot - (high - low), 2),
        "s3": round(low - 2 * (high - pivot), 2),
    }


def calculate_sma(prices: list[float], period: int) -> float | None:
    """Calculate Simple Moving Average.

    Args:
        prices: List of prices (most recent first)
        period: Number of periods

    Returns:
        SMA value or None if insufficient data
    """
    if len(prices) < period:
        return None
    return round(sum(prices[:period]) / period, 2)


def calculate_ema(prices: list[float], period: int) -> float | None:
    """Calculate Exponential Moving Average.

    Args:
        prices: List of prices (most recent first)
        period: Number of periods

    Returns:
        EMA value or None if insufficient data
    """
    if len(prices) < period:
        return None

    # Reverse to get oldest first for calculation
    prices_rev = list(reversed(prices))

    # Start with SMA for first EMA value
    multiplier = 2 / (period + 1)
    ema = sum(prices_rev[:period]) / period

    # Calculate EMA for remaining prices
    for price in prices_rev[period:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))

    return round(ema, 2)


def calculate_rsi(prices: list[float], period: int = 14) -> float | None:
    """Calculate Relative Strength Index.

    Args:
        prices: List of closing prices (most recent first)
        period: RSI period (default 14)

    Returns:
        RSI value (0-100) or None if insufficient data
    """
    if len(prices) < period + 1:
        return None

    # Reverse to get oldest first
    prices_rev = list(reversed(prices))

    # Calculate price changes
    gains = []
    losses = []

    for i in range(1, len(prices_rev)):
        change = prices_rev[i] - prices_rev[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    if len(gains) < period:
        return None

    # Calculate initial average gain/loss
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    # Smooth with subsequent values
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return round(rsi, 2)


def calculate_macd(
    prices: list[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> dict[str, float | None]:
    """Calculate MACD indicator.

    Args:
        prices: List of closing prices (most recent first)
        fast_period: Fast EMA period (default 12)
        slow_period: Slow EMA period (default 26)
        signal_period: Signal line period (default 9)

    Returns:
        Dict with macd, signal, and histogram values
    """
    if len(prices) < slow_period + signal_period:
        return {"macd": None, "signal": None, "histogram": None}

    # Calculate EMAs
    prices_rev = list(reversed(prices))

    # Fast EMA
    fast_mult = 2 / (fast_period + 1)
    fast_ema = sum(prices_rev[:fast_period]) / fast_period
    fast_emas = [fast_ema]
    for price in prices_rev[fast_period:]:
        fast_ema = (price * fast_mult) + (fast_ema * (1 - fast_mult))
        fast_emas.append(fast_ema)

    # Slow EMA
    slow_mult = 2 / (slow_period + 1)
    slow_ema = sum(prices_rev[:slow_period]) / slow_period
    slow_emas = [None] * (slow_period - fast_period) + [slow_ema]
    for price in prices_rev[slow_period:]:
        slow_ema = (price * slow_mult) + (slow_ema * (1 - slow_mult))
        slow_emas.append(slow_ema)

    # MACD line (fast - slow)
    macd_line = []
    for i, (fast, slow) in enumerate(zip(fast_emas, slow_emas)):
        if fast is not None and slow is not None:
            macd_line.append(fast - slow)

    if len(macd_line) < signal_period:
        return {"macd": None, "signal": None, "histogram": None}

    # Signal line (EMA of MACD)
    signal_mult = 2 / (signal_period + 1)
    signal = sum(macd_line[:signal_period]) / signal_period
    for val in macd_line[signal_period:]:
        signal = (val * signal_mult) + (signal * (1 - signal_mult))

    macd_val = macd_line[-1]
    histogram = macd_val - signal

    return {
        "macd": round(macd_val, 4),
        "signal": round(signal, 4),
        "histogram": round(histogram, 4),
    }


def calculate_bbands(
    prices: list[float],
    period: int = 20,
    std_dev: float = 2.0
) -> dict[str, float | None]:
    """Calculate Bollinger Bands.

    Args:
        prices: List of closing prices (most recent first)
        period: Moving average period (default 20)
        std_dev: Standard deviation multiplier (default 2)

    Returns:
        Dict with upper, middle, and lower band values
    """
    if len(prices) < period:
        return {"upper": None, "middle": None, "lower": None}

    # Middle band is SMA
    middle = sum(prices[:period]) / period

    # Calculate standard deviation
    variance = sum((p - middle) ** 2 for p in prices[:period]) / period
    std = variance ** 0.5

    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)

    return {
        "upper": round(upper, 2),
        "middle": round(middle, 2),
        "lower": round(lower, 2),
    }
