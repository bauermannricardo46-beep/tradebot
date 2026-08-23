from __future__ import annotations

import json
import sqlite3
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
                CREATE INDEX IF NOT EXISTS idx_analysis_time ON analysis_snapshots(analyzed_at);
                CREATE INDEX IF NOT EXISTS idx_analysis_setup ON analysis_snapshots(symbol, mode, side, analyzed_at);
                """
            )

    def save_candles(self, symbol: str, mode: str, timeframe: str, rows: list[dict[str, Any]]) -> int:
        inserted = 0
        with self.lock, self._connect() as conn:
            for row in rows:
                cur = conn.execute(
                    """
                    INSERT OR IGNORE INTO market_snapshots
                    (collected_at, symbol, mode, timeframe, open_time, open, high, low, close, volume)
                    VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (symbol, mode, timeframe, row['open_time'], row['open'], row['high'], row['low'], row['close'], row['volume']),
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
                VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (setup.symbol, setup.mode, setup.side, setup.timeframe, setup.confidence,
                 setup.probability, setup.expected_value_r, int(setup.model_ready), setup.model_version,
                 setup.entry, setup.stop_loss, setup.take_profit_1, setup.take_profit_2,
                 setup.risk_reward, json.dumps(setup.reasons, ensure_ascii=False)),
            )
            analysis_id = int(cur.lastrowid)
            conn.execute("INSERT INTO outcome_tracking (analysis_id, status) VALUES (?, ?)", (analysis_id, status))
            return analysis_id

    def stats(self) -> dict[str, int]:
        with self.lock, self._connect() as conn:
            return {
                "candles": int(conn.execute("SELECT COUNT(*) FROM market_snapshots").fetchone()[0]),
                "analyses": int(conn.execute("SELECT COUNT(*) FROM analysis_snapshots").fetchone()[0]),
                "open_outcomes": int(conn.execute("SELECT COUNT(*) FROM outcome_tracking WHERE status='OPEN'").fetchone()[0]),
                "resolved_outcomes": int(conn.execute("SELECT COUNT(*) FROM outcome_tracking WHERE status='RESOLVED'").fetchone()[0]),
            }

    def recent_analyses(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM analysis_snapshots ORDER BY id DESC LIMIT ?", (max(1, min(limit, 500)),)
            ).fetchall()
            return [dict(row) for row in rows]


store = TradeDataStore()
