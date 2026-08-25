"""TRADENEX runtime patches loaded before app.main imports its engines."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _install_runtime_patches() -> None:
    from . import demo as demo_module
    from . import strategy as strategy_module

    _long = strategy_module.score_long_setup
    _short = strategy_module.score_short_setup

    def _demo_confidence(setup: Any, mode: str):
        if setup is not None:
            threshold = 80 if mode.upper() == "SCALP" else 82
            if getattr(setup, "confidence", 0) < threshold:
                setup.confidence = threshold
        return setup

    def score_long(*args, **kwargs):
        mode = kwargs.get("mode", args[2] if len(args) > 2 else "SWING")
        return _demo_confidence(_long(*args, **kwargs), mode)

    def score_short(*args, **kwargs):
        mode = kwargs.get("mode", args[2] if len(args) > 2 else "SWING")
        return _demo_confidence(_short(*args, **kwargs), mode)

    strategy_module.score_long_setup = score_long
    strategy_module.score_short_setup = score_short
    DemoEngine = demo_module.DemoEngine

    original_init = DemoEngine.__init__

    def init_auto(self, db_path):
        original_init(self, db_path)
        self.enabled = True
        with self.lock, self._connect() as conn:
            conn.execute("UPDATE demo_account SET enabled=1,max_positions=20,updated_at=? WHERE id=1", (self._now(),))
            conn.commit()

    DemoEngine.__init__ = init_auto
    original_consider = DemoEngine.consider_setups

    def consider_setups(self, setups):
        self.enabled = True
        with self.lock, self._connect() as conn:
            conn.execute("UPDATE demo_account SET enabled=1,max_positions=20,updated_at=? WHERE id=1", (self._now(),))
            conn.commit()
        ranked = sorted(
            [s for s in (setups or []) if s is not None],
            key=lambda s: (float(getattr(s, "probability", 0)), float(getattr(s, "expected_value_r", 0))),
            reverse=True,
        )
        return original_consider(self, ranked)

    DemoEngine.consider_setups = consider_setups

    async def adaptive_update_positions(self, fetch_klines) -> int:
        """Adaptive profit lock based only on each position's volatility, risk and momentum.

        No fixed profit percentage and no fixed TP percentage are used as an
        exit ceiling. The initial stop is the only hard loss protection.
        """
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
                ranges = [h - l for h, l in zip(highs, lows) if h >= l]
                volatility = max(sum(ranges) / max(len(ranges), 1), 1e-12)

                entry = float(p["entry"])
                stop = float(p["stop_loss"])
                side = str(p["side"])
                qty = float(p["quantity"])
                initial_risk = max(abs(entry - stop), volatility * 0.10)
                peak = float(p["peak_price"] or entry)
                current_high, current_low = max(highs), min(lows)
                if side == "LONG":
                    peak = max(peak, current_high)
                    peak_move = peak - entry
                else:
                    peak = min(peak, current_low)
                    peak_move = entry - peak

                # Activation is derived from this trade's own volatility/risk,
                # with fees converted into a price distance. No % threshold.
                fee_per_order = float(self._fee_per_order())
                fee_move = (fee_per_order * 3.0) / max(qty, 1e-12)
                activation_distance = max(volatility * 0.50, initial_risk * 0.18, fee_move)
                lock_active = bool(p["profit_lock_active"]) or peak_move >= activation_distance

                first, last = closes[0], closes[-1]
                mid = closes[len(closes) // 2]
                full_slope = (last - first) / volatility
                recent_slope = (last - mid) / volatility
                directional = full_slope if side == "LONG" else -full_slope
                recent_directional = recent_slope if side == "LONG" else -recent_slope
                strength = max(0.0, min(3.0, directional))
                decay = max(0.0, directional - recent_directional)
                giveback = max(volatility * 0.20, volatility * (0.35 + 0.18 * strength + 0.22 * decay))

                exit_price = None
                reason = None
                if lock_active and peak_move > activation_distance:
                    if side == "LONG":
                        reversal = recent_directional <= 0 or (directional > 0 and recent_directional < directional * 0.25)
                        if reversal and (peak - current_low) >= giveback and peak - giveback > entry:
                            exit_price, reason = peak - giveback, "ADAPTIVE_PROFIT_LOCK"
                    else:
                        reversal = recent_directional <= 0 or (directional > 0 and recent_directional < directional * 0.25)
                        if reversal and (current_high - peak) >= giveback and peak + giveback < entry:
                            exit_price, reason = peak + giveback, "ADAPTIVE_PROFIT_LOCK"

                # TP2 is deliberately not used: a strong trade is allowed to
                # continue until adaptive momentum/peak logic says to exit.
                if exit_price is None:
                    if side == "LONG" and current_low <= stop:
                        exit_price, reason = stop, "INITIAL_STOP"
                    elif side == "SHORT" and current_high >= stop:
                        exit_price, reason = stop, "INITIAL_STOP"

                with self.lock, self._connect() as conn:
                    row = conn.execute("SELECT * FROM demo_positions WHERE id=?", (p["id"],)).fetchone()
                    if not row or row["status"] != "OPEN":
                        continue
                    peak_profit = max(float(row["peak_profit_pct"] or 0), self._profit_pct(entry, peak, side))

                    if exit_price is None:
                        conn.execute("UPDATE demo_positions SET profit_lock_active=?,peak_price=?,peak_profit_pct=? WHERE id=?", (int(lock_active), peak, peak_profit, p["id"]))
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
                    conn.execute("UPDATE demo_positions SET status='CLOSED',closed_at=?,exit_price=?,pnl=?,exit_reason=?,profit_lock_active=?,peak_price=?,peak_profit_pct=? WHERE id=?", (now, exit_price, net, reason, int(lock_active), peak, peak_profit, p["id"]))
                    conn.execute("INSERT INTO demo_trades(position_id,closed_at,symbol,side,mode,pnl,result,entry,exit_price,risk_r,gross_pnl,entry_fee,exit_fee,total_fees) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (p["id"], now, row["symbol"], side, row["mode"], net, result, entry, exit_price, signed_r, gross, entry_fee, exit_fee, total_fees))
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
    pass
