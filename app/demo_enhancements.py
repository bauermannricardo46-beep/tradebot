from __future__ import annotations

from typing import Any

from .config import settings
from .demo import DemoEngine


class EnhancedDemoEngine(DemoEngine):
    """Demo extensions: fixed fees and custom peak-aware profit lock."""

    def __init__(self, db_path):
        super().__init__(db_path)
        self._migrate()

    def _migrate(self) -> None:
        with self.lock, self._connect() as conn:
            position_cols = {row[1] for row in conn.execute("PRAGMA table_info(demo_positions)").fetchall()}
            trade_cols = {row[1] for row in conn.execute("PRAGMA table_info(demo_trades)").fetchall()}
            for name, definition in {
                "profit_lock_active": "INTEGER NOT NULL DEFAULT 0",
                "peak_price": "REAL",
                "peak_profit_pct": "REAL NOT NULL DEFAULT 0",
            }.items():
                if name not in position_cols:
                    conn.execute(f"ALTER TABLE demo_positions ADD COLUMN {name} {definition}")
            for name, definition in {
                "gross_pnl": "REAL NOT NULL DEFAULT 0",
                "entry_fee": "REAL NOT NULL DEFAULT 0",
                "exit_fee": "REAL NOT NULL DEFAULT 0",
                "total_fees": "REAL NOT NULL DEFAULT 0",
            }.items():
                if name not in trade_cols:
                    conn.execute(f"ALTER TABLE demo_trades ADD COLUMN {name} {definition}")
            conn.commit()

    @staticmethod
    def _fee_per_order() -> float:
        return float(
            settings.hyperliquid_maker_fee
            if str(settings.demo_fee_type).upper() == "MAKER"
            else settings.hyperliquid_taker_fee
        )

    @staticmethod
    def _profit_pct(entry: float, price: float, side: str) -> float:
        if entry <= 0:
            return 0.0
        if side == "LONG":
            return (price - entry) / entry * 100.0
        return (entry - price) / entry * 100.0

    def _apply_candle(self, p, high: float, low: float) -> None:
        """Custom software profit lock: activate at a profit threshold and exit on peak retracement."""
        with self.lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM demo_positions WHERE id=?", (p["id"],)).fetchone()
            if not row or row["status"] != "OPEN":
                return

            side = row["side"]
            entry = float(row["entry"])
            stop = float(row["stop_loss"])
            tp2 = float(row["tp2"])
            lock_active = bool(row["profit_lock_active"])
            old_peak = row["peak_price"]
            peak = float(old_peak) if old_peak is not None else entry
            peak_profit = float(row["peak_profit_pct"] or 0.0)
            activation = float(settings.scalp_profit_lock_activation_pct if row["mode"] == "SCALP" else settings.swing_profit_lock_activation_pct)
            retracement = float(settings.scalp_profit_lock_retracement_pct if row["mode"] == "SCALP" else settings.swing_profit_lock_retracement_pct)

            if side == "LONG":
                peak = max(peak, high)
                peak_profit = max(peak_profit, self._profit_pct(entry, peak, side))
                if peak_profit >= activation:
                    lock_active = True
                    locked_profit = max(activation, peak_profit - retracement)
                    stop = max(stop, entry * (1.0 + locked_profit / 100.0))
                exit_price = None
                reason = None
                if lock_active and low <= peak * (1.0 - retracement / 100.0):
                    exit_price, reason = max(stop, peak * (1.0 - retracement / 100.0)), "DYNAMIC_PROFIT_LOCK"
                elif high >= tp2:
                    exit_price, reason = tp2, "TP2"
                elif low <= stop:
                    exit_price, reason = stop, "INITIAL_STOP"
            else:
                peak = min(peak, low) if old_peak is not None else low
                peak_profit = max(peak_profit, self._profit_pct(entry, peak, side))
                if peak_profit >= activation:
                    lock_active = True
                    locked_profit = max(activation, peak_profit - retracement)
                    stop = min(stop, entry * (1.0 - locked_profit / 100.0))
                exit_price = None
                reason = None
                if lock_active and high >= peak * (1.0 + retracement / 100.0):
                    exit_price, reason = min(stop, peak * (1.0 + retracement / 100.0)), "DYNAMIC_PROFIT_LOCK"
                elif low <= tp2:
                    exit_price, reason = tp2, "TP2"
                elif high >= stop:
                    exit_price, reason = stop, "INITIAL_STOP"

            if exit_price is None:
                conn.execute(
                    "UPDATE demo_positions SET stop_loss=?,trailing_stop=?,profit_lock_active=?,peak_price=?,peak_profit_pct=? WHERE id=?",
                    (stop, stop if lock_active else row["trailing_stop"], int(lock_active), peak, peak_profit, row["id"]),
                )
                conn.commit()
                return

            qty = float(row["quantity"])
            gross_pnl = ((exit_price - entry) if side == "LONG" else (entry - exit_price)) * qty
            entry_fee = self._fee_per_order()
            exit_fee = self._fee_per_order()
            total_fees = entry_fee + exit_fee
            net_pnl = gross_pnl - total_fees
            risk_distance = abs(entry - float(row["stop_loss"]))
            signed_r = ((exit_price - entry) if side == "LONG" else (entry - exit_price)) / risk_distance if risk_distance else 0.0
            result = "WIN" if net_pnl > 0 else "LOSS"
            now = self._now()
            conn.execute(
                "UPDATE demo_positions SET status='CLOSED',closed_at=?,exit_price=?,pnl=?,exit_reason=?,stop_loss=?,trailing_stop=?,profit_lock_active=?,peak_price=?,peak_profit_pct=? WHERE id=?",
                (now, exit_price, net_pnl, reason, stop, stop if lock_active else row["trailing_stop"], int(lock_active), peak, peak_profit, row["id"]),
            )
            conn.execute(
                "INSERT INTO demo_trades(position_id,closed_at,symbol,side,mode,pnl,result,entry,exit_price,risk_r,gross_pnl,entry_fee,exit_fee,total_fees) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (row["id"], now, row["symbol"], side, row["mode"], net_pnl, result, entry, exit_price, signed_r, gross_pnl, entry_fee, exit_fee, total_fees),
            )
            conn.execute("UPDATE demo_account SET equity=equity+?,updated_at=? WHERE id=1", (net_pnl, now))
            conn.commit()

    def journal(self, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 500))
        with self.lock, self._connect() as conn:
            rows = conn.execute(
                """SELECT p.id AS position_id,p.opened_at,p.closed_at,p.symbol,p.side,p.mode,p.timeframe,p.entry,p.exit_price,p.pnl,p.status,
                CASE WHEN p.status='OPEN' THEN 'OPEN' WHEN p.pnl > 0 THEN 'WIN' ELSE 'LOSS' END AS result,
                CASE WHEN p.status='OPEN' THEN NULL ELSE t.risk_r END AS risk_r,p.exit_reason,p.stop_loss,p.tp1,p.tp2,p.trailing_stop,p.quantity,
                t.gross_pnl,t.entry_fee,t.exit_fee,t.total_fees
                FROM demo_positions p LEFT JOIN demo_trades t ON t.position_id=p.id
                ORDER BY COALESCE(p.closed_at,p.opened_at) DESC LIMIT ?""",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
