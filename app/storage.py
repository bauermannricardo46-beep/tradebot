from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any


class TradeDataStore:
    """Persistent market/analysis/outcome store with safe schema migration."""

    def __init__(self, root: str = "data") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "tradebot.db"
        self.lock = Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _ensure_column(self, conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

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
                    source_open_time TEXT,
                    signal_key TEXT,
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
                    swing_high REAL,
                    swing_low REAL,
                    fib_382 REAL,
                    fib_500 REAL,
                    fib_618 REAL,
                    fib_786 REAL,
                    trailing_stop REAL,
                    analysis_timeframes_json TEXT,
                    reasons_json TEXT NOT NULL,
                    features_json TEXT
                );
                CREATE TABLE IF NOT EXISTS outcome_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id INTEGER NOT NULL UNIQUE,
                    status TEXT NOT NULL DEFAULT 'OPEN',
                    resolved_at TEXT,
                    result TEXT,
                    exit_price REAL,
                    pnl_r REAL,
                    tp1_hit INTEGER NOT NULL DEFAULT 0,
                    max_favorable_r REAL NOT NULL DEFAULT 0,
                    max_adverse_r REAL NOT NULL DEFAULT 0,
                    trailing_stop REAL,
                    candles_observed INTEGER NOT NULL DEFAULT 0,
                    last_checked_open_time TEXT,
                    FOREIGN KEY(analysis_id) REFERENCES analysis_snapshots(id)
                );
                """
            )

            for column, definition in {
                "source_open_time": "TEXT",
                "signal_key": "TEXT",
                "swing_high": "REAL",
                "swing_low": "REAL",
                "fib_382": "REAL",
                "fib_500": "REAL",
                "fib_618": "REAL",
                "fib_786": "REAL",
                "trailing_stop": "REAL",
                "analysis_timeframes_json": "TEXT",
                "features_json": "TEXT",
            }.items():
                self._ensure_column(conn, "analysis_snapshots", column, definition)

            for column, definition in {
                "exit_price": "REAL",
                "pnl_r": "REAL",
                "tp1_hit": "INTEGER NOT NULL DEFAULT 0",
                "max_favorable_r": "REAL NOT NULL DEFAULT 0",
                "max_adverse_r": "REAL NOT NULL DEFAULT 0",
                "trailing_stop": "REAL",
                "candles_observed": "INTEGER NOT NULL DEFAULT 0",
                "last_checked_open_time": "TEXT",
            }.items():
                self._ensure_column(conn, "outcome_tracking", column, definition)

            conn.execute("UPDATE analysis_snapshots SET signal_key='legacy:' || id WHERE signal_key IS NULL")
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_analysis_signal_key ON analysis_snapshots(signal_key)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_market_lookup ON market_snapshots(symbol, mode, timeframe, open_time)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_analysis_time ON analysis_snapshots(analyzed_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_analysis_signal ON analysis_snapshots(symbol, mode, side, timeframe, source_open_time)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_outcome_status ON outcome_tracking(status)")

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
                    (self._now(), symbol, mode, timeframe, row["open_time"], row["open"], row["high"], row["low"], row["close"], row["volume"]),
                )
                inserted += max(0, cur.rowcount)
        return inserted

    def save_analysis(self, setup: Any, features: dict[str, Any] | None = None) -> tuple[int, bool]:
        source_open_time = setup.source_open_time.isoformat() if getattr(setup, "source_open_time", None) else None
        source_key = source_open_time or self._now()
        signal_key = f"{setup.symbol}:{setup.mode}:{setup.side}:{setup.timeframe}:{source_key}"

        with self.lock, self._connect() as conn:
            existing = conn.execute("SELECT id FROM analysis_snapshots WHERE signal_key=?", (signal_key,)).fetchone()
            if existing:
                return int(existing[0]), False

            cur = conn.execute(
                """
                INSERT INTO analysis_snapshots
                (analyzed_at, symbol, mode, side, timeframe, source_open_time, signal_key,
                 confidence, probability, expected_value_r, model_ready, model_version,
                 entry, stop_loss, take_profit_1, take_profit_2, risk_reward,
                 swing_high, swing_low, fib_382, fib_500, fib_618, fib_786, trailing_stop,
                 analysis_timeframes_json, reasons_json, features_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self._now(), setup.symbol, setup.mode, setup.side, setup.timeframe,
                    source_open_time, signal_key, setup.confidence, setup.probability,
                    setup.expected_value_r, int(setup.model_ready), setup.model_version,
                    setup.entry, setup.stop_loss, setup.take_profit_1, setup.take_profit_2,
                    setup.risk_reward, setup.swing_high, setup.swing_low, setup.fib_382,
                    setup.fib_500, setup.fib_618, setup.fib_786, setup.trailing_stop,
                    json.dumps(setup.analysis_timeframes, ensure_ascii=False),
                    json.dumps(setup.reasons, ensure_ascii=False),
                    json.dumps(features or {}, ensure_ascii=False),
                ),
            )
            analysis_id = int(cur.lastrowid)
            conn.execute("INSERT INTO outcome_tracking (analysis_id, status) VALUES (?, 'OPEN')", (analysis_id,))
            return analysis_id, True

    def resolve_open_outcomes(self, symbol: str, mode: str, timeframe: str) -> int:
        resolved = 0
        with self.lock, self._connect() as conn:
            analyses = conn.execute(
                """
                SELECT a.*, o.id AS outcome_id, o.tp1_hit, o.trailing_stop AS outcome_trailing,
                       o.max_favorable_r, o.max_adverse_r, o.candles_observed, o.last_checked_open_time
                FROM analysis_snapshots a
                JOIN outcome_tracking o ON o.analysis_id=a.id
                WHERE o.status='OPEN' AND a.symbol=? AND a.mode=? AND a.timeframe=?
                ORDER BY a.id ASC
                """,
                (symbol, mode, timeframe),
            ).fetchall()

            for analysis in analyses:
                source = analysis["source_open_time"] or analysis["analyzed_at"]
                last_checked = analysis["last_checked_open_time"] or source
                candles = conn.execute(
                    """
                    SELECT * FROM market_snapshots
                    WHERE symbol=? AND mode=? AND timeframe=? AND open_time>? AND open_time>?
                    ORDER BY open_time ASC
                    """,
                    (symbol, mode, timeframe, source, last_checked),
                ).fetchall()
                if not candles:
                    continue

                side = analysis["side"]
                entry = float(analysis["entry"])
                initial_stop = float(analysis["stop_loss"])
                tp1 = float(analysis["take_profit_1"])
                tp2 = float(analysis["take_profit_2"])
                current_stop = initial_stop
                trailing = analysis["outcome_trailing"]
                tp1_hit = bool(analysis["tp1_hit"])
                highest = entry
                lowest = entry
                max_fav = float(analysis["max_favorable_r"] or 0.0)
                max_adv = float(analysis["max_adverse_r"] or 0.0)
                observed = int(analysis["candles_observed"] or 0)
                risk = abs(entry - initial_stop)
                trail_distance = risk * (0.8 if mode == "SCALP" else 1.0)
                exit_price = None
                exit_reason = None
                last_open_time = last_checked

                for candle in candles:
                    high = float(candle["high"])
                    low = float(candle["low"])
                    highest = max(highest, high)
                    lowest = min(lowest, low)
                    observed += 1
                    last_open_time = candle["open_time"]

                    if risk > 0:
                        if side == "LONG":
                            max_fav = max(max_fav, (high - entry) / risk)
                            max_adv = min(max_adv, (low - entry) / risk)
                        else:
                            max_fav = max(max_fav, (entry - low) / risk)
                            max_adv = min(max_adv, (entry - high) / risk)

                    if side == "LONG":
                        if high >= tp1:
                            tp1_hit = True
                        if tp1_hit:
                            new_trail = max(entry, highest - trail_distance)
                            trailing = max(float(trailing or new_trail), new_trail)
                            current_stop = max(current_stop, float(trailing))
                        hit_stop = low <= current_stop
                        hit_tp2 = high >= tp2
                        if hit_stop:
                            exit_price, exit_reason = current_stop, ("TRAILING_STOP" if tp1_hit else "INITIAL_STOP")
                        elif hit_tp2:
                            exit_price, exit_reason = tp2, "TP2_EXTENDED_MOVE"
                    else:
                        if low <= tp1:
                            tp1_hit = True
                        if tp1_hit:
                            new_trail = min(entry, lowest + trail_distance)
                            trailing = min(float(trailing or new_trail), new_trail)
                            current_stop = min(current_stop, float(trailing))
                        hit_stop = high >= current_stop
                        hit_tp2 = low <= tp2
                        if hit_stop:
                            exit_price, exit_reason = current_stop, ("TRAILING_STOP" if tp1_hit else "INITIAL_STOP")
                        elif hit_tp2:
                            exit_price, exit_reason = tp2, "TP2_EXTENDED_MOVE"

                    if exit_price is not None:
                        break

                if exit_price is not None:
                    pnl_r = (((exit_price - entry) if side == "LONG" else (entry - exit_price)) / risk) if risk else 0.0
                    conn.execute(
                        """
                        UPDATE outcome_tracking
                        SET status='RESOLVED', resolved_at=?, result=?, exit_price=?, pnl_r=?,
                            tp1_hit=?, max_favorable_r=?, max_adverse_r=?, trailing_stop=?,
                            candles_observed=?, last_checked_open_time=? WHERE id=?
                        """,
                        (self._now(), exit_reason, exit_price, pnl_r, int(tp1_hit), max_fav, max_adv, trailing, observed, last_open_time, analysis["outcome_id"]),
                    )
                    resolved += 1
                else:
                    conn.execute(
                        """
                        UPDATE outcome_tracking
                        SET tp1_hit=?, max_favorable_r=?, max_adverse_r=?, trailing_stop=?,
                            candles_observed=?, last_checked_open_time=? WHERE id=?
                        """,
                        (int(tp1_hit), max_fav, max_adv, trailing, observed, last_open_time, analysis["outcome_id"]),
                    )
        return resolved

    def stats(self) -> dict[str, Any]:
        with self.lock, self._connect() as conn:
            total = int(conn.execute("SELECT COUNT(*) FROM outcome_tracking WHERE status='RESOLVED'").fetchone()[0])
            positive = int(conn.execute("SELECT COUNT(*) FROM outcome_tracking WHERE status='RESOLVED' AND pnl_r>0").fetchone()[0])
            avg_r = conn.execute("SELECT AVG(pnl_r) FROM outcome_tracking WHERE status='RESOLVED'").fetchone()[0]
            return {
                "candles": int(conn.execute("SELECT COUNT(*) FROM market_snapshots").fetchone()[0]),
                "analyses": int(conn.execute("SELECT COUNT(*) FROM analysis_snapshots").fetchone()[0]),
                "open_outcomes": int(conn.execute("SELECT COUNT(*) FROM outcome_tracking WHERE status='OPEN'").fetchone()[0]),
                "resolved_outcomes": total,
                "positive_outcomes": positive,
                "losses": int(conn.execute("SELECT COUNT(*) FROM outcome_tracking WHERE status='RESOLVED' AND pnl_r<=0").fetchone()[0]),
                "win_rate": (positive / total) if total else 0.0,
                "average_r": float(avg_r or 0.0),
            }

    def recent_analyses(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT a.*, o.status AS outcome_status, o.result AS outcome_result,
                       o.pnl_r AS outcome_pnl_r, o.exit_price, o.resolved_at,
                       o.max_favorable_r, o.max_adverse_r, o.tp1_hit
                FROM analysis_snapshots a
                LEFT JOIN outcome_tracking o ON o.analysis_id=a.id
                ORDER BY a.id DESC LIMIT ?
                """,
                (max(1, min(limit, 500)),),
            ).fetchall()
            return [dict(row) for row in rows]

    def training_rows(self, limit: int = 10000) -> list[dict[str, Any]]:
        with self.lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT a.symbol, a.mode, a.side, a.timeframe, a.source_open_time,
                       a.confidence, a.probability, a.expected_value_r, a.model_ready,
                       a.model_version, a.entry, a.stop_loss, a.take_profit_1,
                       a.take_profit_2, a.risk_reward, a.swing_high, a.swing_low,
                       a.fib_382, a.fib_500, a.fib_618, a.fib_786,
                       a.features_json, o.result, o.pnl_r, o.max_favorable_r,
                       o.max_adverse_r, o.candles_observed
                FROM analysis_snapshots a
                JOIN outcome_tracking o ON o.analysis_id=a.id
                WHERE o.status='RESOLVED' AND o.pnl_r IS NOT NULL
                ORDER BY a.id DESC LIMIT ?
                """,
                (max(1, min(limit, 100000)),),
            ).fetchall()
            return [dict(row) for row in rows]


store = TradeDataStore()
