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
    risk_per_trade: float = Field(default=0.005, ge=0.001, le=0.03)
    max_daily_loss: float = Field(default=0.02, ge=0.001, le=0.2)
    scalp_sl_atr: float = Field(default=0.75, ge=0.1, le=10.0)
    scalp_tp1_rr: float = Field(default=1.8, ge=0.2, le=20.0)
    scalp_tp2_rr: float = Field(default=2.7, ge=0.5, le=50.0)
    swing_sl_atr: float = Field(default=1.35, ge=0.1, le=10.0)
    swing_tp1_rr: float = Field(default=2.2, ge=0.2, le=20.0)
    swing_tp2_rr: float = Field(default=4.0, ge=0.5, le=50.0)


class ExecutionPayload(BaseModel):
    mode: str


class ControlStore:
    def __init__(self):
        self.execution = ExecutionMode(store.db_path)
        self._ensure()

    def _ensure(self):
        with sqlite3.connect(store.db_path) as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS app_settings (
                    id INTEGER PRIMARY KEY CHECK(id=1),
                    scalp_enabled INTEGER NOT NULL DEFAULT 1,
                    swing_enabled INTEGER NOT NULL DEFAULT 1,
                    new_setups INTEGER NOT NULL DEFAULT 1,
                    new_trades INTEGER NOT NULL DEFAULT 1,
                    risk_per_trade REAL NOT NULL DEFAULT 0.005,
                    max_daily_loss REAL NOT NULL DEFAULT 0.02,
                    scalp_sl_atr REAL NOT NULL DEFAULT 0.75,
                    scalp_tp1_rr REAL NOT NULL DEFAULT 1.8,
                    scalp_tp2_rr REAL NOT NULL DEFAULT 2.7,
                    swing_sl_atr REAL NOT NULL DEFAULT 1.35,
                    swing_tp1_rr REAL NOT NULL DEFAULT 2.2,
                    swing_tp2_rr REAL NOT NULL DEFAULT 4.0,
                    updated_at TEXT NOT NULL
                )"""
            )
            existing = {row[1] for row in conn.execute("PRAGMA table_info(app_settings)").fetchall()}
            migrations = {
                "scalp_sl_atr": "ALTER TABLE app_settings ADD COLUMN scalp_sl_atr REAL NOT NULL DEFAULT 0.75",
                "scalp_tp1_rr": "ALTER TABLE app_settings ADD COLUMN scalp_tp1_rr REAL NOT NULL DEFAULT 1.8",
                "scalp_tp2_rr": "ALTER TABLE app_settings ADD COLUMN scalp_tp2_rr REAL NOT NULL DEFAULT 2.7",
                "swing_sl_atr": "ALTER TABLE app_settings ADD COLUMN swing_sl_atr REAL NOT NULL DEFAULT 1.35",
                "swing_tp1_rr": "ALTER TABLE app_settings ADD COLUMN swing_tp1_rr REAL NOT NULL DEFAULT 2.2",
                "swing_tp2_rr": "ALTER TABLE app_settings ADD COLUMN swing_tp2_rr REAL NOT NULL DEFAULT 4.0",
            }
            for column, sql in migrations.items():
                if column not in existing:
                    conn.execute(sql)
            conn.execute(
                """INSERT OR IGNORE INTO app_settings(
                    id,scalp_enabled,swing_enabled,new_setups,new_trades,
                    risk_per_trade,max_daily_loss,scalp_sl_atr,scalp_tp1_rr,scalp_tp2_rr,
                    swing_sl_atr,swing_tp1_rr,swing_tp2_rr,updated_at
                ) VALUES(1,1,1,1,1,0.005,0.02,0.75,1.8,2.7,1.35,2.2,4.0,?)""",
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
                "risk_per_trade": float(row[5]),
                "max_daily_loss": float(row[6]),
                "scalp_sl_atr": float(row[7]),
                "scalp_tp1_rr": float(row[8]),
                "scalp_tp2_rr": float(row[9]),
                "swing_sl_atr": float(row[10]),
                "swing_tp1_rr": float(row[11]),
                "swing_tp2_rr": float(row[12]),
                "updated_at": row[13],
            }

    def save_settings(self, p: SettingsPayload):
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(store.db_path) as conn:
            conn.execute(
                """UPDATE app_settings SET
                    scalp_enabled=?,swing_enabled=?,new_setups=?,new_trades=?,
                    risk_per_trade=?,max_daily_loss=?,
                    scalp_sl_atr=?,scalp_tp1_rr=?,scalp_tp2_rr=?,
                    swing_sl_atr=?,swing_tp1_rr=?,swing_tp2_rr=?,updated_at=?
                    WHERE id=1""",
                (
                    int(p.scalp_enabled), int(p.swing_enabled), int(p.new_setups), int(p.new_trades),
                    p.risk_per_trade, p.max_daily_loss,
                    p.scalp_sl_atr, p.scalp_tp1_rr, p.scalp_tp2_rr,
                    p.swing_sl_atr, p.swing_tp1_rr, p.swing_tp2_rr, now,
                ),
            )
            conn.commit()
        try:
            settings.scalping_enabled = p.scalp_enabled
            settings.swing_enabled = p.swing_enabled
            settings.risk_per_trade = p.risk_per_trade
            settings.max_daily_loss = p.max_daily_loss
            settings.scalp_sl_atr_multiplier = p.scalp_sl_atr
            settings.scalp_tp1_rr = p.scalp_tp1_rr
            settings.scalp_tp2_rr = p.scalp_tp2_rr
            settings.swing_sl_atr_multiplier = p.swing_sl_atr
            settings.swing_tp1_rr = p.swing_tp1_rr
            settings.swing_tp2_rr = p.swing_tp2_rr
        except Exception:
            pass
        return self.settings()


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
