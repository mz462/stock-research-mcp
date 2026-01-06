"""Macro economic indicators tool."""

from typing import Any
from mcp.server import FastMCP

from stock_research.services.alpha_vantage_mcp import get_av_client
from stock_research.services.cache import get_or_fetch
from stock_research.config import config


def register_macro_tools(mcp: FastMCP) -> None:
    """Register macro economic tools with the MCP server."""

    @mcp.tool()
    async def get_macro_context() -> dict[str, Any]:
        """Get current macroeconomic indicators and context.

        Returns:
            Key economic indicators including Fed funds rate, treasury yields,
            GDP growth, unemployment, and inflation (CPI).
        """
        cache_key = "macro:context"

        async def fetch():
            client = get_av_client()
            result = {}

            # Federal Funds Rate
            try:
                fed_data = await client.get_federal_funds_rate()
                fed_series = fed_data.get("data", [])
                if fed_series:
                    result["fed_funds_rate"] = float(fed_series[0].get("value", 0))
                    result["fed_funds_date"] = fed_series[0].get("date", "")
            except Exception as e:
                result["fed_funds_rate_error"] = str(e)

            # Treasury Yields
            try:
                ten_year = await client.get_treasury_yield("10year")
                two_year = await client.get_treasury_yield("2year")

                ten_series = ten_year.get("data", [])
                two_series = two_year.get("data", [])

                if ten_series:
                    result["ten_year_yield"] = float(ten_series[0].get("value", 0))
                if two_series:
                    result["two_year_yield"] = float(two_series[0].get("value", 0))

                # Calculate yield curve
                if result.get("ten_year_yield") and result.get("two_year_yield"):
                    spread = result["ten_year_yield"] - result["two_year_yield"]
                    result["yield_spread"] = round(spread, 2)
                    if spread < 0:
                        result["yield_curve"] = "inverted"
                    elif spread < 0.25:
                        result["yield_curve"] = "flat"
                    else:
                        result["yield_curve"] = "normal"
            except Exception as e:
                result["treasury_error"] = str(e)

            # GDP
            try:
                gdp_data = await client.get_real_gdp()
                gdp_series = gdp_data.get("data", [])
                if len(gdp_series) >= 2:
                    current_gdp = float(gdp_series[0].get("value", 0))
                    prev_gdp = float(gdp_series[1].get("value", 0))
                    if prev_gdp > 0:
                        gdp_growth = ((current_gdp - prev_gdp) / prev_gdp) * 100
                        result["gdp_growth_qoq"] = round(gdp_growth, 2)
                    result["gdp_latest"] = current_gdp
                    result["gdp_date"] = gdp_series[0].get("date", "")
            except Exception as e:
                result["gdp_error"] = str(e)

            # Unemployment
            try:
                unemp_data = await client.get_unemployment()
                unemp_series = unemp_data.get("data", [])
                if unemp_series:
                    result["unemployment_rate"] = float(unemp_series[0].get("value", 0))
                    result["unemployment_date"] = unemp_series[0].get("date", "")
            except Exception as e:
                result["unemployment_error"] = str(e)

            # CPI / Inflation
            try:
                cpi_data = await client.get_cpi()
                cpi_series = cpi_data.get("data", [])
                if len(cpi_series) >= 13:  # Need 12 months for YoY
                    current_cpi = float(cpi_series[0].get("value", 0))
                    year_ago_cpi = float(cpi_series[12].get("value", 0))
                    if year_ago_cpi > 0:
                        inflation_yoy = ((current_cpi - year_ago_cpi) / year_ago_cpi) * 100
                        result["cpi_yoy"] = round(inflation_yoy, 2)
                    result["cpi_latest"] = current_cpi
                    result["cpi_date"] = cpi_series[0].get("date", "")
            except Exception as e:
                result["cpi_error"] = str(e)

            # Market environment assessment
            result["environment"] = _assess_market_environment(result)

            return result

        return await get_or_fetch(cache_key, config.CACHE_TTL_MACRO, fetch)


def _assess_market_environment(data: dict) -> dict[str, Any]:
    """Assess overall market environment from macro indicators."""
    signals = []
    notes = []

    # Fed funds rate assessment
    fed_rate = data.get("fed_funds_rate", 0)
    if fed_rate > 5:
        signals.append(-1)
        notes.append("High interest rates (restrictive)")
    elif fed_rate < 2:
        signals.append(1)
        notes.append("Low interest rates (accommodative)")
    else:
        signals.append(0)
        notes.append("Moderate interest rates")

    # Yield curve
    yield_curve = data.get("yield_curve", "")
    if yield_curve == "inverted":
        signals.append(-1)
        notes.append("Inverted yield curve (recession signal)")
    elif yield_curve == "normal":
        signals.append(1)
        notes.append("Normal yield curve")

    # Unemployment
    unemp = data.get("unemployment_rate", 0)
    if unemp < 4:
        signals.append(1)
        notes.append("Low unemployment")
    elif unemp > 6:
        signals.append(-1)
        notes.append("High unemployment")

    # Inflation
    cpi_yoy = data.get("cpi_yoy", 0)
    if cpi_yoy > 4:
        signals.append(-1)
        notes.append(f"High inflation ({cpi_yoy:.1f}%)")
    elif cpi_yoy < 2:
        signals.append(0)
        notes.append("Low inflation")
    else:
        signals.append(1)
        notes.append("Moderate inflation")

    # Overall assessment
    avg_signal = sum(signals) / len(signals) if signals else 0

    if avg_signal > 0.3:
        outlook = "favorable"
    elif avg_signal < -0.3:
        outlook = "challenging"
    else:
        outlook = "mixed"

    return {
        "outlook": outlook,
        "signal_score": round(avg_signal, 2),
        "notes": notes,
    }
