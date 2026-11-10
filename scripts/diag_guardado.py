"""Prueba aislada del camino de guardado de un corte de caja.

Inserta una fila de prueba en cash_cuts, la verifica y la borra.
Si el insert falla, ese es el error que ve el cliente.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import cuts  # noqa: E402
from app.db.client import get_client  # noqa: E402


def main() -> int:
    print("1) Probando cuts.save_cut() ...")
    try:
        row = cuts.save_cut(
            total=0,
            tickets=0,
            details="TEST diagnostico - borrar",
            user_name="TEST",
        )
        print(f"   OK, insert devolvio: {row}")
    except Exception as error:
        print(f"   FALLA: {type(error).__name__}: {error}")
        return 1

    cut_id = row.get("id")
    if not cut_id:
        print("   ALERTA: el insert no devolvio id (fila puede existir sin retorno).")
        rows = (
            get_client()
            .table("cash_cuts")
            .select("*")
            .eq("details", "TEST diagnostico - borrar")
            .execute()
            .data
            or []
        )
        print(f"   filas de prueba encontradas: {len(rows)}")
        for r in rows:
            cut_id = r["id"]
            break

    print(f"2) Verificando lectura con list_cuts() ...")
    all_cuts = cuts.list_cuts()
    found = any(c.get("id") == cut_id for c in all_cuts)
    print(f"   el corte de prueba aparece en list_cuts: {found}")

    print(f"3) Limpiando fila de prueba id={cut_id} ...")
    try:
        get_client().table("cash_cuts").delete().eq("id", cut_id).execute()
        remaining = [
            c for c in cuts.list_cuts() if c.get("id") == cut_id
        ]
        print(f"   borrada: {not remaining}")
    except Exception as error:
        print(f"   NO SE PUDO BORRAR: {type(error).__name__}: {error}")
        print("   (borrarla manualmente en el panel de Supabase)")
        return 1

    print("\nRESULTADO: el camino de guardado funciona.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
