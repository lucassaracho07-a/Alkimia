import hashlib
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from app.db.client import get_client
from app.version import APP_VERSION

TABLE = "app_releases"
CHUNK_SIZE = 256 * 1024


def _version_tuple(value: str) -> tuple[int, ...]:
    numbers = re.findall(r"\d+", str(value or ""))
    if not numbers:
        return (0,)
    return tuple(int(part) for part in numbers[:4])


def is_newer(remote: str, local: str = APP_VERSION) -> bool:
    return _version_tuple(remote) > _version_tuple(local)


def is_mandatory(release: dict, local: str = APP_VERSION) -> bool:
    if bool(release.get("mandatory")):
        return True
    minimum = str(release.get("min_supported_version") or "").strip()
    return bool(minimum) and _version_tuple(local) < _version_tuple(minimum)


def latest_release() -> dict | None:
    result = (
        get_client()
        .table(TABLE)
        .select("*")
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    rows = result.data or []
    best = None
    for row in rows:
        version = str(row.get("version") or "").strip()
        if not version:
            continue
        if best is None or _version_tuple(version) > _version_tuple(
            best.get("version", "")
        ):
            best = row
    return best


def download_installer(release: dict) -> Path:
    url = str(release.get("download_url") or "").strip()
    if not url:
        raise ValueError("La actualización no tiene un enlace de descarga.")
    version = re.sub(
        r"[^0-9A-Za-z._-]+", "-", str(release.get("version") or "nueva")
    )
    target = Path(tempfile.gettempdir()) / f"ALKIMIA-Setup-{version}.exe"
    request = urllib.request.Request(
        url, headers={"User-Agent": "ALKIMIA-POS-Updater"}
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response, target.open(
            "wb"
        ) as file:
            while True:
                chunk = response.read(CHUNK_SIZE)
                if not chunk:
                    break
                file.write(chunk)
    except Exception:
        target.unlink(missing_ok=True)
        raise

    expected = str(release.get("sha256") or "").strip().lower()
    if not expected:
        target.unlink(missing_ok=True)
        raise ValueError("La actualización no tiene SHA-256 para verificar.")

    digest = hashlib.sha256()
    with target.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != expected:
        target.unlink(missing_ok=True)
        raise ValueError(
            "El instalador descargado no coincide con el SHA-256 publicado."
        )
    return target


def launch_installer(path: Path) -> None:
    args = [str(path)]
    if sys.platform == "win32":
        args.extend(["/SILENT", "/CLOSEAPPLICATIONS", "/NORESTART"])
    subprocess.Popen(args, close_fds=True)
