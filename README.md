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
- **Trading execution** via Alpaca (paper and live trading)

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

# Alpaca Trading (optional)
ALPACA_API_KEY=your_key_here
ALPACA_SECRET_KEY=your_secret_here
ALPACA_PAPER=true  # Set to false for live trading

# Risk Controls (optional)
TRADING_MAX_ORDER_VALUE=5000
TRADING_MAX_POSITION_SIZE=10000
TRADING_ALLOWED_SYMBOLS=AAPL,MSFT,GOOGL  # Leave empty for all symbols
```

Get free API keys at:
- Alpha Vantage: https://www.alphavantage.co/support/#api-key
- Finnhub: https://finnhub.io/register
- Alpaca: https://alpaca.markets/ (free paper trading account)

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

### Trading (Alpaca)
- `get_trading_account()` - Account info, buying power, equity
- `get_positions()` - All open positions
- `get_position(symbol)` - Position for specific symbol
- `place_market_order(symbol, qty, side)` - Market order
- `place_limit_order(symbol, qty, side, limit_price)` - Limit order
- `place_stop_order(symbol, qty, side, stop_price)` - Stop order
- `place_stop_limit_order(symbol, qty, side, stop_price, limit_price)` - Stop-limit order
- `get_orders(status)` - List orders (open/closed/all)
- `cancel_order(order_id)` - Cancel specific order
- `cancel_all_orders()` - Cancel all open orders
- `close_position(symbol)` - Close position for symbol
- `close_all_positions()` - Liquidate all positions
- `get_trading_config()` - View current risk limits

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

### Trading Examples

```
"Show me my current positions"
"Buy 10 shares of AAPL at market"
"Place a limit order for 5 shares of MSFT at $400"
"Set a stop loss on my NVDA position at $120"
"What's my account buying power?"
```

> ⚠️ **Warning**: Trading involves real money. Start with paper trading (`ALPACA_PAPER=true`) to test your strategies. The server includes risk controls but you are responsible for your trades.

## Rate Limits

- **Alpha Vantage Free Tier**: 25 API calls/day
- **Finnhub Free Tier**: 60 API calls/minute

The server uses aggressive caching to stay within free tier limits.

## License

MIT
