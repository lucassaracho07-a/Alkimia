"""Diagnóstico: cortes de caja vs ventas registradas."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import cuts, sales  # noqa: E402


def main() -> int:
    print("=== ULTIMOS 10 CORTES ===")
    rows = cuts.list_cuts()[:10]
    if not rows:
        print("(sin cortes)")
    for row in rows:
        print(
            f"  id={row.get('id')}  created_at={row.get('created_at')}  "
            f"total={row.get('total')}  tickets={row.get('tickets')}  "
            f"user={row.get('user_name')}  details={row.get('details')!r}"
        )

    print("\n=== VENTAS DE HOY ===")
    today = sales.sales_today()
    print(f"  cantidad: {len(today)}")
    for row in today[:10]:
        print(
            f"  ticket={row.get('ticket_number')}  created_at={row.get('created_at')}  "
            f"total={row.get('total')}  metodo={row.get('payment_method')}"
        )

    print("\n=== ULTIMAS 10 VENTAS (cualquier dia) ===")
    from app.db.client import get_client  # noqa: E402

    result = (
        get_client()
        .table("sales")
        .select("id, ticket_number, total, created_at")
        .order("id", desc=True)
        .limit(10)
        .execute()
    )
    for row in result.data or []:
        print(
            f"  id={row.get('id')}  ticket={row.get('ticket_number')}  "
            f"created_at={row.get('created_at')}  total={row.get('total')}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
