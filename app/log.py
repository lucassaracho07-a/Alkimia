"""Logging de la aplicación.

Escribe en %LOCALAPPDATA%\\ALKIMIA\\logs\\alkimia.log con rotación, para que
los errores queden registrados aunque la app esté compilada y sin consola.
"""

import logging
import sys
import threading
from logging.handlers import RotatingFileHandler

from app.paths import is_frozen, logs_dir

LOG_FILE = "alkimia.log"
MAX_BYTES = 512 * 1024
BACKUP_COUNT = 3
FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"

_configured = False


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configura el logging una sola vez y devuelve el logger de la app."""
    global _configured
    if _configured:
        return logging.getLogger("alkimia")
    _configured = True

    formatter = logging.Formatter(FORMAT)
    root = logging.getLogger()
    root.setLevel(level)

    file_handler = RotatingFileHandler(
        logs_dir() / LOG_FILE,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    # En desarrollo también a consola; el .exe compilado no tiene consola.
    if not is_frozen():
        console = logging.StreamHandler(sys.stderr)
        console.setFormatter(formatter)
        root.addHandler(console)

    sys.excepthook = _excepthook
    threading.excepthook = _thread_excepthook
    _patch_tk_callback_errors()

    return logging.getLogger("alkimia")


def _excepthook(exc_type, exc, tb) -> None:
    logging.getLogger("alkimia").critical(
        "Excepción no controlada", exc_info=(exc_type, exc, tb)
    )
    sys.__excepthook__(exc_type, exc, tb)


def _thread_excepthook(args) -> None:
    logging.getLogger("alkimia").error(
        "Excepción en hilo secundario", exc_info=(args.exc_type, args.exc_value, args.exc_traceback)
    )


def _patch_tk_callback_errors() -> None:
    """Registra en el log las excepciones que tkinter descarta de los callbacks."""
    try:
        import tkinter
    except Exception:  # pragma: no cover - tkinter siempre disponible en escritorio
        return

    # Los callbacks de todos los widgets terminan en Tk.report_callback_exception.
    original = tkinter.Tk.report_callback_exception
    if getattr(original, "_alkimia_logged", False):
        return

    def report(self, exc, val, tb):
        logging.getLogger("tkinter").error(
            "Excepción en callback de la interfaz", exc_info=(exc, val, tb)
        )
        original(self, exc, val, tb)

    report._alkimia_logged = True  # type: ignore[attr-defined]
    tkinter.Tk.report_callback_exception = report
