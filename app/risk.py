from __future__ import annotations

from dataclasses import dataclass

from .config import settings
from .models import TradeSetup


@dataclass
class RiskDecision:
    allowed: bool
    quantity: float
    risk_amount: float
    reason: str


def size_position(equity: float, setup: TradeSetup, open_positions: int, daily_pnl: float) -> RiskDecision:
    if open_positions >= settings.max_concurrent_positions:
        return RiskDecision(False, 0.0, 0.0, "maximum concurrent positions reached")

    max_daily_loss = -abs(equity) * settings.max_daily_loss
    if daily_pnl <= max_daily_loss:
        return RiskDecision(False, 0.0, 0.0, "daily loss limit reached")

    if setup.confidence < settings.min_confidence:
        return RiskDecision(False, 0.0, 0.0, f"confidence below {settings.min_confidence}")

    if setup.risk_reward < 2.0:
        return RiskDecision(False, 0.0, 0.0, "risk/reward below 1:2")

    risk_per_unit = abs(setup.stop_loss - setup.entry)
    if risk_per_unit <= 0:
        return RiskDecision(False, 0.0, 0.0, "invalid stop distance")

    risk_amount = equity * settings.risk_per_trade
    quantity = risk_amount / risk_per_unit
    return RiskDecision(True, quantity, risk_amount, "approved")


# Backwards-compatible alias for existing short-only callers.
size_short_position = size_position
