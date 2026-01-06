"""Analyst tools: ratings, price targets, upgrades/downgrades.

This is the only tool that uses Finnhub instead of Alpha Vantage.
"""

from typing import Any
from mcp.server import FastMCP

from stock_research.services.finnhub import get_finnhub_client
from stock_research.services.cache import get_or_fetch
from stock_research.config import config


def register_analyst_tools(mcp: FastMCP) -> None:
    """Register analyst tools with the MCP server."""

    @mcp.tool()
    async def get_analyst_ratings(ticker: str) -> dict[str, Any]:
        """Get analyst ratings and price targets for a stock.

        Args:
            ticker: Stock symbol (e.g., 'AAPL', 'MSFT')

        Returns:
            Analyst consensus, rating counts, and price targets.
        """
        cache_key = f"analysts:{ticker.upper()}"

        async def fetch():
            client = get_finnhub_client()

            # Get recommendations (always works on free tier)
            try:
                recommendations = await client.get_analyst_recommendations(ticker.upper())
            except Exception:
                recommendations = []

            # Price targets require premium - gracefully handle 403
            try:
                price_target = await client.get_price_target(ticker.upper())
            except Exception:
                price_target = {}

            # Upgrades/downgrades
            try:
                upgrades = await client.get_upgrades_downgrades(ticker.upper())
            except Exception:
                upgrades = []

            # Get latest recommendation counts
            latest = recommendations[0] if recommendations else {}

            buy_count = latest.get("buy", 0) + latest.get("strongBuy", 0)
            hold_count = latest.get("hold", 0)
            sell_count = latest.get("sell", 0) + latest.get("strongSell", 0)
            total = buy_count + hold_count + sell_count

            # Determine consensus
            if total > 0:
                if buy_count / total > 0.6:
                    consensus = "strong_buy"
                elif buy_count / total > 0.4:
                    consensus = "buy"
                elif sell_count / total > 0.4:
                    consensus = "sell"
                elif sell_count / total > 0.6:
                    consensus = "strong_sell"
                else:
                    consensus = "hold"
            else:
                consensus = "no_data"

            # Format recent changes
            recent_changes = []
            for change in upgrades[:10]:
                recent_changes.append({
                    "date": change.get("gradeTime", "")[:10] if change.get("gradeTime") else "",
                    "firm": change.get("company", ""),
                    "action": change.get("action", ""),
                    "from_rating": change.get("fromGrade", ""),
                    "to_rating": change.get("toGrade", ""),
                })

            return {
                "ticker": ticker.upper(),
                "consensus": consensus,
                "buy_count": buy_count,
                "hold_count": hold_count,
                "sell_count": sell_count,
                "total_analysts": total,
                "strong_buy": latest.get("strongBuy", 0),
                "strong_sell": latest.get("strongSell", 0),
                "price_target_avg": price_target.get("targetMean"),
                "price_target_high": price_target.get("targetHigh"),
                "price_target_low": price_target.get("targetLow"),
                "price_target_median": price_target.get("targetMedian"),
                "recent_changes": recent_changes,
            }

        return await get_or_fetch(cache_key, config.CACHE_TTL_ANALYSTS, fetch)
