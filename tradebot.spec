# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_data_files

# Do not rely on import analysis alone for this package. The previous builds
# passed hidden-imports but still produced an EXE that could not import
# app.demo at runtime. Collect the complete app package and its Python source
# files, then keep a clean explicit hidden-import list as a second guard.
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
