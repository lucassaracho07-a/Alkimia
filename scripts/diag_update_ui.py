"""Prueba del dialogo de actualizacion: barra, descarga real y reintenario.

Levanta un servidor local y hace clic en "Actualizar ahora" sobre el dialogo
real, verificando que la barra pase a modo determinado con los MB, que la
descarga termine y que un fallo muestre el error y cambie el boton a
"Reintentar" (el caso que falto en la PC del cliente).
"""
import hashlib
import http.server
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import customtkinter as ctk  # noqa: E402

PAYLOAD = bytes(range(256)) * 4096  # 1 MB
EXPECTED_SHA = hashlib.sha256(PAYLOAD).hexdigest()
STATE = {"mode": "ok", "hits": 0}
ERRORS: list[str] = []
LAUNCHED: list[str] = []


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        STATE["hits"] += 1
        if STATE["mode"] == "not_found":
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Length", str(len(PAYLOAD)))
        self.end_headers()
        self.wfile.write(PAYLOAD)

    def log_message(self, *args):
        pass


class FakeMaster(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.user_name = "TEST"

    def currency_symbol(self):
        return "$"


def pump(widget, times: int = 50) -> None:
    for _ in range(times):
        widget.update()
        widget.after(20)
        widget.update()


def wait_for(predicate, dialog, limit: int = 600) -> bool:
    for _ in range(limit):
        dialog.update()
        dialog.after(20)
        dialog.update()
        if predicate():
            return True
    return predicate()


def main() -> int:
    from app.services import updates
    from app.ui.dialogs import actualizacion

    actualizacion.messagebox.showerror = lambda *a, **k: ERRORS.append(str(a[-1]))
    updates.launch_installer = lambda path: LAUNCHED.append(str(path))

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}/installer.exe"
    release = {
        "version": "9.9.9",
        "download_url": url,
        "sha256": EXPECTED_SHA,
        "notes": "Prueba de novedades: corte de caja con todos los productos.",
        "mandatory": False,
    }

    checks: list[tuple[str, str, bool]] = []

    # ---------- caso OK ----------
    STATE.update(mode="ok", hits=0)
    master = FakeMaster()
    dialog = actualizacion.UpdateDialog(master, release, mandatory=False)
    pump(dialog)

    checks.append(("dialogo visible", str(dialog.winfo_ismapped()),
                   dialog.winfo_ismapped()))
    checks.append(("novedades cargadas", dialog.notes_box.get("1.0", "end").strip()[:30],
                   "Prueba de novedades" in dialog.notes_box.get("1.0", "end")))
    checks.append(("boton inicial", dialog.update_button.cget("text"),
                   dialog.update_button.cget("text") == "Actualizar ahora"))

    dialog._close_app = lambda: None
    progress_calls: list[tuple[int, int | None]] = []
    seen_status: list[str] = []
    original_progress = dialog._on_progress

    def spy_progress(value):
        progress_calls.append(tuple(value))
        # Muestrea el texto mientras el progreso sigue vivo.
        original_progress(value)
        seen_status.append(str(dialog.status.cget("text")))

    dialog._on_progress = spy_progress
    dialog._start_update()
    checks.append(("busy al iniciar", str(dialog._busy), dialog._busy is True))
    checks.append(("boton deshabilitado", dialog.update_button.cget("text"),
                   dialog.update_button.cget("text") == "Descargando..."))
    done = wait_for(lambda: bool(LAUNCHED) or not dialog._busy, dialog)
    checks.append(("descarga termino", str(done), done))

    bar_mode = dialog.progress.cget("mode")
    bar_value = dialog.progress.get()
    checks.append(("barra determinada", str(bar_mode), bar_mode == "determinate"))
    checks.append(("barra llena", f"{bar_value:.2f}", abs(bar_value - 1.0) < 0.01))
    checks.append(("progreso invocado", str(progress_calls[:2]), bool(progress_calls)))
    checks.append(("progreso acumulado", str(progress_calls[-1] if progress_calls else None),
                   bool(progress_calls) and progress_calls[-1][0] == len(PAYLOAD)))
    mb_text = [text for text in seen_status if "MB" in text]
    checks.append(("estado con MB", str(mb_text[:1]), bool(mb_text)))
    checks.append(("estado en español", str(mb_text[:1]),
                   bool(mb_text) and mb_text[0].startswith("Descargando...")))
    checks.append(("instalador lanzado", str(LAUNCHED),
                   len(LAUNCHED) == 1 and Path(LAUNCHED[0]).exists()))
    checks.append(("sin error", str(ERRORS), ERRORS == []))

    dialog.destroy()
    master.destroy()

    # ---------- caso de fallo (el que falto en la PC del cliente) ----------
    ERRORS.clear()
    LAUNCHED.clear()
    STATE.update(mode="not_found", hits=0)
    bad = dict(release, version="9.9.8", download_url=url + "/x")
    master2 = FakeMaster()
    dialog2 = actualizacion.UpdateDialog(master2, bad, mandatory=False)
    pump(dialog2)
    dialog2._close_app = lambda: None
    dialog2._start_update()
    wait_for(lambda: not dialog2._busy, dialog2)

    checks.append(("fallo -> busy False", str(dialog2._busy), dialog2._busy is False))
    checks.append(("fallo -> boton Reintentar", dialog2.update_button.cget("text"),
                   dialog2.update_button.cget("text") == "Reintentar"))
    checks.append(("fallo -> mensaje", str(ERRORS),
                   len(ERRORS) == 1 and "404" in ERRORS[0]))
    checks.append(("fallo -> barra en 0", f"{dialog2.progress.get():.2f}",
                   dialog2.progress.get() == 0))

    dialog2.destroy()
    master2.destroy()
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
