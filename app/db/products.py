from app.db.client import get_client

TABLE = "products"
FIELDS = (
    "barcode",
    "code",
    "name",
    "price",
    "price_wholesale",
    "unit",
    "stock",
    "active",
)


def _clean_payload(data: dict) -> dict:
    payload = {key: data[key] for key in FIELDS if key in data}
    for key in ("barcode", "code"):
        if key in payload:
            value = (payload[key] or "").strip()
            payload[key] = value or None
    if "name" in payload:
        payload["name"] = (payload["name"] or "").strip()
    if "unit" in payload:
        payload["unit"] = (payload["unit"] or "").strip() or "U"
    return payload


def list_products(search: str = "") -> list[dict]:
    query = get_client().table(TABLE).select("*").eq("active", True)
    term = (search or "").strip()
    if term:
        term = term.replace(",", " ").replace("(", " ").replace(")", " ")
        query = query.or_(
            f"name.ilike.%{term}%,code.ilike.%{term}%,barcode.ilike.%{term}%"
        )
    result = query.order("id").execute()
    return result.data or []


def find_exact(value: str) -> dict | None:
    term = (value or "").strip()
    if not term:
        return None
    client = get_client()
    for column in ("barcode", "code"):
        result = (
            client.table(TABLE)
            .select("*")
            .eq(column, term)
            .eq("active", True)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]
    result = (
        client.table(TABLE)
        .select("*")
        .ilike("name", term)
        .eq("active", True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def get_product(product_id: int) -> dict | None:
    result = (
        get_client().table(TABLE).select("*").eq("id", product_id).limit(1).execute()
    )
    return result.data[0] if result.data else None


def create_product(data: dict) -> dict:
    result = get_client().table(TABLE).insert(_clean_payload(data)).execute()
    return result.data[0]


def update_product(product_id: int, data: dict) -> dict:
    result = (
        get_client()
        .table(TABLE)
        .update(_clean_payload(data))
        .eq("id", product_id)
        .execute()
    )
    return result.data[0] if result.data else {}


def delete_product(product_id: int) -> None:
    get_client().table(TABLE).delete().eq("id", product_id).execute()
