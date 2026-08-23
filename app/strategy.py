from __future__ import annotations

import pandas as pd

from .features import add_indicators
from .models import TradeSetup
from .probability import engine, probability_confidence


def _build_levels(entry: float, atr: float, side: str, mode: str) -> tuple[float, float, float]:
    # SCALP reacts to shorter-term volatility; SWING gives the position more room.
    atr_multiplier = 1.0 if mode == "SCALP" else 1.8
    minimum_pct = 0.0025 if mode == "SCALP" else 0.006
    distance = max(atr_multiplier * atr, entry * minimum_pct)
    if side == "SHORT":
        return entry + distance, entry - distance * 2, entry - distance * 3
    return entry - distance, entry + distance * 2, entry + distance * 3


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


def score_setup(symbol: str, df: pd.DataFrame, side: str, mode: str, timeframe: str) -> TradeSetup | None:
    data = add_indicators(df).dropna()
    if len(data) < 120:
        return None
    r = data.iloc[-1]
    rule_score, reasons = _rule_score(r, side)
    entry = float(r.close)
    atr = float(r.atr)
    stop, tp1, tp2 = _build_levels(entry, atr, side, mode)
    risk = abs(stop - entry)
    rr = abs(tp1 - entry) / risk if risk else 0.0

    prob = engine.predict(data, side, mode, rr)
    if prob.model_ready:
        confidence = probability_confidence(prob.probability, True)
        reasons.append(f"kalibrierte Modellwahrscheinlichkeit {prob.probability * 100:.1f}%")
        if prob.expected_value_r > 0:
            reasons.append(f"positiver Erwartungswert {prob.expected_value_r:+.2f}R")
        else:
            reasons.append(f"Erwartungswert {prob.expected_value_r:+.2f}R")
        # A model can only promote a setup when the traditional market structure
        # agrees with it; this avoids a black-box trade override.
        if rule_score < 35 or prob.expected_value_r <= 0:
            return None
    else:
        confidence = rule_score
        fallback_probability = rule_score / 100.0
        prob = prob.__class__(
            fallback_probability,
            fallback_probability,
            False,
            prob.model_version,
            prob.evidence,
            fallback_probability * rr - (1 - fallback_probability),
            rr,
        )
        reasons.append("Modell noch nicht trainiert – regelbasierter Fallback")

    if confidence < 50:
        return None
    return TradeSetup(
        symbol=symbol,
        side=side,
        mode=mode,
        timeframe=timeframe,
        confidence=confidence,
        probability=prob.probability,
        expected_value_r=round(prob.expected_value_r, 3),
        model_ready=prob.model_ready,
        model_version=prob.model_version,
        entry=round(entry, 8),
        stop_loss=round(stop, 8),
        take_profit_1=round(tp1, 8),
        take_profit_2=round(tp2, 8),
        risk_reward=round(rr, 2),
        reasons=reasons,
    )


def score_short_setup(symbol: str, df: pd.DataFrame, mode: str = "SWING", timeframe: str = "1h") -> TradeSetup | None:
    return score_setup(symbol, df, "SHORT", mode, timeframe)


def score_long_setup(symbol: str, df: pd.DataFrame, mode: str = "SWING", timeframe: str = "1h") -> TradeSetup | None:
    return score_setup(symbol, df, "LONG", mode, timeframe)
