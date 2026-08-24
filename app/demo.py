from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any


class DemoEngine:
    """Persistent virtual-money simulator using the live analysis engine."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.lock = Lock()
        self.enabled = False
        self._init_db()
        self.enabled = bool(self.status()["enabled"])

    def _connect(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self.lock, self._connect() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS demo_account (
                id INTEGER PRIMARY KEY CHECK(id=1), starting_budget REAL NOT NULL,
                equity REAL NOT NULL, risk_per_trade REAL NOT NULL DEFAULT 0.005,
                max_positions INTEGER NOT NULL DEFAULT 5, enabled INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS demo_positions (
                id TEXT PRIMARY KEY, symbol TEXT NOT NULL, side TEXT NOT NULL, mode TEXT NOT NULL,
                timeframe TEXT NOT NULL, entry REAL NOT NULL, stop_loss REAL NOT NULL, tp1 REAL NOT NULL,
                tp2 REAL NOT NULL, trailing_stop REAL, trail_distance REAL NOT NULL, quantity REAL NOT NULL,
                tp1_hit INTEGER NOT NULL DEFAULT 0, opened_at TEXT NOT NULL, closed_at TEXT,
                exit_price REAL, pnl REAL, exit_reason TEXT, status TEXT NOT NULL DEFAULT 'OPEN'
            );
            CREATE TABLE IF NOT EXISTS demo_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT, position_id TEXT NOT NULL, closed_at TEXT NOT NULL,
                symbol TEXT NOT NULL, side TEXT NOT NULL, mode TEXT NOT NULL, pnl REAL NOT NULL,
                result TEXT NOT NULL, entry REAL NOT NULL, exit_price REAL NOT NULL, risk_r REAL NOT NULL
            );
            """)
            if conn.execute("SELECT id FROM demo_account WHERE id=1").fetchone() is None:
                conn.execute(
                    "INSERT INTO demo_account(id,starting_budget,equity,risk_per_trade,max_positions,enabled,updated_at) VALUES(1,10000,10000,0.005,5,0,?)",
                    (self._now(),),
                )
            conn.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def configure(self, budget: float, risk_per_trade: float = 0.005, max_positions: int = 5) -> dict[str, Any]:
        if budget <= 0:
            raise ValueError("budget must be > 0")
        if not 0.001 <= risk_per_trade <= 0.03:
            raise ValueError("risk_per_trade must be between 0.1% and 3%")
        if not 1 <= max_positions <= 20:
            raise ValueError("max_positions must be between 1 and 20")
        with self.lock, self._connect() as conn:
            if conn.execute("SELECT COUNT(*) FROM demo_positions WHERE status='OPEN'").fetchone()[0]:
                raise ValueError("stop or reset the demo before changing its budget")
            conn.execute(
                "UPDATE demo_account SET starting_budget=?,equity=?,risk_per_trade=?,max_positions=?,updated_at=? WHERE id=1",
                (budget, budget, risk_per_trade, max_positions, self._now()),
            )
            conn.commit()
        return self.status()

    def set_enabled(self, enabled: bool) -> dict[str, Any]:
        with self.lock, self._connect() as conn:
            conn.execute("UPDATE demo_account SET enabled=?,updated_at=? WHERE id=1", (int(enabled), self._now()))
            conn.commit()
        self.enabled = enabled
        return self.status()

    def reset(self) -> dict[str, Any]:
        with self.lock, self._connect() as conn:
            row = conn.execute("SELECT starting_budget FROM demo_account WHERE id=1").fetchone()
            budget = float(row[0]) if row else 10000.0
            conn.execute("DELETE FROM demo_positions")
            conn.execute("DELETE FROM demo_trades")
            conn.execute("UPDATE demo_account SET equity=?,enabled=0,updated_at=? WHERE id=1", (budget, self._now()))
            conn.commit()
        self.enabled = False
        return self.status()

    def _account(self, conn):
        return conn.execute("SELECT * FROM demo_account WHERE id=1").fetchone()

    def consider_setup(self, setup: Any) -> bool:
        with self.lock, self._connect() as conn:
            account = self._account(conn)
            if not account or not account["enabled"]:
                return False
            if conn.execute("SELECT COUNT(*) FROM demo_positions WHERE status='OPEN'").fetchone()[0] >= account["max_positions"]:
                return False
            if conn.execute("SELECT 1 FROM demo_positions WHERE status='OPEN' AND symbol=? AND side=? AND mode=?", (setup.symbol, setup.side, setup.mode)).fetchone():
                return False
            distance = abs(float(setup.entry) - float(setup.stop_loss))
            if distance <= 0:
                return False
            risk_amount = float(account["equity"]) * float(account["risk_per_trade"])
            quantity = min(risk_amount / distance, float(account["equity"]) / float(setup.entry))
            if quantity <= 0:
                return False
            import uuid
            trail_distance = distance * (0.8 if setup.mode == "SCALP" else 1.0)
            conn.execute(
                "INSERT INTO demo_positions(id,symbol,side,mode,timeframe,entry,stop_loss,tp1,tp2,trailing_stop,trail_distance,quantity,opened_at,status) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?, 'OPEN')",
                (str(uuid.uuid4()), setup.symbol, setup.side, setup.mode, setup.timeframe, setup.entry, setup.stop_loss, setup.take_profit_1, setup.take_profit_2, setup.trailing_stop, trail_distance, quantity, self._now()),
            )
            conn.commit()
            return True

    async def update_positions(self, fetch_klines) -> int:
        with self.lock, self._connect() as conn:
            positions = conn.execute("SELECT * FROM demo_positions WHERE status='OPEN'").fetchall()
        changed = 0
        for p in positions:
            try:
                df = await fetch_klines(p["symbol"], p["timeframe"], 3)
                if not df.empty:
                    c = df.iloc[-1]
                    self._apply_candle(p, float(c.high), float(c.low))
                    changed += 1
            except Exception:
                continue
        return changed

    def _apply_candle(self, p, high: float, low: float) -> None:
        with self.lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM demo_positions WHERE id=?", (p["id"],)).fetchone()
            if not row or row["status"] != "OPEN":
                return
            side = row["side"]
            tp1_hit = bool(row["tp1_hit"])
            stop = float(row["stop_loss"])
            trailing = row["trailing_stop"]
            trail = float(row["trail_distance"])
            entry = float(row["entry"])
            exit_price = None
            reason = None

            if side == "LONG":
                if high >= float(row["tp1"]):
                    tp1_hit = True
                if tp1_hit:
                    trailing = max(float(trailing or entry), high - trail)
                    stop = max(stop, trailing)
                if high >= float(row["tp2"]):
                    exit_price, reason = float(row["tp2"]), "TP2"
                elif low <= stop:
                    exit_price, reason = stop, ("TRAILING_STOP" if tp1_hit else "INITIAL_STOP")
            else:
                if low <= float(row["tp1"]):
                    tp1_hit = True
                if tp1_hit:
                    trailing = min(float(trailing or entry), low + trail)
                    stop = min(stop, trailing)
                if low <= float(row["tp2"]):
                    exit_price, reason = float(row["tp2"]), "TP2"
                elif high >= stop:
                    exit_price, reason = stop, ("TRAILING_STOP" if tp1_hit else "INITIAL_STOP")

            if exit_price is None:
                conn.execute("UPDATE demo_positions SET stop_loss=?,trailing_stop=?,tp1_hit=? WHERE id=?", (stop, trailing, int(tp1_hit), row["id"]))
                conn.commit()
                return

            qty = float(row["quantity"])
            pnl = ((exit_price - entry) if side == "LONG" else (entry - exit_price)) * qty
            risk_distance = abs(entry - float(row["stop_loss"]))
            signed_r = ((exit_price - entry) if side == "LONG" else (entry - exit_price)) / risk_distance if risk_distance else 0.0
            result = "WIN" if pnl > 0 else "LOSS"
            now = self._now()
            conn.execute("UPDATE demo_positions SET status='CLOSED',closed_at=?,exit_price=?,pnl=?,exit_reason=?,stop_loss=?,trailing_stop=?,tp1_hit=? WHERE id=?", (now, exit_price, pnl, reason, stop, trailing, int(tp1_hit), row["id"]))
            conn.execute("INSERT INTO demo_trades(position_id,closed_at,symbol,side,mode,pnl,result,entry,exit_price,risk_r) VALUES(?,?,?,?,?,?,?,?,?,?)", (row["id"], now, row["symbol"], side, row["mode"], pnl, result, entry, exit_price, signed_r))
            conn.execute("UPDATE demo_account SET equity=equity+?,updated_at=? WHERE id=1", (pnl, now))
            conn.commit()

    def status(self) -> dict[str, Any]:
        with self.lock, self._connect() as conn:
            a = self._account(conn)
            total = int(conn.execute("SELECT COUNT(*) FROM demo_trades").fetchone()[0])
            wins = int(conn.execute("SELECT COUNT(*) FROM demo_trades WHERE pnl > 0").fetchone()[0])
            losses = int(conn.execute("SELECT COUNT(*) FROM demo_trades WHERE pnl < 0").fetchone()[0])
            gross_profit = float(conn.execute("SELECT COALESCE(SUM(pnl),0) FROM demo_trades WHERE pnl > 0").fetchone()[0])
            gross_loss = float(conn.execute("SELECT COALESCE(SUM(pnl),0) FROM demo_trades WHERE pnl < 0").fetchone()[0])
            net = gross_profit + gross_loss
            open_positions = int(conn.execute("SELECT COUNT(*) FROM demo_positions WHERE status='OPEN'").fetchone()[0])
            budget = float(a["starting_budget"])
            return {
                "enabled": bool(a["enabled"]), "budget": budget, "equity": float(a["equity"]),
                "pnl": net, "pnl_pct": net / budget * 100 if budget else 0.0,
                "gross_profit": gross_profit, "gross_loss": gross_loss, "net_pnl": net,
                "trades": total, "closed_trades": total, "wins": wins, "losses": losses,
                "win_rate": wins / total * 100 if total else 0.0,
                "risk_per_trade": float(a["risk_per_trade"]), "max_positions": int(a["max_positions"]),
                "open_positions": open_positions, "updated_at": a["updated_at"],
            }

    def open_positions(self) -> list[dict[str, Any]]:
        with self.lock, self._connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM demo_positions WHERE status='OPEN' ORDER BY opened_at DESC").fetchall()]

    def trades(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.lock, self._connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM demo_trades ORDER BY id DESC LIMIT ?", (max(1, min(limit, 500)),)).fetchall()]
