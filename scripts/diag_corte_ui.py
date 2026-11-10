"""Prueba de la ventana de corte: lista completa de productos vendidos.

Parchea app.db.sales para devolver datos de prueba (sin tocar la base) y
verifica que la ventana liste todos los productos ordenados del mas vendido
al menos, y que el 'details' guardado incluya la lista completa.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import customtkinter as ctk  # noqa: E402

from app.db import sales  # noqa: E402

FAKE_SALES = [
    {"id": 1, "ticket_number": 1, "total": 10000, "payment_method": "Efectivo"},
    {"id": 2, "ticket_number": 2, "total": 5000, "payment_method": "Efectivo"},
]

FAKE_ITEMS = [
    {"name": "Coca cola 2lt", "qty": 2},
    {"name": "Corona 710ml", "qty": 5},
    {"name": "Coca cola 2lt", "qty": 1},
    {"name": "Pan", "qty": 3},
    {"name": "Agua mineral", "qty": 1},
]


def product_rows(window) -> list[tuple[str, str]]:
    """(nombre, unidades) de cada fila pintada en la lista de productos."""
    rows = []
    for child in window.products.winfo_children():
        labels = [
            label.cget("text")
            for label in child.winfo_children()
            if isinstance(label, ctk.CTkLabel)
        ]
        if len(labels) == 2:
            rows.append((labels[0], labels[1]))
    return rows


class FakeMaster(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.user_name = "TEST"
        self._history_refreshed = False

    def currency_symbol(self):
        return "$"

    def refresh_history(self):
        self._history_refreshed = True


def pump(window, times: int = 10) -> None:
    for _ in range(times):
        window.update()
        window.after(40)
        window.update()


def main() -> int:
    from app.ui.views.corte_caja import CorteCajaWindow

    checks: list[tuple[str, str, bool]] = []

    # 1) Orden del ranking (logica pura)
    ranking = sales.products_ranked(FAKE_ITEMS)
    expected = [
        ("Corona 710ml", 5.0),
        ("Coca cola 2lt", 3.0),
        ("Pan", 3.0),
        ("Agua mineral", 1.0),
    ]
    checks.append(("ranking ordenado", str(ranking), ranking == expected))
    checks.append(
        ("ranking con limit", str(sales.top_products_from_items(FAKE_ITEMS, 2)),
         sales.top_products_from_items(FAKE_ITEMS, 2) == expected[:2])
    )
    checks.append(
        ("ranking vacio", str(sales.products_ranked([])), sales.products_ranked([]) == [])
    )

    # 2) Ventana con datos
    sales.sales_today = lambda: list(FAKE_SALES)
    sales.items_for_sales = lambda ids: list(FAKE_ITEMS)

    master = FakeMaster()
    window = CorteCajaWindow(master)
    pump(window)  # deja que llegue el resultado asincrono

    units_text = window.units_label.cget("text")
    checks.append(("unidades", units_text, units_text == "Unidades vendidas: 12"))

    rows = product_rows(window)
    checks.append(
        ("lista completa", str(rows),
         rows == [
             ("Corona 710ml", "5 un."),
             ("Coca cola 2lt", "3 un."),
             ("Pan", "3 un."),
             ("Agua mineral", "1 un."),
         ])
    )

    details = window._details()
    checks.append(
        ("details con todos",
         details,
         "Productos: Corona 710ml (5 un.), Coca cola 2lt (3 un.), Pan (3 un.), Agua mineral (1 un.)" in details)
    )
    checks.append(("details con unidades", details, "Unidades: 12" in details))
    checks.append(
        ("details con medios", details, "Efectivo: $15,000.00 (2 ventas)" in details)
    )

    # 3) Caso sin ventas
    sales.sales_today = lambda: []
    sales.items_for_sales = lambda ids: []
    window.refresh()
    pump(window)

    empty_details = window._details()
    empty_rows = product_rows(window)
    empty_text = [
        child.cget("text")
        for child in window.products.winfo_children()
        if isinstance(child, ctk.CTkLabel)
    ]
    checks.append(("sin ventas -> details vacio", repr(empty_details), empty_details == ""))
    checks.append(("sin ventas -> lista", str(empty_rows), empty_rows == []))
    checks.append(
        ("sin ventas -> aviso", str(empty_text),
         empty_text == ["No hay productos vendidos hoy."])
    )
    checks.append(
        ("sin ventas -> unidades 0",
         window.units_label.cget("text"),
         window.units_label.cget("text") == "Unidades vendidas: 0")
    )

    window.destroy()
    master.destroy()

    ok = True
    for label, value, passed in checks:
        status = "OK  " if passed else "FALLA"
        if not passed:
            ok = False
        print(f"[{status}] {label}: {value}")

    print("\nRESULTADO:", "TODO OK" if ok else "HAY FALLOS")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
