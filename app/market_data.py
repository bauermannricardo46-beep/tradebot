from __future__ import annotations

import asyncio
import time
from typing import Final

import httpx
import pandas as pd

BINANCE_KLINES: Final = "https://api.binance.com/api/v3/klines"

CACHE_TTL: Final[dict[str, float]] = {
    "1m": 2.0,
    "5m": 5.0,
    "15m": 15.0,
    "1h": 30.0,
    "4h": 60.0,
}

_client: httpx.AsyncClient | None = None
_client_lock = asyncio.Lock()
_request_sem = asyncio.Semaphore(8)
_cache: dict[tuple[str, str, int], tuple[float, pd.DataFrame]] = {}
_cache_lock = asyncio.Lock()


async def _get_client() -> httpx.AsyncClient:
    global _client
    async with _client_lock:
        if _client is None or _client.is_closed:
            # Keep HTTP/2 disabled for maximum compatibility with packaged Windows builds.
            _client = httpx.AsyncClient(
                timeout=httpx.Timeout(8.0, connect=3.0),
                limits=httpx.Limits(max_connections=16, max_keepalive_connections=16),
                http2=False,
                headers={"User-Agent": "TRADENEX/1.4"},
            )
        return _client


async def close_market_data() -> None:
    global _client
    async with _client_lock:
        if _client is not None and not _client.is_closed:
            await _client.aclose()
        _client = None


def _cache_ttl(interval: str) -> float:
    return CACHE_TTL.get(interval, 5.0)


def _build_frame(rows: list[list]) -> pd.DataFrame:
    columns = [
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades", "taker_base", "taker_quote", "ignore",
    ]
    df = pd.DataFrame(rows, columns=columns)
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    return df[["open_time", "open", "high", "low", "close", "volume"]].dropna().reset_index(drop=True)


async def fetch_klines(symbol: str, interval: str, limit: int = 200) -> pd.DataFrame:
    key = (symbol.upper(), interval, int(limit))
    now = time.monotonic()
    ttl = _cache_ttl(interval)
    async with _cache_lock:
        cached = _cache.get(key)
        if cached and now - cached[0] < ttl:
            return cached[1].copy(deep=True)

    params = {"symbol": symbol.upper(), "interval": interval, "limit": int(limit)}
    client = await _get_client()
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            async with _request_sem:
                response = await client.get(BINANCE_KLINES, params=params)
                response.raise_for_status()
                frame = _build_frame(response.json())
            if frame.empty:
                raise ValueError("Binance returned no candle data")
            async with _cache_lock:
                _cache[key] = (time.monotonic(), frame)
            return frame.copy(deep=True)
        except Exception as exc:
            last_error = exc
            if attempt == 0:
                await asyncio.sleep(0.15)
    raise RuntimeError(f"Binance market data unavailable for {symbol}/{interval}: {last_error}") from last_error
