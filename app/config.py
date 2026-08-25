from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    paper_trading: bool = True
    starting_equity: float = 10_000.0
    risk_per_trade: float = 0.005
    max_concurrent_positions: int = 8
    max_daily_loss: float = 0.02
    min_confidence: int = 87
    symbols: str = "BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT"
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
    # Fast control loop. Binance REST requests are cached per timeframe below,
    # so this does not mean hammering every endpoint every two seconds.
    collector_interval_seconds: float = 2.0

    # Independent SCALP risk/target profile.
    scalp_sl_atr_multiplier: float = 0.75
    scalp_tp1_rr: float = 1.8
    scalp_tp2_rr: float = 2.7

    # Independent SWING risk/target profile.
    swing_sl_atr_multiplier: float = 1.35
    swing_tp1_rr: float = 2.2
    swing_tp2_rr: float = 4.0

    data_dir: str = Field(default="data", validation_alias=AliasChoices("DATA_DIR", "TRADEBOT_DATA_DIR"))

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", populate_by_name=True)

    @property
    def symbol_list(self) -> list[str]:
        return [s.strip().upper() for s in self.symbols.split(",") if s.strip()]


settings = Settings()
