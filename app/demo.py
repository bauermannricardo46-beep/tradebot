from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import settings


class DemoEngine:
    """Persistent virtual-money simulator with automatic scanner execution."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.lock = __import__("threading").Lock()
        self.enabled = False
        self._init_db()
        self._migrate()
        self.enabled = bool(self.status()["enabled"])

    def _connect(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self.lock, self._connect() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS demo_account (
                id INTEGER PRIMARY KEY CHECK(id=1), starting_budget REAL NOT NULL,
                equity REAL NOT NULL, risk_per_trade REAL NOT NULL DEFAULT 0.005,
                max_positions INTEGER NOT NULL DEFAULT 20, enabled INTEGER NOT NULL DEFAULT 1,
                auto_scan_user_set INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS demo_positions (
                id TEXT PRIMARY KEY, symbol TEXT NOT NULL, side TEXT NOT NULL, mode TEXT NOT NULL,
                timeframe TEXT NOT NULL, entry REAL NOT NULL, stop_loss REAL NOT NULL,
                tp1 REAL NOT NULL, tp2 REAL NOT NULL, trailing_stop REAL,
                trail_distance REAL NOT NULL, quantity REAL NOT NULL, tp1_hit INTEGER NOT NULL DEFAULT 0,
                opened_at TEXT NOT NULL, closed_at TEXT, exit_price REAL, pnl REAL,
                exit_reason TEXT, status TEXT NOT NULL DEFAULT 'OPEN',
                profit_lock_active INTEGER NOT NULL DEFAULT 0, peak_price REAL,
                peak_profit_pct REAL NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS demo_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT, position_id TEXT NOT NULL,
                closed_at TEXT NOT NULL, symbol TEXT NOT NULL, side TEXT NOT NULL, mode TEXT NOT NULL,
                pnl REAL NOT NULL, result TEXT NOT NULL, entry REAL NOT NULL, exit_price REAL NOT NULL,
                risk_r REAL NOT NULL, gross_pnl REAL NOT NULL DEFAULT 0, entry_fee REAL NOT NULL DEFAULT 0,
                exit_fee REAL NOT NULL DEFAULT 0, total_fees REAL NOT NULL DEFAULT 0
            );
            """)
            existing = {row[1] for row in conn.execute("PRAGMA table_info(demo_account)").fetchall()}
            if "auto_scan_user_set" not in existing:
                conn.execute("ALTER TABLE demo_account ADD COLUMN auto_scan_user_set INTEGER NOT NULL DEFAULT 0")
            if conn.execute("SELECT id FROM demo_account WHERE id=1").fetchone() is None:
                conn.execute("INSERT INTO demo_account(id,starting_budget,equity,risk_per_trade,max_positions,enabled,auto_scan_user_set,updated_at) VALUES(1,500,500,0.005,20,1,0,?)", (self._now(),))
            else:
                conn.execute("UPDATE demo_account SET max_positions=20 WHERE max_positions < 20 AND auto_scan_user_set=0")
            conn.commit()

    def _migrate(self) -> None:
        with self.lock, self._connect() as conn:
            pc = {row[1] for row in conn.execute("PRAGMA table_info(demo_positions)").fetchall()}
            tc = {row[1] for row in conn.execute("PRAGMA table_info(demo_trades)").fetchall()}
            for name, definition in {"profit_lock_active":"INTEGER NOT NULL DEFAULT 0", "peak_price":"REAL", "peak_profit_pct":"REAL NOT NULL DEFAULT 0"}.items():
                if name not in pc: conn.execute(f"ALTER TABLE demo_positions ADD COLUMN {name} {definition}")
            for name, definition in {"gross_pnl":"REAL NOT NULL DEFAULT 0", "entry_fee":"REAL NOT NULL DEFAULT 0", "exit_fee":"REAL NOT NULL DEFAULT 0", "total_fees":"REAL NOT NULL DEFAULT 0"}.items():
                if name not in tc: conn.execute(f"ALTER TABLE demo_trades ADD COLUMN {name} {definition}")
            conn.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _fee_per_order() -> float:
        return float(settings.hyperliquid_maker_fee if str(settings.demo_fee_type).upper() == "MAKER" else settings.hyperliquid_taker_fee)

    @staticmethod
    def _profit_pct(entry: float, price: float, side: str) -> float:
        return ((price-entry)/entry*100) if side == "LONG" else ((entry-price)/entry*100)

    def configure(self, budget: float, risk_per_trade: float = 0.005, max_positions: int = 20) -> dict[str, Any]:
        if budget <= 0: raise ValueError("budget must be > 0")
        if not 0.001 <= risk_per_trade <= 0.03: raise ValueError("risk_per_trade must be between 0.1% and 3%")
        if not 1 <= max_positions <= 20: raise ValueError("max_positions must be between 1 and 20")
        with self.lock, self._connect() as conn:
            if conn.execute("SELECT COUNT(*) FROM demo_positions WHERE status='OPEN'").fetchone()[0]: raise ValueError("stop or reset the demo before changing its budget")
            conn.execute("UPDATE demo_account SET starting_budget=?,equity=?,risk_per_trade=?,max_positions=?,enabled=1,updated_at=? WHERE id=1", (budget,budget,risk_per_trade,max_positions,self._now())); conn.commit()
        self.enabled=True
        return self.status()

    def set_enabled(self, enabled: bool) -> dict[str, Any]:
        with self.lock, self._connect() as conn:
            conn.execute("UPDATE demo_account SET enabled=?,auto_scan_user_set=1,updated_at=? WHERE id=1", (int(enabled),self._now())); conn.commit()
        self.enabled=enabled
        return self.status()

    def reset(self) -> dict[str, Any]:
        with self.lock, self._connect() as conn:
            row=conn.execute("SELECT starting_budget FROM demo_account WHERE id=1").fetchone(); budget=float(row[0]) if row else 500.0
            conn.execute("DELETE FROM demo_positions"); conn.execute("DELETE FROM demo_trades")
            conn.execute("UPDATE demo_account SET equity=?,enabled=1,auto_scan_user_set=1,max_positions=20,updated_at=? WHERE id=1",(budget,self._now())); conn.commit()
        self.enabled=True
        return self.status()

    def open_count(self) -> int:
        with self.lock, self._connect() as conn: return int(conn.execute("SELECT COUNT(*) FROM demo_positions WHERE status='OPEN'").fetchone()[0])

    def free_slots(self) -> int:
        with self.lock, self._connect() as conn:
            a=self._account(conn); n=int(conn.execute("SELECT COUNT(*) FROM demo_positions WHERE status='OPEN'").fetchone()[0]) if a else 0
            return max(0,int(a["max_positions"])-n) if a else 0

    def _account(self, conn): return conn.execute("SELECT * FROM demo_account WHERE id=1").fetchone()

    def consider_setups(self, setups: list[Any]) -> int:
        """Automatically turn every valid scanner opportunity into a paper position."""
        if not setups or not self.enabled: return 0
        ranked=sorted((s for s in setups if s is not None),key=lambda s:(float(getattr(s,"probability",0)),float(getattr(s,"expected_value_r",0))),reverse=True)
        opened=0
        with self.lock, self._connect() as conn:
            a=self._account(conn)
            if not a or not a["enabled"]: return 0
            slots=max(0,int(a["max_positions"])-int(conn.execute("SELECT COUNT(*) FROM demo_positions WHERE status='OPEN'").fetchone()[0]))
            used=set()
            for setup in ranked:
                if opened>=slots: break
                symbol=str(getattr(setup,"symbol","")).strip().upper()
                if not symbol or symbol not in settings.symbol_list: continue
                side=str(getattr(setup,"side","")).upper(); mode=str(getattr(setup,"mode","")).upper()
                key=(symbol,side,mode)
                if key in used or conn.execute("SELECT 1 FROM demo_positions WHERE status='OPEN' AND symbol=? AND side=? AND mode=?",key).fetchone(): continue
                entry=float(getattr(setup,"entry",0)); stop=float(getattr(setup,"stop_loss",0)); distance=abs(entry-stop)
                if entry<=0 or distance<=0: continue
                equity=float(a["equity"]); qty=min(equity*float(a["risk_per_trade"])/distance,equity/entry)
                if qty<=0: continue
                conn.execute("INSERT INTO demo_positions(id,symbol,side,mode,timeframe,entry,stop_loss,tp1,tp2,trailing_stop,trail_distance,quantity,opened_at,status,peak_price) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,'OPEN',?)",(str(uuid.uuid4()),symbol,side,mode,str(getattr(setup,"timeframe","5m")),entry,stop,float(getattr(setup,"take_profit_1",entry)),float(getattr(setup,"take_profit_2",entry)),float(getattr(setup,"trailing_stop",stop)),distance*(0.8 if mode=="SCALP" else 1.0),qty,self._now(),entry))
                used.add(key); opened+=1
            conn.commit()
        return opened

    def consider_setup(self, setup: Any) -> bool: return bool(self.consider_setups([setup]))

    async def update_positions(self, fetch_klines) -> int:
        with self.lock, self._connect() as conn: positions=conn.execute("SELECT * FROM demo_positions WHERE status='OPEN'").fetchall()
        changed=0
        for p in positions:
            try:
                df=await fetch_klines(p["symbol"],p["timeframe"],40)
                if df.empty: continue
                candle=df.iloc[-1]
                candle_time=getattr(candle,"open_time",None)
                opened_at=datetime.fromisoformat(str(p["opened_at"]).replace("Z","+00:00"))
                if candle_time is not None:
                    candle_time=datetime.fromisoformat(str(candle_time).replace("Z","+00:00")) if isinstance(candle_time,str) else candle_time
                    if getattr(candle_time,"tzinfo",None) is None: candle_time=candle_time.replace(tzinfo=timezone.utc)
                    if candle_time <= opened_at: continue
                self._apply_candle(p,float(candle.high),float(candle.low)); changed+=1
            except Exception: continue
        return changed

    def _apply_candle(self,p,high:float,low:float)->None:
        with self.lock,self._connect() as conn:
            r=conn.execute("SELECT * FROM demo_positions WHERE id=?",(p["id"],)).fetchone()
            if not r or r["status"]!="OPEN": return
            side=r["side"]; entry=float(r["entry"]); stop=float(r["stop_loss"]); peak=float(r["peak_price"] or entry); peak=max(peak,high) if side=="LONG" else min(peak,low); peak_profit=max(float(r["peak_profit_pct"] or 0),self._profit_pct(entry,peak,side))
            if (side=="LONG" and low<=stop) or (side=="SHORT" and high>=stop):
                exit_price=stop; qty=float(r["quantity"]); gross=((exit_price-entry) if side=="LONG" else (entry-exit_price))*qty; fee=self._fee_per_order(); net=gross-2*fee; now=self._now(); result="WIN" if net>0 else "LOSS"; risk=abs(entry-stop); signed_r=((exit_price-entry) if side=="LONG" else (entry-exit_price))/risk if risk else 0
                conn.execute("UPDATE demo_positions SET status='CLOSED',closed_at=?,exit_price=?,pnl=?,exit_reason='INITIAL_STOP',peak_price=?,peak_profit_pct=? WHERE id=?",(now,exit_price,net,peak,peak_profit,r["id"]))
                conn.execute("INSERT INTO demo_trades(position_id,closed_at,symbol,side,mode,pnl,result,entry,exit_price,risk_r,gross_pnl,entry_fee,exit_fee,total_fees) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(r["id"],now,r["symbol"],side,r["mode"],net,result,entry,exit_price,signed_r,gross,fee,fee,2*fee)); conn.execute("UPDATE demo_account SET equity=equity+?,updated_at=? WHERE id=1",(net,now)); conn.commit()
            else:
                conn.execute("UPDATE demo_positions SET peak_price=?,peak_profit_pct=? WHERE id=?",(peak,peak_profit,r["id"])); conn.commit()

    def status(self)->dict[str,Any]:
        with self.lock,self._connect() as conn:
            a=self._account(conn); total=int(conn.execute("SELECT COUNT(*) FROM demo_trades").fetchone()[0]); wins=int(conn.execute("SELECT COUNT(*) FROM demo_trades WHERE pnl>0").fetchone()[0]); losses=int(conn.execute("SELECT COUNT(*) FROM demo_trades WHERE pnl<0").fetchone()[0]); net=float(conn.execute("SELECT COALESCE(SUM(pnl),0) FROM demo_trades").fetchone()[0]); gp=float(conn.execute("SELECT COALESCE(SUM(pnl),0) FROM demo_trades WHERE pnl>0").fetchone()[0]); gl=float(conn.execute("SELECT COALESCE(SUM(pnl),0) FROM demo_trades WHERE pnl<0").fetchone()[0]); opens=int(conn.execute("SELECT COUNT(*) FROM demo_positions WHERE status='OPEN'").fetchone()[0]); budget=float(a["starting_budget"])
            return {"enabled":bool(a["enabled"]),"budget":budget,"equity":float(a["equity"]),"pnl":net,"pnl_pct":net/budget*100 if budget else 0,"gross_profit":gp,"gross_loss":gl,"net_pnl":net,"trades":total,"closed_trades":total,"wins":wins,"losses":losses,"win_rate":wins/total*100 if total else 0,"risk_per_trade":float(a["risk_per_trade"]),"max_positions":int(a["max_positions"]),"open_positions":opens,"target_open_positions":int(a["max_positions"]),"free_slots":max(0,int(a["max_positions"])-opens),"updated_at":a["updated_at"],"fee_per_order":self._fee_per_order(),"fee_type":settings.demo_fee_type,"whitelist":list(settings.symbol_list)}

    def open_positions(self)->list[dict[str,Any]]:
        with self.lock,self._connect() as conn:return [dict(r) for r in conn.execute("SELECT * FROM demo_positions WHERE status='OPEN' ORDER BY opened_at DESC").fetchall()]

    def trades(self,limit:int=100)->list[dict[str,Any]]: return self.journal(limit)

    def journal(self,limit:int=100)->list[dict[str,Any]]:
        with self.lock,self._connect() as conn:
            rows=conn.execute("SELECT p.id AS position_id,p.opened_at,p.closed_at,p.symbol,p.side,p.mode,p.timeframe,p.entry,p.exit_price,p.pnl,p.status,CASE WHEN p.status='OPEN' THEN 'OPEN' WHEN p.pnl>0 THEN 'WIN' ELSE 'LOSS' END result,CASE WHEN p.status='OPEN' THEN NULL ELSE t.risk_r END risk_r,p.exit_reason,p.stop_loss,p.tp1,p.tp2,p.trailing_stop,p.quantity,t.gross_pnl,t.entry_fee,t.exit_fee,t.total_fees FROM demo_positions p LEFT JOIN demo_trades t ON t.position_id=p.id ORDER BY COALESCE(p.closed_at,p.opened_at) DESC LIMIT ?",(max(1,min(limit,500)),)).fetchall(); return [dict(r) for r in rows]
