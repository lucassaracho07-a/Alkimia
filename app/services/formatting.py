from datetime import datetime


def money(value, symbol: str = "$") -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    return f"{symbol}{number:,.2f}"


def qty_text(value) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "0"
    return f"{number:g}"


def price_text(value) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    return f"{number:.2f}"


def parse_number(value: str) -> float:
    text = (value or "").strip().replace(" ", "")
    if not text:
        return 0.0
    text = text.replace(",", ".")
    return float(text)


def local_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).astimezone()
    except ValueError:
        return None


def datetime_text(value: str) -> str:
    parsed = local_datetime(value)
    if parsed is None:
        return value or ""
    return parsed.strftime("%Y-%m-%d %H:%M:%S")
