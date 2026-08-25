from __future__ import annotations

import asyncio
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import settings
from .demo import DemoEngine
from .execution import ExecutionMode
from .live_collector import collector
from .market_data import close_market_data, fetch_klines
from .multi_timeframe import fetch_contexts
from .notifications import send_push
from .notification_routes import router as notification_router
from .paper import PaperBroker
from .probability import engine
from .risk import size_position
from .storage import store
from .strategy import score_long_setup, score_short_setup

broker = PaperBroker(settings.starting_equity)
demo = DemoEngine(store.db_path)
execution = ExecutionMode(store.db_path)
monitor_task: asyncio.Task | None = None
demo_task: asyncio.Task | None = None

demo_scan_state = {
    "running": False,
    "last_scan_at": None,
    "scalp": {"scanned": 0, "qualified": 0, "rejected": 0, "errors": 0},
    "swing": {"scanned": 0, "qualified": 0, "rejected": 0, "errors": 0},
    "best_setup": None,
    "opened_last_cycle": 0,
    "last_error": None,
}


def web_directory() -> str:
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    else:
        base = Path(__file__).resolve().parent.parent
    candidate = base / "web"
    if not candidate.is_dir():
        raise RuntimeError(f"TradeBot UI-Verzeichnis fehlt: {candidate}")
    return str(candidate)


class DemoConfig(BaseModel):
    budget: float = Field(gt=0)
    risk_per_trade: float = Field(default=0.005, ge=0.001, le=0.03)
    max_positions: int = Field(default=5, ge=1, le=20)


class DemoToggle(BaseModel):
    enabled: bool


class ExecutionConfig(BaseModel):
    mode: str = "DEMO"


async def monitor_positions() -> None:
    while True:
        try:
            for position in list(broker.open_positions()):
                df = await fetch_klines(position.symbol, position.timeframe, 10)
                if df.empty:
                    continue
                candle = df.iloc[-1]
                before = position.status
                updated = broker.mark_candle(position.id, float(candle.high), float(candle.low), float(candle.close))
                if before == "OPEN" and updated.status == "CLOSED":
                    send_push(f"Trade geschlossen · {updated.side} {updated.symbol}", f"{updated.exit_reason} · P&L {updated.pnl:+.2f}", "/index.html")
        except Exception:
            pass
        await asyncio.sleep(5)


async def demo_loop() -> None:
    global demo_scan_state
    while True:
        if demo.enabled and execution.get()["mode"] == "DEMO":
            demo_scan_state["running"] = True
            demo_scan_state["last_error"] = None
            demo_scan_state["opened_last_cycle"] = 0
            try:
                scalp, swing = await asyncio.gather(
                    _scan_mode("SCALP", persist=False),
                    _scan_mode("SWING", persist=False),
                )
                demo_scan_state["scalp"] = {k: scalp.get(k, 0) for k in ("scanned", "qualified", "rejected", "errors")}
                demo_scan_state["swing"] = {k: swing.get(k, 0) for k in ("scanned", "qualified", "rejected", "errors")}

                candidates = scalp["setups"] + swing["setups"]
                candidates.sort(key=lambda x: (x.probability, x.expected_value_r), reverse=True)
                demo_scan_state["best_setup"] = candidates[0] if candidates else None
                demo_scan_state["opened_last_cycle"] = demo.consider_setups(candidates)
                await demo.update_positions(fetch_klines)
                demo_scan_state["last_scan_at"] = datetime.now(timezone.utc).isoformat()
            except Exception as exc:
                demo_scan_state["last_error"] = str(exc)
                demo_scan_state["last_scan_at"] = datetime.now(timezone.utc).isoformat()
            finally:
                demo_scan_state["running"] = False
        await asyncio.sleep(2.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global monitor_task, demo_task
    collector.start()
    monitor_task = asyncio.create_task(monitor_positions())
    if demo.enabled and execution.get()["mode"] == "DEMO":
        demo_task = asyncio.create_task(demo_loop())
    yield
    for task in (monitor_task, demo_task):
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    monitor_task = None
    demo_task = None
    await collector.stop()
    await close_market_data()


app = FastAPI(title="TradeBot AI Long/Short Trader", version="1.3.1", lifespan=lifespan)
app.include_router(notification_router)


def mode_config(mode: str) -> tuple[str, int, int, bool]:
    mode = mode.upper()
    if mode == "SCALP":
        return settings.scalping_timeframe, settings.scalp_min_confidence, settings.max_scalp_positions, settings.scalping_enabled
    if mode == "SWING":
        return settings.swing_timeframe, settings.swing_min_confidence, settings.max_swing_positions, settings.swing_enabled
    raise HTTPException(status_code=400, detail="mode must be SCALP or SWING")


async def analyze_symbol(symbol: str, mode: str):
    timeframe, _, _, enabled = mode_config(mode)
    if not enabled:
        return timeframe, None, None
    contexts, raw = await fetch_contexts(symbol, mode, settings.candle_limit)
    primary = raw.get(timeframe)
    if primary is None:
        primary = await fetch_klines(symbol, timeframe, settings.candle_limit)
    return timeframe, contexts, primary


@app.get("/")
def root():
    return {
        "name": "TradeBot AI Long/Short Trader",
        "version": "1.3.1",
        "paper_trading": settings.paper_trading,
        "ui": "/index.html",
        "execution": execution.get(),
        "demo": demo.status(),
        "demo_scan": demo_scan_state,
        "data": {"directory": settings.data_dir, "database": str(store.db_path), "collector_interval_seconds": settings.collector_interval_seconds},
        "modes": {
            "SCALP": {"timeframe": settings.scalping_timeframe, "min_confidence": settings.scalp_min_confidence, "max_positions": settings.max_scalp_positions, "model_ready": engine.ready("SCALP"), "analysis": ["1m", "5m", "15m", "1h", "4h"]},
            "SWING": {"timeframe": settings.swing_timeframe, "min_confidence": settings.swing_min_confidence, "max_positions": settings.max_swing_positions, "model_ready": engine.ready("SWING"), "analysis": ["5m", "15m", "1h", "4h"]},
        },
        "sides": ["LONG", "SHORT"],
        "time_based_exit": False,
        "dynamic_exit": True,
    }


@app.get("/health")
def health():
    return {"status": "ok", "paper_trading": settings.paper_trading, "collector_running": collector.running, "position_monitor": monitor_task is not None, "demo_running": demo.enabled, "execution_mode": execution.get()["mode"], "demo_scan": demo_scan_state, "database": str(store.db_path)}


@app.get("/execution")
def execution_status():
    return execution.get()


@app.post("/execution")
def execution_config(payload: ExecutionConfig):
    global demo_task
    try:
        result = execution.set(payload.mode)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result["mode"] == "LIVE":
        demo.set_enabled(False)
        if demo_task:
            demo_task.cancel()
            demo_task = None
    elif demo.enabled and (demo_task is None or demo_task.done()):
        demo_task = asyncio.create_task(demo_loop())
    return result


@app.get("/ai/status")
def ai_status():
    return {"SCALP": {"ready": engine.ready("SCALP")}, "SWING": {"ready": engine.ready("SWING")}, "method": "logistic + histogram gradient boosting + calibration", "fib_features": True, "multi_timeframe": True, "dynamic_exit": True, "walk_forward": "3/6/9"}


@app.get("/data/stats")
def data_stats():
    return {"directory": settings.data_dir, "database": str(store.db_path), "collector_running": collector.running, **store.stats()}


@app.get("/data/analyses")
def data_analyses(limit: int = 50):
    return {"items": store.recent_analyses(limit)}


@app.get("/data/training")
def data_training(limit: int = 10000):
    items = store.training_rows(limit)
    return {"items": items, "count": len(items)}


@app.post("/data/collect-now")
async def collect_now():
    scalp = await collector.collect_mode("SCALP")
    swing = await collector.collect_mode("SWING")
    return {"SCALP": scalp, "SWING": swing, "stats": store.stats()}


@app.get("/demo/status")
def demo_status():
    return demo.status()


@app.get("/demo/scan")
def demo_scan_status():
    return demo_scan_state


@app.get("/demo/positions")
def demo_positions():
    return {"items": demo.open_positions()}


@app.get("/demo/trades")
def demo_trades(limit: int = 100):
    return {"items": demo.journal(limit)}


@app.post("/demo/config")
def demo_config(payload: DemoConfig):
    if execution.get()["mode"] != "DEMO":
        raise HTTPException(status_code=409, detail="Demo-Budget kann nur im DEMO-Modus geändert werden")
    try:
        return demo.configure(payload.budget, payload.risk_per_trade, payload.max_positions)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/demo/toggle")
def demo_toggle(payload: DemoToggle):
    global demo_task
    if execution.get()["mode"] != "DEMO":
        raise HTTPException(status_code=409, detail="DEMO ist aktuell nicht der aktive Betriebsmodus")
    result = demo.set_enabled(payload.enabled)
    if payload.enabled:
        if demo_task is None or demo_task.done():
            demo_task = asyncio.create_task(demo_loop())
    elif demo_task:
        demo_task.cancel()
        demo_task = None
    return result


def _scan_mode_sync(mode: str):
    return mode
