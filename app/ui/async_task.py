import queue
import threading


def run_async(widget, task, on_success=None, on_error=None, poll_ms: int = 30) -> None:
    result: queue.Queue = queue.Queue()

    def worker() -> None:
        try:
            result.put((True, task()))
        except Exception as error:
            result.put((False, error))

    threading.Thread(target=worker, daemon=True).start()

    def poll() -> None:
        try:
            ok, value = result.get_nowait()
        except queue.Empty:
            try:
                widget.after(poll_ms, poll)
            except Exception:
                pass
            return
        try:
            if not widget.winfo_exists():
                return
        except Exception:
            return
        if ok:
            if on_success is not None:
                on_success(value)
        elif on_error is not None:
            on_error(value)

    widget.after(poll_ms, poll)
