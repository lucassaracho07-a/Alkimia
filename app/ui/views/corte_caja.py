import logging
import tkinter.messagebox as messagebox

import customtkinter as ctk

from app.db import cuts, sales
from app.services.formatting import money
from app.ui import theme
from app.ui.async_task import run_async

logger = logging.getLogger(__name__)


class CorteCajaWindow(ctk.CTkToplevel):
    def __init__(self, master) -> None:
        super().__init__(master)
        self.withdraw()
        theme.apply_window_icon(self)
        self.title("Corte de Caja - Resumen del Día")
        self.geometry("440x740")
        self.resizable(False, False)
        self.configure(fg_color=theme.COLORS["bg"])
        self.transient(master)
        self._sales: list[dict] = []
        self._items: list[dict] = []
        self._saved = False
        self._build()
        self.refresh()
        self.after(10, self._activate)

    def _build(self) -> None:
        ctk.CTkLabel(
            self,
            text="CORTE DE CAJA",
            font=(theme.FONT, 20, "bold"),
            text_color=theme.COLORS["text"],
        ).pack(pady=(18, 4))

        ctk.CTkLabel(
            self,
            text="Ventas del día actual",
            font=(theme.FONT, 13),
            text_color=theme.COLORS["text"],
        ).pack(pady=(0, 10))

        self.summary = ctk.CTkScrollableFrame(
            self,
            fg_color=theme.COLORS["panel"],
            corner_radius=6,
            height=140,
            scrollbar_button_color=theme.COLORS["border"],
            scrollbar_button_hover_color=theme.COLORS["muted"],
        )
        self.summary.pack(fill="x", padx=20)

        self.total_label = ctk.CTkLabel(
            self,
            text="TOTAL GENERAL: $0.00",
            font=(theme.FONT, 16, "bold"),
            text_color=theme.COLORS["text"],
        )
        self.total_label.pack(pady=(16, 4))

        self.tickets_label = ctk.CTkLabel(
            self,
            text="Tickets: 0",
            font=(theme.FONT, 13),
            text_color=theme.COLORS["text"],
        )
        self.tickets_label.pack(pady=(0, 4))

        self.units_label = ctk.CTkLabel(
            self,
            text="Unidades vendidas: 0",
            font=(theme.FONT, 13),
            text_color=theme.COLORS["text"],
        )
        self.units_label.pack(pady=(0, 4))

        ctk.CTkLabel(
            self,
            text="Productos vendidos (de más a menos)",
            font=(theme.FONT, 13, "bold"),
            text_color=theme.COLORS["text"],
        ).pack(pady=(10, 4))

        self.products = ctk.CTkScrollableFrame(
            self,
            fg_color=theme.COLORS["panel"],
            corner_radius=6,
            height=170,
            scrollbar_button_color=theme.COLORS["border"],
            scrollbar_button_hover_color=theme.COLORS["muted"],
        )
        self.products.pack(fill="x", padx=20)

        self.save_button = ctk.CTkButton(
            self,
            text="Guardar Corte de Caja",
            command=self._save,
            height=34,
            width=220,
            corner_radius=5,
            fg_color=theme.COLORS["accent"],
            hover_color=theme.COLORS["accent_hover"],
            font=(theme.FONT, 12),
        )
        self.save_button.pack(pady=(0, 8))

        ctk.CTkButton(
            self,
            text="Cerrar",
            command=self.destroy,
            height=34,
            width=220,
            corner_radius=5,
            fg_color=theme.COLORS["accent"],
            hover_color=theme.COLORS["accent_hover"],
            font=(theme.FONT, 12),
        ).pack()

    def _activate(self) -> None:
        theme.center_window(self, self.master)
        self.deiconify()

    def refresh(self) -> None:
        logger.info("Corte: cargando ventas del dia (sales_today)")
        run_async(
            self,
            self._load_day,
            on_success=self._apply_sales,
            on_error=self._load_error,
        )

    @staticmethod
    def _load_day() -> tuple[list[dict], list[dict]]:
        rows = sales.sales_today()
        items = sales.items_for_sales([row.get("id") for row in rows])
        return rows, items

    def _load_error(self, error) -> None:
        logger.error("Corte: fallo al cargar ventas: %s: %s", type(error).__name__, error)
        messagebox.showerror(
            "Corte de caja",
            "No se pudieron cargar las ventas:\n\n" + str(error),
            parent=self,
        )

    def _apply_sales(self, payload: tuple[list[dict], list[dict]]) -> None:
        rows, items = payload
        try:
            self._apply_sales_inner(rows, items)
        except Exception:
            logger.exception("Corte: fallo al pintar las ventas cargadas (%s filas)", len(rows))
            messagebox.showerror(
                "Corte de caja",
                "Ocurrio un error al mostrar las ventas.",
                parent=self,
            )

    def _apply_sales_inner(self, rows: list[dict], items: list[dict]) -> None:
        logger.info("Corte: ventas cargadas: %s | renglones: %s", len(rows), len(items))
        self._sales = rows
        self._items = items
        for widget in self.summary.winfo_children():
            widget.destroy()

        symbol = self.master.currency_symbol()
        if not self._sales:
            ctk.CTkLabel(
                self.summary,
                text="No hay ventas registradas hoy.",
                font=(theme.FONT, 12),
                text_color=theme.COLORS["text"],
            ).pack(pady=24)
        else:
            for sale in self._sales:
                text = (
                    f"Ticket #{sale.get('ticket_number', '')}   "
                    f"{sale.get('payment_method') or 'Efectivo'}   "
                    f"{money(sale.get('total'), symbol)}"
                )
                ctk.CTkLabel(
                    self.summary,
                    text=text,
                    font=(theme.FONT, 12),
                    text_color=theme.COLORS["text"],
                    anchor="w",
                ).pack(fill="x", padx=8, pady=3)

        total = sum(float(sale.get("total") or 0) for sale in self._sales)
        units = sum(self._item_qty(item) for item in self._items)
        ranking = sales.products_ranked(self._items)

        for widget in self.products.winfo_children():
            widget.destroy()
        if not ranking:
            ctk.CTkLabel(
                self.products,
                text="No hay productos vendidos hoy.",
                font=(theme.FONT, 12),
                text_color=theme.COLORS["text"],
            ).pack(pady=16)
        else:
            for name, qty in ranking:
                row = ctk.CTkFrame(self.products, fg_color="transparent")
                row.pack(fill="x", padx=8, pady=1)
                row.grid_columnconfigure(0, weight=1)
                ctk.CTkLabel(
                    row,
                    text=name,
                    font=(theme.FONT, 12),
                    text_color=theme.COLORS["text"],
                    anchor="w",
                ).grid(row=0, column=0, sticky="w")
                ctk.CTkLabel(
                    row,
                    text=f"{self._qty_text(qty)} un.",
                    font=(theme.FONT, 12, "bold"),
                    text_color=theme.COLORS["accent"],
                    anchor="e",
                ).grid(row=0, column=1, sticky="e")

        self.total_label.configure(text=f"TOTAL GENERAL: {money(total, symbol)}")
        self.tickets_label.configure(text=f"Tickets: {len(self._sales)}")
        self.units_label.configure(text=f"Unidades vendidas: {self._qty_text(units)}")
        logger.info(
            "Corte: resumen -> total=%s tickets=%s unidades=%s productos=%s",
            total,
            len(self._sales),
            units,
            [(name, qty) for name, qty in ranking],
        )

    @staticmethod
    def _item_qty(item: dict) -> float:
        try:
            return float(item.get("qty") or 0)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _qty_text(value: float) -> str:
        return f"{value:g}"

    def _details(self) -> str:
        if not self._sales:
            return ""
        symbol = self.master.currency_symbol()
        breakdown: dict[str, dict] = {}
        for sale in self._sales:
            method = sale.get("payment_method") or "Efectivo"
            entry = breakdown.setdefault(method, {"total": 0.0, "count": 0})
            entry["total"] += float(sale.get("total") or 0)
            entry["count"] += 1
        parts = [
            f"{method}: {money(data['total'], symbol)} ({data['count']} ventas)"
            for method, data in breakdown.items()
        ]
        units = sum(self._item_qty(item) for item in self._items)
        parts.append(f"Unidades: {self._qty_text(units)}")
        ranking = sales.products_ranked(self._items)
        if ranking:
            product_parts = [
                f"{name} ({self._qty_text(qty)} un.)" for name, qty in ranking
            ]
            parts.append("Productos: " + ", ".join(product_parts))
        return " | ".join(parts)

    def _save(self) -> None:
        if self._saved:
            return
        logger.info(
            "Corte: click en 'Guardar Corte de Caja' (ventas en memoria: %s)",
            len(self._sales),
        )
        try:
            total = sum(float(sale.get("total") or 0) for sale in self._sales)
            details = self._details() or "Sin ventas"
        except Exception:
            logger.exception("Corte: fallo al calcular total/detalles antes de guardar")
            messagebox.showerror(
                "Corte de caja",
                "Ocurrio un error al preparar el corte para guardarlo.",
                parent=self,
            )
            return
        logger.info("Corte: guardando total=%s tickets=%s details=%r", total, len(self._sales), details)
        try:
            row = cuts.save_cut(
                total=total,
                tickets=len(self._sales),
                details=details,
                user_name=self.master.user_name,
            )
        except Exception as error:
            logger.error("Corte: save_cut fallo: %s: %s", type(error).__name__, error)
            messagebox.showerror(
                "Corte de caja",
                "No se pudo guardar el corte:\n\n" + str(error),
                parent=self,
            )
            return
        logger.info("Corte: guardado OK, fila devuelta: %s", row)
        self._saved = True
        self.save_button.configure(state="disabled", text="Corte guardado")
        messagebox.showinfo(
            "Corte de caja", "Corte de caja guardado correctamente.", parent=self
        )
        self.master.refresh_history()
