"""TRADENEX runtime patches loaded before app.main imports its engines."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _serialize_setup(setup: Any) -> dict[str, Any] | None:
    if setup is None:
        return None
    try:
        data = setup.model_dump()
    except AttributeError:
        data = dict(vars(setup))
    # Keep the API JSON-safe even if a model contains datetime-like values.
    return {str(k): (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in data.items()}


def _install_runtime_patches() -> None:
    from . import demo as demo_module

    DemoEngine = demo_module.DemoEngine
    original_init = DemoEngine.__init__
    original_consider = DemoEngine.consider_setups
    original_status = DemoEngine.status
    original_update_positions = DemoEngine.update_positions

    def init_auto(self, db_path):
        original_init(self, db_path)
        self.latest_setups = []
        self.enabled = True
        with self.lock, self._connect() as conn:
            conn.execute(
                "UPDATE demo_account SET enabled=1,max_positions=20,updated_at=? WHERE id=1",
                (self._now(),),
            )
            conn.commit()

    DemoEngine.__init__ = init_auto

    def consider_setups(self, setups):
        ranked = sorted(
            [s for s in (setups or []) if s is not None],
            key=lambda s: (
                float(getattr(s, "probability", 0)),
                float(getattr(s, "expected_value_r", 0)),
            ),
            reverse=True,
        )
        # Cache the exact scanner result used by the execution loop. The UI can
        # consume this snapshot instead of launching a second full market scan.
        self.latest_setups = ranked
        return original_consider(self, ranked)

    DemoEngine.consider_setups = consider_setups

    def status(self):
        result = original_status(self)
        result["setups"] = [
            item
            for item in (_serialize_setup(s) for s in getattr(self, "latest_setups", []))
            if item is not None
        ]
        return result

    DemoEngine.status = status

    async def adaptive_update_positions(self, fetch_klines) -> int:
        """Dynamic exit: protect profit when momentum reverses, otherwise keep the trade open."""
        with self.lock, self._connect() as conn:
            positions = conn.execute("SELECT * FROM demo_positions WHERE status='OPEN'").fetchall()
        changed = 0
        for p in positions:
            try:
                df = await fetch_klines(p["symbol"], p["timeframe"], 40)
                if df is None or len(df) < 10:
                    continue
                highs = [float(x) for x in df["high"].tail(20)]
                lows = [float(x) for x in df["low"].tail(20)]
                closes = [float(x) for x in df["close"].tail(14)]
                volatility = max(
                    sum(h - l for h, l in zip(highs, lows)) / max(len(highs), 1),
                    1e-12,
                )
                entry = float(p["entry"])
                stop = float(p["stop_loss"])
                side = str(p["side"])
                qty = float(p["quantity"])
                initial_risk = max(abs(entry - stop), volatility * 0.10)
                peak = float(p["peak_price"] or entry)
                current_high = max(highs)
                current_low = min(lows)
                if side == "LONG":
                    peak = max(peak, current_high)
                    peak_move = peak - entry
                else:
                    peak = min(peak, current_low)
                    peak_move = entry - peak

                round_trip_fee = self._fee_for_order(entry * qty) * 2.0
                fee_move = round_trip_fee / max(qty, 1e-12)
                activation = max(volatility * 0.50, initial_risk * 0.18, fee_move)
                lock = bool(p["profit_lock_active"]) or peak_move >= activation

                first, last = closes[0], closes[-1]
                mid = closes[len(closes) // 2]
                full = (last - first) / volatility
                recent = (last - mid) / volatility
                directional = full if side == "LONG" else -full
                recent_directional = recent if side == "LONG" else -recent
                strength = max(0.0, min(3.0, directional))
                decay = max(0.0, directional - recent_directional)
                giveback = max(
                    volatility * 0.20,
                    volatility * (0.35 + 0.18 * strength + 0.22 * decay),
                )

                exit_price = None
                reason = None
                if lock and peak_move > activation:
                    reversal = recent_directional <= 0 or (
                        directional > 0 and recent_directional < directional * 0.25
                    )
                    if side == "LONG" and reversal and peak - current_low >= giveback and peak - giveback > entry:
                        exit_price, reason = peak - giveback, "ADAPTIVE_PROFIT_LOCK"
                    elif side == "SHORT" and reversal and current_high - peak >= giveback and peak + giveback < entry:
                        exit_price, reason = peak + giveback, "ADAPTIVE_PROFIT_LOCK"

                if exit_price is None:
                    if side == "LONG" and current_low <= stop:
                        exit_price, reason = stop, "INITIAL_STOP"
                    elif side == "SHORT" and current_high >= stop:
                        exit_price, reason = stop, "INITIAL_STOP"

                with self.lock, self._connect() as conn:
                    row = conn.execute(
                        "SELECT * FROM demo_positions WHERE id=?", (p["id"],)
                    ).fetchone()
                    if not row or row["status"] != "OPEN":
                        continue
                    peak_profit = max(
                        float(row["peak_profit_pct"] or 0),
                        self._profit_pct(entry, peak, side),
                    )
                    if exit_price is None:
                        conn.execute(
                            "UPDATE demo_positions SET profit_lock_active=?,peak_price=?,peak_profit_pct=? WHERE id=?",
                            (int(lock), peak, peak_profit, p["id"]),
                        )
                        conn.commit()
                        changed += 1
                        continue

                    gross = (
                        ((exit_price - entry) if side == "LONG" else (entry - exit_price))
                        * qty
                    )
                    entry_fee = self._fee_for_order(entry * qty)
                    exit_fee = self._fee_for_order(exit_price * qty)
                    total_fees = entry_fee + exit_fee
                    net = gross - total_fees
                    risk = abs(entry - float(row["stop_loss"]))
                    signed_r = (
                        ((exit_price - entry) if side == "LONG" else (entry - exit_price)) / risk
                        if risk
                        else 0.0
                    )
                    now = datetime.now(timezone.utc).isoformat()
                    result = "WIN" if net > 0 else "LOSS"
                    conn.execute(
                        "UPDATE demo_positions SET status='CLOSED',closed_at=?,exit_price=?,pnl=?,exit_reason=?,profit_lock_active=?,peak_price=?,peak_profit_pct=? WHERE id=?",
                        (now, exit_price, net, reason, int(lock), peak, peak_profit, p["id"]),
                    )
                    conn.execute(
                        "INSERT INTO demo_trades(position_id,closed_at,symbol,side,mode,pnl,result,entry,exit_price,risk_r,gross_pnl,entry_fee,exit_fee,total_fees) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            p["id"], now, row["symbol"], side, row["mode"], net, result,
                            entry, exit_price, signed_r, gross, entry_fee, exit_fee, total_fees,
                        ),
                    )
                    conn.execute(
                        "UPDATE demo_account SET equity=equity+?,updated_at=? WHERE id=1",
                        (net, now),
                    )
                    conn.commit()
                    changed += 1
            except Exception:
                # One bad market-data sample must not stop monitoring all positions.
                continue
        return changed

    DemoEngine.update_positions = adaptive_update_positions


try:
    _install_runtime_patches()
except Exception:
    # Import-time patch failures must never prevent the application package from loading.
    pass
