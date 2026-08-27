from __future__ import annotations

import logging
import os
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.parse
from pathlib import Path

# Direct import is intentional: it makes app.demo a hard dependency of the
# PyInstaller entrypoint and catches packaging regressions during the build.
from app.demo import DemoEngine as _FrozenDemoEngine  # noqa: F401

APP_NAME = "TRADENEX AI"
HOST = "127.0.0.1"
PORT = 8765


def runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def normalize_demo_budget(data_dir: Path) -> None:
    """Migrate legacy 10,000 EUR demo state to 500 EUR without erasing P&L history."""
    db_path = data_dir / "tradebot.db"
    if not db_path.exists():
        return
    try:
        with sqlite3.connect(db_path, timeout=5) as conn:
            tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "demo_account" not in tables:
                return
            columns = {row[1] for row in conn.execute("PRAGMA table_info(demo_account)")}
            if "starting_budget" not in columns or "equity" not in columns:
                return
            row = conn.execute("SELECT starting_budget FROM demo_account WHERE id=1").fetchone()
            if not row or float(row[0]) != 10000.0:
                return
            net_pnl = 0.0
            if "demo_trades" in tables:
                pnl_row = conn.execute("SELECT COALESCE(SUM(pnl),0) FROM demo_trades").fetchone()
                net_pnl = float(pnl_row[0] or 0.0)
            equity = 500.0 + net_pnl
            conn.execute(
                "UPDATE demo_account SET starting_budget=500,equity=?,updated_at=? WHERE id=1 AND starting_budget=10000",
                (equity, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
            )
            conn.commit()
    except Exception as exc:
        logging.warning("Demo-Budget konnte beim Start nicht normalisiert werden: %s", exc)


def start_server():
    import uvicorn
    from app.main import app

    logging.basicConfig(level=logging.WARNING, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    config = uvicorn.Config(app, host=HOST, port=PORT, log_level="warning", access_log=False, log_config=None)
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, name="TradeBotServer", daemon=True)
    thread.start()
    return server, thread


def wait_for_server(timeout: float = 30.0) -> bool:
    import urllib.request

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"http://{HOST}:{PORT}/health", timeout=1.5) as response:
                return response.status == 200
        except Exception:
            time.sleep(0.25)
    return False


def _browser_candidates() -> list[Path]:
    candidates: list[Path] = []
    if os.name == "nt":
        program_files = [os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"), os.environ.get("LOCALAPPDATA")]
        for base in filter(None, program_files):
            root = Path(base)
            candidates.extend([
                root / "Microsoft" / "Edge" / "Application" / "msedge.exe",
                root / "Google" / "Chrome" / "Application" / "chrome.exe",
            ])
    return candidates


def open_app(server) -> None:
    """Open the dashboard without pywebview/pythonnet and keep the server alive."""
    url = f"http://{HOST}:{PORT}/splash.html"
    app_url = urllib.parse.quote(url, safe=":/?=&%.-_~")

    edge = next((p for p in _browser_candidates() if p.exists()), None)
    if edge is not None:
        try:
            subprocess.Popen(
                [str(edge), f"--app={url}", "--new-window", "--disable-features=Translate"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            edge = None

    if edge is None:
        chrome = shutil.which("chrome") or shutil.which("chrome.exe")
        if chrome:
            try:
                subprocess.Popen(
                    [chrome, f"--app={url}", "--new-window"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                edge = Path(chrome)
            except OSError:
                edge = None

    if edge is None:
        import webbrowser
        if not webbrowser.open(url, new=1):
            raise RuntimeError(f"TRADENEX Dashboard konnte nicht geöffnet werden: {app_url}")

    # The desktop UI is now hosted by the installed browser. Keep the
    # background server process alive until the user terminates TRADENEX.
    while not server.should_exit:
        time.sleep(1.0)


def main() -> None:
    appdata = Path(os.getenv("LOCALAPPDATA", runtime_root())) / "TradeBotAI"
    data_dir = appdata / "data"
    model_dir = appdata / "models"
    data_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("TRADEBOT_DATA_DIR", str(data_dir))
    os.environ.setdefault("TRADEBOT_MODEL_DIR", str(model_dir))

    normalize_demo_budget(data_dir)

    try:
        server, _ = start_server()
        if not wait_for_server():
            raise RuntimeError("TRADENEX Server konnte nicht gestartet werden.")
        open_app(server)
    except Exception as exc:
        import tkinter as tk
        error = tk.Tk()
        error.title(APP_NAME)
        error.geometry("560x220")
        tk.Label(error, text="TRADENEX konnte nicht gestartet werden", font=("Segoe UI", 16, "bold")).pack(pady=(35, 10))
        tk.Label(error, text=str(exc), wraplength=500, justify="center").pack(padx=25, pady=10)
        tk.Button(error, text="Schließen", command=error.destroy).pack(pady=8)
        error.mainloop()
        raise


if __name__ == "__main__":
    main()
