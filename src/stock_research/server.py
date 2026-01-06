#!/usr/bin/env python3
"""Stock Research MCP Server - Main entry point."""

import asyncio
from contextlib import asynccontextmanager
from mcp.server import FastMCP

from stock_research.tools.market_data import register_market_data_tools
from stock_research.tools.company import register_company_tools
from stock_research.tools.analysts import register_analyst_tools
from stock_research.tools.sentiment import register_sentiment_tools
from stock_research.tools.technicals import register_technical_tools
from stock_research.tools.macro import register_macro_tools
from stock_research.services.cache import init_cache, close_cache


@asynccontextmanager
async def lifespan(app):
    """Manage server lifecycle - initialize and cleanup resources."""
    await init_cache()
    yield
    await close_cache()


# Create the MCP server using FastMCP
mcp = FastMCP("stock-research", lifespan=lifespan)


def register_all_tools():
    """Register all tool modules with the server."""
    register_market_data_tools(mcp)
    register_company_tools(mcp)
    register_analyst_tools(mcp)
    register_sentiment_tools(mcp)
    register_technical_tools(mcp)
    register_macro_tools(mcp)


# Register tools at module load time
register_all_tools()


def main():
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
