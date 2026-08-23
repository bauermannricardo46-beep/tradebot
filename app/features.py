from __future__ import annotations

import numpy as np
import pandas as pd

FEATURES = [
    "ret_1", "ret_3", "ret_12", "atr_pct", "rsi",
    "ema20_gap", "ema50_gap", "ema_slope", "macd_hist_pct",
    "volume_z", "range_pct", "close_location", "breakout_gap",
    "fib_382_dist", "fib_500_dist", "fib_618_dist", "fib_786_dist",
    "trend_strength", "volatility_regime", "side_long",
]


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
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
    out["vol_std20"] = out["volume"].rolling(20).std()
    out["swing_low20"] = out["low"].rolling(20).min().shift(1)
    out["swing_high20"] = out["high"].rolling(20).max().shift(1)
    out["range_pct"] = (out["high"] - out["low"]) / out["close"]
    return out


def _fib_levels(r: pd.Series) -> dict[str, float]:
    high = float(r["high20"])
    low = float(r["low20"])
    span = max(high - low, 1e-12)
    return {
        "382": high - span * 0.382,
        "500": high - span * 0.500,
        "618": high - span * 0.618,
        "786": high - span * 0.786,
    }


def feature_frame(df: pd.DataFrame, side: str) -> pd.DataFrame:
    out = add_indicators(df)
    out["ret_1"] = out["close"].pct_change(1)
    out["ret_3"] = out["close"].pct_change(3)
    out["ret_12"] = out["close"].pct_change(12)
    out["atr_pct"] = out["atr"] / out["close"]
    out["ema20_gap"] = out["close"] / out["ema20"] - 1
    out["ema50_gap"] = out["close"] / out["ema50"] - 1
    out["ema_slope"] = out["ema20"].pct_change(5)
    out["macd_hist_pct"] = out["macd_hist"] / out["close"]
    out["volume_z"] = (out["volume"] - out["vol_ma20"]) / out["vol_std20"].replace(0, np.nan)
    out["close_location"] = (out["close"] - out["low"]) / (out["high"] - out["low"]).replace(0, np.nan)
    out["breakout_gap"] = np.where(
        side.upper() == "LONG",
        out["close"] / out["swing_high20"] - 1,
        out["close"] / out["swing_low20"] - 1,
    )
    out["high20"] = out["high"].rolling(20).max()
    out["low20"] = out["low"].rolling(20).min()
    span = (out["high20"] - out["low20"]).replace(0, np.nan)
    for key, ratio in (("382", .382), ("500", .500), ("618", .618), ("786", .786)):
        level = out["high20"] - span * ratio
        out[f"fib_{key}_dist"] = (out["close"] - level).abs() / out["close"]
    out["trend_strength"] = (out["ema20"] - out["ema50"]).abs() / out["close"]
    out["volatility_regime"] = out["atr_pct"] / out["atr_pct"].rolling(100).median()
    out["side_long"] = 1.0 if side.upper() == "LONG" else 0.0
    return out[FEATURES].replace([np.inf, -np.inf], np.nan).dropna()


def latest_features(df: pd.DataFrame, side: str) -> pd.Series | None:
    frame = feature_frame(df, side)
    return None if frame.empty else frame.iloc[-1]
