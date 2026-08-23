from datetime import datetime
from pydantic import BaseModel, Field


class Candle(BaseModel):
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class TradeSetup(BaseModel):
    symbol: str
    side: str = "SHORT"
    confidence: int = Field(ge=0, le=100)
    entry: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    risk_reward: float
    reasons: list[str]


class PaperPosition(BaseModel):
    id: str
    symbol: str
    side: str = "SHORT"
    entry: float
    stop_loss: float
    take_profit: float
    quantity: float
    opened_at: datetime
    closed_at: datetime | None = None
    exit_price: float | None = None
    pnl: float | None = None
    status: str = "OPEN"
