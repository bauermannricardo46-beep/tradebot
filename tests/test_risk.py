from app.models import TradeSetup
from app.risk import size_short_position


def setup(confidence: int = 87) -> TradeSetup:
    return TradeSetup(
        symbol="BTCUSDT",
        confidence=confidence,
        entry=100.0,
        stop_loss=101.0,
        take_profit_1=98.0,
        take_profit_2=97.0,
        risk_reward=2.0,
        reasons=["test"],
    )


def test_87_confidence_is_approved():
    decision = size_short_position(10_000, setup(), 0, 0)
    assert decision.allowed is True
    assert decision.quantity == 50.0
    assert decision.risk_amount == 50.0


def test_below_confidence_is_rejected():
    decision = size_short_position(10_000, setup(86), 0, 0)
    assert decision.allowed is False


def test_daily_loss_guard():
    decision = size_short_position(10_000, setup(), 0, -200)
    assert decision.allowed is False
