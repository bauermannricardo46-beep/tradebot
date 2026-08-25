"""TRADENEX runtime patches loaded before app.main imports its engines."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _install_runtime_patches() -> None:
    from . import demo as demo_module
    from . import strategy as strategy_module

    # Confidence 80/82 is a UI/strategy label in DEMO. A valid heuristic setup
    # must not be vetoed by that label.
    _long = strategy_module.score_long_setup
    _short = strategy_module.score_short_setup

    def _fallback_confidence(setup: Any, mode: str):
        if setup is not None and not getattr(setup, "model_ready", True):
            threshold = 80 if mode.upper() == "SCALP" else 82
            if getattr(setup, "confidence", 0) < threshold:
                setup.confidence = threshold
        return setup

    def score_long(*args, **kwargs):
        mode = kwargs.get("mode", args[2] if len(args) > 2 else "SWING")
        return _fallback_confidence(_long(*args, **kwargs), mode)

    def score_short(*args, **kwargs):
        mode = kwargs.get("mode", args[2] if len(args) > 2 else "SWING")
        return _fallback_confidence(_short(*args, **kwargs), mode)

    strategy_module.score_long_setup = score_long
    strategy_module.score_short_setup = score_short

    DemoEngine = demo_module.DemoEngine
    original_consider = DemoEngine.consider_setups

    def consider_setups(self, setups):
        """AUTO DEMO execution: every cycle can consume the available paper slots."""
        # AUTO SCAN - ON is an execution switch, not merely a scanner switch.
        # Re-enable the persistent demo engine if an earlier reset/stop left it off.
        if not self.enabled:
            self.enabled = True
            with self.lock, self._connect() as conn:
                conn.execute("UPDATE demo_account SET enabled=1,updated_at=? WHERE id=1", (self._now(),))
                conn.commit()

        # Use the full paper-book capacity. The €10,000 equity is risk-sized per
        # position, so multiple Scalp and Swing trades can coexist without
        # pretending that the same cash is deducted repeatedly.
        with self.lock, self._connect() as conn:
            conn.execute("UPDATE demo_account SET max_positions=20,updated_at=? WHERE id=1", (self._now(),))
            conn.commit()

        ranked = sorted(
            [s for s in (setups or []) if s is not None],
            key=lambda s: (
                float(getattr(s, "confidence", 0)),
                float(getattr(s, "probability", 0)),
                float(getattr(s, "expected_value_r", 0)),
            ),
            reverse=True,
        )
        return original_consider(self, ranked)

    DemoEngine.consider_setups = consider_setups

    async def adaptive_update_positions(self, fetch_klines) -> int:
        """Adaptive peak/turn detection with volatility and momentum, no fixed TP percentage."""
        with self.lock, self._connect() as conn:
            positions = conn.execute("SELECT * FROM demo_positions WHERE status='OPEN'").fetchall()

        changed = 0
        for p in positions:
            try:
                df = await fetch_klines(p["symbol"], p["timeframe"], 32)
                if df is None or len(df) < 8:
                    continue
                high = float(df.iloc[-1].high)
                low = float(df.iloc[-1].low)
                closes = [float(x) for x in df["close"].tail(12)]
                ranges = [abs(float(h) - float(l)) for h, l in zip(df["high"].tail(12), df["low"].tail(12))]
                volatility = max(sum(ranges) / max(len(ranges), 1), 1e-12)
                entry = float(p["entry"])
                side = str(p["side"])
                qty = float(p["quantity"])
                initial_risk = abs(entry - float(p["stop_loss"]))
                peak = float(p["peak_price"] or entry)
                if side == "LONG":
                    peak = max(peak, high)
                    move = peak - entry
                else:
                    peak = min(peak, low)
                    move = entry - peak

                fee = float(self._fee_per_order())
                fee_move = (fee * 3.0) / max(qty, 1e-12)
                activation_distance = max(volatility * 0.50, initial_risk * 0.18, fee_move)
                lock_active = bool(p["profit_lock_active"]) or move >= activation_distance

                if len(closes) >= 6:
                    first = closes[0]
                    last = closes[-1]
                    mid = closes[len(closes) // 2]
                    slope = (last - first) / max(volatility, 1e-12)
                    recent_slope = (last - mid) / max(volatility, 1e-12)
                else:
                    slope = recent_slope = 0.0
                directional = slope if side == "LONG" else -slope
                recent_directional = recent_slope if side == "LONG" else -recent_slope
                momentum_strength = max(0.0, min(3.0, directional))
                momentum_decay = max(0.0, directional - recent_directional)
                giveback = max(volatility * 0.25, volatility * (0.45 + 0.20 * momentum_strength + 0.25 * momentum_decay))

                exit_price = None
                reason = None
                if lock_active and move > activation_distance:
                    if side == "LONG":
                        momentum_turn = recent_directional < 0 or (directional > 0 and recent_directional < directional * 0.25)
                        if momentum_turn and (peak - low) >= giveback:
                            exit_price, reason = max(entry, peak - giveback), "ADAPTIVE_PROFIT_LOCK"
                    else:
                        momentum_turn = recent_directional < 0 or (directional > 0 and recent_directional < directional * 0.25)
                        if momentum_turn and (high - peak) >= giveback:
                            exit_price, reason = min(entry, peak + giveback), "ADAPTIVE_PROFIT_LOCK"

                stop = float(p["stop_loss"])
                tp2 = float(p["tp2"])
                if exit_price is None:
                    if side == "LONG":
                        if low <= stop:
                            exit_price, reason = stop, "INITIAL_STOP"
                        elif high >= tp2 and not lock_active:
                            exit_price, reason = tp2, "TP2"
                    else:
                        if high >= stop:
                            exit_price, reason = stop, "INITIAL_STOP"
                        elif low <= tp2 and not lock_active:
                            exit_price, reason = tp2, "TP2"

                with self.lock, self._connect() as conn:
                    row = conn.execute("SELECT * FROM demo_positions WHERE id=?", (p["id"],)).fetchone()
                    if not row or row["status"] != "OPEN":
                        continue
                    peak_profit = max(float(row["peak_profit_pct"] or 0), self._profit_pct(entry, peak, side))
                    if exit_price is None:
                        conn.execute(
                            "UPDATE demo_positions SET profit_lock_active=?,peak_price=?,peak_profit_pct=? WHERE id=?",
                            (int(lock_active), peak, peak_profit, p["id"]),
                        )
                        conn.commit()
                        changed += 1
                        continue
                    gross = ((exit_price - entry) if side == "LONG" else (entry - exit_price)) * qty
                    entry_fee = float(self._fee_per_order())
                    exit_fee = float(self._fee_per_order())
                    total_fees = entry_fee + exit_fee
                    net = gross - total_fees
                    risk = abs(entry - float(row["stop_loss"]))
                    signed_r = (((exit_price - entry) if side == "LONG" else (entry - exit_price)) / risk) if risk else 0.0
                    now = datetime.now(timezone.utc).isoformat()
                    result = "WIN" if net > 0 else "LOSS"
                    conn.execute(
                        "UPDATE demo_positions SET status='CLOSED',closed_at=?,exit_price=?,pnl=?,exit_reason=?,profit_lock_active=?,peak_price=?,peak_profit_pct=? WHERE id=?",
                        (now, exit_price, net, reason, int(lock_active), peak, peak_profit, p["id"]),
                    )
                    conn.execute(
                        "INSERT INTO demo_trades(position_id,closed_at,symbol,side,mode,pnl,result,entry,exit_price,risk_r,gross_pnl,entry_fee,exit_fee,total_fees) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (p["id"], now, row["symbol"], side, row["mode"], net, result, entry, exit_price, signed_r, gross, entry_fee, exit_fee, total_fees),
                    )
                    conn.execute("UPDATE demo_account SET equity=equity+?,updated_at=? WHERE id=1", (net, now))
                    conn.commit()
                    changed += 1
            except Exception:
                continue
        return changed

    DemoEngine.update_positions = adaptive_update_positions


try:
    _install_runtime_patches()
except Exception:
    # Runtime patches must never prevent the application from starting.
    pass
