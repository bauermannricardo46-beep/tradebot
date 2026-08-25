from __future__ import annotations

import asyncio
import time

from .features import latest_features
from .github_sync import sync_analysis_archive
from .storage import store
from .strategy import score_long_setup, score_short_setup


class LiveCollector:
    def __init__(self) -> None:
        self.running = False
        self.task: asyncio.Task | None = None
        self.store = store
        self.last_github_sync = 0.0

    async def _collect_symbol(self, mode: str, symbol: str) -> dict[str, int]:
        timeframe = settings.scalping_timeframe if mode == "SCALP" else settings.swing_timeframe
        saved_candles = 0
        saved_analyses = 0
        resolved = 0
        try:
            contexts, raw = await fetch_contexts(symbol, mode, settings.candle_limit)
            df = raw.get(timeframe)
            if df is None:
                return {"candles": 0, "analyses_new": 0, "resolved": 0}

            for tf, frame in raw.items():
                rows = [
                    {
                        "open_time": row.open_time.isoformat(),
                        "open": float(row.open),
                        "high": float(row.high),
                        "low": float(row.low),
                        "close": float(row.close),
                        "volume": float(row.volume),
                    }
                    for row in frame.tail(min(len(frame), 250)).itertuples(index=False)
                ]
                saved_candles += self.store.save_candles(symbol, mode, tf, rows)

            threshold = settings.scalp_min_confidence if mode == "SCALP" else settings.swing_min_confidence
            setups = (
                score_long_setup(symbol, df, mode, timeframe, contexts),
                score_short_setup(symbol, df, mode, timeframe, contexts),
            )
            for setup in setups:
                if setup is None or setup.confidence < threshold:
                    continue
                features = latest_features(df, setup.side)
                feature_dict = {} if features is None else {k: float(v) for k, v in features.to_dict().items()}
                _, inserted = self.store.save_analysis(setup, feature_dict)
                saved_analyses += int(inserted)

            resolved += self.store.resolve_open_outcomes(symbol, mode, timeframe)
        except Exception:
            pass
        return {"candles": saved_candles, "analyses_new": saved_analyses, "resolved": resolved}

    async def collect_mode(self, mode: str) -> dict[str, int]:
        mode = mode.upper()
        batches = await asyncio.gather(
            *(self._collect_symbol(mode, symbol) for symbol in settings.symbol_list),
        )
        return {
            "candles": sum(x["candles"] for x in batches),
            "analyses_new": sum(x["analyses_new"] for x in batches),
            "resolved": sum(x["resolved"] for x in batches),
        }

    async def run_forever(self) -> None:
        self.running = True
        while self.running:
            await asyncio.gather(
                self.collect_mode("SCALP"),
                self.collect_mode("SWING"),
            )

            now = time.monotonic()
            if settings.github_sync_enabled and settings.github_sync_token and now - self.last_github_sync >= settings.github_sync_interval_seconds:
                try:
                    await asyncio.to_thread(sync_analysis_archive)
                except Exception:
                    pass
                self.last_github_sync = now

            await asyncio.sleep(settings.collector_interval_seconds)

    def start(self) -> None:
        if self.task and not self.task.done():
            return
        self.task = asyncio.create_task(self.run_forever(), name="tradenex-live-collector")

    async def stop(self) -> None:
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None


from .config import settings
from .multi_timeframe import fetch_contexts

collector = LiveCollector()
