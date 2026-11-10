import logging
import sys

import tkinter

from app.log import setup_logging
from app.ui.login import LoginWindow

logger = logging.getLogger("alkimia")


def main() -> None:
    setup_logging()

    def log_unhandled(exc_type, exc_value, exc_tb) -> None:
        logger.error("Excepcion no capturada", exc_info=(exc_type, exc_value, exc_tb))

    sys.excepthook = log_unhandled
    _install_tk_exception_logging()
    logger.info("ALKIMIA iniciando")
    LoginWindow().mainloop()
    logger.info("ALKIMIA finalizado")


def _install_tk_exception_logging() -> None:
    """Tkinter manda las excepciones de callbacks a stderr; en el .exe no se ve."""
    original = getattr(tkinter, "report_callback_exception", None)

    def report(exc, val, tb) -> None:
        logger.error("Excepcion en callback de la interfaz", exc_info=(exc, val, tb))
        if original is not None:
            original(exc, val, tb)

    tkinter.report_callback_exception = report


if __name__ == "__main__":
    main()
