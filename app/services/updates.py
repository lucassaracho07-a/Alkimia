import hashlib
import logging
import re
import ssl
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

import httpx

from app.db.client import get_client
from app.version import APP_VERSION

logger = logging.getLogger(__name__)

TABLE = "app_releases"
CHUNK_SIZE = 256 * 1024
DOWNLOAD_ATTEMPTS = 3
# Si en 60 s no llega un solo bloque, la conexion esta muerta: se reintenta.
READ_TIMEOUT = 60.0


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


def _tls_context() -> ssl.SSLContext:
    """Contexto TLS con las dos fuentes posibles de certificados.

    - certifi: viaja dentro del .exe, es la que ya usa httpx para Supabase.
    - load_default_certs: la tienda de certificados de Windows.

    Se cargan juntos para que la descarga funcione aunque una de las dos
    fuentes este vacia o corrupta en la PC del cliente.
    """
    import certifi

    context = ssl.create_default_context(cafile=certifi.where())
    try:
        context.load_default_certs(ssl.Purpose.SERVER_AUTH)
    except (OSError, ssl.SSLError):  # pragma: no cover - tienda no disponible
        pass
    return context


def _unwrap(error: BaseException, limit: int = 6) -> BaseException:
    """Baja la cadena __cause__/__context__ hasta encontrar el error real."""
    current = error
    seen = 0
    while seen < limit:
        deeper = current.__cause__ or current.__context__
        if deeper is None:
            break
        current = deeper
        seen += 1
    return current


def _retryable(error: BaseException) -> bool:
    """Solo se reintentan fallos de red; un 404 o un certificado malo no."""
    root = _unwrap(error)
    if isinstance(root, ssl.SSLError):
        return False
    if isinstance(error, httpx.HTTPStatusError):
        code = error.response.status_code
        return code >= 500 or code == 429
    return isinstance(error, (httpx.TimeoutException, httpx.NetworkError))


def _download_once(url: str, target: Path, progress) -> None:
    # httpx valida contra certifi, que viaja dentro del .exe; urllib usaba la
    # CA del sistema, que en la PC del cliente no existia.
    with httpx.stream(
        "GET",
        url,
        headers={"User-Agent": "ALKIMIA-POS-Updater"},
        follow_redirects=True,
        timeout=httpx.Timeout(READ_TIMEOUT, connect=20.0),
        verify=_tls_context(),
    ) as response:
        response.raise_for_status()
        header = str(response.headers.get("content-length") or "")
        total = int(header) if header.isdigit() else None
        done = 0
        with target.open("wb") as file:
            for chunk in response.iter_bytes(CHUNK_SIZE):
                file.write(chunk)
                done += len(chunk)
                if progress is not None:
                    progress(done, total)


def download_installer(
    release: dict,
    progress: Callable[[int, int | None], None] | None = None,
) -> Path:
    url = str(release.get("download_url") or "").strip()
    if not url:
        raise ValueError("La actualización no tiene un enlace de descarga.")

    expected = str(release.get("sha256") or "").strip().lower()
    if not expected:
        raise ValueError("La actualización no tiene SHA-256 para verificar.")

    version = re.sub(
        r"[^0-9A-Za-z._-]+", "-", str(release.get("version") or "nueva")
    )
    target = Path(tempfile.gettempdir()) / f"ALKIMIA-Setup-{version}.exe"

    failure: BaseException | None = None
    for attempt in range(1, DOWNLOAD_ATTEMPTS + 1):
        try:
            _download_once(url, target, progress)
            failure = None
            break
        except Exception as error:
            target.unlink(missing_ok=True)
            failure = error
            retry = _retryable(error) and attempt < DOWNLOAD_ATTEMPTS
            logger.warning(
                "Actualizacion: descarga fallo (intento %s/%s, retry=%s): %s: %s",
                attempt,
                DOWNLOAD_ATTEMPTS,
                retry,
                type(error).__name__,
                error,
            )
            if not retry:
                break

    if failure is not None:
        friendly = _friendly(failure)
        if friendly is failure:
            raise failure
        raise friendly from failure

    digest = hashlib.sha256()
    with target.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != expected:
        target.unlink(missing_ok=True)
        raise ValueError(
            "El instalador descargado no coincide con el SHA-256 publicado."
        )
    logger.info(
        "Actualizacion: instalador verificado (%s bytes, sha256 ok)", target.stat().st_size
    )
    return target


def _friendly(error: BaseException) -> BaseException:
    """Convierte errores criptograficos/de red en un mensaje accionable."""
    root = _unwrap(error)
    if isinstance(root, ssl.SSLCertVerificationError):
        return ValueError(
            "No se pudo validar el certificado seguro del sitio de descarga.\n\n"
            "Detalle tecnico: " + str(root)
        )
    if isinstance(error, httpx.HTTPStatusError):
        code = error.response.status_code
        if code == 404:
            return ValueError(
                "El instalador ya no esta disponible (404). Consulta con soporte."
            )
        return ValueError(f"El servidor respondio con error HTTP {code}.")
    if isinstance(root, (httpx.TimeoutException, httpx.NetworkError)):
        return ValueError(
            "No se pudo descargar el instalador: la conexion se interrumpio "
            "o esta muy lenta.\n\n"
            "Revisa tu conexion a internet y presiona \"Reintentar\"."
        )
    return error


def launch_installer(path: Path) -> None:
    args = [str(path)]
    if sys.platform == "win32":
        args.extend(["/SILENT", "/CLOSEAPPLICATIONS", "/NORESTART"])
    subprocess.Popen(args, close_fds=True)
