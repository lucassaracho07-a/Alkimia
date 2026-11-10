"""Captura una imagen de la ventana de corte con datos de prueba."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import customtkinter as ctk  # noqa: E402
from PIL import ImageGrab  # noqa: E402

from app.db import sales  # noqa: E402

OUT = Path(__file__).resolve().parent / "_corte_preview.png"

FAKE_SALES = [
    {"id": 1, "ticket_number": 141, "total": 10000, "payment_method": "Efectivo"},
    {"id": 2, "ticket_number": 142, "total": 5000, "payment_method": "Efectivo"},
    {"id": 3, "ticket_number": 143, "total": 20000, "payment_method": "Efectivo"},
]
FAKE_ITEMS = [
    {"name": "Coca cola 2lt", "qty": 2},
    {"name": "Corona 710ml", "qty": 4},
    {"name": "Coca cola 2lt", "qty": 3},
    {"name": "Pan lactal", "qty": 2},
    {"name": "Mirinda 2.25lt", "qty": 1},
    {"name": "Fideos 500g", "qty": 6},
    {"name": "Aceite girasol 1.5lt", "qty": 2},
    {"name": "Azúcar 1kg", "qty": 3},
    {"name": "Yerba mate 1kg", "qty": 1},
    {"name": "Galletitas saladas", "qty": 4},
    {"name": "Leche entera 1lt", "qty": 5},
    {"name": "Detergente 750ml", "qty": 2},
]


class FakeMaster(ctk.CTk):
    def currency_symbol(self):
        return "$"

    def refresh_history(self):
        pass


def main() -> int:
    from app.ui.views.corte_caja import CorteCajaWindow

    sales.sales_today = lambda: list(FAKE_SALES)
    sales.items_for_sales = lambda ids: list(FAKE_ITEMS)

    master = FakeMaster()
    window = CorteCajaWindow(master)
    for _ in range(15):
        window.update()
        window.after(40)
        window.update()
    window.update_idletasks()

    x = window.winfo_rootx()
    y = window.winfo_rooty()
    w = window.winfo_width()
    h = window.winfo_height()
    time.sleep(0.3)
    window.update()
    image = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    image.save(OUT)
    print(f"imagen guardada: {OUT} ({w}x{h})")

    window.destroy()
    master.destroy()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
