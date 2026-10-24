import base64
import hashlib
import hmac
import json
import secrets
import shutil
from pathlib import Path

from app.paths import app_data_dir, app_root

AUTH_FILE = app_data_dir() / "auth.json"
ITERATIONS = 240_000


def _migrate_legacy_auth(legacy: Path, target: Path) -> None:
    if target.exists() or not legacy.is_file():
        return
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(legacy, target)
    except OSError:
        pass


_migrate_legacy_auth(app_root() / "data" / "auth.json", AUTH_FILE)


def _encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _decode(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


def has_user() -> bool:
    return AUTH_FILE.exists()


def username() -> str:
    try:
        payload = json.loads(AUTH_FILE.read_text(encoding="utf-8"))
        return str(payload.get("username", ""))
    except (OSError, ValueError, KeyError):
        return ""


def create_user(user: str, password: str) -> None:
    user = user.strip()
    if not user:
        raise ValueError("El usuario es obligatorio.")
    if len(password) < 4:
        raise ValueError("La contraseña debe tener al menos 4 caracteres.")
    if has_user():
        raise ValueError("Ya existe un usuario registrado.")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    payload = {
        "username": user,
        "salt": _encode(salt),
        "hash": _encode(digest),
        "iterations": ITERATIONS,
    }
    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    AUTH_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def verify(user: str, password: str) -> bool:
    try:
        payload = json.loads(AUTH_FILE.read_text(encoding="utf-8"))
        stored_user = str(payload.get("username", ""))
        salt = _decode(payload["salt"])
        expected = _decode(payload["hash"])
        iterations = int(payload.get("iterations", ITERATIONS))
    except (OSError, ValueError, KeyError, TypeError):
        return False
    if user.strip() != stored_user:
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    return hmac.compare_digest(digest, expected)
