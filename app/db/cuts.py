import logging

from app.db.client import get_client

logger = logging.getLogger(__name__)

TABLE = "cash_cuts"


def save_cut(
    total: float, tickets: int, details: str, user_name: str = "ALKIMIA"
) -> dict:
    payload = {
        "total": total,
        "tickets": tickets,
        "details": details,
        "user_name": user_name,
    }
    logger.info("save_cut: INSERT %s -> %s", TABLE, payload)
    result = get_client().table(TABLE).insert(payload).execute()
    rows = result.data or []
    if not rows:
        # PostgREST devuelve lista vacia (sin excepcion) cuando RLS bloquea el
        # insert. Sin esta comprobacion la app reportaria "guardado" sin guardar.
        logger.error(
            "save_cut: el insert no devolvio filas (RLS/permisos bloquearon %s). status=%s",
            TABLE,
            getattr(result, "status_code", "?"),
        )
        raise RuntimeError(
            "El servidor no acepto el corte (permisos denegados sobre cash_cuts)."
        )
    logger.info("save_cut: OK fila id=%s", rows[0].get("id"))
    return rows[0]


def list_cuts() -> list[dict]:
    result = get_client().table(TABLE).select("*").order("id", desc=True).execute()
    return result.data or []
