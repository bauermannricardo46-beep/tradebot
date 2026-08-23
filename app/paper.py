from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from .models import PaperPosition, TradeSetup


class PaperBroker:
    def __init__(self, starting_equity: float):
        self.equity = starting_equity
        self.positions: dict[str, PaperPosition] = {}
        self.realized_pnl = 0.0

    def open_position(self, setup: TradeSetup, quantity: float) -> PaperPosition:
        trail_distance = abs(setup.entry - setup.stop_loss) * (0.8 if setup.mode == "SCALP" else 1.0)
        position = PaperPosition(
            id=str(uuid4()), symbol=setup.symbol, side=setup.side, mode=setup.mode,
            timeframe=setup.timeframe, analysis_timeframes=setup.analysis_timeframes,
            entry=setup.entry, stop_loss=setup.stop_loss,
            take_profit_1=setup.take_profit_1, take_profit_2=setup.take_profit_2,
            quantity=quantity, opened_at=datetime.now(timezone.utc),
            trailing_stop=setup.trailing_stop, trail_distance=trail_distance,
            highest_price=setup.entry, lowest_price=setup.entry,
        )
        self.positions[position.id] = position
        return position

    def open_short(self, setup: TradeSetup, quantity: float) -> PaperPosition:
        return self.open_position(setup, quantity)

    def open_long(self, setup: TradeSetup, quantity: float) -> PaperPosition:
        return self.open_position(setup, quantity)

    def mark_candle(self, position_id: str, high: float, low: float, close: float) -> PaperPosition:
        position = self.positions[position_id]
        if position.status != "OPEN":
            return position

        side = position.side
        tp1_hit = position.tp1_hit
        stop = position.stop_loss
        trailing = position.trailing_stop
        highest = max(position.highest_price or position.entry, high)
        lowest = min(position.lowest_price or position.entry, low)
        trail_distance = position.trail_distance or abs(position.entry - position.stop_loss)
        exit_price = None
        exit_reason = None

        if side == "LONG":
            if high >= position.take_profit_1:
                tp1_hit = True
            if tp1_hit:
                new_trailing = max(position.entry, highest - trail_distance)
                trailing = max(trailing or new_trailing, new_trailing)
                stop = max(stop, trailing)
            if high >= position.take_profit_2:
                exit_price, exit_reason = position.take_profit_2, "TP2_EXTENDED_MOVE"
            elif low <= stop:
                exit_price, exit_reason = stop, "TRAILING_STOP" if tp1_hit else "INITIAL_STOP"
        else:
            if low <= position.take_profit_1:
                tp1_hit = True
            if tp1_hit:
                new_trailing = min(position.entry, lowest + trail_distance)
                trailing = min(trailing or new_trailing, new_trailing)
                stop = min(stop, trailing)
            if low <= position.take_profit_2:
                exit_price, exit_reason = position.take_profit_2, "TP2_EXTENDED_MOVE"
            elif high >= stop:
                exit_price, exit_reason = stop, "TRAILING_STOP" if tp1_hit else "INITIAL_STOP"

        updated = position.model_copy(update={
            "stop_loss": stop,
            "trailing_stop": trailing,
            "highest_price": highest,
            "lowest_price": lowest,
            "tp1_hit": tp1_hit,
        })

        if exit_price is not None:
            pnl = ((exit_price - position.entry) if side == "LONG" else (position.entry - exit_price)) * position.quantity
            updated = updated.model_copy(update={
                "status": "CLOSED", "closed_at": datetime.now(timezone.utc),
                "exit_price": exit_price, "pnl": pnl, "exit_reason": exit_reason,
            })
            self.realized_pnl += pnl
            self.equity += pnl

        self.positions[position_id] = updated
        return updated

    def mark_price(self, position_id: str, price: float) -> PaperPosition:
        return self.mark_candle(position_id, high=price, low=price, close=price)

    def open_positions(self, mode: str | None = None) -> list[PaperPosition]:
        positions = [p for p in self.positions.values() if p.status == "OPEN"]
        if mode is None:
            return positions
        return [p for p in positions if p.mode == mode]
