from datetime import date, datetime, time, timedelta

from app.db.client import get_client

TABLE = "sales"


def register_sale(
    items: list[dict],
    amount_received: float | None = None,
    change_amount: float | None = None,
    payment_method: str = "Efectivo",
    user_name: str = "ALKIMIA",
) -> dict:
    result = (
        get_client()
        .rpc(
            "register_sale",
            {
                "p_items": items,
                "p_payment_method": payment_method,
                "p_amount_received": amount_received,
                "p_change_amount": change_amount,
                "p_user_name": user_name,
            },
        )
        .execute()
    )
    data = result.data
    if isinstance(data, list):
        return data[0] if data else {}
    return data or {}


def next_ticket_number() -> int:
    result = (
        get_client()
        .table(TABLE)
        .select("ticket_number")
        .order("ticket_number", desc=True)
        .limit(1)
        .execute()
    )
    if result.data:
        return int(result.data[0]["ticket_number"]) + 1
    return 1


def sales_today() -> list[dict]:
    start = datetime.combine(date.today(), time.min).astimezone()
    end = start + timedelta(days=1)
    result = (
        get_client()
        .table(TABLE)
        .select("*")
        .gte("created_at", start.isoformat())
        .lt("created_at", end.isoformat())
        .order("ticket_number")
        .execute()
    )
    return result.data or []


def items_for_sales(sale_ids: list[int]) -> list[dict]:
    """Detalle (nombre, cantidad) de los renglones de las ventas indicadas."""
    ids = [int(value) for value in sale_ids if value]
    if not ids:
        return []
    result = (
        get_client()
        .table("sale_items")
        .select("name, qty")
        .in_("sale_id", ids)
        .execute()
    )
    return result.data or []


def top_product_today() -> tuple[str, float]:
    """(nombre, unidades) del producto mas vendido hoy. ("", 0) si no hay."""
    rows = items_for_sales([row.get("id") for row in sales_today()])
    return top_product_from_items(rows)


def products_ranked(items: list[dict]) -> list[tuple[str, float]]:
    """Todos los productos vendidos, de mas vendido a menos: [(nombre, unidades)].

    Suma las unidades de cada renglon por nombre. Ordena por unidades
    descendente; a igualdad desempata por nombre para que el resultado sea
    estable entre ejecuciones.
    """
    totals: dict[str, float] = {}
    for item in items:
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        try:
            qty = float(item.get("qty") or 0)
        except (TypeError, ValueError):
            continue
        totals[name] = totals.get(name, 0.0) + qty
    return sorted(totals.items(), key=lambda pair: (-pair[1], pair[0]))


def top_products_from_items(
    items: list[dict], limit: int = 3
) -> list[tuple[str, float]]:
    """Primeros `limit` productos del ranking (ver products_ranked)."""
    ranked = products_ranked(items)
    if limit <= 0:
        return []
    return ranked[:limit]


def top_product_from_items(items: list[dict]) -> tuple[str, float]:
    """(nombre, unidades) del producto mas vendido. ("", 0) si no hay."""
    ranking = top_products_from_items(items, limit=1)
    return ranking[0] if ranking else ("", 0.0)
