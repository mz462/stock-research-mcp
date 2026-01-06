"""Company tools: profile and financials."""

from typing import Any
from mcp.server import FastMCP

from stock_research.services.alpha_vantage_mcp import get_av_client
from stock_research.services.cache import get_or_fetch
from stock_research.config import config


def register_company_tools(mcp: FastMCP) -> None:
    """Register company tools with the MCP server."""

    @mcp.tool()
    async def get_company_profile(ticker: str) -> dict[str, Any]:
        """Get company profile and overview.

        Args:
            ticker: Stock symbol (e.g., 'AAPL', 'MSFT')

        Returns:
            Company profile including name, sector, industry, description, etc.
        """
        cache_key = f"profile:{ticker.upper()}"

        async def fetch():
            client = get_av_client()
            raw = await client.get_company_overview(ticker.upper())

            return {
                "ticker": ticker.upper(),
                "name": raw.get("Name", ""),
                "description": raw.get("Description", ""),
                "sector": raw.get("Sector", ""),
                "industry": raw.get("Industry", ""),
                "exchange": raw.get("Exchange", ""),
                "market_cap": int(raw.get("MarketCapitalization", 0)),
                "employees": int(raw.get("FullTimeEmployees", 0)) if raw.get("FullTimeEmployees") else None,
                "website": raw.get("OfficialSite", ""),
                "ipo_date": raw.get("IPODate", ""),
                "country": raw.get("Country", ""),
                "currency": raw.get("Currency", ""),
            }

        return await get_or_fetch(cache_key, config.CACHE_TTL_PROFILE, fetch)

    @mcp.tool()
    async def get_financials(ticker: str) -> dict[str, Any]:
        """Get key financial metrics and ratios.

        Args:
            ticker: Stock symbol (e.g., 'AAPL', 'MSFT')

        Returns:
            Financial metrics including valuation ratios, margins, growth rates.
        """
        cache_key = f"financials:{ticker.upper()}"

        async def fetch():
            client = get_av_client()
            overview = await client.get_company_overview(ticker.upper())

            def safe_float(val, default=None):
                try:
                    return float(val) if val and val != "None" else default
                except (ValueError, TypeError):
                    return default

            # Calculate gross margin as percentage
            gross_profit = safe_float(overview.get("GrossProfitTTM"))
            revenue = safe_float(overview.get("RevenueTTM"))
            gross_margin = None
            if gross_profit and revenue and revenue > 0:
                gross_margin = round(gross_profit / revenue, 4)  # As decimal (e.g., 0.75 for 75%)

            return {
                "ticker": ticker.upper(),
                # Valuation
                "pe_ratio": safe_float(overview.get("PERatio")),
                "forward_pe": safe_float(overview.get("ForwardPE")),
                "peg_ratio": safe_float(overview.get("PEGRatio")),
                "pb_ratio": safe_float(overview.get("PriceToBookRatio")),
                "ps_ratio": safe_float(overview.get("PriceToSalesRatioTTM")),
                "ev_ebitda": safe_float(overview.get("EVToEBITDA")),
                "ev_revenue": safe_float(overview.get("EVToRevenue")),
                # Profitability
                "gross_margin": gross_margin,
                "operating_margin": safe_float(overview.get("OperatingMarginTTM")),
                "profit_margin": safe_float(overview.get("ProfitMargin")),
                "roe": safe_float(overview.get("ReturnOnEquityTTM")),
                "roa": safe_float(overview.get("ReturnOnAssetsTTM")),
                # Growth
                "revenue_growth_yoy": safe_float(overview.get("QuarterlyRevenueGrowthYOY")),
                "earnings_growth_yoy": safe_float(overview.get("QuarterlyEarningsGrowthYOY")),
                # Dividend
                "dividend_yield": safe_float(overview.get("DividendYield")),
                "dividend_per_share": safe_float(overview.get("DividendPerShare")),
                "payout_ratio": safe_float(overview.get("PayoutRatio")),
                # Balance Sheet
                "beta": safe_float(overview.get("Beta")),
                "52_week_high": safe_float(overview.get("52WeekHigh")),
                "52_week_low": safe_float(overview.get("52WeekLow")),
                "50_day_ma": safe_float(overview.get("50DayMovingAverage")),
                "200_day_ma": safe_float(overview.get("200DayMovingAverage")),
                "shares_outstanding": safe_float(overview.get("SharesOutstanding")),
                # EPS
                "eps": safe_float(overview.get("EPS")),
                "book_value": safe_float(overview.get("BookValue")),
            }

        return await get_or_fetch(cache_key, config.CACHE_TTL_FUNDAMENTALS, fetch)

    @mcp.tool()
    async def get_earnings(ticker: str) -> dict[str, Any]:
        """Get earnings history and upcoming earnings date.

        Args:
            ticker: Stock symbol (e.g., 'AAPL', 'MSFT')

        Returns:
            Earnings data including quarterly history and surprises.
        """
        cache_key = f"earnings:{ticker.upper()}"

        async def fetch():
            client = get_av_client()
            raw = await client.get_earnings(ticker.upper())

            quarterly = raw.get("quarterlyEarnings", [])
            annual = raw.get("annualEarnings", [])

            def safe_eps(val):
                """Convert EPS value, handling 'None' strings."""
                if val is None or val == "" or val == "None":
                    return None
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return None

            # Process quarterly earnings
            recent_quarters = []
            for q in quarterly[:8]:  # Last 8 quarters
                reported = safe_eps(q.get("reportedEPS"))
                estimated = safe_eps(q.get("estimatedEPS"))
                surprise = None
                surprise_pct = None

                if reported is not None and estimated is not None and estimated != 0:
                    surprise = round(reported - estimated, 4)
                    surprise_pct = round((surprise / abs(estimated)) * 100, 2)

                recent_quarters.append({
                    "fiscal_date": q.get("fiscalDateEnding", ""),
                    "reported_date": q.get("reportedDate", ""),
                    "eps_estimate": estimated,
                    "eps_actual": reported,
                    "surprise": surprise,
                    "surprise_percent": surprise_pct,
                })

            return {
                "ticker": ticker.upper(),
                "recent_quarters": recent_quarters,
                "annual_earnings": [
                    {
                        "fiscal_year": a.get("fiscalDateEnding", "")[:4] if a.get("fiscalDateEnding") else "",
                        "eps": safe_eps(a.get("reportedEPS")),
                    }
                    for a in annual[:5]
                ],
            }

        return await get_or_fetch(cache_key, config.CACHE_TTL_FUNDAMENTALS, fetch)
