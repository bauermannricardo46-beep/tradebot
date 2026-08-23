from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any


class TradeDataStore:
    def __init__(self, root: str = "data") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "tradebot.db"
        self.lock = Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self.lock, self._connect() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS market_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    collected_at TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    open_time TEXT NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume REAL NOT NULL,
                    UNIQUE(symbol, mode, timeframe, open_time)
                );
                CREATE TABLE IF NOT EXISTS analysis_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analyzed_at TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    side TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    confidence INTEGER NOT NULL,
                    probability REAL NOT NULL,
                    expected_value_r REAL NOT NULL,
                    model_ready INTEGER NOT NULL,
                    model_version TEXT NOT NULL,
                    entry REAL NOT NULL,
                    stop_loss REAL NOT NULL,
                    take_profit_1 REAL NOT NULL,
                    take_profit_2 REAL NOT NULL,
                    risk_reward REAL NOT NULL,
                    reasons_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS outcome_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id INTEGER NOT NULL UNIQUE,
                    status TEXT NOT NULL DEFAULT 'OPEN',
                    resolved_at TEXT,
                    result TEXT,
                    pnl_r REAL,
                    exit_price REAL,
                    FOREIGN KEY(analysis_id) REFERENCES analysis_snapshots(id)
                );
                CREATE INDEX IF NOT EXISTS idx_market_lookup ON market_snapshots(symbol, mode, timeframe, open_time);
                CREATE INDEX IF NOT EXISTS idx_analysis_time ON analysis_snapshots(analyzed_at);
                CREATE INDEX IF NOT EXISTS idx_analysis_setup ON analysis_snapshots(symbol, mode, side, analyzed_at);
                CREATE INDEX IF NOT EXISTS idx_outcome_status ON outcome_tracking(status);
                """
            )

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def save_candles(self, symbol: str, mode: str, timeframe: str, rows: list[dict[str, Any]]) -> int:
        inserted = 0
        with self.lock, self._connect() as conn:
            for row in rows:
                cur = conn.execute(
                    """
                    INSERT OR IGNORE INTO market_snapshots
                    (collected_at, symbol, mode, timeframe, open_time, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (self._now(), symbol, mode, timeframe, row['open_time'], row['open'], row['high'], row['low'], row['close'], row['volume']),
                )
                inserted += cur.rowcount
        return inserted

    def save_analysis(self, setup: Any, status: str = "OPEN") -> int:
        with self.lock, self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO analysis_snapshots
                (analyzed_at, symbol, mode, side, timeframe, confidence, probability,
                 expected_value_r, model_ready, model_version, entry, stop_loss,
                 take_profit_1, take_profit_2, risk_reward, reasons_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (self._now(), setup.symbol, setup.mode, setup.side, setup.timeframe, setup.confidence,
                 setup.probability, setup.expected_value_r, int(setup.model_ready), setup.model_version,
                 setup.entry, setup.stop_loss, setup.take_profit_1, setup.take_profit_2,
                 setup.risk_reward, json.dumps(setup.reasons, ensure_ascii=False)),
            )
            analysis_id = int(cur.lastrowid)
            conn.execute("INSERT INTO outcome_tracking (analysis_id, status) VALUES (?, ?)", (analysis_id, status))
            return analysis_id

    def resolve_open_outcomes(self, symbol: str, mode: str, timeframe: str) -> int:
        resolved = 0
        with self.lock, self._connect() as conn:
            open_rows = conn.execute(
                """
                SELECT a.*, o.id AS outcome_id
                FROM analysis_snapshots a
                JOIN outcome_tracking o ON o.analysis_id = a.id
                WHERE o.status='OPEN' AND a.symbol=? AND a.mode=? AND a.timeframe=?
                ORDER BY a.id ASC
                """,
                (symbol, mode, timeframe),
            ).fetchall()

            for analysis in open_rows:
                candles = conn.execute(
                    """
                    SELECT * FROM market_snapshots
                    WHERE symbol=? AND mode=? AND timeframe=? AND open_time>?
                    ORDER BY open_time ASC
                    """,
                    (symbol, mode, timeframe, analysis['analyzed_at']),
                ).fetchall()
                for candle in candles:
                    side = analysis['side']
                    stop = float(analysis['stop_loss'])
                    target = float(analysis['take_profit_1'])
                    entry = float(analysis['entry'])
                    if side == 'LONG':
                        hit_stop = float(candle['low']) <= stop
                        hit_target = float(candle['high']) >= target
                    else:
                        hit_stop = float(candle['high']) >= stop
                        hit_target = float(candle['low']) <= target

                    if hit_stop and hit_target:
                        result, exit_price = 'LOSS_STOP_FIRST', stop
                    elif hit_stop:
                        result, exit_price = 'LOSS_STOP', stop
                    elif hit_target:
                        result, exit_price = 'WIN_TP1', target
                    else:
                        continue

                    risk = abs(stop - entry)
                    pnl_r = ((exit_price - entry) if side == 'LONG' else (entry - exit_price)) / risk if risk else 0.0
                    conn.execute(
                        "UPDATE outcome_tracking SET status='RESOLVED', resolved_at=?, result=?, pnl_r=?, exit_price=? WHERE id=?",
                        (self._now(), result, pnl_r, exit_price, analysis['outcome_id']),
                    )
                    resolved += 1
                    break
        return resolved

    def stats(self) -> dict[str, int]:
        with self.lock, self._connect() as conn:
            return {
                "candles": int(conn.execute("SELECT COUNT(*) FROM market_snapshots").fetchone()[0]),
                "analyses": int(conn.execute("SELECT COUNT(*) FROM analysis_snapshots").fetchone()[0]),
                "open_outcomes": int(conn.execute("SELECT COUNT(*) FROM outcome_tracking WHERE status='OPEN'").fetchone()[0]),
                "resolved_outcomes": int(conn.execute("SELECT COUNT(*) FROM outcome_tracking WHERE status='RESOLVED'").fetchone()[0]),
                "wins": int(conn.execute("SELECT COUNT(*) FROM outcome_tracking WHERE result='WIN_TP1'").fetchone()[0]),
                "losses": int(conn.execute("SELECT COUNT(*) FROM outcome_tracking WHERE result LIKE 'LOSS_%'").fetchone()[0]),
            }

    def recent_analyses(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM analysis_snapshots ORDER BY id DESC LIMIT ?", (max(1, min(limit, 500)),)
            ).fetchall()
            return [dict(row) for row in rows]


store = TradeDataStore()
