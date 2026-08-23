from __future__ import annotations

import asyncio

from .config import settings
from .multi_timeframe import fetch_contexts
from .storage import TradeDataStore
from .strategy import score_long_setup, score_short_setup


class LiveCollector:
    def __init__(self) -> None:
        self.running = False
        self.task: asyncio.Task | None = None
        self.store = TradeDataStore(settings.data_dir)

    async def collect_mode(self, mode: str) -> dict[str, int]:
        mode = mode.upper()
        timeframe = settings.scalping_timeframe if mode == "SCALP" else settings.swing_timeframe
        saved_candles = 0
        saved_analyses = 0
        resolved = 0

        for symbol in settings.symbol_list:
            try:
                contexts, raw = await fetch_contexts(symbol, mode, settings.candle_limit)
                df = raw.get(timeframe)
                if df is None:
                    continue
                primary_rows = [
                    {"open_time": row.open_time.isoformat(), "open": float(row.open), "high": float(row.high), "low": float(row.low), "close": float(row.close), "volume": float(row.volume)}
                    for row in df.tail(min(len(df), 100)).itertuples(index=False)
                ]
                saved_candles += self.store.save_candles(symbol, mode, timeframe, primary_rows)

                for setup in (
                    score_long_setup(symbol, df, mode, timeframe, contexts),
                    score_short_setup(symbol, df, mode, timeframe, contexts),
                ):
                    if setup is None:
                        continue
                    threshold = settings.scalp_min_confidence if mode == "SCALP" else settings.swing_min_confidence
                    if setup.confidence >= threshold:
                        self.store.save_analysis(setup)
                        saved_analyses += 1

                resolved += self.store.resolve_open_outcomes(symbol, mode, timeframe)
            except Exception:
                continue

        return {"candles": saved_candles, "analyses": saved_analyses, "resolved": resolved}

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
