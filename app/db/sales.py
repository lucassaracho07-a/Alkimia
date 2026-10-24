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
