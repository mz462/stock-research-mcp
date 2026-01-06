"""Alpaca trading client for executing trades.

Supports both paper and live trading with built-in risk controls.
"""

from typing import Any, Optional
from decimal import Decimal

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    MarketOrderRequest,
    LimitOrderRequest,
    StopOrderRequest,
    StopLimitOrderRequest,
    GetOrdersRequest,
)
from alpaca.trading.enums import OrderSide, TimeInForce, OrderStatus, QueryOrderStatus
from alpaca.common.exceptions import APIError

from stock_research.config import config


class TradingError(Exception):
    """Custom exception for trading errors."""
    pass


class RiskLimitError(TradingError):
    """Raised when a trade exceeds risk limits."""
    pass


class AlpacaTradingClient:
    """Wrapper around Alpaca Trading API with risk controls."""

    def __init__(self):
        if not config.ALPACA_API_KEY or not config.ALPACA_SECRET_KEY:
            raise TradingError("Alpaca API keys not configured")

        self.client = TradingClient(
            api_key=config.ALPACA_API_KEY,
            secret_key=config.ALPACA_SECRET_KEY,
            paper=config.ALPACA_PAPER,
        )
        self.paper = config.ALPACA_PAPER
        self.max_position_size = config.TRADING_MAX_POSITION_SIZE
        self.max_order_value = config.TRADING_MAX_ORDER_VALUE
        self.allowed_symbols = config.TRADING_ALLOWED_SYMBOLS

    def _validate_symbol(self, symbol: str) -> None:
        """Check if symbol is in the allowed list (if configured)."""
        if self.allowed_symbols and symbol.upper() not in [s.upper() for s in self.allowed_symbols]:
            raise RiskLimitError(
                f"Symbol {symbol} not in allowed list. "
                f"Allowed: {', '.join(self.allowed_symbols)}"
            )

    def _validate_order_value(self, qty: float, price: Optional[float] = None) -> None:
        """Validate order doesn't exceed max order value."""
        if price and (qty * price) > self.max_order_value:
            raise RiskLimitError(
                f"Order value ${qty * price:.2f} exceeds max ${self.max_order_value:.2f}"
            )

    async def get_account(self) -> dict[str, Any]:
        """Get account information including buying power and equity."""
        account = self.client.get_account()
        return {
            "account_id": account.id,
            "status": account.status.value if account.status else None,
            "currency": account.currency,
            "buying_power": float(account.buying_power) if account.buying_power else 0,
            "cash": float(account.cash) if account.cash else 0,
            "portfolio_value": float(account.portfolio_value) if account.portfolio_value else 0,
            "equity": float(account.equity) if account.equity else 0,
            "last_equity": float(account.last_equity) if account.last_equity else 0,
            "long_market_value": float(account.long_market_value) if account.long_market_value else 0,
            "short_market_value": float(account.short_market_value) if account.short_market_value else 0,
            "pattern_day_trader": account.pattern_day_trader,
            "trading_blocked": account.trading_blocked,
            "paper": self.paper,
        }

    async def get_positions(self) -> list[dict[str, Any]]:
        """Get all open positions."""
        positions = self.client.get_all_positions()
        return [
            {
                "symbol": pos.symbol,
                "qty": float(pos.qty) if pos.qty else 0,
                "side": pos.side.value if pos.side else None,
                "market_value": float(pos.market_value) if pos.market_value else 0,
                "cost_basis": float(pos.cost_basis) if pos.cost_basis else 0,
                "unrealized_pl": float(pos.unrealized_pl) if pos.unrealized_pl else 0,
                "unrealized_plpc": float(pos.unrealized_plpc) if pos.unrealized_plpc else 0,
                "current_price": float(pos.current_price) if pos.current_price else 0,
                "avg_entry_price": float(pos.avg_entry_price) if pos.avg_entry_price else 0,
                "change_today": float(pos.change_today) if pos.change_today else 0,
            }
            for pos in positions
        ]

    async def get_position(self, symbol: str) -> Optional[dict[str, Any]]:
        """Get position for a specific symbol."""
        try:
            pos = self.client.get_open_position(symbol.upper())
            return {
                "symbol": pos.symbol,
                "qty": float(pos.qty) if pos.qty else 0,
                "side": pos.side.value if pos.side else None,
                "market_value": float(pos.market_value) if pos.market_value else 0,
                "cost_basis": float(pos.cost_basis) if pos.cost_basis else 0,
                "unrealized_pl": float(pos.unrealized_pl) if pos.unrealized_pl else 0,
                "unrealized_plpc": float(pos.unrealized_plpc) if pos.unrealized_plpc else 0,
                "current_price": float(pos.current_price) if pos.current_price else 0,
                "avg_entry_price": float(pos.avg_entry_price) if pos.avg_entry_price else 0,
            }
        except APIError:
            return None

    async def place_market_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        time_in_force: str = "day",
    ) -> dict[str, Any]:
        """Place a market order.

        Args:
            symbol: Stock symbol
            qty: Number of shares
            side: 'buy' or 'sell'
            time_in_force: 'day', 'gtc', 'ioc', 'fok'
        """
        self._validate_symbol(symbol)

        order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
        tif = TimeInForce[time_in_force.upper()]

        request = MarketOrderRequest(
            symbol=symbol.upper(),
            qty=qty,
            side=order_side,
            time_in_force=tif,
        )

        order = self.client.submit_order(request)
        return self._format_order(order)

    async def place_limit_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        limit_price: float,
        time_in_force: str = "day",
    ) -> dict[str, Any]:
        """Place a limit order.

        Args:
            symbol: Stock symbol
            qty: Number of shares
            side: 'buy' or 'sell'
            limit_price: Limit price
            time_in_force: 'day', 'gtc', 'ioc', 'fok'
        """
        self._validate_symbol(symbol)
        self._validate_order_value(qty, limit_price)

        order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
        tif = TimeInForce[time_in_force.upper()]

        request = LimitOrderRequest(
            symbol=symbol.upper(),
            qty=qty,
            side=order_side,
            time_in_force=tif,
            limit_price=limit_price,
        )

        order = self.client.submit_order(request)
        return self._format_order(order)

    async def place_stop_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        stop_price: float,
        time_in_force: str = "day",
    ) -> dict[str, Any]:
        """Place a stop order.

        Args:
            symbol: Stock symbol
            qty: Number of shares
            side: 'buy' or 'sell'
            stop_price: Stop trigger price
            time_in_force: 'day', 'gtc'
        """
        self._validate_symbol(symbol)

        order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
        tif = TimeInForce[time_in_force.upper()]

        request = StopOrderRequest(
            symbol=symbol.upper(),
            qty=qty,
            side=order_side,
            time_in_force=tif,
            stop_price=stop_price,
        )

        order = self.client.submit_order(request)
        return self._format_order(order)

    async def place_stop_limit_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        stop_price: float,
        limit_price: float,
        time_in_force: str = "day",
    ) -> dict[str, Any]:
        """Place a stop-limit order.

        Args:
            symbol: Stock symbol
            qty: Number of shares
            side: 'buy' or 'sell'
            stop_price: Stop trigger price
            limit_price: Limit price after trigger
            time_in_force: 'day', 'gtc'
        """
        self._validate_symbol(symbol)
        self._validate_order_value(qty, limit_price)

        order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
        tif = TimeInForce[time_in_force.upper()]

        request = StopLimitOrderRequest(
            symbol=symbol.upper(),
            qty=qty,
            side=order_side,
            time_in_force=tif,
            stop_price=stop_price,
            limit_price=limit_price,
        )

        order = self.client.submit_order(request)
        return self._format_order(order)

    async def get_order(self, order_id: str) -> dict[str, Any]:
        """Get order by ID."""
        order = self.client.get_order_by_id(order_id)
        return self._format_order(order)

    async def get_orders(
        self,
        status: str = "open",
        limit: int = 50,
        symbol: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Get orders with optional filters.

        Args:
            status: 'open', 'closed', 'all'
            limit: Max number of orders to return
            symbol: Filter by symbol
        """
        status_map = {
            "open": QueryOrderStatus.OPEN,
            "closed": QueryOrderStatus.CLOSED,
            "all": QueryOrderStatus.ALL,
        }

        request = GetOrdersRequest(
            status=status_map.get(status, QueryOrderStatus.OPEN),
            limit=limit,
            symbols=[symbol.upper()] if symbol else None,
        )

        orders = self.client.get_orders(request)
        return [self._format_order(order) for order in orders]

    async def cancel_order(self, order_id: str) -> dict[str, Any]:
        """Cancel an order by ID."""
        self.client.cancel_order_by_id(order_id)
        return {"status": "cancelled", "order_id": order_id}

    async def cancel_all_orders(self) -> dict[str, Any]:
        """Cancel all open orders."""
        cancel_statuses = self.client.cancel_orders()
        return {
            "cancelled_count": len(cancel_statuses),
            "statuses": [
                {"order_id": str(cs.id), "status": str(cs.status)}
                for cs in cancel_statuses
            ],
        }

    async def close_position(self, symbol: str) -> dict[str, Any]:
        """Close a position for a symbol."""
        order = self.client.close_position(symbol.upper())
        return self._format_order(order)

    async def close_all_positions(self) -> dict[str, Any]:
        """Close all open positions."""
        close_responses = self.client.close_all_positions(cancel_orders=True)
        return {
            "closed_count": len(close_responses),
            "responses": [
                {
                    "symbol": cr.symbol,
                    "status": "closed" if cr.status == 200 else "failed",
                }
                for cr in close_responses
            ],
        }

    def _format_order(self, order) -> dict[str, Any]:
        """Format order object to dict."""
        return {
            "order_id": str(order.id),
            "client_order_id": order.client_order_id,
            "symbol": order.symbol,
            "qty": float(order.qty) if order.qty else None,
            "filled_qty": float(order.filled_qty) if order.filled_qty else 0,
            "side": order.side.value if order.side else None,
            "type": order.type.value if order.type else None,
            "status": order.status.value if order.status else None,
            "limit_price": float(order.limit_price) if order.limit_price else None,
            "stop_price": float(order.stop_price) if order.stop_price else None,
            "filled_avg_price": float(order.filled_avg_price) if order.filled_avg_price else None,
            "time_in_force": order.time_in_force.value if order.time_in_force else None,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "submitted_at": order.submitted_at.isoformat() if order.submitted_at else None,
            "filled_at": order.filled_at.isoformat() if order.filled_at else None,
        }


# Singleton client instance
_client: Optional[AlpacaTradingClient] = None


def get_trading_client() -> AlpacaTradingClient:
    """Get the Alpaca trading client singleton."""
    global _client
    if _client is None:
        _client = AlpacaTradingClient()
    return _client


def reset_trading_client() -> None:
    """Reset the trading client (useful for testing)."""
    global _client
    _client = None
