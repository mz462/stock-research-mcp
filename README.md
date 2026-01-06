# Stock Research MCP Server

An MCP (Model Context Protocol) server that provides comprehensive stock research tools for Claude. Aggregates data from Alpha Vantage and Finnhub APIs.

## Features

- **Real-time quotes** and historical price data
- **Company profiles** and fundamental analysis
- **Technical indicators** (SMA, EMA, RSI, MACD, Bollinger Bands)
- **Support/resistance** level calculations
- **Analyst ratings** and price targets
- **News sentiment** analysis
- **Insider trading** activity
- **Macro economic** indicators
- **Deep research** reports combining all data sources

## Installation

1. Clone the repository:
```bash
cd stock-research-mcp
```

2. Create a virtual environment and install the package:
```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

3. Configure API keys in `.env`:
```
ALPHA_VANTAGE_API_KEY=your_key_here
FINNHUB_API_KEY=your_key_here
```

Get free API keys at:
- Alpha Vantage: https://www.alphavantage.co/support/#api-key
- Finnhub: https://finnhub.io/register

## Usage with Claude Code

Add to your Claude Code MCP configuration:

```bash
claude mcp add stock-research -- .venv/bin/python -m stock_research.server
```

Or use the installed script:

```bash
claude mcp add stock-research -- .venv/bin/stock-research-mcp
```

Or manually add to `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "stock-research": {
      "command": "/path/to/stock-research-mcp/.venv/bin/stock-research-mcp"
    }
  }
}
```

## Available Tools

### Market Data
- `get_quote(ticker)` - Real-time quote
- `get_historical_prices(ticker, timeframe, interval)` - Historical OHLCV data

### Company Analysis
- `get_company_profile(ticker)` - Company overview
- `get_financials(ticker)` - Key financial metrics and ratios
- `get_earnings(ticker)` - Earnings history and surprises

### Technical Analysis
- `get_technical_indicators(ticker, indicators)` - SMA, EMA, RSI, MACD, BBands
- `get_support_resistance(ticker, lookback_days)` - Support/resistance levels

### Sentiment & Activity
- `get_news_sentiment(ticker, limit)` - News articles with sentiment
- `get_insider_trades(ticker)` - Insider buying/selling
- `get_analyst_ratings(ticker)` - Analyst consensus and price targets

### Macro
- `get_macro_context()` - Economic indicators (Fed rate, yields, GDP, CPI)

### Research
- `generate_deep_research(ticker, research_type)` - Comprehensive research report

## Development

Run tests:
```bash
pytest
```

## Example Usage

Once configured, ask Claude:

```
"Give me a deep research report on NVDA"
"What's the current price and technical setup for AAPL?"
"Show me analyst ratings for MSFT"
"What's the macro environment looking like?"
```

## Rate Limits

- **Alpha Vantage Free Tier**: 25 API calls/day
- **Finnhub Free Tier**: 60 API calls/minute

The server uses aggressive caching to stay within free tier limits.

## License

MIT
