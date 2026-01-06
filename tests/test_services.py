"""Tests for service layer."""

import pytest
import httpx
import respx
import os
import tempfile

from stock_research.services.cache import init_cache, close_cache, get, set, get_or_fetch, clear_expired
from stock_research.services.alpha_vantage_mcp import AlphaVantageClient
from stock_research.services.finnhub import FinnhubClient


class TestCache:
    """Tests for cache service."""

    @pytest.fixture(autouse=True)
    async def setup_cache(self, temp_cache_db):
        """Set up and tear down cache for each test."""
        # Override config
        import stock_research.config
        original_path = stock_research.config.config.CACHE_DB_PATH
        stock_research.config.config.CACHE_DB_PATH = temp_cache_db

        await init_cache()
        yield
        await close_cache()

        stock_research.config.config.CACHE_DB_PATH = original_path

    async def test_set_and_get(self):
        """Test basic set and get operations."""
        await set("test_key", {"value": 123}, ttl=60)
        result = await get("test_key")
        assert result == {"value": 123}

    async def test_get_nonexistent(self):
        """Test getting a key that doesn't exist."""
        result = await get("nonexistent_key")
        assert result is None

    async def test_expired_key(self):
        """Test that expired keys return None."""
        await set("expire_key", {"value": "old"}, ttl=0)  # Expires immediately
        result = await get("expire_key")
        assert result is None

    async def test_get_or_fetch_cached(self):
        """Test get_or_fetch returns cached value."""
        await set("cached_key", {"cached": True}, ttl=60)

        async def fetch_fn():
            return {"cached": False}

        result = await get_or_fetch("cached_key", 60, fetch_fn)
        assert result == {"cached": True}

    async def test_get_or_fetch_fetches(self):
        """Test get_or_fetch calls fetch function when not cached."""
        fetch_called = False

        async def fetch_fn():
            nonlocal fetch_called
            fetch_called = True
            return {"fetched": True}

        result = await get_or_fetch("new_key", 60, fetch_fn)
        assert fetch_called
        assert result == {"fetched": True}

        # Verify it was cached
        cached = await get("new_key")
        assert cached == {"fetched": True}


class TestAlphaVantageClient:
    """Tests for Alpha Vantage client."""

    @pytest.fixture
    def client(self):
        """Create a client instance."""
        return AlphaVantageClient()

    @respx.mock
    async def test_get_quote(self, client, av_quote_response):
        """Test getting a stock quote."""
        respx.get("https://www.alphavantage.co/query").mock(
            return_value=httpx.Response(200, json=av_quote_response)
        )

        result = await client.get_quote("AAPL")

        assert result["05. price"] == "151.50"
        assert result["06. volume"] == "50000000"

    @respx.mock
    async def test_get_daily_prices(self, client, av_daily_response):
        """Test getting daily price data."""
        respx.get("https://www.alphavantage.co/query").mock(
            return_value=httpx.Response(200, json=av_daily_response)
        )

        result = await client.get_daily_prices("AAPL")

        assert "Time Series (Daily)" in result
        assert "2026-01-03" in result["Time Series (Daily)"]

    @respx.mock
    async def test_get_company_overview(self, client, av_company_overview_response):
        """Test getting company overview."""
        respx.get("https://www.alphavantage.co/query").mock(
            return_value=httpx.Response(200, json=av_company_overview_response)
        )

        result = await client.get_company_overview("AAPL")

        assert result["Name"] == "Apple Inc"
        assert result["Sector"] == "Technology"
        assert result["PERatio"] == "28.5"

    @respx.mock
    async def test_get_earnings(self, client, av_earnings_response):
        """Test getting earnings data."""
        respx.get("https://www.alphavantage.co/query").mock(
            return_value=httpx.Response(200, json=av_earnings_response)
        )

        result = await client.get_earnings("AAPL")

        assert "quarterlyEarnings" in result
        assert len(result["quarterlyEarnings"]) == 2

    @respx.mock
    async def test_get_news_sentiment(self, client, av_news_sentiment_response):
        """Test getting news sentiment."""
        respx.get("https://www.alphavantage.co/query").mock(
            return_value=httpx.Response(200, json=av_news_sentiment_response)
        )

        result = await client.get_news_sentiment("AAPL", limit=10)

        assert "feed" in result
        assert len(result["feed"]) == 2

    @respx.mock
    async def test_get_insider_transactions(self, client, av_insider_response):
        """Test getting insider transactions."""
        respx.get("https://www.alphavantage.co/query").mock(
            return_value=httpx.Response(200, json=av_insider_response)
        )

        result = await client.get_insider_transactions("AAPL")

        assert "data" in result
        assert len(result["data"]) == 2

    @respx.mock
    async def test_get_rsi(self, client, av_rsi_response):
        """Test getting RSI indicator."""
        respx.get("https://www.alphavantage.co/query").mock(
            return_value=httpx.Response(200, json=av_rsi_response)
        )

        result = await client.get_rsi("AAPL")

        assert "Technical Analysis: RSI" in result

    @respx.mock
    async def test_get_macd(self, client, av_macd_response):
        """Test getting MACD indicator."""
        respx.get("https://www.alphavantage.co/query").mock(
            return_value=httpx.Response(200, json=av_macd_response)
        )

        result = await client.get_macd("AAPL")

        assert "Technical Analysis: MACD" in result

    @respx.mock
    async def test_api_error_handling(self, client):
        """Test handling of API errors."""
        respx.get("https://www.alphavantage.co/query").mock(
            return_value=httpx.Response(200, json={"Error Message": "Invalid API call"})
        )

        with pytest.raises(ValueError, match="Alpha Vantage API error"):
            await client.get_quote("INVALID")

    @respx.mock
    async def test_rate_limit_handling(self, client):
        """Test handling of rate limit responses."""
        respx.get("https://www.alphavantage.co/query").mock(
            return_value=httpx.Response(200, json={"Note": "API call frequency exceeded"})
        )

        with pytest.raises(ValueError, match="Alpha Vantage rate limit"):
            await client.get_quote("AAPL")


class TestFinnhubClient:
    """Tests for Finnhub client."""

    @pytest.fixture
    def client(self):
        """Create a client instance."""
        return FinnhubClient()

    @respx.mock
    async def test_get_analyst_recommendations(self, client, finnhub_recommendations_response):
        """Test getting analyst recommendations."""
        respx.get("https://finnhub.io/api/v1/stock/recommendation").mock(
            return_value=httpx.Response(200, json=finnhub_recommendations_response)
        )

        result = await client.get_analyst_recommendations("AAPL")

        assert len(result) == 1
        assert result[0]["buy"] == 25
        assert result[0]["strongBuy"] == 15

    @respx.mock
    async def test_get_price_target(self, client, finnhub_price_target_response):
        """Test getting price targets."""
        respx.get("https://finnhub.io/api/v1/stock/price-target").mock(
            return_value=httpx.Response(200, json=finnhub_price_target_response)
        )

        result = await client.get_price_target("AAPL")

        assert result["targetMean"] == 185.0
        assert result["targetHigh"] == 220.0
        assert result["targetLow"] == 140.0

    @respx.mock
    async def test_get_upgrades_downgrades(self, client, finnhub_upgrades_response):
        """Test getting upgrades/downgrades."""
        respx.get("https://finnhub.io/api/v1/stock/upgrade-downgrade").mock(
            return_value=httpx.Response(200, json=finnhub_upgrades_response)
        )

        result = await client.get_upgrades_downgrades("AAPL")

        assert len(result) == 2
        assert result[0]["action"] == "upgrade"
        assert result[0]["company"] == "Morgan Stanley"
