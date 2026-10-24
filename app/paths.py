import os
import sys
from pathlib import Path

APP_NAME = "ALKIMIA"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def app_root() -> Path:
    """Carpeta donde vive el .exe (o la raíz del proyecto en dev).
    SOLO LECTURA cuando está instalado."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def resource_path(*parts: str) -> Path:
    """Assets empaquetados con PyInstaller (_MEIPASS) o archivos del repo en dev."""
    if is_frozen():
        base = Path(getattr(sys, "_MEIPASS", app_root()))
    else:
        base = Path(__file__).resolve().parents[1]
    return base.joinpath(*parts)


def app_data_dir() -> Path:
    """Carpeta escribible para DB, configs y logs del usuario."""
    if sys.platform == "win32":
        root = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    else:
        root = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    path = root / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


# Atajos concretos (opcional, pero te ahorra repetir rutas)
def db_path() -> Path:
    return app_data_dir() / "alkimia.db"

def config_path() -> Path:
    return app_data_dir() / "config.json"

def logs_dir() -> Path:
    p = app_data_dir() / "logs"
    p.mkdir(parents=True, exist_ok=True)
    return p