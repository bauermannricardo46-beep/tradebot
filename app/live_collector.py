from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from .config import settings
from .market_data import fetch_klines
from .storage import store
from .strategy import score_long_setup, score_short_setup


class LiveCollector:
    def __init__(self) -> None:
        self.running = False
        self.task: asyncio.Task | None = None

    async def collect_mode(self, mode: str) -> dict[str, int]:
        mode = mode.upper()
        timeframe = settings.scalping_timeframe if mode == "SCALP" else settings.swing_timeframe
        saved_candles = 0
        saved_analyses = 0

        for symbol in settings.symbol_list:
            try:
                df = await fetch_klines(symbol, timeframe, settings.candle_limit)
                candle_rows = [
                    {
                        "open_time": row.open_time.isoformat(),
                        "open": float(row.open),
                        "high": float(row.high),
                        "low": float(row.low),
                        "close": float(row.close),
                        "volume": float(row.volume),
                    }
                    for row in df.tail(min(len(df), 50)).itertuples(index=False)
                ]
                saved_candles += store.save_candles(symbol, mode, timeframe, candle_rows)

                for setup in (
                    score_long_setup(symbol, df, mode, timeframe),
                    score_short_setup(symbol, df, mode, timeframe),
                ):
                    if setup is not None:
                        threshold = settings.scalp_min_confidence if mode == "SCALP" else settings.swing_min_confidence
                        if setup.confidence >= threshold:
                            store.save_analysis(setup)
                            saved_analyses += 1
            except Exception:
                continue

        return {"candles": saved_candles, "analyses": saved_analyses}

    async def run_forever(self) -> None:
        self.running = True
        while self.running:
            await self.collect_mode("SCALP")
            await self.collect_mode("SWING")
            await asyncio.sleep(settings.collector_interval_seconds)

    def start(self) -> None:
        if self.task and not self.task.done():
            return
        self.task = asyncio.create_task(self.run_forever())

    async def stop(self) -> None:
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None


collector = LiveCollector()
