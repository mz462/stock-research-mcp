"""Finnhub API client for analyst ratings.

This is the only data not available in Alpha Vantage MCP.
"""

import httpx
from typing import Any, Optional
from datetime import datetime, timedelta

from stock_research.config import config


class FinnhubClient:
    """Client for Finnhub API."""

    def __init__(self):
        self.api_key = config.FINNHUB_API_KEY
        self.base_url = config.FINNHUB_BASE_URL
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def _request(self, endpoint: str, **params) -> Any:
        """Make a request to Finnhub API."""
        params["token"] = self.api_key
        url = f"{self.base_url}/{endpoint}"

        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def get_analyst_recommendations(self, symbol: str) -> list[dict[str, Any]]:
        """Get analyst recommendations/ratings for a symbol.

        Returns list of recommendations with fields:
        - buy, hold, sell, strongBuy, strongSell counts
        - period (date)
        - symbol
        """
        return await self._request("stock/recommendation", symbol=symbol)

    async def get_price_target(self, symbol: str) -> dict[str, Any]:
        """Get analyst price targets.

        Returns:
        - lastUpdated
        - symbol
        - targetHigh
        - targetLow
        - targetMean
        - targetMedian
        """
        return await self._request("stock/price-target", symbol=symbol)

    async def get_recommendation_trends(self, symbol: str) -> list[dict[str, Any]]:
        """Get recommendation trends over time."""
        return await self._request("stock/recommendation", symbol=symbol)

    async def get_upgrades_downgrades(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """Get analyst upgrades/downgrades.

        Returns list of rating changes with fields:
        - action (upgrade, downgrade, etc)
        - company (firm name)
        - fromGrade
        - toGrade
        - gradeTime
        """
        if from_date is None:
            from_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        if to_date is None:
            to_date = datetime.now().strftime("%Y-%m-%d")

        params = {
            "symbol": symbol,
            "from": from_date,
            "to": to_date
        }
        return await self._request("stock/upgrade-downgrade", **params)


# Singleton client instance
_client: Optional[FinnhubClient] = None


def get_finnhub_client() -> FinnhubClient:
    """Get the Finnhub client singleton."""
    global _client
    if _client is None:
        _client = FinnhubClient()
    return _client


async def close_finnhub_client() -> None:
    """Close the Finnhub client."""
    global _client
    if _client:
        await _client.close()
        _client = None
