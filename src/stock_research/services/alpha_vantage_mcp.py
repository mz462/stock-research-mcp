"""Alpha Vantage MCP client wrapper.

This service calls the Alpha Vantage MCP server via HTTP to fetch stock data.
The AV MCP provides tools through the MCP protocol, but we can also call
their underlying API directly for simpler integration.
"""

import httpx
from typing import Any, Optional

from stock_research.config import config

# Alpha Vantage base URL (direct API, simpler than MCP protocol)
AV_BASE_URL = "https://www.alphavantage.co/query"


class AlphaVantageClient:
    """Client for Alpha Vantage API."""

    def __init__(self):
        self.api_key = config.ALPHA_VANTAGE_API_KEY
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def _request(self, function: str, **params) -> dict[str, Any]:
        """Make a request to Alpha Vantage API."""
        params["function"] = function
        params["apikey"] = self.api_key

        response = await self.client.get(AV_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        # Check for API errors
        if "Error Message" in data:
            raise ValueError(f"Alpha Vantage API error: {data['Error Message']}")
        if "Note" in data:
            raise ValueError(f"Alpha Vantage rate limit: {data['Note']}")

        return data

    # Core Stock APIs
    async def get_quote(self, symbol: str) -> dict[str, Any]:
        """Get real-time quote for a symbol."""
        data = await self._request("GLOBAL_QUOTE", symbol=symbol)
        return data.get("Global Quote", {})

    async def get_daily_prices(
        self,
        symbol: str,
        outputsize: str = "compact"  # compact=100 days, full=20+ years
    ) -> dict[str, Any]:
        """Get daily time series data."""
        data = await self._request(
            "TIME_SERIES_DAILY",
            symbol=symbol,
            outputsize=outputsize
        )
        return data

    async def get_intraday_prices(
        self,
        symbol: str,
        interval: str = "5min",  # 1min, 5min, 15min, 30min, 60min
        outputsize: str = "compact"
    ) -> dict[str, Any]:
        """Get intraday time series data."""
        data = await self._request(
            "TIME_SERIES_INTRADAY",
            symbol=symbol,
            interval=interval,
            outputsize=outputsize
        )
        return data

    # Fundamental Data
    async def get_company_overview(self, symbol: str) -> dict[str, Any]:
        """Get company overview and fundamentals."""
        return await self._request("OVERVIEW", symbol=symbol)

    async def get_income_statement(self, symbol: str) -> dict[str, Any]:
        """Get income statement data."""
        return await self._request("INCOME_STATEMENT", symbol=symbol)

    async def get_balance_sheet(self, symbol: str) -> dict[str, Any]:
        """Get balance sheet data."""
        return await self._request("BALANCE_SHEET", symbol=symbol)

    async def get_cash_flow(self, symbol: str) -> dict[str, Any]:
        """Get cash flow statement data."""
        return await self._request("CASH_FLOW", symbol=symbol)

    async def get_earnings(self, symbol: str) -> dict[str, Any]:
        """Get earnings data."""
        return await self._request("EARNINGS", symbol=symbol)

    # Alpha Intelligence
    async def get_news_sentiment(
        self,
        tickers: str,
        limit: int = 50
    ) -> dict[str, Any]:
        """Get news sentiment for tickers."""
        return await self._request(
            "NEWS_SENTIMENT",
            tickers=tickers,
            limit=limit
        )

    async def get_insider_transactions(self, symbol: str) -> dict[str, Any]:
        """Get insider transactions."""
        return await self._request("INSIDER_TRANSACTIONS", symbol=symbol)

    # Technical Indicators
    async def get_sma(
        self,
        symbol: str,
        interval: str = "daily",
        time_period: int = 20,
        series_type: str = "close"
    ) -> dict[str, Any]:
        """Get Simple Moving Average."""
        return await self._request(
            "SMA",
            symbol=symbol,
            interval=interval,
            time_period=time_period,
            series_type=series_type
        )

    async def get_ema(
        self,
        symbol: str,
        interval: str = "daily",
        time_period: int = 20,
        series_type: str = "close"
    ) -> dict[str, Any]:
        """Get Exponential Moving Average."""
        return await self._request(
            "EMA",
            symbol=symbol,
            interval=interval,
            time_period=time_period,
            series_type=series_type
        )

    async def get_rsi(
        self,
        symbol: str,
        interval: str = "daily",
        time_period: int = 14,
        series_type: str = "close"
    ) -> dict[str, Any]:
        """Get Relative Strength Index."""
        return await self._request(
            "RSI",
            symbol=symbol,
            interval=interval,
            time_period=time_period,
            series_type=series_type
        )

    async def get_macd(
        self,
        symbol: str,
        interval: str = "daily",
        series_type: str = "close"
    ) -> dict[str, Any]:
        """Get MACD indicator."""
        return await self._request(
            "MACD",
            symbol=symbol,
            interval=interval,
            series_type=series_type
        )

    async def get_bbands(
        self,
        symbol: str,
        interval: str = "daily",
        time_period: int = 20,
        series_type: str = "close"
    ) -> dict[str, Any]:
        """Get Bollinger Bands."""
        return await self._request(
            "BBANDS",
            symbol=symbol,
            interval=interval,
            time_period=time_period,
            series_type=series_type
        )

    # Economic Indicators
    async def get_federal_funds_rate(self) -> dict[str, Any]:
        """Get federal funds rate."""
        return await self._request("FEDERAL_FUNDS_RATE")

    async def get_treasury_yield(self, maturity: str = "10year") -> dict[str, Any]:
        """Get treasury yield. Maturity: 3month, 2year, 5year, 7year, 10year, 30year."""
        return await self._request("TREASURY_YIELD", maturity=maturity)

    async def get_cpi(self) -> dict[str, Any]:
        """Get Consumer Price Index."""
        return await self._request("CPI")

    async def get_unemployment(self) -> dict[str, Any]:
        """Get unemployment rate."""
        return await self._request("UNEMPLOYMENT")

    async def get_real_gdp(self) -> dict[str, Any]:
        """Get real GDP."""
        return await self._request("REAL_GDP")


# Singleton client instance
_client: Optional[AlphaVantageClient] = None


def get_av_client() -> AlphaVantageClient:
    """Get the Alpha Vantage client singleton."""
    global _client
    if _client is None:
        _client = AlphaVantageClient()
    return _client


async def close_av_client() -> None:
    """Close the Alpha Vantage client."""
    global _client
    if _client:
        await _client.close()
        _client = None
