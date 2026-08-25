from __future__ import annotations

import pandas as pd
from .config import settings
from .features import add_indicators
from .models import TradeSetup
from .multi_timeframe import TimeframeContext, trend_alignment
from .probability import engine, probability_confidence


def _fib_levels(swing_low: float, swing_high: float) -> tuple[float, float, float, float]:
    span=swing_high-swing_low
    return (swing_high-span*0.382,swing_high-span*0.500,swing_high-span*0.618,swing_high-span*0.786)


def _build_levels(entry: float, atr: float, side: str, mode: str, swing_low: float, swing_high: float) -> tuple[float,float,float,float]:
    mode=mode.upper()
    if mode=="SCALP": sl_atr,tp1_rr,tp2_rr,min_buffer_pct,trail_fraction=settings.scalp_sl_atr_multiplier,settings.scalp_tp1_rr,settings.scalp_tp2_rr,0.0018,0.35
    else: sl_atr,tp1_rr,tp2_rr,min_buffer_pct,trail_fraction=settings.swing_sl_atr_multiplier,settings.swing_tp1_rr,settings.swing_tp2_rr,0.0045,0.15
    buffer=max(atr*sl_atr,entry*min_buffer_pct)
    if side=="LONG": stop=min(swing_low-buffer,entry-buffer); risk=abs(entry-stop); tp1=entry+risk*tp1_rr; tp2=entry+risk*tp2_rr; trailing=entry+buffer*trail_fraction
    else: stop=max(swing_high+buffer,entry+buffer); risk=abs(stop-entry); tp1=entry-risk*tp1_rr; tp2=entry-risk*tp2_rr; trailing=entry-buffer*trail_fraction
    return stop,tp1,tp2,trailing


def _scalp_score(r: pd.Series, side: str) -> tuple[int,list[str]]:
    score=0; reasons=[]
    if side=="LONG":
        if r.close>r.ema20>r.ema50: score+=22; reasons.append("5m Microtrend bullish (EMA20 > EMA50)")
        elif r.close>r.ema20: score+=10; reasons.append("Preis über EMA20")
        if 35<=r.rsi<=56: score+=18; reasons.append("RSI im Scalp-Long-Momentumfenster")
        elif r.rsi>70: score-=5; reasons.append("Scalp-Long bereits überdehnt")
        if r.macd_hist>0: score+=16; reasons.append("positives kurzfristiges MACD-Momentum")
        if r.close>r.swing_high12: score+=22; reasons.append("12-Candle Momentum-Breakout")
        elif r.close>r.open: score+=8; reasons.append("bullishe Impulskerze")
    else:
        if r.close<r.ema20<r.ema50: score+=22; reasons.append("5m Microtrend bearish (EMA20 < EMA50)")
        elif r.close<r.ema20: score+=10; reasons.append("Preis unter EMA20")
        if 44<=r.rsi<=65: score+=18; reasons.append("RSI im Scalp-Short-Momentumfenster")
        elif r.rsi<30: score-=5; reasons.append("Scalp-Short bereits überdehnt")
        if r.macd_hist<0: score+=16; reasons.append("negatives kurzfristiges MACD-Momentum")
        if r.close<r.swing_low12: score+=22; reasons.append("12-Candle Momentum-Breakdown")
        elif r.close<r.open: score+=8; reasons.append("bearishe Impulskerze")
    if r.volume>r.vol_ma20*1.10: score+=12; reasons.append("Scalp-Volumen über Durchschnitt")
    return max(0,min(score,100)),reasons


def _swing_score(r: pd.Series, side: str) -> tuple[int,list[str]]:
    score=0; reasons=[]
    if side=="LONG":
        if r.close>r.ema20>r.ema50: score+=28; reasons.append("1h Trendstruktur bullish (EMA20 > EMA50)")
        elif r.close>r.ema50: score+=12; reasons.append("Preis über EMA50")
        if 40<=r.rsi<=58: score+=14; reasons.append("RSI unterstützt nachhaltigen Swing-Long")
        elif r.rsi>68: score-=4; reasons.append("Swing-Long stark überdehnt")
        if r.macd_hist>0: score+=14; reasons.append("positiver Swing-Momentumfilter")
        if r.close>r.swing_high40: score+=24; reasons.append("40-Candle Structure Breakout")
        elif r.close>r.open: score+=6; reasons.append("bullishe Swing-Struktur")
    else:
        if r.close<r.ema20<r.ema50: score+=28; reasons.append("1h Trendstruktur bearish (EMA20 < EMA50)")
        elif r.close<r.ema50: score+=12; reasons.append("Preis unter EMA50")
        if 42<=r.rsi<=60: score+=14; reasons.append("RSI unterstützt nachhaltigen Swing-Short")
        elif r.rsi<32: score-=4; reasons.append("Swing-Short stark überdehnt")
        if r.macd_hist<0: score+=14; reasons.append("negativer Swing-Momentumfilter")
        if r.close<r.swing_low40: score+=24; reasons.append("40-Candle Structure Breakdown")
        elif r.close<r.open: score+=6; reasons.append("bearishe Swing-Struktur")
    if r.volume>r.vol_ma20*1.25: score+=10; reasons.append("Swing-Volumen deutlich über Durchschnitt")
    return max(0,min(score,100)),reasons


def score_setup(symbol: str, df: pd.DataFrame, side: str, mode: str, timeframe: str, contexts: dict[str,TimeframeContext]|None=None) -> TradeSetup|None:
    data=add_indicators(df).copy(); data["swing_high12"]=data["high"].rolling(12).max().shift(1); data["swing_low12"]=data["low"].rolling(12).min().shift(1); data["swing_high40"]=data["high"].rolling(40).max().shift(1); data["swing_low40"]=data["low"].rolling(40).min().shift(1); data=data.dropna()
    if len(data)<140:return None
    r=data.iloc[-1]; side=side.upper(); mode=mode.upper(); structure_lookback=30 if mode=="SCALP" else 100
    swing_high=float(data["high"].rolling(structure_lookback).max().iloc[-2]); swing_low=float(data["low"].rolling(structure_lookback).min().iloc[-2]); stop,tp1,tp2,trailing=_build_levels(float(r.close),float(r.atr),side,mode,swing_low,swing_high); risk=abs(stop-float(r.close)); rr=abs(tp2-float(r.close))/risk if risk else 0.0
    rule_score,reasons=_scalp_score(r,side) if mode=="SCALP" else _swing_score(r,side); alignment=trend_alignment(contexts,side) if contexts else 0.5; reasons.append(f"Multi-Timeframe Alignment {alignment:.0%}"); alignment_min=0.50 if mode=="SCALP" else 0.75; alignment_bonus=10 if mode=="SCALP" else 8
    if alignment>=alignment_min: rule_score=min(100,rule_score+alignment_bonus)
    elif alignment<(0.40 if mode=="SCALP" else 0.50): rule_score=max(0,rule_score-10)
    fib382,fib500,fib618,fib786=_fib_levels(swing_low,swing_high); price=float(r.close); nearest_fib=min((fib382,fib500,fib618,fib786),key=lambda x:abs(x-price)); fib_distance_limit=0.018 if mode=="SCALP" else 0.022
    if abs(nearest_fib-price)/price<fib_distance_limit: rule_score=min(100,rule_score+(4 if mode=="SCALP" else 7)); reasons.append(f"Fib-Confluence ({'kurzfristig' if mode=='SCALP' else 'strukturell'})")
    if rr<(1.00 if mode=="SCALP" else 1.80): return None
    prob=engine.predict(data,side,mode,rr)
    if prob.model_ready:
        confidence=probability_confidence(prob.probability,True); reasons.append(f"kalibrierte {mode}-Modellwahrscheinlichkeit {prob.probability*100:.1f}%"); reasons.append(f"Expected Value {prob.expected_value_r:+.2f}R"); ev_floor=0.02 if mode=="SCALP" else 0.10
        if rule_score<(35 if mode=="SCALP" else 50) or prob.expected_value_r<=ev_floor or alignment<alignment_min:return None
    else:
        # Heuristic mode is now a genuine market filter, not a confidence-label bypass.
        # 80/82 are display thresholds only. A setup must earn its way through using
        # live structure, momentum, MTF alignment and positive risk-adjusted EV.
        fallback_probability=max(0.01,min(0.99,rule_score/100.0)); prob=prob.__class__(fallback_probability,fallback_probability,False,prob.model_version,prob.evidence,fallback_probability*rr-(1-fallback_probability),rr)
        heuristic_floor=60 if mode=="SCALP" else 65
        if rule_score<heuristic_floor or alignment<alignment_min or prob.expected_value_r<=0:return None
        confidence=rule_score
        reasons.append(f"{mode}-Heuristik · echter Live-Marktfilter · Modell nicht erforderlich")
    if confidence<50:return None
    reasons.append(f"{mode} Profil · SL {settings.scalp_sl_atr_multiplier if mode=='SCALP' else settings.swing_sl_atr_multiplier:.2f}×ATR · TP1 {settings.scalp_tp1_rr if mode=='SCALP' else settings.swing_tp1_rr:.2f}R · TP2 {settings.scalp_tp2_rr if mode=='SCALP' else settings.swing_tp2_rr:.2f}R")
    return TradeSetup(symbol=symbol,side=side,mode=mode,timeframe=timeframe,source_open_time=pd.to_datetime(r.open_time,utc=True).to_pydatetime(),analysis_timeframes=list(contexts.keys()) if contexts else [timeframe],confidence=confidence,probability=prob.probability,expected_value_r=round(prob.expected_value_r,3),model_ready=prob.model_ready,model_version=prob.model_version,entry=round(price,8),stop_loss=round(stop,8),take_profit_1=round(tp1,8),take_profit_2=round(tp2,8),risk_reward=round(rr,2),swing_high=round(swing_high,8),swing_low=round(swing_low,8),fib_382=round(fib382,8),fib_500=round(fib500,8),fib_618=round(fib618,8),fib_786=round(fib786,8),trailing_stop=round(trailing,8),reasons=reasons)


def score_short_setup(symbol:str,df:pd.DataFrame,mode:str="SWING",timeframe:str="1h",contexts:dict[str,TimeframeContext]|None=None)->TradeSetup|None:return score_setup(symbol,df,"SHORT",mode,timeframe,contexts)
def score_long_setup(symbol:str,df:pd.DataFrame,mode:str="SWING",timeframe:str="1h",contexts:dict[str,TimeframeContext]|None=None)->TradeSetup|None:return score_setup(symbol,df,"LONG",mode,timeframe,contexts)
