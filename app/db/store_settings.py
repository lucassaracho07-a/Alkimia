from app.db.client import get_client

TABLE = "settings"

DEFAULTS = {
    "business_name": "ALKIMIA",
    "user_name": "ALKIMIA",
    "currency_symbol": "$",
    "ticket_footer": "Gracias por su compra",
    "default_unit": "U",
}


def get_settings() -> dict:
    result = get_client().table(TABLE).select("key,value").execute()
    values = dict(DEFAULTS)
    for row in result.data or []:
        values[row["key"]] = row["value"]
    return values


def save_settings(values: dict) -> None:
    rows = [{"key": str(key), "value": str(value)} for key, value in values.items()]
    if not rows:
        return
    get_client().table(TABLE).upsert(rows, on_conflict="key").execute()
