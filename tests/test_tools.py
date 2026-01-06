"""Tests for MCP tools."""

import pytest
import httpx
import respx

from stock_research.services.cache import init_cache, close_cache
from stock_research.services.alpha_vantage_mcp import AlphaVantageClient, get_av_client
from stock_research.services.finnhub import FinnhubClient, get_finnhub_client


class TestMarketDataTools:
    """Tests for market data tools."""

    @pytest.fixture(autouse=True)
    async def setup(self, temp_cache_db):
        """Set up cache for each test."""
        import stock_research.config
        stock_research.config.config.CACHE_DB_PATH = temp_cache_db
        await init_cache()
        yield
        await close_cache()

    @respx.mock
    async def test_get_quote_normalization(self, av_quote_response):
        """Test that quote data is properly normalized."""
        from mcp.server import FastMCP
        from stock_research.tools.market_data import register_market_data_tools

        respx.get("https://www.alphavantage.co/query").mock(
            return_value=httpx.Response(200, json=av_quote_response)
        )

        mcp = FastMCP("test")
        register_market_data_tools(mcp)

        # Find the get_quote tool and call it
        tools = mcp._tool_manager._tools
        get_quote_tool = tools.get("get_quote")
        assert get_quote_tool is not None

        result = await get_quote_tool.fn(ticker="AAPL")

        assert result["ticker"] == "AAPL"
        assert result["price"] == 151.50
        assert result["change"] == 2.00
        assert result["volume"] == 50000000

    @respx.mock
    async def test_get_historical_prices(self, av_daily_response):
        """Test historical prices tool."""
        from mcp.server import FastMCP
        from stock_research.tools.market_data import register_market_data_tools

        respx.get("https://www.alphavantage.co/query").mock(
            return_value=httpx.Response(200, json=av_daily_response)
        )

        mcp = FastMCP("test")
        register_market_data_tools(mcp)

        tools = mcp._tool_manager._tools
        get_historical = tools.get("get_historical_prices")

        result = await get_historical.fn(ticker="AAPL", timeframe="1W", interval="1day")

        assert result["ticker"] == "AAPL"
        assert result["timeframe"] == "1W"
        assert len(result["candles"]) <= 5  # 1W = 5 trading days


class TestCompanyTools:
    """Tests for company tools."""

    @pytest.fixture(autouse=True)
    async def setup(self, temp_cache_db):
        """Set up cache for each test."""
        import stock_research.config
        stock_research.config.config.CACHE_DB_PATH = temp_cache_db
        await init_cache()
        yield
        await close_cache()

    @respx.mock
    async def test_get_company_profile(self, av_company_overview_response):
        """Test company profile normalization."""
        from mcp.server import FastMCP
        from stock_research.tools.company import register_company_tools

        respx.get("https://www.alphavantage.co/query").mock(
            return_value=httpx.Response(200, json=av_company_overview_response)
        )

        mcp = FastMCP("test")
        register_company_tools(mcp)

        tools = mcp._tool_manager._tools
        get_profile = tools.get("get_company_profile")

        result = await get_profile.fn(ticker="AAPL")

        assert result["ticker"] == "AAPL"
        assert result["name"] == "Apple Inc"
        assert result["sector"] == "Technology"
        assert result["market_cap"] == 3000000000000

    @respx.mock
    async def test_get_financials(self, av_company_overview_response):
        """Test financials extraction."""
        from mcp.server import FastMCP
        from stock_research.tools.company import register_company_tools

        respx.get("https://www.alphavantage.co/query").mock(
            return_value=httpx.Response(200, json=av_company_overview_response)
        )

        mcp = FastMCP("test")
        register_company_tools(mcp)

        tools = mcp._tool_manager._tools
        get_financials = tools.get("get_financials")

        result = await get_financials.fn(ticker="AAPL")

        assert result["ticker"] == "AAPL"
        assert result["pe_ratio"] == 28.5
        assert result["forward_pe"] == 25.0
        assert result["beta"] == 1.2

    @respx.mock
    async def test_get_earnings(self, av_earnings_response):
        """Test earnings data processing."""
        from mcp.server import FastMCP
        from stock_research.tools.company import register_company_tools

        respx.get("https://www.alphavantage.co/query").mock(
            return_value=httpx.Response(200, json=av_earnings_response)
        )

        mcp = FastMCP("test")
        register_company_tools(mcp)

        tools = mcp._tool_manager._tools
        get_earnings = tools.get("get_earnings")

        result = await get_earnings.fn(ticker="AAPL")

        assert result["ticker"] == "AAPL"
        assert len(result["recent_quarters"]) == 2
        assert result["recent_quarters"][0]["eps_actual"] == 2.10


class TestAnalystTools:
    """Tests for analyst tools."""

    @pytest.fixture(autouse=True)
    async def setup(self, temp_cache_db):
        """Set up cache for each test."""
        import stock_research.config
        stock_research.config.config.CACHE_DB_PATH = temp_cache_db
        await init_cache()
        yield
        await close_cache()

    @respx.mock
    async def test_get_analyst_ratings(
        self,
        finnhub_recommendations_response,
        finnhub_price_target_response,
        finnhub_upgrades_response
    ):
        """Test analyst ratings aggregation."""
        from mcp.server import FastMCP
        from stock_research.tools.analysts import register_analyst_tools

        # Mock all three Finnhub endpoints
        respx.get("https://finnhub.io/api/v1/stock/recommendation").mock(
            return_value=httpx.Response(200, json=finnhub_recommendations_response)
        )
        respx.get("https://finnhub.io/api/v1/stock/price-target").mock(
            return_value=httpx.Response(200, json=finnhub_price_target_response)
        )
        respx.get("https://finnhub.io/api/v1/stock/upgrade-downgrade").mock(
            return_value=httpx.Response(200, json=finnhub_upgrades_response)
        )

        mcp = FastMCP("test")
        register_analyst_tools(mcp)

        tools = mcp._tool_manager._tools
        get_ratings = tools.get("get_analyst_ratings")

        result = await get_ratings.fn(ticker="AAPL")

        assert result["ticker"] == "AAPL"
        assert result["buy_count"] == 40  # 25 buy + 15 strongBuy
        assert result["hold_count"] == 10
        assert result["sell_count"] == 3  # 2 sell + 1 strongSell
        assert result["price_target_avg"] == 185.0
        assert result["consensus"] in ["strong_buy", "buy", "hold", "sell", "strong_sell"]


class TestSentimentTools:
    """Tests for sentiment tools."""

    @pytest.fixture(autouse=True)
    async def setup(self, temp_cache_db):
        """Set up cache for each test."""
        import stock_research.config
        stock_research.config.config.CACHE_DB_PATH = temp_cache_db
        await init_cache()
        yield
        await close_cache()

    @respx.mock
    async def test_get_news_sentiment(self, av_news_sentiment_response):
        """Test news sentiment aggregation."""
        from mcp.server import FastMCP
        from stock_research.tools.sentiment import register_sentiment_tools

        respx.get("https://www.alphavantage.co/query").mock(
            return_value=httpx.Response(200, json=av_news_sentiment_response)
        )

        mcp = FastMCP("test")
        register_sentiment_tools(mcp)

        tools = mcp._tool_manager._tools
        get_news = tools.get("get_news_sentiment")

        result = await get_news.fn(ticker="AAPL", limit=10)

        assert result["ticker"] == "AAPL"
        assert result["article_count"] == 2
        assert "average_score" in result
        assert result["overall_sentiment"] in ["bullish", "bearish", "neutral"]

    @respx.mock
    async def test_get_insider_trades(self, av_insider_response):
        """Test insider trading analysis."""
        from mcp.server import FastMCP
        from stock_research.tools.sentiment import register_sentiment_tools

        respx.get("https://www.alphavantage.co/query").mock(
            return_value=httpx.Response(200, json=av_insider_response)
        )

        mcp = FastMCP("test")
        register_sentiment_tools(mcp)

        tools = mcp._tool_manager._tools
        get_insiders = tools.get("get_insider_trades")

        result = await get_insiders.fn(ticker="AAPL")

        assert result["ticker"] == "AAPL"
        assert result["total_bought"] == 10000
        assert result["total_sold"] == 50000
        assert result["net_insider_sentiment"] == "selling"


class TestTechnicalTools:
    """Tests for technical analysis tools."""

    @pytest.fixture(autouse=True)
    async def setup(self, temp_cache_db):
        """Set up cache for each test."""
        import stock_research.config
        stock_research.config.config.CACHE_DB_PATH = temp_cache_db
        await init_cache()
        yield
        await close_cache()

    @respx.mock
    async def test_get_technical_indicators_rsi(self, av_daily_response):
        """Test RSI indicator retrieval."""
        from mcp.server import FastMCP
        from stock_research.tools.technicals import register_technical_tools

        # Create extended daily data for RSI calculation (needs 15+ days)
        extended_response = av_daily_response.copy()
        time_series = extended_response["Time Series (Daily)"]

        # Add enough days for RSI calculation with alternating up/down moves
        for i in range(4, 50):
            date = f"2025-12-{31-i:02d}" if i < 31 else f"2025-11-{61-i:02d}"
            # Alternate between up and down days to get neutral RSI
            base_price = 145 + (i % 3)
            time_series[date] = {
                "1. open": str(base_price),
                "2. high": str(base_price + 2),
                "3. low": str(base_price - 1),
                "4. close": str(base_price + 1),
                "5. volume": "40000000",
            }

        respx.get("https://www.alphavantage.co/query").mock(
            return_value=httpx.Response(200, json=extended_response)
        )

        mcp = FastMCP("test")
        register_technical_tools(mcp)

        tools = mcp._tool_manager._tools
        get_technicals = tools.get("get_technical_indicators")

        result = await get_technicals.fn(ticker="AAPL", indicators=["rsi"])

        assert result["ticker"] == "AAPL"
        assert "rsi" in result
        assert result["rsi"]["rsi_14"] is not None
        assert result["rsi"]["signal"] in ["overbought", "oversold", "neutral"]

    @respx.mock
    async def test_get_support_resistance(self, av_daily_response):
        """Test support/resistance calculation."""
        from mcp.server import FastMCP
        from stock_research.tools.technicals import register_technical_tools

        # Create more price data for support/resistance calculation
        extended_response = av_daily_response.copy()
        time_series = extended_response["Time Series (Daily)"]

        # Add more days with varying prices
        for i in range(4, 70):
            date = f"2025-12-{31-i:02d}" if i < 31 else f"2025-11-{61-i:02d}"
            base_price = 145 + (i % 10)
            time_series[date] = {
                "1. open": str(base_price),
                "2. high": str(base_price + 3),
                "3. low": str(base_price - 2),
                "4. close": str(base_price + 1),
                "5. volume": "40000000",
            }

        respx.get("https://www.alphavantage.co/query").mock(
            return_value=httpx.Response(200, json=extended_response)
        )

        mcp = FastMCP("test")
        register_technical_tools(mcp)

        tools = mcp._tool_manager._tools
        get_sr = tools.get("get_support_resistance")

        result = await get_sr.fn(ticker="AAPL", lookback_days=60)

        assert result["ticker"] == "AAPL"
        assert "support_levels" in result
        assert "resistance_levels" in result
        assert "current_price" in result
