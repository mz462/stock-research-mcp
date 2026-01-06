"""Sentiment tools: news sentiment and insider trading."""

from typing import Any
from mcp.server import FastMCP

from stock_research.services.alpha_vantage_mcp import get_av_client
from stock_research.services.cache import get_or_fetch
from stock_research.config import config


def register_sentiment_tools(mcp: FastMCP) -> None:
    """Register sentiment tools with the MCP server."""

    @mcp.tool()
    async def get_news_sentiment(ticker: str, limit: int = 20) -> dict[str, Any]:
        """Get news articles and sentiment analysis for a stock.

        Args:
            ticker: Stock symbol (e.g., 'AAPL', 'MSFT')
            limit: Maximum number of articles to return (default 20)

        Returns:
            News articles with sentiment scores and overall sentiment summary.
        """
        cache_key = f"news:{ticker.upper()}:{limit}"

        async def fetch():
            client = get_av_client()
            raw = await client.get_news_sentiment(ticker.upper(), limit)

            feed = raw.get("feed", [])
            articles = []
            sentiment_scores = []

            for article in feed[:limit]:
                # Find ticker-specific sentiment
                ticker_sentiment = None
                for ts in article.get("ticker_sentiment", []):
                    if ts.get("ticker", "").upper() == ticker.upper():
                        ticker_sentiment = ts
                        break

                score = float(ticker_sentiment.get("ticker_sentiment_score", 0)) if ticker_sentiment else 0
                sentiment_scores.append(score)

                # Categorize sentiment
                if score > 0.25:
                    sentiment_label = "positive"
                elif score < -0.25:
                    sentiment_label = "negative"
                else:
                    sentiment_label = "neutral"

                articles.append({
                    "title": article.get("title", ""),
                    "source": article.get("source", ""),
                    "url": article.get("url", ""),
                    "published": article.get("time_published", ""),
                    "summary": article.get("summary", "")[:500],  # Truncate long summaries
                    "sentiment": sentiment_label,
                    "sentiment_score": score,
                    "relevance": float(ticker_sentiment.get("relevance_score", 0)) if ticker_sentiment else 0,
                })

            # Calculate overall sentiment
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0

            if avg_sentiment > 0.15:
                overall = "bullish"
            elif avg_sentiment < -0.15:
                overall = "bearish"
            else:
                overall = "neutral"

            positive_count = sum(1 for s in sentiment_scores if s > 0.25)
            negative_count = sum(1 for s in sentiment_scores if s < -0.25)
            neutral_count = len(sentiment_scores) - positive_count - negative_count

            return {
                "ticker": ticker.upper(),
                "overall_sentiment": overall,
                "average_score": round(avg_sentiment, 3),
                "article_count": len(articles),
                "positive_count": positive_count,
                "neutral_count": neutral_count,
                "negative_count": negative_count,
                "articles": articles,
            }

        return await get_or_fetch(cache_key, config.CACHE_TTL_NEWS, fetch)

    @mcp.tool()
    async def get_insider_trades(ticker: str) -> dict[str, Any]:
        """Get insider trading activity for a stock.

        Args:
            ticker: Stock symbol (e.g., 'AAPL', 'MSFT')

        Returns:
            Recent insider transactions and overall insider sentiment.
        """
        cache_key = f"insiders:{ticker.upper()}"

        async def fetch():
            client = get_av_client()
            raw = await client.get_insider_transactions(ticker.upper())

            transactions_raw = raw.get("data", [])
            transactions = []
            total_bought = 0
            total_sold = 0

            def safe_float(val):
                """Convert value handling 'None' strings and empty values."""
                if val is None or val == "" or val == "None":
                    return None
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return None

            def safe_int(val):
                """Convert value to int handling floats and strings."""
                if val is None or val == "" or val == "None":
                    return 0
                try:
                    return int(float(val))
                except (ValueError, TypeError):
                    return 0

            for t in transactions_raw[:50]:  # Last 50 transactions
                shares = safe_int(t.get("shares"))
                acquisition = t.get("acquisition_or_disposition", "")

                if acquisition == "A":  # Acquisition
                    total_bought += shares
                elif acquisition == "D":  # Disposition
                    total_sold += shares

                # Try multiple possible field names for executive info
                name = t.get("executive_name") or t.get("ownerName") or t.get("name") or ""
                title = t.get("executive_title") or t.get("ownerTitle") or t.get("title") or ""

                transactions.append({
                    "name": name,
                    "title": title,
                    "transaction_date": t.get("transaction_date") or t.get("transactionDate") or "",
                    "transaction_type": "buy" if acquisition == "A" else "sell",
                    "shares": shares,
                    "value": safe_float(t.get("value")),
                    "security_type": t.get("security_type") or t.get("securityType") or "",
                })

            # Determine insider sentiment
            net = total_bought - total_sold
            if net > 0:
                sentiment = "buying"
            elif net < 0:
                sentiment = "selling"
            else:
                sentiment = "neutral"

            return {
                "ticker": ticker.upper(),
                "net_insider_sentiment": sentiment,
                "total_bought": total_bought,
                "total_sold": total_sold,
                "net_shares": net,
                "transaction_count": len(transactions),
                "transactions": transactions[:20],  # Return top 20
            }

        return await get_or_fetch(cache_key, config.CACHE_TTL_NEWS, fetch)
