"""Quien hizo las ventas recientes y con que usuario (para saber si son del cliente)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.client import get_client  # noqa: E402


def main() -> int:
    result = (
        get_client()
        .table("sales")
        .select("id, ticket_number, total, user_name, payment_method, created_at")
        .order("id", desc=True)
        .limit(15)
        .execute()
    )
    for row in result.data or []:
        print(
            f"  ticket={row.get('ticket_number')}  user={row.get('user_name')!r}  "
            f"metodo={row.get('payment_method')!r}  total={row.get('total')}  "
            f"at={row.get('created_at')}"
        )

    print("\nsettings actuales:")
    result = get_client().table("settings").select("key,value").execute()
    for row in result.data or []:
        print(f"  {row.get('key')} = {row.get('value')!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
