from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .config import settings
from .execution import ExecutionMode
from .notifications import public_key, remove_subscription, save_subscription, send_push, subscriptions, vapid_configured
from .storage import store

router = APIRouter(prefix="/notifications", tags=["notifications"])


class PushSubscription(BaseModel):
    endpoint: str
    keys: dict[str, str]


class TestNotification(BaseModel):
    title: str = "TradeBot AI"
    body: str = "Test-Benachrichtigung"
    url: str = "/"


class SettingsPayload(BaseModel):
    scalp_enabled: bool = True
    swing_enabled: bool = True
    new_setups: bool = True
    new_trades: bool = True
    auto_scan_enabled: bool = True
    risk_per_trade: float = Field(default=0.005, ge=0.001, le=0.03)
    max_daily_loss: float = Field(default=0.02, ge=0.001, le=0.2)
    scalp_sl_atr: float = Field(default=0.75, ge=0.1, le=10.0)
    scalp_tp1_rr: float = Field(default=1.8, ge=0.2, le=20.0)
    scalp_tp2_rr: float = Field(default=2.7, ge=0.5, le=50.0)
    swing_sl_atr: float = Field(default=1.35, ge=0.1, le=10.0)
    swing_tp1_rr: float = Field(default=2.2, ge=0.2, le=20.0)
    swing_tp2_rr: float = Field(default=4.0, ge=0.5, le=50.0)


class VisualPayload(BaseModel):
    preset: str = "tradenex"
    accent: str = Field(default="#55e7ff", pattern=r"^#[0-9a-fA-F]{6}$")
    accent2: str = Field(default="#8c5cff", pattern=r"^#[0-9a-fA-F]{6}$")
    accent3: str = Field(default="#ff39d1", pattern=r"^#[0-9a-fA-F]{6}$")
    metal: str = Field(default="#c8d0df", pattern=r"^#[0-9a-fA-F]{6}$")
    background: str = "grid"
    motion: bool = True
    glow: int = Field(default=12, ge=0, le=30)
    panel: int = Field(default=88, ge=55, le=98)
    logo_brightness: int = Field(default=100, ge=60, le=140)
    logo_glow: int = Field(default=100, ge=0, le=160)
    effect_strength: int = Field(default=65, ge=0, le=100)


class ExecutionPayload(BaseModel):
    mode: str


class ControlStore:
    def __init__(self):
        self.execution = ExecutionMode(store.db_path)
        self._ensure()
        self.apply_runtime(self.settings())

    def _ensure(self):
        with sqlite3.connect(store.db_path) as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS app_settings (
                    id INTEGER PRIMARY KEY CHECK(id=1),
                    scalp_enabled INTEGER NOT NULL DEFAULT 1,
                    swing_enabled INTEGER NOT NULL DEFAULT 1,
                    new_setups INTEGER NOT NULL DEFAULT 1,
                    new_trades INTEGER NOT NULL DEFAULT 1,
                    auto_scan_enabled INTEGER NOT NULL DEFAULT 1,
                    risk_per_trade REAL NOT NULL DEFAULT 0.005,
                    max_daily_loss REAL NOT NULL DEFAULT 0.02,
                    scalp_sl_atr REAL NOT NULL DEFAULT 0.75,
                    scalp_tp1_rr REAL NOT NULL DEFAULT 1.8,
                    scalp_tp2_rr REAL NOT NULL DEFAULT 2.7,
                    swing_sl_atr REAL NOT NULL DEFAULT 1.35,
                    swing_tp1_rr REAL NOT NULL DEFAULT 2.2,
                    swing_tp2_rr REAL NOT NULL DEFAULT 4.0,
                    visual_preset TEXT NOT NULL DEFAULT 'tradenex',
                    visual_accent TEXT NOT NULL DEFAULT '#55e7ff',
                    visual_accent2 TEXT NOT NULL DEFAULT '#8c5cff',
                    visual_accent3 TEXT NOT NULL DEFAULT '#ff39d1',
                    visual_metal TEXT NOT NULL DEFAULT '#c8d0df',
                    visual_background TEXT NOT NULL DEFAULT 'grid',
                    visual_motion INTEGER NOT NULL DEFAULT 1,
                    visual_glow INTEGER NOT NULL DEFAULT 12,
                    visual_panel INTEGER NOT NULL DEFAULT 88,
                    visual_logo_brightness INTEGER NOT NULL DEFAULT 100,
                    visual_logo_glow INTEGER NOT NULL DEFAULT 100,
                    visual_effect_strength INTEGER NOT NULL DEFAULT 65,
                    updated_at TEXT NOT NULL
                )"""
            )
            existing = {row[1] for row in conn.execute("PRAGMA table_info(app_settings)").fetchall()}
            migrations = {
                "auto_scan_enabled": "ALTER TABLE app_settings ADD COLUMN auto_scan_enabled INTEGER NOT NULL DEFAULT 1",
                "scalp_sl_atr": "ALTER TABLE app_settings ADD COLUMN scalp_sl_atr REAL NOT NULL DEFAULT 0.75",
                "scalp_tp1_rr": "ALTER TABLE app_settings ADD COLUMN scalp_tp1_rr REAL NOT NULL DEFAULT 1.8",
                "scalp_tp2_rr": "ALTER TABLE app_settings ADD COLUMN scalp_tp2_rr REAL NOT NULL DEFAULT 2.7",
                "swing_sl_atr": "ALTER TABLE app_settings ADD COLUMN swing_sl_atr REAL NOT NULL DEFAULT 1.35",
                "swing_tp1_rr": "ALTER TABLE app_settings ADD COLUMN swing_tp1_rr REAL NOT NULL DEFAULT 2.2",
                "swing_tp2_rr": "ALTER TABLE app_settings ADD COLUMN swing_tp2_rr REAL NOT NULL DEFAULT 4.0",
                "visual_preset": "ALTER TABLE app_settings ADD COLUMN visual_preset TEXT NOT NULL DEFAULT 'tradenex'",
                "visual_accent": "ALTER TABLE app_settings ADD COLUMN visual_accent TEXT NOT NULL DEFAULT '#55e7ff'",
                "visual_accent2": "ALTER TABLE app_settings ADD COLUMN visual_accent2 TEXT NOT NULL DEFAULT '#8c5cff'",
                "visual_accent3": "ALTER TABLE app_settings ADD COLUMN visual_accent3 TEXT NOT NULL DEFAULT '#ff39d1'",
                "visual_metal": "ALTER TABLE app_settings ADD COLUMN visual_metal TEXT NOT NULL DEFAULT '#c8d0df'",
                "visual_background": "ALTER TABLE app_settings ADD COLUMN visual_background TEXT NOT NULL DEFAULT 'grid'",
                "visual_motion": "ALTER TABLE app_settings ADD COLUMN visual_motion INTEGER NOT NULL DEFAULT 1",
                "visual_glow": "ALTER TABLE app_settings ADD COLUMN visual_glow INTEGER NOT NULL DEFAULT 12",
                "visual_panel": "ALTER TABLE app_settings ADD COLUMN visual_panel INTEGER NOT NULL DEFAULT 88",
                "visual_logo_brightness": "ALTER TABLE app_settings ADD COLUMN visual_logo_brightness INTEGER NOT NULL DEFAULT 100",
                "visual_logo_glow": "ALTER TABLE app_settings ADD COLUMN visual_logo_glow INTEGER NOT NULL DEFAULT 100",
                "visual_effect_strength": "ALTER TABLE app_settings ADD COLUMN visual_effect_strength INTEGER NOT NULL DEFAULT 65",
            }
            for column, sql in migrations.items():
                if column not in existing:
                    conn.execute(sql)
            conn.execute(
                """INSERT OR IGNORE INTO app_settings(
                    id,scalp_enabled,swing_enabled,new_setups,new_trades,auto_scan_enabled,
                    risk_per_trade,max_daily_loss,scalp_sl_atr,scalp_tp1_rr,scalp_tp2_rr,
                    swing_sl_atr,swing_tp1_rr,swing_tp2_rr,
                    visual_preset,visual_accent,visual_accent2,visual_accent3,visual_metal,
                    visual_background,visual_motion,visual_glow,visual_panel,visual_logo_brightness,
                    visual_logo_glow,visual_effect_strength,updated_at
                ) VALUES(1,1,1,1,1,1,0.005,0.02,0.75,1.8,2.7,1.35,2.2,4.0,
                    'tradenex','#55e7ff','#8c5cff','#ff39d1','#c8d0df','grid',1,12,88,100,100,65,?)""",
                (datetime.now(timezone.utc).isoformat(),),
            )
            conn.commit()

    def settings(self):
        with sqlite3.connect(store.db_path) as conn:
            row = conn.execute("SELECT * FROM app_settings WHERE id=1").fetchone()
            return {
                "scalp_enabled": bool(row[1]),
                "swing_enabled": bool(row[2]),
                "new_setups": bool(row[3]),
                "new_trades": bool(row[4]),
                "auto_scan_enabled": bool(row[5]),
                "risk_per_trade": float(row[6]),
                "max_daily_loss": float(row[7]),
                "scalp_sl_atr": float(row[8]),
                "scalp_tp1_rr": float(row[9]),
                "scalp_tp2_rr": float(row[10]),
                "swing_sl_atr": float(row[11]),
                "swing_tp1_rr": float(row[12]),
                "swing_tp2_rr": float(row[13]),
                "visual": self.visual_settings_from_row(row),
                "updated_at": row[-1],
            }

    @staticmethod
    def visual_settings_from_row(row):
        # Stable offsets are used because visual columns are appended after the legacy settings.
        return {
            "preset": row[14], "accent": row[15], "accent2": row[16], "accent3": row[17],
            "metal": row[18], "background": row[19], "motion": bool(row[20]),
            "glow": int(row[21]), "panel": int(row[22]), "logo_brightness": int(row[23]),
            "logo_glow": int(row[24]), "effect_strength": int(row[25]),
        }

    def visual(self):
        with sqlite3.connect(store.db_path) as conn:
            row = conn.execute("SELECT * FROM app_settings WHERE id=1").fetchone()
            return self.visual_settings_from_row(row)

    def save_visual(self, p: VisualPayload):
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(store.db_path) as conn:
            conn.execute(
                """UPDATE app_settings SET
                    visual_preset=?,visual_accent=?,visual_accent2=?,visual_accent3=?,visual_metal=?,
                    visual_background=?,visual_motion=?,visual_glow=?,visual_panel=?,visual_logo_brightness=?,
                    visual_logo_glow=?,visual_effect_strength=?,updated_at=? WHERE id=1""",
                (p.preset, p.accent, p.accent2, p.accent3, p.metal, p.background, int(p.motion),
                 p.glow, p.panel, p.logo_brightness, p.logo_glow, p.effect_strength, now),
            )
            conn.commit()
        return self.visual()

    @staticmethod
    def apply_runtime(values: dict):
        settings.scalping_enabled = values["scalp_enabled"]
        settings.swing_enabled = values["swing_enabled"]
        settings.risk_per_trade = values["risk_per_trade"]
        settings.max_daily_loss = values["max_daily_loss"]
        settings.scalp_sl_atr_multiplier = values["scalp_sl_atr"]
        settings.scalp_tp1_rr = values["scalp_tp1_rr"]
        settings.scalp_tp2_rr = values["scalp_tp2_rr"]
        settings.swing_sl_atr_multiplier = values["swing_sl_atr"]
        settings.swing_tp1_rr = values["swing_tp1_rr"]
        settings.swing_tp2_rr = values["swing_tp2_rr"]

    def save_settings(self, p: SettingsPayload):
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(store.db_path) as conn:
            conn.execute(
                """UPDATE app_settings SET
                    scalp_enabled=?,swing_enabled=?,new_setups=?,new_trades=?,auto_scan_enabled=?,
                    risk_per_trade=?,max_daily_loss=?,
                    scalp_sl_atr=?,scalp_tp1_rr=?,scalp_tp2_rr=?,
                    swing_sl_atr=?,swing_tp1_rr=?,swing_tp2_rr=?,updated_at=?
                    WHERE id=1""",
                (
                    int(p.scalp_enabled), int(p.swing_enabled), int(p.new_setups), int(p.new_trades), int(p.auto_scan_enabled),
                    p.risk_per_trade, p.max_daily_loss,
                    p.scalp_sl_atr, p.scalp_tp1_rr, p.scalp_tp2_rr,
                    p.swing_sl_atr, p.swing_tp1_rr, p.swing_tp2_rr, now,
                ),
            )
            conn.commit()
        values = self.settings()
        self.apply_runtime(values)
        return values


control = ControlStore()


@router.get("/config")
def notification_config():
    return {"supported": True, "push_configured": vapid_configured(), "subscribers": len(subscriptions), "public_key": public_key()}


@router.post("/subscribe")
def subscribe(subscription: PushSubscription):
    save_subscription(subscription.model_dump())
    return {"ok": True, "subscribers": len(subscriptions)}


@router.delete("/subscribe")
def unsubscribe(endpoint: str):
    return {"ok": remove_subscription(endpoint), "subscribers": len(subscriptions)}


@router.post("/test")
def test_notification(payload: TestNotification):
    return send_push(payload.title, payload.body, payload.url)


@router.get("/settings")
def get_settings():
    return control.settings()


@router.post("/settings")
def update_settings(payload: SettingsPayload):
    return control.save_settings(payload)


@router.get("/visual")
def get_visual_settings():
    return control.visual()


@router.post("/visual")
def update_visual_settings(payload: VisualPayload):
    return control.save_visual(payload)


@router.get("/execution")
def get_execution():
    return control.execution.get()


@router.post("/execution")
def set_execution(payload: ExecutionPayload):
    return control.execution.set(payload.mode)


@router.get("/history/summary")
def history_summary():
    with sqlite3.connect(store.db_path) as conn:
        row = conn.execute("SELECT COALESCE(SUM(CASE WHEN pnl > 0 THEN pnl ELSE 0 END),0), COALESCE(SUM(CASE WHEN pnl < 0 THEN pnl ELSE 0 END),0), COUNT(*), COALESCE(SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END),0) FROM demo_trades").fetchone()
    gross_profit, gross_loss, trades, wins = float(row[0] or 0), float(row[1] or 0), int(row[2] or 0), int(row[3] or 0)
    return {"gross_profit": gross_profit, "gross_loss": gross_loss, "net_pnl": gross_profit + gross_loss, "trades": trades, "wins": wins, "losses": trades - wins, "win_rate": (wins / trades * 100) if trades else 0.0}