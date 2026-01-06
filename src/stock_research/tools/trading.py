"""Trading tools: order execution and position management via Alpaca."""

from typing import Any, Optional
from mcp.server import FastMCP

from stock_research.services.alpaca import (
    get_trading_client,
    TradingError,
    RiskLimitError,
)
from stock_research.config import config


def register_trading_tools(mcp: FastMCP) -> None:
    """Register trading tools with the MCP server."""

    @mcp.tool()
    async def get_trading_account() -> dict[str, Any]:
        """Get trading account information.

        Returns account details including:
        - Buying power and cash available
        - Portfolio value and equity
        - Account status and restrictions
        - Whether this is a paper trading account
        """
        try:
            client = get_trading_client()
            return await client.get_account()
        except TradingError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_positions() -> dict[str, Any]:
        """Get all open positions in the portfolio.

        Returns a list of positions with:
        - Symbol and quantity
        - Market value and cost basis
        - Unrealized P/L and percentage
        - Current price and average entry price
        """
        try:
            client = get_trading_client()
            positions = await client.get_positions()
            return {
                "positions": positions,
                "count": len(positions),
                "paper": client.paper,
            }
        except TradingError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_position(symbol: str) -> dict[str, Any]:
        """Get position for a specific symbol.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')

        Returns position details or null if no position exists.
        """
        try:
            client = get_trading_client()
            position = await client.get_position(symbol)
            if position:
                return {"position": position, "paper": client.paper}
            return {"position": None, "message": f"No position in {symbol.upper()}"}
        except TradingError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def place_market_order(
        symbol: str,
        qty: float,
        side: str,
        time_in_force: str = "day",
    ) -> dict[str, Any]:
        """Place a market order to buy or sell shares.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            qty: Number of shares to trade
            side: 'buy' or 'sell'
            time_in_force: Order duration - 'day', 'gtc' (good till cancelled),
                          'ioc' (immediate or cancel), 'fok' (fill or kill)

        Returns order confirmation with order ID and status.

        Note: Market orders execute at the current market price.
        Use limit orders for price control.
        """
        try:
            client = get_trading_client()
            order = await client.place_market_order(symbol, qty, side, time_in_force)
            return {
                "order": order,
                "paper": client.paper,
                "warning": "PAPER TRADING" if client.paper else "LIVE TRADING",
            }
        except RiskLimitError as e:
            return {"error": str(e), "type": "risk_limit"}
        except TradingError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def place_limit_order(
        symbol: str,
        qty: float,
        side: str,
        limit_price: float,
        time_in_force: str = "day",
    ) -> dict[str, Any]:
        """Place a limit order at a specified price.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            qty: Number of shares to trade
            side: 'buy' or 'sell'
            limit_price: Maximum price (buy) or minimum price (sell)
            time_in_force: 'day', 'gtc', 'ioc', 'fok'

        Returns order confirmation. Order will only fill at limit_price or better.
        """
        try:
            client = get_trading_client()
            order = await client.place_limit_order(
                symbol, qty, side, limit_price, time_in_force
            )
            return {
                "order": order,
                "paper": client.paper,
                "warning": "PAPER TRADING" if client.paper else "LIVE TRADING",
            }
        except RiskLimitError as e:
            return {"error": str(e), "type": "risk_limit"}
        except TradingError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def place_stop_order(
        symbol: str,
        qty: float,
        side: str,
        stop_price: float,
        time_in_force: str = "day",
    ) -> dict[str, Any]:
        """Place a stop order that triggers at a specified price.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            qty: Number of shares to trade
            side: 'buy' or 'sell'
            stop_price: Price at which the order becomes a market order
            time_in_force: 'day' or 'gtc'

        Useful for stop-loss orders to limit downside risk.
        """
        try:
            client = get_trading_client()
            order = await client.place_stop_order(
                symbol, qty, side, stop_price, time_in_force
            )
            return {
                "order": order,
                "paper": client.paper,
                "warning": "PAPER TRADING" if client.paper else "LIVE TRADING",
            }
        except RiskLimitError as e:
            return {"error": str(e), "type": "risk_limit"}
        except TradingError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def place_stop_limit_order(
        symbol: str,
        qty: float,
        side: str,
        stop_price: float,
        limit_price: float,
        time_in_force: str = "day",
    ) -> dict[str, Any]:
        """Place a stop-limit order combining stop and limit orders.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            qty: Number of shares to trade
            side: 'buy' or 'sell'
            stop_price: Price at which the limit order is triggered
            limit_price: Limit price for the triggered order
            time_in_force: 'day' or 'gtc'

        When stop_price is reached, a limit order at limit_price is placed.
        """
        try:
            client = get_trading_client()
            order = await client.place_stop_limit_order(
                symbol, qty, side, stop_price, limit_price, time_in_force
            )
            return {
                "order": order,
                "paper": client.paper,
                "warning": "PAPER TRADING" if client.paper else "LIVE TRADING",
            }
        except RiskLimitError as e:
            return {"error": str(e), "type": "risk_limit"}
        except TradingError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_order(order_id: str) -> dict[str, Any]:
        """Get details of a specific order by ID.

        Args:
            order_id: The order ID returned when placing an order

        Returns order status, fill details, and timestamps.
        """
        try:
            client = get_trading_client()
            order = await client.get_order(order_id)
            return {"order": order, "paper": client.paper}
        except TradingError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_orders(
        status: str = "open",
        limit: int = 50,
        symbol: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get a list of orders with optional filters.

        Args:
            status: Filter by status - 'open', 'closed', or 'all'
            limit: Maximum number of orders to return (default 50)
            symbol: Filter by stock symbol (optional)

        Returns list of orders matching the criteria.
        """
        try:
            client = get_trading_client()
            orders = await client.get_orders(status, limit, symbol)
            return {
                "orders": orders,
                "count": len(orders),
                "paper": client.paper,
            }
        except TradingError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def cancel_order(order_id: str) -> dict[str, Any]:
        """Cancel an open order.

        Args:
            order_id: The order ID to cancel

        Returns confirmation of cancellation.
        """
        try:
            client = get_trading_client()
            result = await client.cancel_order(order_id)
            return {**result, "paper": client.paper}
        except TradingError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def cancel_all_orders() -> dict[str, Any]:
        """Cancel all open orders.

        Use with caution - this will cancel ALL pending orders.

        Returns count of cancelled orders.
        """
        try:
            client = get_trading_client()
            result = await client.cancel_all_orders()
            return {
                **result,
                "paper": client.paper,
                "warning": "All open orders have been cancelled",
            }
        except TradingError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def close_position(symbol: str) -> dict[str, Any]:
        """Close an entire position for a symbol.

        Args:
            symbol: Stock symbol to close position for

        Places a market order to sell (for long) or buy (for short)
        all shares of the position.
        """
        try:
            client = get_trading_client()
            order = await client.close_position(symbol)
            return {
                "order": order,
                "paper": client.paper,
                "warning": "PAPER TRADING" if client.paper else "LIVE TRADING",
            }
        except TradingError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def close_all_positions() -> dict[str, Any]:
        """Close all open positions.

        Use with extreme caution - this will liquidate your entire portfolio.
        Also cancels all open orders.

        Returns count of positions closed.
        """
        try:
            client = get_trading_client()
            result = await client.close_all_positions()
            return {
                **result,
                "paper": client.paper,
                "warning": "ALL POSITIONS CLOSED - " + (
                    "PAPER TRADING" if client.paper else "LIVE TRADING"
                ),
            }
        except TradingError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_trading_config() -> dict[str, Any]:
        """Get current trading configuration and risk limits.

        Returns:
        - Whether paper trading is enabled
        - Maximum position size allowed
        - Maximum single order value
        - List of allowed symbols (if restricted)
        """
        return {
            "paper_trading": config.ALPACA_PAPER,
            "max_position_size": config.TRADING_MAX_POSITION_SIZE,
            "max_order_value": config.TRADING_MAX_ORDER_VALUE,
            "allowed_symbols": config.TRADING_ALLOWED_SYMBOLS or "all symbols allowed",
            "api_configured": bool(config.ALPACA_API_KEY and config.ALPACA_SECRET_KEY),
        }
