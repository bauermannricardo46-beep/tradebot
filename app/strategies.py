from __future__ import annotations

import numpy as np
import pandas as pd

from .models import TradeSetup


def _indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ema20"] = out["close"].ewm(span=20, adjust=False).mean()
    out["ema50"] = out["close"].ewm(span=50, adjust=False).mean()
    delta = out["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    out["rsi"] = 100 - (100 / (1 + rs))
    fast = out["close"].ewm(span=12, adjust=False).mean()
    slow = out["close"].ewm(span=26, adjust=False).mean()
    macd = fast - slow
    out["macd_hist"] = macd - macd.ewm(span=9, adjust=False).mean()
    tr = pd.concat([
        out["high"] - out["low"],
        (out["high"] - out["close"].shift()).abs(),
        (out["low"] - out["close"].shift()).abs(),
    ], axis=1).max(axis=1)
    out["atr"] = tr.rolling(14).mean()
    out["vol_ma20"] = out["volume"].rolling(20).mean()
    out["swing_low20"] = out["low"].rolling(20).min().shift(1)
    out["swing_high20"] = out["high"].rolling(20).max().shift(1)
    return out.dropna()


def _build_setup(symbol: str, side: str, score: int, reasons: list[str], entry: float, atr: float) -> TradeSetup | None:
    score = min(100, int(score))
    if score < 50:
        return None

    distance = max(1.5 * atr, entry * 0.004)
    if side == "SHORT":
        stop = entry + distance
        tp1 = entry - distance * 2
        tp2 = entry - distance * 3
    else:
        stop = entry - distance
        tp1 = entry + distance * 2
        tp2 = entry + distance * 3

    return TradeSetup(
        symbol=symbol,
        side=side,
        confidence=score,
        entry=round(entry, 8),
        stop_loss=round(stop, 8),
        take_profit_1=round(tp1, 8),
        take_profit_2=round(tp2, 8),
        risk_reward=2.0,
        reasons=reasons,
    )


def score_long_setup(symbol: str, df: pd.DataFrame) -> TradeSetup | None:
    data = _indicators(df)
    if len(data) < 30:
        return None
    r = data.iloc[-1]
    score = 0
    reasons: list[str] = []

    if r.close > r.ema20 > r.ema50:
        score += 25
        reasons.append("price above EMA20 and EMA50")
    elif r.close > r.ema50:
        score += 12
        reasons.append("price above EMA50")

    if 38 <= r.rsi <= 55:
        score += 15
        reasons.append("RSI supports bullish continuation without being deeply overbought")
    elif r.rsi > 60:
        score += 7
        reasons.append("RSI strong, but upside may be extended")

    if r.macd_hist > 0:
        score += 15
        reasons.append("positive MACD histogram")

    if r.close > r.swing_high20:
        score += 25
        reasons.append("20-candle resistance breakout")
    elif r.close > r.open:
        score += 7
        reasons.append("bullish current candle")

    if r.volume > r.vol_ma20 * 1.25:
        score += 10
        reasons.append("above-average volume")

    return _build_setup(symbol, "LONG", score, reasons, float(r.close), float(r.atr))
