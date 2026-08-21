# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the IB-CMC Windows desktop experiment."""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

ROOT = Path.cwd()


def _openssl_binaries():
    """_ssl.pyd 와 같은 파이썬 설치본의 OpenSSL DLL을 강제로 넣는다.

    PyInstaller는 libssl/libcrypto를 시스템 PATH에서 찾는데, 이 PC에는 다른
    프로그램이 설치한 OpenSSL이 먼저 잡혀서 짝이 안 맞는 DLL이 들어갔었다.
    그러면 exe 안에서 `import _ssl`이 실패하고, 증상은 실험 도중 조용히
    "구글시트 연결 실패"로만 나타난다 (2026-08-22에 실제로 겪음).

    아나콘다 기반 venv면 base_prefix/Library/bin 에, python.org 배포본이면
    base_prefix/DLLs 에 있다. 둘 다 훑어서 있는 것만 담는다.
    """
    names = ("libssl-3-x64.dll", "libcrypto-3-x64.dll", "libssl-3.dll", "libcrypto-3.dll")
    base = Path(sys.base_prefix)
    found = []
    for folder in (base / "Library" / "bin", base / "DLLs", base):
        for name in names:
            dll = folder / name
            if dll.is_file():
                found.append((str(dll), "."))
        if found:
            break  # _ssl.pyd 와 같은 곳에서 나온 한 벌만 쓴다
    return found

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

binaries = _openssl_binaries()
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