# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_data_files

# IMPORTANT: build TRADENEX as ONEDIR, not ONEFILE.
# The previous one-file builds failed on the user's Windows machine while
# reopening the embedded PyInstaller archive during extraction. ONEDIR keeps
# the Python files and native libraries beside the executable, so there is no
# runtime self-extraction step and therefore no _MEI archive extraction risk.
app_datas, app_binaries, app_hiddenimports = collect_all("app")
app_py_sources = collect_data_files("app", include_py_files=True)

hiddenimports = list(dict.fromkeys(
    list(app_hiddenimports)
    + [
        "app",
        "app.demo",
        "app.demo_enhancements",
        "app.strategies",
        "webview",
    ]
))

datas = list(app_datas) + list(app_py_sources) + [("web", "web")]


a = Analysis(
    ["launcher.py"],
    pathex=["."],
    binaries=list(app_binaries),
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest"],
    noarchive=True,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TRADENEX",
    icon="web/tradenex.ico",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    version=None,
    uac_admin=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="TRADENEX",
)
