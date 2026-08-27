from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


TOP20_SYMBOLS: tuple[str, ...] = (
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    "ADAUSDT", "AVAXUSDT", "LINKUSDT", "SUIUSDT", "NEARUSDT",
    "TRXUSDT", "DOGEUSDT", "ARBUSDT", "OPUSDT", "RENDERUSDT",
    "ATOMUSDT", "LTCUSDT", "BCHUSDT", "INJUSDT", "AAVEUSDT",
)
TOP20_SYMBOL_SET = frozenset(TOP20_SYMBOLS)


def is_allowed_symbol(symbol: str) -> bool:
    return str(symbol).strip().upper() in TOP20_SYMBOL_SET


class Settings(BaseSettings):
    app_env: str = "development"
    paper_trading: bool = True
    starting_equity: float = 500.0
    risk_per_trade: float = 0.005
    max_concurrent_positions: int = 20
    max_daily_loss: float = 0.02
    min_confidence: int = 0
    symbols: str = ",".join(TOP20_SYMBOLS)
    scalping_timeframe: str = "5m"
    swing_timeframe: str = "1h"
    candle_limit: int = 250
    max_scalp_positions: int = 12
    max_swing_positions: int = 4
    scalp_min_confidence: int = 80
    swing_min_confidence: int = 82
    scalp_risk_multiplier: float = 0.6
    swing_risk_multiplier: float = 1.0
    scalping_enabled: bool = True
    swing_enabled: bool = True
    collector_interval_seconds: float = 2.0

    scalp_sl_atr_multiplier: float = 0.75
    scalp_tp1_rr: float = 1.8
    scalp_tp2_rr: float = 2.7
    swing_sl_atr_multiplier: float = 1.35
    swing_tp1_rr: float = 2.2
    swing_tp2_rr: float = 4.0

    # Hyperliquid Perpetuals Tier 0 (0% HYPE staking discount).
    # Fees are rates applied to the actual notional at entry and exit.
    hyperliquid_maker_fee: float = 0.00015  # 0.015%
    hyperliquid_taker_fee: float = 0.00045  # 0.045%
    demo_fee_type: str = "TAKER"

    scalp_profit_lock_activation_pct: float = 0.8
    scalp_profit_lock_retracement_pct: float = 0.25
    swing_profit_lock_activation_pct: float = 1.5
    swing_profit_lock_retracement_pct: float = 0.50

    github_sync_enabled: bool = True
    github_sync_interval_seconds: int = 300
    github_sync_repo: str = "bauermannricardo46-beep/tradebot"
    github_sync_branch: str = "main"
    github_sync_path: str = "data/analysis_archive"
    github_sync_token: str = Field(default="", validation_alias=AliasChoices("GITHUB_SYNC_TOKEN", "TRADEBOT_GITHUB_TOKEN"))

    data_dir: str = Field(default="data", validation_alias=AliasChoices("DATA_DIR", "TRADEBOT_DATA_DIR"))

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", populate_by_name=True)

    @property
    def symbol_list(self) -> list[str]:
        return list(TOP20_SYMBOLS)


settings = Settings()
