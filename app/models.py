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
    side: str = Field(default="SHORT", pattern="^(LONG|SHORT)$")
    mode: str = Field(default="SWING", pattern="^(SCALP|SWING)$")
    timeframe: str = "1h"
    source_open_time: datetime | None = None
    analysis_timeframes: list[str] = Field(default_factory=list)
    confidence: int = Field(ge=0, le=100)
    probability: float = Field(default=0.5, ge=0.0, le=1.0)
    expected_value_r: float = 0.0
    model_ready: bool = False
    model_version: str = "heuristic-fallback"
    entry: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    risk_reward: float
    swing_high: float | None = None
    swing_low: float | None = None
    fib_382: float | None = None
    fib_500: float | None = None
    fib_618: float | None = None
    fib_786: float | None = None
    trailing_stop: float | None = None
    reasons: list[str]


class PaperPosition(BaseModel):
    id: str
    symbol: str
    side: str = Field(default="SHORT", pattern="^(LONG|SHORT)$")
    mode: str = Field(default="SWING", pattern="^(SCALP|SWING)$")
    timeframe: str = "1h"
    analysis_timeframes: list[str] = Field(default_factory=list)
    entry: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    quantity: float
    opened_at: datetime
    trailing_stop: float | None = None
    trail_distance: float | None = None
    highest_price: float | None = None
    lowest_price: float | None = None
    tp1_hit: bool = False
    closed_at: datetime | None = None
    exit_price: float | None = None
    pnl: float | None = None
    status: str = "OPEN"
    exit_reason: str | None = None
