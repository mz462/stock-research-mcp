"""Market data tools: quotes and historical prices."""

from typing import Any
from mcp.server import FastMCP

from stock_research.services.alpha_vantage_mcp import get_av_client
from stock_research.services.cache import get_or_fetch
from stock_research.config import config


def register_market_data_tools(mcp: FastMCP) -> None:
    """Register market data tools with the MCP server."""

    @mcp.tool()
    async def get_quote(ticker: str) -> dict[str, Any]:
        """Get real-time quote for a stock.

        Args:
            ticker: Stock symbol (e.g., 'AAPL', 'MSFT')

        Returns:
            Quote data including price, change, volume, and more.
        """
        cache_key = f"quote:{ticker.upper()}"

        async def fetch():
            client = get_av_client()
            raw = await client.get_quote(ticker.upper())

            # Normalize the response
            return {
                "ticker": ticker.upper(),
                "price": float(raw.get("05. price", 0)),
                "change": float(raw.get("09. change", 0)),
                "change_percent": raw.get("10. change percent", "0%").replace("%", ""),
                "open": float(raw.get("02. open", 0)),
                "high": float(raw.get("03. high", 0)),
                "low": float(raw.get("04. low", 0)),
                "prev_close": float(raw.get("08. previous close", 0)),
                "volume": int(raw.get("06. volume", 0)),
                "latest_trading_day": raw.get("07. latest trading day", ""),
            }

        return await get_or_fetch(cache_key, config.CACHE_TTL_QUOTE, fetch)

    @mcp.tool()
    async def get_historical_prices(
        ticker: str,
        timeframe: str = "1M",
        interval: str = "1day"
    ) -> dict[str, Any]:
        """Get historical price data for a stock.

        Args:
            ticker: Stock symbol (e.g., 'AAPL', 'MSFT')
            timeframe: Time range - '1D', '1W', '1M', '3M', '1Y', '5Y'
            interval: Data interval - '1min', '5min', '15min', '30min', '60min', '1day'

        Returns:
            Historical OHLCV data as a list of candles.
        """
        cache_key = f"historical:{ticker.upper()}:{timeframe}:{interval}"

        async def fetch():
            client = get_av_client()

            # Determine output size based on timeframe
            outputsize = "full" if timeframe in ["1Y", "5Y"] else "compact"

            if interval == "1day":
                raw = await client.get_daily_prices(ticker.upper(), outputsize)
                time_series = raw.get("Time Series (Daily)", {})
            else:
                raw = await client.get_intraday_prices(ticker.upper(), interval, outputsize)
                time_series = raw.get(f"Time Series ({interval})", {})

            # Convert to list of candles
            candles = []
            for date, values in sorted(time_series.items(), reverse=True):
                candles.append({
                    "date": date,
                    "open": float(values.get("1. open", 0)),
                    "high": float(values.get("2. high", 0)),
                    "low": float(values.get("3. low", 0)),
                    "close": float(values.get("4. close", 0)),
                    "volume": int(values.get("5. volume", 0)),
                })

            # Limit based on timeframe
            limits = {
                "1D": 1,
                "1W": 5,
                "1M": 22,
                "3M": 66,
                "1Y": 252,
                "5Y": 1260,
            }
            limit = limits.get(timeframe, 22)

            return {
                "ticker": ticker.upper(),
                "timeframe": timeframe,
                "interval": interval,
                "candles": candles[:limit],
            }

        return await get_or_fetch(cache_key, config.CACHE_TTL_QUOTE, fetch)
