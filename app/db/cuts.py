from app.db.client import get_client

TABLE = "cash_cuts"


def save_cut(
    total: float, tickets: int, details: str, user_name: str = "ALKIMIA"
) -> dict:
    result = (
        get_client()
        .table(TABLE)
        .insert(
            {
                "total": total,
                "tickets": tickets,
                "details": details,
                "user_name": user_name,
            }
        )
        .execute()
    )
    return result.data[0] if result.data else {}


def list_cuts() -> list[dict]:
    result = get_client().table(TABLE).select("*").order("id", desc=True).execute()
    return result.data or []
