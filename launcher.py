from __future__ import annotations

import logging
import os
import sys
import threading
import time
from pathlib import Path

APP_NAME = "TRADENEX AI"
HOST = "127.0.0.1"
PORT = 8765


def runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


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


def open_app(server):
    import webview

    window = webview.create_window(
        APP_NAME,
        f"http://{HOST}:{PORT}/splash.html",
        width=1480,
        height=920,
        min_size=(980, 680),
        resizable=True,
    )

    def on_closed():
        server.should_exit = True

    window.events.closed += on_closed
    webview.start(debug=False)


def main() -> None:
    appdata = Path(os.getenv("LOCALAPPDATA", runtime_root())) / "TradeBotAI"
    data_dir = appdata / "data"
    model_dir = appdata / "models"
    data_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("TRADEBOT_DATA_DIR", str(data_dir))
    os.environ.setdefault("TRADEBOT_MODEL_DIR", str(model_dir))

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
