"""Prueba del filtro de fechas de sales_today() replicando su logica."""
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.client import get_client  # noqa: E402


def query_range(start: datetime, end: datetime) -> list[dict]:
    result = (
        get_client()
        .table("sales")
        .select("id, ticket_number, total, created_at")
        .gte("created_at", start.isoformat())
        .lt("created_at", end.isoformat())
        .order("ticket_number")
        .execute()
    )
    return result.data or []


def main() -> int:
    print(f"date.today() = {date.today()}")
    print(f"datetime.now() = {datetime.now()}")

    # Misma logica que app/db/sales.py::sales_today
    start = datetime.combine(date.today(), time.min).astimezone()
    end = start + timedelta(days=1)
    print(f"rango de sales_today: {start.isoformat()} .. {end.isoformat()}")
    rows = query_range(start, end)
    print(f"ventas devueltas: {len(rows)}")

    # Replicar el rango de AYER para ver si el filtro encuentra dias con ventas
    y = date.today() - timedelta(days=1)
    s2 = datetime.combine(y, time.min).astimezone()
    e2 = s2 + timedelta(days=1)
    print(f"\nrango de ayer: {s2.isoformat()} .. {e2.isoformat()}")
    rows2 = query_range(s2, e2)
    print(f"ventas de ayer: {len(rows2)}")
    for row in rows2:
        print(f"  ticket={row['ticket_number']} total={row['total']} at={row['created_at']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
