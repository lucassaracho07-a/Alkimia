# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

project_dir = Path(SPECPATH)

datas = []
binaries = []
hiddenimports = []

for package in (
    "customtkinter",
    "supabase",
    "postgrest",
    "gotrue",
    "storage3",
    "realtime",
):
    try:
        package_datas, package_binaries, package_hiddenimports = collect_all(package)
    except Exception:
        continue
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

assets_dir = project_dir / "assets"
if assets_dir.is_dir():
    datas.append((str(assets_dir), "assets"))

env_file = project_dir / ".env"
if env_file.is_file():
    datas.append((str(env_file), "."))

icon_file = assets_dir / "alkimia.ico"

a = Analysis(
    ["main.py"],
    pathex=[str(project_dir)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ALKIMIA",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_file) if icon_file.is_file() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ALKIMIA",
)
