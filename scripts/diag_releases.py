"""Consulta rapida: app_releases (que versiones estan publicadas)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.client import get_client  # noqa: E402


def main() -> int:
    result = (
        get_client()
        .table("app_releases")
        .select("*")
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )
    rows = result.data or []
    if not rows:
        print("app_releases: sin filas")
    for row in rows:
        print(
            f"  v{row.get('version')}  mandatory={row.get('mandatory')}  "
            f"min={row.get('min_supported_version')}  created={row.get('created_at')}  "
            f"notes={row.get('notes')!r}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
