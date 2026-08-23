from __future__ import annotations

import pandas as pd

from .features import add_indicators
from .models import TradeSetup
from .multi_timeframe import TimeframeContext, trend_alignment
from .probability import engine, probability_confidence


def _fib_levels(swing_low: float, swing_high: float) -> tuple[float, float, float, float]:
    span = swing_high - swing_low
    return (
        swing_high - span * 0.382,
        swing_high - span * 0.500,
        swing_high - span * 0.618,
        swing_high - span * 0.786,
    )


def _build_levels(entry: float, atr: float, side: str, mode: str, swing_low: float, swing_high: float) -> tuple[float, float, float, float]:
    buffer = max(atr * (0.8 if mode == "SCALP" else 1.2), entry * (0.002 if mode == "SCALP" else 0.004))
    fib382, fib500, fib618, fib786 = _fib_levels(swing_low, swing_high)
    if side == "LONG":
        stop = min(swing_low - buffer, entry - buffer)
        candidates = [x for x in (fib382, fib500, fib618, fib786, swing_high) if x > entry * 1.005]
        tp1 = min(candidates) if candidates else entry + buffer * 2
        extension = swing_high + (swing_high - swing_low) * (0.272 if mode == "SCALP" else 0.618)
        tp2 = max(tp1, extension)
        trailing = max(entry, entry + buffer)
    else:
        stop = max(swing_high + buffer, entry + buffer)
        candidates = [x for x in (fib382, fib500, fib618, fib786, swing_low) if x < entry * 0.995]
        tp1 = max(candidates) if candidates else entry - buffer * 2
        extension = swing_low - (swing_high - swing_low) * (0.272 if mode == "SCALP" else 0.618)
        tp2 = min(tp1, extension)
        trailing = min(entry, entry - buffer)
    return stop, tp1, tp2, trailing


def _rule_score(r: pd.Series, side: str) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    if side == "SHORT":
        if r.close < r.ema20 < r.ema50:
            score += 25; reasons.append("Preis unter EMA20 und EMA50")
        elif r.close < r.ema50:
            score += 12; reasons.append("Preis unter EMA50")
        if 45 <= r.rsi <= 62:
            score += 15; reasons.append("RSI unterstützt bearishe Fortsetzung")
        elif r.rsi < 40:
            score += 7; reasons.append("RSI schwach, Bewegung kann aber bereits überdehnt sein")
        if r.macd_hist < 0:
            score += 15; reasons.append("negatives MACD-Histogramm")
        if r.close < r.swing_low20:
            score += 25; reasons.append("20-Candle-Support-Breakdown")
        elif r.close < r.open:
            score += 7; reasons.append("bearishe aktuelle Candle")
    else:
        if r.close > r.ema20 > r.ema50:
            score += 25; reasons.append("Preis über EMA20 und EMA50")
        elif r.close > r.ema50:
            score += 12; reasons.append("Preis über EMA50")
        if 38 <= r.rsi <= 55:
            score += 15; reasons.append("RSI unterstützt bullishe Fortsetzung")
        elif r.rsi > 60:
            score += 7; reasons.append("RSI stark, Bewegung kann aber bereits überdehnt sein")
        if r.macd_hist > 0:
            score += 15; reasons.append("positives MACD-Histogramm")
        if r.close > r.swing_high20:
            score += 25; reasons.append("20-Candle-Resistance-Breakout")
        elif r.close > r.open:
            score += 7; reasons.append("bullishe aktuelle Candle")
    if r.volume > r.vol_ma20 * 1.25:
        score += 10; reasons.append("überdurchschnittliches Volumen")
    return min(score, 100), reasons


def score_setup(symbol: str, df: pd.DataFrame, side: str, mode: str, timeframe: str, contexts: dict[str, TimeframeContext] | None = None) -> TradeSetup | None:
    data = add_indicators(df).dropna()
    if len(data) < 120:
        return None
    r = data.iloc[-1]
    side = side.upper(); mode = mode.upper()
    swing_high = float(data["high"].rolling(80).max().iloc[-2])
    swing_low = float(data["low"].rolling(80).min().iloc[-2])
    stop, tp1, tp2, trailing = _build_levels(float(r.close), float(r.atr), side, mode, swing_low, swing_high)
    risk = abs(stop - float(r.close))
    rr = abs(tp2 - float(r.close)) / risk if risk else 0.0
    rule_score, reasons = _rule_score(r, side)

    alignment = trend_alignment(contexts, side) if contexts else 0.5
    if contexts:
        reasons.append(f"Multi-Timeframe Alignment {alignment:.0%}")
        if alignment >= 0.75:
            rule_score = min(100, rule_score + 8)
        elif alignment < 0.50:
            rule_score = max(0, rule_score - 8)

    fib382, fib500, fib618, fib786 = _fib_levels(swing_low, swing_high)
    price = float(r.close)
    nearest_fib = min((fib382, fib500, fib618, fib786), key=lambda x: abs(x - price))
    if abs(nearest_fib - price) / price < 0.012:
        rule_score = min(100, rule_score + 5)
        reasons.append("Fib-Confluence in Entry-Nähe")

    prob = engine.predict(data, side, mode, rr)
    if prob.model_ready:
        confidence = probability_confidence(prob.probability, True)
        reasons.append(f"kalibrierte Modellwahrscheinlichkeit {prob.probability * 100:.1f}%")
        reasons.append(f"Expected Value {prob.expected_value_r:+.2f}R")
        if rule_score < 35 or prob.expected_value_r <= 0.05 or alignment < 0.50:
            return None
    else:
        confidence = rule_score
        fallback_probability = max(0.01, min(0.99, rule_score / 100.0))
        prob = prob.__class__(fallback_probability, fallback_probability, False, prob.model_version, prob.evidence, fallback_probability * rr - (1 - fallback_probability), rr)
        reasons.append("Modell noch nicht validiert – regelbasierter Fallback")

    if confidence < 50:
        return None
    return TradeSetup(
        symbol=symbol, side=side, mode=mode, timeframe=timeframe,
        analysis_timeframes=list(contexts.keys()) if contexts else [timeframe],
        confidence=confidence,
        probability=prob.probability,
        expected_value_r=round(prob.expected_value_r, 3),
        model_ready=prob.model_ready, model_version=prob.model_version,
        entry=round(price, 8), stop_loss=round(stop, 8),
        take_profit_1=round(tp1, 8), take_profit_2=round(tp2, 8),
        risk_reward=round(rr, 2), swing_high=round(swing_high, 8), swing_low=round(swing_low, 8),
        fib_382=round(fib382, 8), fib_500=round(fib500, 8), fib_618=round(fib618, 8), fib_786=round(fib786, 8),
        trailing_stop=round(trailing, 8), reasons=reasons,
    )


def score_short_setup(symbol: str, df: pd.DataFrame, mode: str = "SWING", timeframe: str = "1h", contexts: dict[str, TimeframeContext] | None = None) -> TradeSetup | None:
    return score_setup(symbol, df, "SHORT", mode, timeframe, contexts)


def score_long_setup(symbol: str, df: pd.DataFrame, mode: str = "SWING", timeframe: str = "1h", contexts: dict[str, TimeframeContext] | None = None) -> TradeSetup | None:
    return score_setup(symbol, df, "LONG", mode, timeframe, contexts)
