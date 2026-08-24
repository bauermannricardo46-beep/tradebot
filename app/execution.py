from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock


class ExecutionMode:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.lock = Lock()
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self.lock, self._connect() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS execution_state (id INTEGER PRIMARY KEY CHECK(id=1), mode TEXT NOT NULL, updated_at TEXT NOT NULL)")
            if conn.execute("SELECT 1 FROM execution_state WHERE id=1").fetchone() is None:
                conn.execute("INSERT INTO execution_state(id,mode,updated_at) VALUES(1,'DEMO',?)", (self._now(),))

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    def get(self):
        with self.lock, self._connect() as conn:
            row = conn.execute("SELECT mode,updated_at FROM execution_state WHERE id=1").fetchone()
            return {"mode": row["mode"] if row else "DEMO", "live_ready": False, "live_status": "LOCKED_UNTIL_EXCHANGE_CONFIGURATION", "updated_at": row["updated_at"] if row else None}

    def set(self, mode: str):
        mode = mode.upper()
        if mode not in {"DEMO", "LIVE"}:
            raise ValueError("mode muss DEMO oder LIVE sein")
        with self.lock, self._connect() as conn:
            conn.execute("UPDATE execution_state SET mode=?,updated_at=? WHERE id=1", (mode, self._now()))
        return self.get()
