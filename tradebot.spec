# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_data_files

# Windows release is ONEDIR. Keep native Python libraries beside the EXE and
# avoid both PyInstaller ONEFILE extraction and pywebview/pythonnet loading.
app_datas, app_binaries, app_hiddenimports = collect_all("app")
app_py_sources = collect_data_files("app", include_py_files=True)

hiddenimports = list(dict.fromkeys(
    list(app_hiddenimports)
    + [
        "app",
        "app.demo",
        "app.demo_enhancements",
        "app.strategies",
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
    excludes=["pytest", "webview", "pythonnet", "clr_loader"],
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
