from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from .models import PaperPosition, TradeSetup


class PaperBroker:
    def __init__(self, starting_equity: float):
        self.equity = starting_equity
        self.positions: dict[str, PaperPosition] = {}
        self.realized_pnl = 0.0

    def open_short(self, setup: TradeSetup, quantity: float) -> PaperPosition:
        position = PaperPosition(
            id=str(uuid4()),
            symbol=setup.symbol,
            entry=setup.entry,
            stop_loss=setup.stop_loss,
            take_profit=setup.take_profit_1,
            quantity=quantity,
            opened_at=datetime.now(timezone.utc),
        )
        self.positions[position.id] = position
        return position

    def mark_price(self, position_id: str, price: float) -> PaperPosition:
        position = self.positions[position_id]
        if position.status != "OPEN":
            return position

        exit_price = None
        if price >= position.stop_loss:
            exit_price = position.stop_loss
        elif price <= position.take_profit:
            exit_price = position.take_profit

        if exit_price is not None:
            pnl = (position.entry - exit_price) * position.quantity
            updated = position.model_copy(
                update={
                    "status": "CLOSED",
                    "closed_at": datetime.now(timezone.utc),
                    "exit_price": exit_price,
                    "pnl": pnl,
                }
            )
            self.positions[position_id] = updated
            self.realized_pnl += pnl
            self.equity += pnl
            return updated

        return position

    def open_positions(self) -> list[PaperPosition]:
        return [p for p in self.positions.values() if p.status == "OPEN"]
