# Product Requirements Document
## Stock Research MCP Server

**Version:** 1.1
**Author:** MJ
**Date:** January 2026
**Status:** Draft (Updated for AV MCP architecture)

---

## Executive Summary

Build a Model Context Protocol (MCP) server that aggregates free-tier financial APIs to provide Claude with comprehensive stock research capabilities. The server enables professional-grade deep research reports for individual stocks, combining fundamental analysis, technical signals, sentiment data, and macro context—all within a $0-5/month budget.

---

## Problem Statement

Professional stock research requires data from multiple sources: price data, fundamentals, analyst ratings, insider activity, news sentiment, and macro indicators. Currently, accessing this data requires:

- Multiple expensive API subscriptions ($50-500+/month)
- Manual aggregation across disparate sources
- Custom code for each data provider

Home traders need institutional-quality research without institutional budgets.

---

## Solution

A unified MCP server that:

1. Uses **Alpha Vantage MCP** as the primary data source (covers 90% of needs)
2. Supplements with **Finnhub API** for analyst ratings (the one gap)
3. Exposes structured tools for Claude to call
4. Returns normalized JSON for consistent analysis
5. Enables comprehensive deep research prompts

### Why Alpha Vantage MCP?

Alpha Vantage provides an official MCP server at `mcp.alphavantage.co` that already exposes:
- Core stock data (quotes, historical prices, symbol search)
- Fundamental data (company overview, financial statements, earnings)
- Alpha Intelligence (news sentiment, insider transactions)
- Economic indicators (GDP, CPI, unemployment, treasury yields, fed funds rate)
- 50+ technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands, etc.)

This eliminates the need to build integrations for Alpaca, FRED, and raw Alpha Vantage API.

---

## User Personas

**Primary:** Professional home trader (like MJ)
- 5-15 years investing experience
- Manages $100K-1M+ portfolio
- Makes 10-50 trades/month
- Needs fundamental + technical analysis
- Budget-conscious but quality-focused

**Secondary:** AI-assisted research workflows
- Claude-based analysis pipelines
- Automated screening and alerts
- Portfolio monitoring dashboards

---

## Core Features

### Phase 1: Foundation (MVP)

#### 1.1 Company Profile Tool
```
Tool: get_company_profile
Input: { ticker: string }
Output: {
  name, sector, industry, market_cap,
  employees, description, website,
  exchange, ipo_date
}
Source: AV MCP → COMPANY_OVERVIEW
```

#### 1.2 Real-Time Quote Tool
```
Tool: get_quote
Input: { ticker: string }
Output: {
  price, change, change_percent,
  high, low, open, prev_close,
  volume, timestamp
}
Source: AV MCP → GLOBAL_QUOTE
```

#### 1.3 Historical Price Tool
```
Tool: get_historical_prices
Input: {
  ticker: string,
  timeframe: "1D" | "1W" | "1M" | "3M" | "1Y" | "5Y",
  interval: "1min" | "5min" | "1hour" | "1day"
}
Output: Array<{ date, open, high, low, close, volume }>
Source: AV MCP → TIME_SERIES_INTRADAY, TIME_SERIES_DAILY, etc.
```

#### 1.4 Analyst Ratings Tool
```
Tool: get_analyst_ratings
Input: { ticker: string }
Output: {
  consensus: "buy" | "hold" | "sell",
  buy_count, hold_count, sell_count,
  price_target_avg, price_target_high, price_target_low,
  recent_changes: Array<{ date, firm, from_rating, to_rating }>
}
Source: Finnhub API (not available in AV MCP)
```

#### 1.5 News & Sentiment Tool
```
Tool: get_news_sentiment
Input: { ticker: string, days: number }
Output: {
  articles: Array<{
    headline, source, url, datetime,
    sentiment: "positive" | "neutral" | "negative"
  }>,
  sentiment_score: number (-1 to 1),
  article_count: number
}
Source: AV MCP → NEWS_SENTIMENT
```

#### 1.6 Insider Trading Tool
```
Tool: get_insider_trades
Input: { ticker: string, months: number }
Output: {
  transactions: Array<{
    name, title, transaction_type,
    shares, price, value, date
  }>,
  net_insider_sentiment: "buying" | "selling" | "neutral",
  total_bought: number,
  total_sold: number
}
Source: AV MCP → INSIDER_TRANSACTIONS
```

#### 1.7 Earnings Tool
```
Tool: get_earnings
Input: { ticker: string }
Output: {
  next_earnings_date: string,
  recent_quarters: Array<{
    date, eps_estimate, eps_actual,
    surprise_percent, revenue_estimate, revenue_actual
  }>
}
Source: AV MCP → EARNINGS, EARNINGS_CALENDAR
```

#### 1.8 Basic Financials Tool
```
Tool: get_financials
Input: { ticker: string }
Output: {
  pe_ratio, pb_ratio, ps_ratio,
  ev_ebitda, peg_ratio,
  gross_margin, operating_margin, net_margin,
  roe, roa, roic,
  debt_to_equity, current_ratio,
  revenue_growth_yoy, earnings_growth_yoy,
  dividend_yield, payout_ratio
}
Source: AV MCP → COMPANY_OVERVIEW, INCOME_STATEMENT, BALANCE_SHEET, CASH_FLOW
```

### Phase 2: Technical Analysis

#### 2.1 Technical Indicators Tool
```
Tool: get_technical_indicators
Input: {
  ticker: string,
  indicators: Array<"sma" | "ema" | "rsi" | "macd" | "bbands">
}
Output: {
  sma_20, sma_50, sma_200,
  ema_12, ema_26,
  rsi_14,
  macd: { macd, signal, histogram },
  bbands: { upper, middle, lower },
  trend: "bullish" | "bearish" | "neutral"
}
Source: AV MCP → SMA, EMA, RSI, MACD, BBANDS (50+ indicators available)
```

#### 2.2 Support/Resistance Tool
```
Tool: get_support_resistance
Input: { ticker: string, lookback_days: number }
Output: {
  support_levels: Array<number>,
  resistance_levels: Array<number>,
  current_position: "near_support" | "near_resistance" | "mid_range"
}
Source: Calculated from AV MCP → TIME_SERIES_DAILY data
```

### Phase 3: Macro Context

#### 3.1 Macro Indicators Tool
```
Tool: get_macro_context
Input: { indicators?: Array<string> }
Output: {
  fed_funds_rate: number,
  ten_year_yield: number,
  two_year_yield: number,
  yield_curve: "normal" | "inverted" | "flat",
  gdp_growth: number,
  unemployment: number,
  cpi_yoy: number,
  vix: number
}
Source: AV MCP → FEDERAL_FUNDS_RATE, TREASURY_YIELD, REAL_GDP, UNEMPLOYMENT, CPI
Note: VIX not available in AV MCP, may need alternative source or omit
```

### Phase 4: Aggregated Research

#### 4.1 Deep Research Tool
```
Tool: generate_deep_research
Input: { 
  ticker: string,
  research_type: "comprehensive" | "quick" | "technical_only" | "fundamental_only"
}
Output: {
  company_overview: {...},
  valuation_metrics: {...},
  financial_health: {...},
  analyst_consensus: {...},
  technical_setup: {...},
  sentiment_analysis: {...},
  insider_activity: {...},
  macro_context: {...},
  catalysts_risks: {...},
  summary: {
    bull_case: string,
    bear_case: string,
    recommendation: string,
    key_levels: { support: number, resistance: number },
    next_catalyst: string
  }
}
Source: Aggregates all tools above
```

---

## API Rate Limits & Strategy

| Provider | Free Limit | Usage |
|----------|------------|-------|
| Alpha Vantage MCP | 25 calls/day (free) | Primary source for all data |
| Alpha Vantage MCP | 75+ calls/min (premium) | Consider upgrade if free tier insufficient |
| Finnhub | 60 calls/min | Analyst ratings only |

**Note:** Alpha Vantage free tier is limited. Consider:
- Premium tier ($49.99/month) for higher limits
- Aggressive caching to stay within free limits
- Batching requests where possible

**Caching Strategy:**
- Company profiles: 24-hour cache
- Financials: 24-hour cache (update on earnings)
- News: 15-minute cache
- Quotes: 1-minute cache (free tier limitation)
- Macro: 24-hour cache
- Technical indicators: 5-minute cache
- Analyst ratings: 6-hour cache

---

## Data Model

```typescript
interface ResearchReport {
  ticker: string;
  generated_at: string;
  data_freshness: {
    quote: string;
    fundamentals: string;
    news: string;
  };
  
  profile: CompanyProfile;
  quote: Quote;
  financials: Financials;
  analysts: AnalystData;
  technicals: TechnicalIndicators;
  sentiment: SentimentData;
  insiders: InsiderData;
  earnings: EarningsData;
  macro: MacroContext;
  
  synthesis: {
    bull_case: string;
    bear_case: string;
    key_metrics: KeyMetric[];
    risk_factors: string[];
    catalysts: Catalyst[];
    recommendation: Recommendation;
  };
}
```

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Claude Client                     │
└─────────────────────┬───────────────────────────────┘
                      │ MCP Protocol
┌─────────────────────▼───────────────────────────────┐
│              Stock Research MCP Server               │
├─────────────────────────────────────────────────────┤
│  Tools Layer (Our Custom Tools)                      │
│  ├── get_company_profile                            │
│  ├── get_quote                                      │
│  ├── get_historical_prices                          │
│  ├── get_analyst_ratings      ← Finnhub only        │
│  ├── get_news_sentiment                             │
│  ├── get_insider_trades                             │
│  ├── get_earnings                                   │
│  ├── get_financials                                 │
│  ├── get_technical_indicators                       │
│  ├── get_support_resistance   ← Calculated          │
│  ├── get_macro_context                              │
│  └── generate_deep_research                         │
├─────────────────────────────────────────────────────┤
│  Service Layer                                       │
│  ├── AlphaVantageMCPClient    ← Primary (90%)       │
│  ├── FinnhubService           ← Analyst ratings     │
│  └── CacheService (SQLite)                          │
├─────────────────────────────────────────────────────┤
│  Cache Layer (SQLite)                               │
│  └── Local file-based caching                       │
└─────────────────────────────────────────────────────┘
          │                           │
    ┌─────▼─────────────────┐   ┌─────▼─────┐
    │  Alpha Vantage MCP    │   │  Finnhub  │
    │  mcp.alphavantage.co  │   │    API    │
    └───────────────────────┘   └───────────┘
```

---

## File Structure

```
stock-research-mcp/
├── src/
│   ├── server.py              # MCP server entry point
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── company.py         # Profile, financials
│   │   ├── market_data.py     # Quotes, historical
│   │   ├── analysts.py        # Ratings, price targets (Finnhub)
│   │   ├── sentiment.py       # News, social sentiment
│   │   ├── insiders.py        # Insider transactions
│   │   ├── technicals.py      # Technical indicators, support/resistance
│   │   ├── macro.py           # Economic indicators
│   │   └── research.py        # Aggregated research
│   ├── services/
│   │   ├── __init__.py
│   │   ├── alpha_vantage_mcp.py  # AV MCP client wrapper
│   │   ├── finnhub.py            # Analyst ratings only
│   │   └── cache.py              # SQLite caching
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py         # Pydantic models
│   └── utils/
│       ├── __init__.py
│       └── calculations.py    # Support/resistance calcs
├── prompts/
│   └── deep_research.md       # Research prompt template
├── tests/
│   └── ...
├── config.py
├── requirements.txt
└── README.md
```

---

## Configuration

```python
# config.py
class Config:
    # API Keys (from environment)
    ALPHA_VANTAGE_API_KEY: str    # For AV MCP authentication
    FINNHUB_API_KEY: str          # For analyst ratings only

    # Alpha Vantage MCP endpoint
    AV_MCP_URL: str = "https://mcp.alphavantage.co/mcp"

    # Cache settings (aggressive due to AV free tier limits)
    CACHE_TTL_QUOTE: int = 60         # 1 min (free tier constraint)
    CACHE_TTL_NEWS: int = 900         # 15 min
    CACHE_TTL_FUNDAMENTALS: int = 86400  # 24 hours
    CACHE_TTL_PROFILE: int = 86400    # 24 hours
    CACHE_TTL_MACRO: int = 86400      # 24 hours
    CACHE_TTL_TECHNICALS: int = 300   # 5 min
    CACHE_TTL_ANALYSTS: int = 21600   # 6 hours

    # Rate limits
    FINNHUB_CALLS_PER_MIN: int = 60
    AV_CALLS_PER_DAY: int = 25        # Free tier limit
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| API cost | $0-50/month (free tier may be insufficient) |
| Research generation time | < 10 seconds |
| Data freshness (quotes) | < 1 minute (free tier) or real-time (premium) |
| Data freshness (fundamentals) | < 24 hours |
| Cache hit rate | > 80% (critical for free tier) |
| API error rate | < 1% |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| AV MCP rate limits (25/day free) | Service unusable | Aggressive caching, consider premium ($49.99/mo) |
| AV MCP server downtime | All data unavailable | Cache fallbacks, monitor status |
| AV MCP discontinued/changed | Major rework needed | Abstract service layer, keep Finnhub as backup option |
| Data quality issues | Bad analysis | Cross-validate critical metrics |
| Latency | Poor UX | Cache aggressively, async requests |
| Free tier insufficient for real use | Poor experience | Budget for premium tier from start |

---

## Timeline

| Phase | Deliverables |
|-------|--------------|
| Phase 1: MVP | AV MCP integration, core tools (profile, quote, news, insiders, earnings, financials), Finnhub for analysts |
| Phase 2: Technicals | Technical indicators via AV MCP, support/resistance calculations |
| Phase 3: Macro | Economic indicators via AV MCP |
| Phase 4: Aggregation | Deep research tool, prompt templates |
| Phase 5: Polish | Error handling, caching optimization, tests, documentation |

**Note:** Simpler architecture (2 integrations vs 4) should reduce timeline significantly.

---

## Future Enhancements

- **Options flow integration** (requires paid API)
- **Short interest data** (FINRA, bi-monthly)
- **13F institutional holdings** (SEC EDGAR parsing)
- **Earnings transcripts** (paid tier upgrade)
- **Custom alerts/screening** (webhook support)
- **Portfolio tracking** (integration with Alpaca positions)
- **Peer comparison** (industry benchmarking)

---

## Appendix: Sample Deep Research Output

```json
{
  "ticker": "NVDA",
  "generated_at": "2026-01-05T14:30:00Z",
  
  "summary": {
    "recommendation": "ACCUMULATE",
    "conviction": "HIGH",
    "bull_case": "AI infrastructure leader with 80%+ data center GPU share, expanding TAM through sovereign AI and enterprise adoption",
    "bear_case": "Elevated valuation (40x forward P/E), China export restrictions, potential custom silicon competition from hyperscalers",
    "key_levels": {
      "support": 125.00,
      "resistance": 145.00
    },
    "next_catalyst": "Q4 earnings Feb 26, 2026"
  },
  
  "valuation": {
    "pe_ratio": 45.2,
    "forward_pe": 38.5,
    "peg_ratio": 1.2,
    "ps_ratio": 28.5,
    "ev_ebitda": 42.1,
    "vs_sector_avg": "+85%",
    "vs_5yr_avg": "+45%"
  },
  
  "technicals": {
    "trend": "BULLISH",
    "rsi_14": 62,
    "above_sma_50": true,
    "above_sma_200": true,
    "macd_signal": "BULLISH_CROSSOVER"
  },
  
  "analysts": {
    "consensus": "STRONG_BUY",
    "buy": 45,
    "hold": 8,
    "sell": 2,
    "avg_price_target": 165.00,
    "upside": "+18%"
  },
  
  "sentiment": {
    "news_score": 0.72,
    "insider_activity": "NEUTRAL",
    "social_buzz": "HIGH"
  }
}
```

---

*Document version 1.1 — Last updated January 2026*
*v1.1: Simplified architecture to use Alpha Vantage MCP as primary data source*
