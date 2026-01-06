import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # API Keys
    ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")

    # Alpha Vantage MCP endpoint
    AV_MCP_URL: str = "https://mcp.alphavantage.co/mcp"

    # Finnhub API endpoint
    FINNHUB_BASE_URL: str = "https://finnhub.io/api/v1"

    # Cache settings (in seconds)
    CACHE_TTL_QUOTE: int = 60  # 1 min
    CACHE_TTL_NEWS: int = 900  # 15 min
    CACHE_TTL_FUNDAMENTALS: int = 86400  # 24 hours
    CACHE_TTL_PROFILE: int = 86400  # 24 hours
    CACHE_TTL_MACRO: int = 86400  # 24 hours
    CACHE_TTL_TECHNICALS: int = 300  # 5 min
    CACHE_TTL_ANALYSTS: int = 21600  # 6 hours

    # Cache database path
    CACHE_DB_PATH: str = os.getenv("CACHE_DB_PATH", "cache.db")


config = Config()
