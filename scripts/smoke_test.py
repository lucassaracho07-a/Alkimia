import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import cuts, products, sales, store_settings


def main() -> int:
    checks: list[tuple[str, str]] = []

    try:
        values = store_settings.get_settings()
        checks.append(("settings", f"OK ({len(values)} claves)"))
    except Exception as error:
        checks.append(("settings", f"ERROR: {error}"))

    try:
        rows = products.list_products()
        checks.append(("products", f"OK ({len(rows)} productos)"))
    except Exception as error:
        checks.append(("products", f"ERROR: {error}"))

    try:
        number = sales.next_ticket_number()
        checks.append(("ticket", f"OK (próximo #{number})"))
    except Exception as error:
        checks.append(("ticket", f"ERROR: {error}"))

    try:
        rows = sales.sales_today()
        checks.append(("sales (hoy)", f"OK ({len(rows)} ventas)"))
    except Exception as error:
        checks.append(("sales (hoy)", f"ERROR: {error}"))

    try:
        rows = cuts.list_cuts()
        checks.append(("cash_cuts", f"OK ({len(rows)} cortes)"))
    except Exception as error:
        checks.append(("cash_cuts", f"ERROR: {error}"))

    for name, status in checks:
        print(f"{name:14} {status}")

    return 0 if all(status.startswith("OK") for _, status in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
