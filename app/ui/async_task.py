import logging
import queue
import threading

logger = logging.getLogger(__name__)


def run_async(
    widget,
    task,
    on_success=None,
    on_error=None,
    poll_ms: int = 30,
    progress: queue.Queue | None = None,
    on_progress=None,
) -> None:
    """Corre ``task`` en un hilo y entrega los callbacks en el hilo de UI.

    ``progress`` es una cola que la tarea puede llenar desde su propio hilo
    (``queue.put``); ``on_progress`` se llama en el hilo de UI con cada valor
    drenado, para actualizar la barra sin tocar Tkinter desde el hilo.
    """
    result: queue.Queue = queue.Queue()

    def worker() -> None:
        try:
            result.put((True, task()))
        except Exception as error:
            logger.warning("Tarea asincrona fallo: %s: %s", type(error).__name__, error)
            result.put((False, error))

    threading.Thread(target=worker, daemon=True).start()

    def drain_progress() -> None:
        if progress is None or on_progress is None:
            return
        while True:
            try:
                value = progress.get_nowait()
            except queue.Empty:
                return
            try:
                on_progress(value)
            except Exception:
                logger.exception("Excepcion en callback de progreso de tarea asincrona")

    def poll() -> None:
        drain_progress()
        try:
            ok, value = result.get_nowait()
        except queue.Empty:
            try:
                widget.after(poll_ms, poll)
            except Exception:
                pass
            return
        drain_progress()
        try:
            if not widget.winfo_exists():
                return
        except Exception:
            return
        try:
            if ok:
                if on_success is not None:
                    on_success(value)
            elif on_error is not None:
                on_error(value)
        except Exception:
            # Sin este try, la excepcion del callback se pierde silenciosamente
            # (Tkinter la manda a stderr, que en el .exe compilado no se ve).
            logger.exception("Excepcion en callback de tarea asincrona (ok=%s)", ok)

    widget.after(poll_ms, poll)
