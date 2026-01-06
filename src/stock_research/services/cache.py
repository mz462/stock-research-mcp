"""SQLite-based caching service."""

import json
import time
import aiosqlite
from typing import Any, Optional, Callable, Awaitable

from stock_research.config import config

_db: Optional[aiosqlite.Connection] = None


async def init_cache() -> None:
    """Initialize the cache database."""
    global _db
    _db = await aiosqlite.connect(config.CACHE_DB_PATH)
    await _db.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            expires_at REAL NOT NULL
        )
    """)
    await _db.execute("CREATE INDEX IF NOT EXISTS idx_expires ON cache(expires_at)")
    await _db.commit()


async def close_cache() -> None:
    """Close the cache database."""
    global _db
    if _db:
        await _db.close()
        _db = None


async def get(key: str) -> Optional[Any]:
    """Get a value from cache if not expired."""
    if not _db:
        return None

    async with _db.execute(
        "SELECT value, expires_at FROM cache WHERE key = ?",
        (key,)
    ) as cursor:
        row = await cursor.fetchone()

    if not row:
        return None

    value, expires_at = row
    if time.time() > expires_at:
        # Expired, delete it
        await _db.execute("DELETE FROM cache WHERE key = ?", (key,))
        await _db.commit()
        return None

    return json.loads(value)


async def set(key: str, value: Any, ttl: int) -> None:
    """Set a value in cache with TTL in seconds."""
    if not _db:
        return

    expires_at = time.time() + ttl
    await _db.execute(
        """
        INSERT OR REPLACE INTO cache (key, value, expires_at)
        VALUES (?, ?, ?)
        """,
        (key, json.dumps(value), expires_at)
    )
    await _db.commit()


async def delete(key: str) -> None:
    """Delete a key from cache."""
    if not _db:
        return

    await _db.execute("DELETE FROM cache WHERE key = ?", (key,))
    await _db.commit()


async def clear_expired() -> int:
    """Clear all expired entries. Returns count of deleted entries."""
    if not _db:
        return 0

    cursor = await _db.execute(
        "DELETE FROM cache WHERE expires_at < ?",
        (time.time(),)
    )
    await _db.commit()
    return cursor.rowcount


async def get_or_fetch(
    key: str,
    ttl: int,
    fetch_fn: Callable[[], Awaitable[Any]]
) -> Any:
    """Get from cache or fetch and cache the result."""
    cached = await get(key)
    if cached is not None:
        return cached

    data = await fetch_fn()
    if data is not None:
        await set(key, data, ttl)
    return data
