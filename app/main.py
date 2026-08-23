from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .config import settings
from .market_data import fetch_klines
from .paper import PaperBroker
from .risk import size_position
from .strategy import score_long_setup, score_short_setup

app = FastAPI(title="TradeBot AI Long/Short Trader", version="0.3.0")
broker = PaperBroker(settings.starting_equity)


def mode_config(mode: str) -> tuple[str, int, int, bool]:
    mode = mode.upper()
    if mode == "SCALP":
        return settings.scalping_timeframe, settings.scalp_min_confidence, settings.max_scalp_positions, settings.scalping_enabled
    if mode == "SWING":
        return settings.swing_timeframe, settings.swing_min_confidence, settings.max_swing_positions, settings.swing_enabled
    raise HTTPException(status_code=400, detail="mode must be SCALP or SWING")


@app.get("/")
def root():
    return {
        "name": "TradeBot AI Long/Short Trader",
        "version": "0.3.0",
        "paper_trading": settings.paper_trading,
        "modes": {
            "SCALP": {"timeframe": settings.scalping_timeframe, "min_confidence": settings.scalp_min_confidence},
            "SWING": {"timeframe": settings.swing_timeframe, "min_confidence": settings.swing_min_confidence},
        },
        "sides": ["LONG", "SHORT"],
        "time_based_exit": False,
    }


@app.get("/health")
def health():
    return {"status": "ok", "paper_trading": settings.paper_trading}


@app.get("/scan")
async def scan_all(mode: str = "SCALP"):
    timeframe, min_confidence, _, enabled = mode_config(mode)
    if not enabled:
        return {"mode": mode.upper(), "enabled": False, "setups": []}

    results = []
    for symbol in settings.symbol_list:
        try:
            df = await fetch_klines(symbol, timeframe, settings.candle_limit)
            long_setup = score_long_setup(symbol, df, mode.upper(), timeframe)
            short_setup = score_short_setup(symbol, df, mode.upper(), timeframe)
            for setup in (long_setup, short_setup):
                if setup is not None and setup.confidence >= min_confidence:
                    results.append(setup)
        except Exception as exc:
            results.append({"symbol": symbol, "error": str(exc)})
    return {"mode": mode.upper(), "timeframe": timeframe, "setups": results}


@app.get("/scan/all")
async def scan_all_modes():
    output = {}
    for mode in ("SCALP", "SWING"):
        output[mode] = await scan_all(mode)
    return output


@app.post("/trade/{mode}/{side}/{symbol}")
async def auto_paper_trade(mode: str, side: str, symbol: str):
    mode = mode.upper()
    side = side.upper()
    symbol = symbol.upper()
    timeframe, min_confidence, max_positions, enabled = mode_config(mode)

    if not enabled:
        raise HTTPException(status_code=409, detail=f"{mode} mode is disabled")
    if side not in {"LONG", "SHORT"}:
        raise HTTPException(status_code=400, detail="side must be LONG or SHORT")
    if symbol not in settings.symbol_list:
        raise HTTPException(status_code=400, detail="symbol not configured")

    df = await fetch_klines(symbol, timeframe, settings.candle_limit)
    setup = (score_long_setup if side == "LONG" else score_short_setup)(symbol, df, mode, timeframe)
    if setup is None or setup.confidence < min_confidence:
        raise HTTPException(status_code=422, detail=f"no qualifying {mode.lower()} {side.lower()} setup detected")

    open_total = broker.open_positions()
    if len([p for p in open_total if p.mode == mode]) >= max_positions:
        raise HTTPException(status_code=409, detail=f"maximum {mode.lower()} positions reached")

    decision = size_position(
        equity=broker.equity,
        setup=setup,
        open_positions=len(open_total),
        daily_pnl=broker.realized_pnl,
    )
    if not decision.allowed:
        raise HTTPException(status_code=409, detail=decision.reason)

    position = broker.open_position(setup, decision.quantity)
    return {
        "setup": setup,
        "risk": decision,
        "position": position,
        "execution": "PAPER_ONLY",
        "exit_policy": "SL/TP/strategy invalidation only; no time-based exit",
    }


@app.get("/positions")
def positions():
    return {
        "equity": broker.equity,
        "realized_pnl": broker.realized_pnl,
        "positions": broker.open_positions(),
    }
