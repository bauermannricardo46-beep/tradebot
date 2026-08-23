from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .market_data import fetch_klines


@dataclass
class TimeframeContext:
    timeframe: str
    close: float
    ema20: float
    ema50: float
    trend: int
    swing_high: float
    swing_low: float


def context(df: pd.DataFrame, timeframe: str) -> TimeframeContext:
    data = df.copy()
    data["ema20"] = data["close"].ewm(span=20, adjust=False).mean()
    data["ema50"] = data["close"].ewm(span=50, adjust=False).mean()
    swing_high = float(data["high"].rolling(40).max().iloc[-2])
    swing_low = float(data["low"].rolling(40).min().iloc[-2])
    close = float(data["close"].iloc[-1])
    trend = 1 if close > float(data["ema20"].iloc[-1]) > float(data["ema50"].iloc[-1]) else -1 if close < float(data["ema20"].iloc[-1]) < float(data["ema50"].iloc[-1]) else 0
    return TimeframeContext(timeframe, close, float(data["ema20"].iloc[-1]), float(data["ema50"].iloc[-1]), trend, swing_high, swing_low)


async def fetch_contexts(symbol: str, mode: str, limit: int = 250) -> tuple[dict[str, TimeframeContext], dict[str, pd.DataFrame]]:
    frames = ["1m", "5m", "15m", "1h", "4h"] if mode.upper() == "SCALP" else ["5m", "15m", "1h", "4h"]
    contexts: dict[str, TimeframeContext] = {}
    raw: dict[str, pd.DataFrame] = {}
    for tf in frames:
        df = await fetch_klines(symbol, tf, limit)
        if len(df) < 60:
            continue
        raw[tf] = df
        contexts[tf] = context(df, tf)
    return contexts, raw


def trend_alignment(contexts: dict[str, TimeframeContext], side: str) -> float:
    wanted = 1 if side.upper() == "LONG" else -1
    scores = [ctx.trend for ctx in contexts.values()]
    if not scores:
        return 0.0
    return sum(1 for s in scores if s == wanted) / len(scores)
