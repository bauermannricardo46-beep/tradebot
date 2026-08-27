# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

# Explicitly include the runtime modules used by the FastAPI demo engine.
# collect_submodules("app") is kept as a broad safety net, while the explicit
# imports prevent PyInstaller from omitting app.demo in the frozen build.
hiddenimports = collect_submodules("app") + [
    "app.demo",
    "app.demo_enhancements",
    "app.strategies",
    "webview",
]

# De-duplicate while preserving order.
hiddenimports = list(dict.fromkeys(hiddenimports))

a = Analysis(
    ["launcher.py"],
    pathex=["."],
    binaries=[],
    datas=[("web", "web")],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="TRADENEX",
    icon="web/tradenex.ico",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    version=None,
    uac_admin=False,
)
