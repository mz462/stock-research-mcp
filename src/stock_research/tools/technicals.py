"""Technical analysis tools: indicators and support/resistance."""

from typing import Any
from mcp.server import FastMCP

from stock_research.services.alpha_vantage_mcp import get_av_client
from stock_research.services.cache import get_or_fetch
from stock_research.config import config
from stock_research.utils.calculations import calculate_support_resistance, calculate_rsi, calculate_macd, calculate_ema, calculate_sma, calculate_bbands


def register_technical_tools(mcp: FastMCP) -> None:
    """Register technical analysis tools with the MCP server."""

    @mcp.tool()
    async def get_technical_indicators(
        ticker: str,
        indicators: list[str] | None = None
    ) -> dict[str, Any]:
        """Get technical indicators for a stock.

        Args:
            ticker: Stock symbol (e.g., 'AAPL', 'MSFT')
            indicators: List of indicators to fetch. Options: 'sma', 'ema', 'rsi', 'macd', 'bbands'.
                       If None, fetches all.

        Returns:
            Technical indicator values and trend analysis.
        """
        if indicators is None:
            indicators = ["sma", "ema", "rsi", "macd", "bbands"]

        cache_key = f"technicals:{ticker.upper()}:{','.join(sorted(indicators))}"

        async def fetch():
            client = get_av_client()
            result = {"ticker": ticker.upper()}

            # Get historical prices first (1 API call) - used for local calculations
            closes = []
            price_error = None
            try:
                # Try compact first (100 days, lower API cost)
                daily = await client.get_daily_prices(ticker.upper(), "compact")
                time_series = daily.get("Time Series (Daily)", {})
                if time_series:
                    closes = [
                        float(v["4. close"])
                        for d, v in sorted(time_series.items(), reverse=True)
                    ]
                else:
                    price_error = "Empty time series in response"
            except Exception as e:
                price_error = str(e)

            # If we need SMA200 and don't have enough data, try full
            if "sma" in indicators and len(closes) < 200 and len(closes) > 0:
                try:
                    daily = await client.get_daily_prices(ticker.upper(), "full")
                    time_series = daily.get("Time Series (Daily)", {})
                    if time_series:
                        closes = [
                            float(v["4. close"])
                            for d, v in sorted(time_series.items(), reverse=True)
                        ][:250]
                except Exception:
                    pass  # Keep whatever we have from compact

            # Calculate indicators locally from price data (saves API calls)
            # Calculate whatever we have enough data for
            if closes and len(closes) >= 20:
                if "sma" in indicators:
                    result["sma"] = {
                        "sma_20": calculate_sma(closes, 20) if len(closes) >= 20 else None,
                        "sma_50": calculate_sma(closes, 50) if len(closes) >= 50 else None,
                        "sma_200": calculate_sma(closes, 200) if len(closes) >= 200 else None,
                    }

                if "ema" in indicators:
                    result["ema"] = {
                        "ema_12": calculate_ema(closes, 12) if len(closes) >= 12 else None,
                        "ema_26": calculate_ema(closes, 26) if len(closes) >= 26 else None,
                    }

                if "rsi" in indicators:
                    rsi_value = calculate_rsi(closes, 14) if len(closes) >= 15 else None
                    if rsi_value is not None:
                        if rsi_value > 70:
                            rsi_signal = "overbought"
                        elif rsi_value < 30:
                            rsi_signal = "oversold"
                        else:
                            rsi_signal = "neutral"
                    else:
                        rsi_signal = "unknown"

                    result["rsi"] = {
                        "rsi_14": rsi_value,
                        "signal": rsi_signal,
                    }

                if "macd" in indicators:
                    macd_data = calculate_macd(closes) if len(closes) >= 35 else {"macd": None, "signal": None, "histogram": None}
                    if macd_data.get("macd") is not None and macd_data.get("signal") is not None:
                        macd_trend = "bullish" if macd_data["macd"] > macd_data["signal"] else "bearish"
                    else:
                        macd_trend = "unknown"

                    result["macd"] = {
                        **macd_data,
                        "trend": macd_trend,
                    }

                if "bbands" in indicators:
                    result["bbands"] = calculate_bbands(closes, 20) if len(closes) >= 20 else {"upper": None, "middle": None, "lower": None}
            elif closes:
                # Fallback to API calls if no price data (uses more API quota)
                if "sma" in indicators:
                    try:
                        sma_20 = await client.get_sma(ticker, time_period=20)
                        result["sma"] = {
                            "sma_20": _get_latest_value(sma_20, "Technical Analysis: SMA"),
                            "sma_50": None,
                            "sma_200": None,
                        }
                    except Exception as e:
                        result["sma"] = {"error": str(e)}

                if "ema" in indicators:
                    result["ema"] = {"ema_12": None, "ema_26": None, "error": "Insufficient price data"}

                if "rsi" in indicators:
                    try:
                        rsi = await client.get_rsi(ticker, time_period=14)
                        rsi_value = _get_latest_value(rsi, "Technical Analysis: RSI")
                        rsi_signal = "overbought" if rsi_value and rsi_value > 70 else "oversold" if rsi_value and rsi_value < 30 else "neutral"
                        result["rsi"] = {"rsi_14": rsi_value, "signal": rsi_signal}
                    except Exception as e:
                        result["rsi"] = {"error": str(e)}

                if "macd" in indicators:
                    try:
                        macd = await client.get_macd(ticker)
                        macd_data = _get_latest_macd(macd)
                        macd_trend = "bullish" if macd_data.get("macd", 0) > macd_data.get("signal", 0) else "bearish"
                        result["macd"] = {**macd_data, "trend": macd_trend}
                    except Exception as e:
                        result["macd"] = {"error": str(e)}

                if "bbands" in indicators:
                    try:
                        bbands = await client.get_bbands(ticker)
                        result["bbands"] = _get_latest_bbands(bbands)
                    except Exception as e:
                        result["bbands"] = {"error": str(e)}
            else:
                # No price data at all - return error state with details
                error_msg = price_error or "No price data available"
                if "sma" in indicators:
                    result["sma"] = {"error": error_msg}
                if "ema" in indicators:
                    result["ema"] = {"error": error_msg}
                if "rsi" in indicators:
                    result["rsi"] = {"error": error_msg}
                if "macd" in indicators:
                    result["macd"] = {"error": error_msg}
                if "bbands" in indicators:
                    result["bbands"] = {"error": error_msg}

            # Overall trend determination
            result["trend"] = _determine_trend(result)

            return result

        return await get_or_fetch(cache_key, config.CACHE_TTL_TECHNICALS, fetch)

    @mcp.tool()
    async def get_support_resistance(
        ticker: str,
        lookback_days: int = 60
    ) -> dict[str, Any]:
        """Calculate support and resistance levels for a stock.

        Args:
            ticker: Stock symbol (e.g., 'AAPL', 'MSFT')
            lookback_days: Number of days to analyze (default 60)

        Returns:
            Support and resistance levels with current price position.
        """
        cache_key = f"support_resistance:{ticker.upper()}:{lookback_days}"

        async def fetch():
            client = get_av_client()

            # Get historical daily prices
            raw = await client.get_daily_prices(ticker.upper(), "compact")
            time_series = raw.get("Time Series (Daily)", {})

            # Extract prices
            prices = []
            for date, values in sorted(time_series.items(), reverse=True)[:lookback_days]:
                prices.append({
                    "date": date,
                    "high": float(values.get("2. high", 0)),
                    "low": float(values.get("3. low", 0)),
                    "close": float(values.get("4. close", 0)),
                })

            if not prices:
                return {"ticker": ticker.upper(), "error": "No price data available"}

            current_price = prices[0]["close"]
            support_levels, resistance_levels = calculate_support_resistance(prices)

            # Determine current position
            nearest_support = max([s for s in support_levels if s < current_price], default=None)
            nearest_resistance = min([r for r in resistance_levels if r > current_price], default=None)

            if nearest_support and nearest_resistance:
                range_size = nearest_resistance - nearest_support
                position_in_range = (current_price - nearest_support) / range_size if range_size > 0 else 0.5

                if position_in_range < 0.2:
                    position = "near_support"
                elif position_in_range > 0.8:
                    position = "near_resistance"
                else:
                    position = "mid_range"
            else:
                position = "unknown"

            return {
                "ticker": ticker.upper(),
                "current_price": current_price,
                "support_levels": support_levels[:5],  # Top 5 support levels
                "resistance_levels": resistance_levels[:5],  # Top 5 resistance levels
                "nearest_support": nearest_support,
                "nearest_resistance": nearest_resistance,
                "current_position": position,
                "lookback_days": lookback_days,
            }

        return await get_or_fetch(cache_key, config.CACHE_TTL_TECHNICALS, fetch)


def _get_latest_value(data: dict, key: str) -> float | None:
    """Extract the latest value from Alpha Vantage indicator response."""
    series = data.get(key, {})
    if not series:
        return None
    latest_date = max(series.keys())
    values = series[latest_date]
    # Get the first (usually only) value
    for v in values.values():
        try:
            return float(v)
        except (ValueError, TypeError):
            pass
    return None


def _get_latest_macd(data: dict) -> dict:
    """Extract the latest MACD values."""
    series = data.get("Technical Analysis: MACD", {})
    if not series:
        return {}
    latest_date = max(series.keys())
    values = series[latest_date]
    return {
        "macd": float(values.get("MACD", 0)),
        "signal": float(values.get("MACD_Signal", 0)),
        "histogram": float(values.get("MACD_Hist", 0)),
    }


def _get_latest_bbands(data: dict) -> dict:
    """Extract the latest Bollinger Bands values."""
    series = data.get("Technical Analysis: BBANDS", {})
    if not series:
        return {}
    latest_date = max(series.keys())
    values = series[latest_date]
    return {
        "upper": float(values.get("Real Upper Band", 0)),
        "middle": float(values.get("Real Middle Band", 0)),
        "lower": float(values.get("Real Lower Band", 0)),
    }


def _determine_trend(data: dict) -> str:
    """Determine overall trend from technical indicators."""
    signals = []

    # RSI signal
    rsi = data.get("rsi", {})
    if rsi.get("signal") == "overbought":
        signals.append(-1)
    elif rsi.get("signal") == "oversold":
        signals.append(1)
    else:
        signals.append(0)

    # MACD signal
    macd = data.get("macd", {})
    if macd.get("trend") == "bullish":
        signals.append(1)
    elif macd.get("trend") == "bearish":
        signals.append(-1)
    else:
        signals.append(0)

    # SMA signals (price vs moving averages would need current price)
    # For now, just use what we have

    avg_signal = sum(signals) / len(signals) if signals else 0

    if avg_signal > 0.3:
        return "bullish"
    elif avg_signal < -0.3:
        return "bearish"
    else:
        return "neutral"
