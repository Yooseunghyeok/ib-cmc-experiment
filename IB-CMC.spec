# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the IB-CMC Windows desktop experiment."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all

ROOT = Path.cwd()

packages_to_collect = [
    "psychopy",
    "pyglet",
    "numpy",
    "scipy",
    "matplotlib",
    "pandas",
    "bidi",
    "gspread",
    "google",
    "google_auth_oauthlib",
    "googleapiclient",
]

binaries = []
datas = [
    (str(ROOT / "assets"), "assets"),
    (str(ROOT / "config"), "config"),
]
hiddenimports = [
    "__future__",
    "scipy._lib._ccallback_c",
    "bidi.bidi",
    "bidi.algorithm",
    "pandas._libs.pandas_parser",
]

for package_name in packages_to_collect:
    try:
        package_datas, package_binaries, package_hiddenimports = collect_all(package_name)
    except Exception:
        # Optional packages may not be installed depending on Google Sheets settings.
        continue
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports


a = Analysis(
    ["main.py"],
    pathex=[str(ROOT / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="IB-CMC",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="IB-CMC",
)