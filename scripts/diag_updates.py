"""Prueba del actualizador: descarga, progreso, reintentos y verificacion.

Levanta un servidor HTTP local para probar download_installer() sin depender
de la red externa: descarga correcta, progreso emitido, reintento ante 500,
404 amigable, SHA-256 correcto/incorrecto y mensajes de error en espanol.
"""
import hashlib
import http.server
import ssl
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402

from app.services import updates  # noqa: E402

PAYLOAD = bytes(range(256)) * 4096  # 1 MB
EXPECTED_SHA = hashlib.sha256(PAYLOAD).hexdigest()

STATE = {"mode": "ok", "hits": 0}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        STATE["hits"] += 1
        if self.path != "/installer.exe":
            self.send_error(404)
            return
        if STATE["mode"] == "fail_once" and STATE["hits"] == 1:
            self.send_error(500)
            return
        if STATE["mode"] == "not_found":
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Length", str(len(PAYLOAD)))
        self.end_headers()
        self.wfile.write(PAYLOAD)

    def log_message(self, *args):  # silencia el servidor
        pass


def expect_error(label, needle, func, checks):
    try:
        func()
    except Exception as error:
        text = str(error)
        checks.append((label, text, needle.lower() in text.lower()))
    else:
        checks.append((label, "no lanzo excepcion", False))


def main() -> int:
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}/installer.exe"
    checks: list[tuple[str, str, bool]] = []

    # 1) Contexto TLS con certificados (certifi + tienda de Windows)
    ctx = updates._tls_context()
    checks.append(("tls con CA", str(len(ctx.get_ca_certs())),
                   len(ctx.get_ca_certs()) > 50))

    # 2) Descarga correcta con progreso
    STATE.update(mode="ok", hits=0)
    seen: list[tuple[int, int | None]] = []
    release = {"version": "9.9.9", "download_url": url, "sha256": EXPECTED_SHA}
    try:
        path = updates.download_installer(
            release, progress=lambda done, total: seen.append((done, total))
        )
        ok = hashlib.sha256(path.read_bytes()).hexdigest() == EXPECTED_SHA
        checks.append(("descarga + sha", path.name, ok))
        checks.append(("progreso final", str(seen[-1] if seen else None),
                       bool(seen) and seen[-1][0] == len(PAYLOAD)
                       and seen[-1][1] == len(PAYLOAD)))
        checks.append(("progreso incremental", str(len(seen)), len(seen) > 1))
        path.unlink(missing_ok=True)
    except Exception as error:
        checks.append(("descarga + sha", f"{type(error).__name__}: {error}", False))

    # 3) Reintenta ante un 500 y termina bien
    STATE.update(mode="fail_once", hits=0)
    try:
        path = updates.download_installer(release)
        checks.append(("reintento 500", f"hits={STATE['hits']}", STATE["hits"] == 2))
        path.unlink(missing_ok=True)
    except Exception as error:
        checks.append(("reintento 500", f"{type(error).__name__}: {error}", False))

    # 4) 404 -> mensaje claro, sin reintentar inutilmente
    STATE.update(mode="not_found", hits=0)
    expect_error("404 amigable", "404",
                 lambda: updates.download_installer(release), checks)
    checks.append(("404 sin reintentos", f"hits={STATE['hits']}", STATE["hits"] == 1))

    # 5) Validaciones previas
    expect_error("sin url", "enlace de descarga",
                 lambda: updates.download_installer(
                     {"version": "1", "download_url": "", "sha256": "aa"}),
                 checks)
    expect_error("sin sha", "SHA-256",
                 lambda: updates.download_installer(
                     {"version": "1", "download_url": url, "sha256": ""}),
                 checks)
    STATE.update(mode="ok", hits=0)
    expect_error("sha incorrecto", "SHA-256",
                 lambda: updates.download_installer(
                     {"version": "1", "download_url": url, "sha256": "0" * 64}),
                 checks)

    # 6) Clasificacion de reintentos
    checks.append(("retry ReadTimeout", str(updates._retryable(httpx.ReadTimeout("x"))),
                   updates._retryable(httpx.ReadTimeout("x")) is True))
    checks.append(("retry ConnectError", str(updates._retryable(httpx.ConnectError("x"))),
                   updates._retryable(httpx.ConnectError("x")) is True))
    checks.append(("no retry SSL",
                   str(updates._retryable(ssl.SSLCertVerificationError("x"))),
                   updates._retryable(ssl.SSLCertVerificationError("x")) is False))
    checks.append(("no retry 404",
                   str(updates._retryable(httpx.HTTPStatusError(
                       "x", request=httpx.Request("GET", "u"),
                       response=httpx.Response(404)))),
                   updates._retryable(httpx.HTTPStatusError(
                       "x", request=httpx.Request("GET", "u"),
                       response=httpx.Response(404))) is False))

    # 7) Mensajes en espanol para los fallos tipicos
    ssl_msg = str(updates._friendly(ssl.SSLCertVerificationError("boom")))
    checks.append(("mensaje SSL", ssl_msg, "certificado" in ssl_msg.lower()))
    timeout_msg = str(updates._friendly(httpx.ReadTimeout("slow")))
    checks.append(("mensaje de red", timeout_msg,
                   "Reintentar" in timeout_msg))

    # 8) Version
    newer = (updates.is_newer("9.9.9"), updates.is_newer("1.0.0"))
    checks.append(("is_newer", str(newer), newer == (True, False)))

    server.shutdown()

    ok = True
    for label, value, passed in checks:
        if not passed:
            ok = False
        print(f"[{'OK  ' if passed else 'FALLA'}] {label}: {value}")
    print("\nRESULTADO:", "TODO OK" if ok else "HAY FALLOS")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
