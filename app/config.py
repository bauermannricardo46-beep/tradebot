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
    symbols: str = "BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT,DOGEUSDT,ADAUSDT,AVAXUSDT,LINKUSDT,DOTUSDT,TRXUSDT,TONUSDT,SHIBUSDT,BCHUSDT,LTCUSDT,UNIUSDT,NEARUSDT,APTUSDT,SUIUSDT,ARBUSDT,OPUSDT,FILUSDT,ATOMUSDT,ETCUSDT,XLMUSDT,HBARUSDT,ICPUSDT,INJUSDT,PEPEUSDT,WIFUSDT,RENDERUSDT,GRTUSDT,AAVEUSDT,MKRUSDT,ALGOUSDT,VETUSDT,EOSUSDT,SANDUSDT,MANAUSDT,XTZUSDT,THETAUSDT,QNTUSDT,EGLDUSDT,RUNEUSDT,KASUSDT,SEIUSDT,JUPUSDT,TIAUSDT,ENAUSDT"
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

    # Fixed absolute demo fees per order, as requested.
    hyperliquid_maker_fee: float = 0.004
    hyperliquid_taker_fee: float = 0.007
    demo_fee_type: str = "TAKER"

    # Custom software profit lock, independent from exchange-native trailing TP.
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
        return [s.strip().upper() for s in self.symbols.split(",") if s.strip()]


settings = Settings()
