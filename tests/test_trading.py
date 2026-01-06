"""Tests for trading tools and Alpaca service."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime
import os

# Set test environment variables before importing
os.environ["ALPACA_API_KEY"] = "test_alpaca_key"
os.environ["ALPACA_SECRET_KEY"] = "test_alpaca_secret"
os.environ["ALPACA_PAPER"] = "true"
os.environ["TRADING_MAX_ORDER_VALUE"] = "5000"
os.environ["TRADING_MAX_POSITION_SIZE"] = "10000"

from stock_research.services.alpaca import (
    AlpacaTradingClient,
    TradingError,
    RiskLimitError,
    reset_trading_client,
)
from stock_research.config import config


@pytest.fixture
def mock_alpaca_order():
    """Create a mock Alpaca order object."""
    order = MagicMock()
    order.id = "order-123"
    order.client_order_id = "client-123"
    order.symbol = "AAPL"
    order.qty = 10
    order.filled_qty = 0
    order.side.value = "buy"
    order.type.value = "market"
    order.status.value = "new"
    order.limit_price = None
    order.stop_price = None
    order.filled_avg_price = None
    order.time_in_force.value = "day"
    order.created_at = datetime.now()
    order.submitted_at = datetime.now()
    order.filled_at = None
    return order


@pytest.fixture
def mock_alpaca_position():
    """Create a mock Alpaca position object."""
    pos = MagicMock()
    pos.symbol = "AAPL"
    pos.qty = 100
    pos.side.value = "long"
    pos.market_value = 15000.0
    pos.cost_basis = 14000.0
    pos.unrealized_pl = 1000.0
    pos.unrealized_plpc = 0.0714
    pos.current_price = 150.0
    pos.avg_entry_price = 140.0
    pos.change_today = 0.02
    return pos


@pytest.fixture
def mock_alpaca_account():
    """Create a mock Alpaca account object."""
    account = MagicMock()
    account.id = "account-123"
    account.status.value = "ACTIVE"
    account.currency = "USD"
    account.buying_power = 50000.0
    account.cash = 25000.0
    account.portfolio_value = 100000.0
    account.equity = 100000.0
    account.last_equity = 98000.0
    account.long_market_value = 75000.0
    account.short_market_value = 0.0
    account.pattern_day_trader = False
    account.trading_blocked = False
    return account


@pytest.fixture(autouse=True)
def reset_client():
    """Reset the trading client singleton before each test."""
    reset_trading_client()
    yield
    reset_trading_client()


class TestAlpacaTradingClient:
    """Tests for the Alpaca trading client service."""

    @patch("stock_research.services.alpaca.TradingClient")
    def test_client_initialization(self, mock_trading_client):
        """Test that client initializes with correct settings."""
        client = AlpacaTradingClient()

        assert client.paper is True
        assert client.max_order_value == 5000.0
        assert client.max_position_size == 10000.0
        mock_trading_client.assert_called_once_with(
            api_key="test_alpaca_key",
            secret_key="test_alpaca_secret",
            paper=True,
        )

    @patch("stock_research.services.alpaca.TradingClient")
    def test_validate_symbol_allowed(self, mock_trading_client):
        """Test symbol validation when allowed list is configured."""
        client = AlpacaTradingClient()
        client.allowed_symbols = ["AAPL", "MSFT", "GOOGL"]

        # Should not raise for allowed symbol
        client._validate_symbol("AAPL")
        client._validate_symbol("msft")  # Case insensitive

        # Should raise for disallowed symbol
        with pytest.raises(RiskLimitError) as exc:
            client._validate_symbol("TSLA")
        assert "not in allowed list" in str(exc.value)

    @patch("stock_research.services.alpaca.TradingClient")
    def test_validate_order_value(self, mock_trading_client):
        """Test order value validation."""
        client = AlpacaTradingClient()
        client.max_order_value = 5000.0

        # Should not raise for order under limit
        client._validate_order_value(10, 100.0)  # $1000

        # Should raise for order over limit
        with pytest.raises(RiskLimitError) as exc:
            client._validate_order_value(100, 100.0)  # $10000
        assert "exceeds max" in str(exc.value)

    @patch("stock_research.services.alpaca.TradingClient")
    async def test_get_account(self, mock_trading_client, mock_alpaca_account):
        """Test getting account information."""
        mock_instance = mock_trading_client.return_value
        mock_instance.get_account.return_value = mock_alpaca_account

        client = AlpacaTradingClient()
        account = await client.get_account()

        assert account["account_id"] == "account-123"
        assert account["buying_power"] == 50000.0
        assert account["equity"] == 100000.0
        assert account["paper"] is True

    @patch("stock_research.services.alpaca.TradingClient")
    async def test_get_positions(self, mock_trading_client, mock_alpaca_position):
        """Test getting all positions."""
        mock_instance = mock_trading_client.return_value
        mock_instance.get_all_positions.return_value = [mock_alpaca_position]

        client = AlpacaTradingClient()
        positions = await client.get_positions()

        assert len(positions) == 1
        assert positions[0]["symbol"] == "AAPL"
        assert positions[0]["qty"] == 100
        assert positions[0]["unrealized_pl"] == 1000.0

    @patch("stock_research.services.alpaca.TradingClient")
    async def test_place_market_order(self, mock_trading_client, mock_alpaca_order):
        """Test placing a market order."""
        mock_instance = mock_trading_client.return_value
        mock_instance.submit_order.return_value = mock_alpaca_order

        client = AlpacaTradingClient()
        order = await client.place_market_order("AAPL", 10, "buy", "day")

        assert order["order_id"] == "order-123"
        assert order["symbol"] == "AAPL"
        assert order["qty"] == 10
        assert order["side"] == "buy"
        mock_instance.submit_order.assert_called_once()

    @patch("stock_research.services.alpaca.TradingClient")
    async def test_place_limit_order(self, mock_trading_client, mock_alpaca_order):
        """Test placing a limit order."""
        mock_instance = mock_trading_client.return_value
        mock_alpaca_order.type.value = "limit"
        mock_alpaca_order.limit_price = 150.0
        mock_instance.submit_order.return_value = mock_alpaca_order

        client = AlpacaTradingClient()
        order = await client.place_limit_order("AAPL", 10, "buy", 150.0, "day")

        assert order["order_id"] == "order-123"
        assert order["type"] == "limit"
        assert order["limit_price"] == 150.0

    @patch("stock_research.services.alpaca.TradingClient")
    async def test_cancel_order(self, mock_trading_client):
        """Test cancelling an order."""
        mock_instance = mock_trading_client.return_value
        mock_instance.cancel_order_by_id.return_value = None

        client = AlpacaTradingClient()
        result = await client.cancel_order("order-123")

        assert result["status"] == "cancelled"
        assert result["order_id"] == "order-123"
        mock_instance.cancel_order_by_id.assert_called_once_with("order-123")

    @patch("stock_research.services.alpaca.TradingClient")
    async def test_close_position(self, mock_trading_client, mock_alpaca_order):
        """Test closing a position."""
        mock_instance = mock_trading_client.return_value
        mock_alpaca_order.side.value = "sell"
        mock_instance.close_position.return_value = mock_alpaca_order

        client = AlpacaTradingClient()
        order = await client.close_position("AAPL")

        assert order["symbol"] == "AAPL"
        assert order["side"] == "sell"
        mock_instance.close_position.assert_called_once_with("AAPL")


class TestTradingConfig:
    """Tests for trading configuration."""

    def test_paper_trading_default(self):
        """Test that paper trading is enabled by default."""
        assert config.ALPACA_PAPER is True

    def test_max_order_value_configured(self):
        """Test that max order value is configured from env."""
        assert config.TRADING_MAX_ORDER_VALUE == 5000.0

    def test_max_position_size_configured(self):
        """Test that max position size is configured from env."""
        assert config.TRADING_MAX_POSITION_SIZE == 10000.0


class TestRiskControls:
    """Tests for trading risk controls."""

    @patch("stock_research.services.alpaca.TradingClient")
    async def test_symbol_restriction_enforced(self, mock_trading_client):
        """Test that symbol restrictions are enforced on orders."""
        client = AlpacaTradingClient()
        client.allowed_symbols = ["AAPL", "MSFT"]

        with pytest.raises(RiskLimitError):
            await client.place_market_order("TSLA", 10, "buy", "day")

    @patch("stock_research.services.alpaca.TradingClient")
    async def test_order_value_limit_enforced(self, mock_trading_client):
        """Test that order value limits are enforced on limit orders."""
        client = AlpacaTradingClient()
        client.max_order_value = 1000.0

        with pytest.raises(RiskLimitError):
            await client.place_limit_order("AAPL", 100, "buy", 150.0, "day")
