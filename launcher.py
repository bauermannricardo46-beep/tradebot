from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path

import tkinter as tk


APP_NAME = "TradeBot AI"
HOST = "127.0.0.1"
PORT = 8765


def runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def show_splash() -> tuple[tk.Tk, tk.Label, tk.Label]:
    root = tk.Tk()
    root.overrideredirect(True)
    root.configure(bg="#070912")
    width, height = 520, 300
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    root.geometry(f"{width}x{height}+{(screen_w-width)//2}+{(screen_h-height)//2}")

    canvas = tk.Canvas(root, width=width, height=height, bg="#070912", highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    canvas.create_text(width//2, 92, text="TRADEBOT", fill="#edf3ff", font=("Segoe UI", 30, "bold"))
    canvas.create_text(width//2, 127, text="AI TRADING ENGINE", fill="#64e7ff", font=("Segoe UI", 11, "bold"))
    canvas.create_rectangle(90, 175, 430, 181, fill="#162039", outline="")
    progress = canvas.create_rectangle(90, 175, 90, 181, fill="#64e7ff", outline="")
    status = canvas.create_text(width//2, 215, text="Starting engine…", fill="#8e9ab4", font=("Segoe UI", 10))
    version = canvas.create_text(width//2, 250, text="LIVE DATA · PAPER TRADING", fill="#53627e", font=("Segoe UI", 9))

    def animate(i: int = 0) -> None:
        if not root.winfo_exists():
            return
        steps = ["Loading AI engine…", "Loading market data…", "Starting live collector…", "Opening control center…"]
        pct = min(1.0, i / 80)
        canvas.coords(progress, 90, 175, 90 + 340 * pct, 181)
        canvas.itemconfigure(status, text=steps[min(len(steps) - 1, i // 20)])
        root.after(40, animate, i + 1)

    animate()
    return root, tk.Label(root), tk.Label(root)


def start_server():
    import uvicorn
    from app.main import app

    config = uvicorn.Config(app, host=HOST, port=PORT, log_level="warning", access_log=False)
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

    window = webview.create_window(APP_NAME, f"http://{HOST}:{PORT}/index.html", width=1480, height=920, min_size=(980, 680), resizable=True)

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

    splash, _, _ = show_splash()
    splash.update()

    try:
        server, _ = start_server()
        if not wait_for_server():
            splash.destroy()
            raise RuntimeError("TradeBot Server konnte nicht gestartet werden.")
        splash.destroy()
        open_app(server)
    except Exception as exc:
        try:
            splash.destroy()
        except Exception:
            pass
        error = tk.Tk()
        error.title(APP_NAME)
        error.geometry("560x220")
        tk.Label(error, text="TradeBot konnte nicht gestartet werden", font=("Segoe UI", 16, "bold")).pack(pady=(35, 10))
        tk.Label(error, text=str(exc), wraplength=500, justify="center").pack(padx=25, pady=10)
        tk.Button(error, text="Schließen", command=error.destroy).pack(pady=8)
        error.mainloop()
        raise


if __name__ == "__main__":
    main()
