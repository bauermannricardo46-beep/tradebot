from __future__ import annotations

import logging
import math
import os
import random
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


def show_splash() -> tk.Tk:
    """Premium animated cyber-style startup screen with smooth easing."""
    root = tk.Tk()
    root.overrideredirect(True)
    root.configure(bg="#05070d")
    width, height = 760, 460
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    root.geometry(f"{width}x{height}+{(screen_w-width)//2}+{(screen_h-height)//2}")

    canvas = tk.Canvas(root, width=width, height=height, bg="#05070d", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    # Layered background glow and grid.
    for y in range(0, height, 46):
        canvas.create_line(0, y, width, y, fill="#0b1020")
    for x in range(0, width, 46):
        canvas.create_line(x, 0, x, height, fill="#0b1020")

    random.seed(42)
    particles = []
    for _ in range(95):
        x = random.randint(20, width - 20)
        y = random.randint(20, height - 20)
        r = random.choice((1, 1, 1, 2))
        item = canvas.create_oval(x-r, y-r, x+r, y+r, fill=random.choice(("#16405a", "#15576d", "#28335c")), outline="")
        particles.append([item, x, y, random.uniform(-0.12, 0.12), random.uniform(-0.28, -0.05)])

    cx, cy = width // 2, 162
    for radius, color in ((104, "#0b1a2b"), (92, "#102b41"), (78, "#123e55")):
        canvas.create_oval(cx-radius, cy-radius, cx+radius, cy+radius, outline=color, width=2)

    ring = canvas.create_oval(cx-66, cy-66, cx+66, cy+66, outline="#64e7ff", width=3)
    glow_ring = canvas.create_oval(cx-82, cy-82, cx+82, cy+82, outline="#183b58", width=2)

    # Stylized TB mark.
    logo = canvas.create_polygon(
        cx, cy-49, cx+43, cy-24, cx+43, cy+24, cx, cy+49, cx-43, cy+24, cx-43, cy-24,
        fill="#07111c", outline="#64e7ff", width=2,
    )
    canvas.create_text(cx, cy-4, text="TB", fill="#edf8ff", font=("Segoe UI", 30, "bold"))
    canvas.create_text(cx, cy+28, text="AI", fill="#64e7ff", font=("Segoe UI", 9, "bold"))

    title = canvas.create_text(cx, 282, text="TRADEBOT", fill="#f2f7ff", font=("Segoe UI", 34, "bold"))
    subtitle = canvas.create_text(cx, 317, text="AI TRADING ENGINE", fill="#64e7ff", font=("Segoe UI", 11, "bold"))

    # Scanner line.
    scan_line = canvas.create_line(125, 347, 635, 347, fill="#15263b", width=2)
    scan_head = canvas.create_line(125, 347, 125, 347, fill="#64e7ff", width=3)

    canvas.create_rectangle(125, 370, 635, 378, fill="#0d1524", outline="")
    progress = canvas.create_rectangle(125, 370, 125, 378, fill="#64e7ff", outline="")
    status = canvas.create_text(cx, 405, text="Initializing AI core…", fill="#9aa9c4", font=("Segoe UI", 10))
    percent = canvas.create_text(635, 405, text="0%", fill="#64e7ff", font=("Segoe UI", 10, "bold"), anchor="e")
    footer = canvas.create_text(cx, 438, text="LIVE DATA  •  PAPER TRADING  •  MULTI-TIMEFRAME", fill="#4f617e", font=("Segoe UI", 8, "bold"))

    steps = [
        "Initializing AI core…",
        "Loading probability engine…",
        "Connecting to live market feed…",
        "Starting data collector…",
        "Loading strategy modules…",
        "Preparing control center…",
    ]

    start = time.perf_counter()

    def ease(t: float) -> float:
        return 1 - (1 - t) ** 3

    def animate(frame: int = 0) -> None:
        if not root.winfo_exists():
            return
        elapsed = time.perf_counter() - start
        t = min(1.0, elapsed / 3.2)
        p = ease(t)
        canvas.coords(progress, 125, 370, 125 + 510 * p, 378)
        canvas.itemconfigure(percent, text=f"{int(p*100):02d}%")
        canvas.itemconfigure(status, text=steps[min(len(steps)-1, int(p * len(steps)))])

        # Smooth scanning head and breathing glow.
        sweep = (frame * 8) % 510
        canvas.coords(scan_head, 125 + sweep, 342, 125 + sweep, 352)
        glow = 2 + int(1.5 * (1 + math.sin(frame / 6)))
        canvas.itemconfigure(ring, width=glow)
        canvas.coords(glow_ring, cx-82-glow, cy-82-glow, cx+82+glow, cy+82+glow)
        canvas.coords(logo, cx, cy-49-glow//2, cx+43, cy-24, cx+43, cy+24, cx, cy+49+glow//2, cx-43, cy+24, cx-43, cy-24)

        for item, x, y, vx, vy in particles:
            y += vy
            x += vx
            if y < 10:
                y = height - 12
            if x < 10 or x > width - 10:
                vx = -vx
            canvas.coords(item, x-1, y-1, x+1, y+1)

        if t < 1.0:
            root.after(30, animate, frame + 1)
        else:
            root.after(220, root.destroy)

    animate()
    return root


def start_server():
    import uvicorn
    from app.main import app

    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    config = uvicorn.Config(
        app,
        host=HOST,
        port=PORT,
        log_level="warning",
        access_log=False,
        log_config=None,
    )
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
        f"http://{HOST}:{PORT}/index.html",
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

    splash = show_splash()
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
