from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .config import settings
from .market_data import fetch_klines
from .paper import PaperBroker
from .risk import size_short_position
from .strategy import score_short_setup

app = FastAPI(title="TradeBot AI Short Trader", version="0.1.0")
broker = PaperBroker(settings.starting_equity)


@app.get("/")
def root():
    return {
        "name": "TradeBot AI Short Trader",
        "version": "0.1.0",
        "paper_trading": settings.paper_trading,
        "min_confidence": settings.min_confidence,
    }


@app.get("/health")
def health():
    return {"status": "ok", "paper_trading": settings.paper_trading}


@app.get("/scan")
async def scan_all():
    results = []
    for symbol in settings.symbol_list:
        try:
            df = await fetch_klines(symbol, settings.timeframe, settings.candle_limit)
            setup = score_short_setup(symbol, df)
            if setup:
                results.append(setup)
        except Exception as exc:
            results.append({"symbol": symbol, "error": str(exc)})
    return {"setups": results}


@app.post("/trade/{symbol}")
async def auto_paper_trade(symbol: str):
    symbol = symbol.upper()
    if symbol not in settings.symbol_list:
        raise HTTPException(status_code=400, detail="symbol not configured")

    df = await fetch_klines(symbol, settings.timeframe, settings.candle_limit)
    setup = score_short_setup(symbol, df)
    if setup is None:
        raise HTTPException(status_code=422, detail="no short setup detected")

    decision = size_short_position(
        equity=broker.equity,
        setup=setup,
        open_positions=len(broker.open_positions()),
        daily_pnl=broker.realized_pnl,
    )
    if not decision.allowed:
        raise HTTPException(status_code=409, detail=decision.reason)

    position = broker.open_short(setup, decision.quantity)
    return {
        "setup": setup,
        "risk": decision,
        "position": position,
        "execution": "PAPER_ONLY",
    }


@app.get("/positions")
def positions():
    return {
        "equity": broker.equity,
        "realized_pnl": broker.realized_pnl,
        "positions": broker.open_positions(),
    }
