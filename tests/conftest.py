"""Test fixtures and configuration."""

import pytest
import os
import tempfile

# Set test environment before importing modules
os.environ["ALPHA_VANTAGE_API_KEY"] = "test_av_key"
os.environ["FINNHUB_API_KEY"] = "test_finnhub_key"


@pytest.fixture
def av_quote_response():
    """Sample Alpha Vantage quote response."""
    return {
        "Global Quote": {
            "01. symbol": "AAPL",
            "02. open": "150.00",
            "03. high": "152.00",
            "04. low": "149.00",
            "05. price": "151.50",
            "06. volume": "50000000",
            "07. latest trading day": "2026-01-03",
            "08. previous close": "149.50",
            "09. change": "2.00",
            "10. change percent": "1.34%",
        }
    }


@pytest.fixture
def av_daily_response():
    """Sample Alpha Vantage daily time series response."""
    return {
        "Meta Data": {
            "1. Information": "Daily Prices",
            "2. Symbol": "AAPL",
        },
        "Time Series (Daily)": {
            "2026-01-03": {
                "1. open": "150.00",
                "2. high": "152.00",
                "3. low": "149.00",
                "4. close": "151.50",
                "5. volume": "50000000",
            },
            "2026-01-02": {
                "1. open": "148.00",
                "2. high": "150.00",
                "3. low": "147.00",
                "4. close": "149.50",
                "5. volume": "45000000",
            },
            "2025-12-31": {
                "1. open": "147.00",
                "2. high": "149.00",
                "3. low": "146.00",
                "4. close": "148.00",
                "5. volume": "40000000",
            },
        },
    }


@pytest.fixture
def av_company_overview_response():
    """Sample Alpha Vantage company overview response."""
    return {
        "Symbol": "AAPL",
        "Name": "Apple Inc",
        "Description": "Apple Inc. designs, manufactures, and markets smartphones...",
        "Exchange": "NASDAQ",
        "Sector": "Technology",
        "Industry": "Consumer Electronics",
        "MarketCapitalization": "3000000000000",
        "PERatio": "28.5",
        "ForwardPE": "25.0",
        "PEGRatio": "1.5",
        "PriceToBookRatio": "45.0",
        "EVToEBITDA": "22.0",
        "ProfitMargin": "0.25",
        "ReturnOnEquityTTM": "0.45",
        "QuarterlyRevenueGrowthYOY": "0.08",
        "QuarterlyEarningsGrowthYOY": "0.12",
        "DividendYield": "0.005",
        "Beta": "1.2",
        "52WeekHigh": "200.00",
        "52WeekLow": "120.00",
        "50DayMovingAverage": "155.00",
        "200DayMovingAverage": "150.00",
        "FullTimeEmployees": "150000",
        "IPODate": "1980-12-12",
        "Country": "USA",
        "Currency": "USD",
    }


@pytest.fixture
def av_earnings_response():
    """Sample Alpha Vantage earnings response."""
    return {
        "symbol": "AAPL",
        "annualEarnings": [
            {"fiscalDateEnding": "2025-09-30", "reportedEPS": "6.50"},
            {"fiscalDateEnding": "2024-09-30", "reportedEPS": "6.00"},
        ],
        "quarterlyEarnings": [
            {
                "fiscalDateEnding": "2025-12-31",
                "reportedDate": "2026-01-25",
                "reportedEPS": "2.10",
                "estimatedEPS": "2.05",
            },
            {
                "fiscalDateEnding": "2025-09-30",
                "reportedDate": "2025-10-25",
                "reportedEPS": "1.95",
                "estimatedEPS": "1.90",
            },
        ],
    }


@pytest.fixture
def av_news_sentiment_response():
    """Sample Alpha Vantage news sentiment response."""
    return {
        "feed": [
            {
                "title": "Apple Reports Strong Q4 Results",
                "url": "https://example.com/article1",
                "source": "Financial Times",
                "time_published": "20260103T120000",
                "summary": "Apple exceeded expectations...",
                "ticker_sentiment": [
                    {
                        "ticker": "AAPL",
                        "relevance_score": "0.95",
                        "ticker_sentiment_score": "0.35",
                        "ticker_sentiment_label": "Bullish",
                    }
                ],
            },
            {
                "title": "Tech Stocks Rally",
                "url": "https://example.com/article2",
                "source": "Reuters",
                "time_published": "20260103T100000",
                "summary": "Technology sector sees gains...",
                "ticker_sentiment": [
                    {
                        "ticker": "AAPL",
                        "relevance_score": "0.80",
                        "ticker_sentiment_score": "0.15",
                        "ticker_sentiment_label": "Neutral",
                    }
                ],
            },
        ]
    }


@pytest.fixture
def av_insider_response():
    """Sample Alpha Vantage insider transactions response."""
    return {
        "data": [
            {
                "executive_name": "Tim Cook",
                "executive_title": "CEO",
                "transaction_date": "2026-01-02",
                "acquisition_or_disposition": "D",
                "shares": "50000",
                "value": "7500000",
                "security_type": "Common Stock",
            },
            {
                "executive_name": "Luca Maestri",
                "executive_title": "CFO",
                "transaction_date": "2025-12-15",
                "acquisition_or_disposition": "A",
                "shares": "10000",
                "value": "1500000",
                "security_type": "Common Stock",
            },
        ]
    }


@pytest.fixture
def av_rsi_response():
    """Sample Alpha Vantage RSI response."""
    return {
        "Technical Analysis: RSI": {
            "2026-01-03": {"RSI": "55.5"},
            "2026-01-02": {"RSI": "52.3"},
        }
    }


@pytest.fixture
def av_macd_response():
    """Sample Alpha Vantage MACD response."""
    return {
        "Technical Analysis: MACD": {
            "2026-01-03": {
                "MACD": "2.5",
                "MACD_Signal": "2.0",
                "MACD_Hist": "0.5",
            },
            "2026-01-02": {
                "MACD": "2.0",
                "MACD_Signal": "2.1",
                "MACD_Hist": "-0.1",
            },
        }
    }


@pytest.fixture
def av_sma_response():
    """Sample Alpha Vantage SMA response."""
    return {
        "Technical Analysis: SMA": {
            "2026-01-03": {"SMA": "150.00"},
            "2026-01-02": {"SMA": "149.50"},
        }
    }


@pytest.fixture
def av_fed_funds_response():
    """Sample Alpha Vantage federal funds rate response."""
    return {
        "data": [
            {"date": "2026-01-01", "value": "5.25"},
            {"date": "2025-12-01", "value": "5.25"},
        ]
    }


@pytest.fixture
def av_treasury_yield_response():
    """Sample Alpha Vantage treasury yield response."""
    return {
        "data": [
            {"date": "2026-01-03", "value": "4.50"},
            {"date": "2026-01-02", "value": "4.48"},
        ]
    }


@pytest.fixture
def finnhub_recommendations_response():
    """Sample Finnhub analyst recommendations response."""
    return [
        {
            "buy": 25,
            "hold": 10,
            "sell": 2,
            "strongBuy": 15,
            "strongSell": 1,
            "period": "2026-01-01",
            "symbol": "AAPL",
        }
    ]


@pytest.fixture
def finnhub_price_target_response():
    """Sample Finnhub price target response."""
    return {
        "lastUpdated": "2026-01-03",
        "symbol": "AAPL",
        "targetHigh": 220.0,
        "targetLow": 140.0,
        "targetMean": 185.0,
        "targetMedian": 180.0,
    }


@pytest.fixture
def finnhub_upgrades_response():
    """Sample Finnhub upgrades/downgrades response."""
    return [
        {
            "action": "upgrade",
            "company": "Morgan Stanley",
            "fromGrade": "Equal-Weight",
            "toGrade": "Overweight",
            "gradeTime": "2026-01-02T10:00:00Z",
            "symbol": "AAPL",
        },
        {
            "action": "reiterated",
            "company": "Goldman Sachs",
            "fromGrade": "Buy",
            "toGrade": "Buy",
            "gradeTime": "2025-12-20T14:00:00Z",
            "symbol": "AAPL",
        },
    ]


@pytest.fixture
def temp_cache_db():
    """Create a temporary cache database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        yield f.name
    # Clean up
    if os.path.exists(f.name):
        os.unlink(f.name)
