import tkinter.messagebox as messagebox

import customtkinter as ctk

from app.db import cuts, sales
from app.services.formatting import money
from app.ui import theme
from app.ui.async_task import run_async


class CorteCajaWindow(ctk.CTkToplevel):
    def __init__(self, master) -> None:
        super().__init__(master)
        self.withdraw()
        theme.apply_window_icon(self)
        self.title("Corte de Caja - Resumen del Día")
        self.geometry("440x560")
        self.resizable(False, False)
        self.configure(fg_color=theme.COLORS["bg"])
        self.transient(master)
        self._sales: list[dict] = []
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
            height=190,
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
        self.tickets_label.pack(pady=(0, 14))

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
        run_async(
            self,
            sales.sales_today,
            on_success=self._apply_sales,
            on_error=self._load_error,
        )

    def _load_error(self, error) -> None:
        messagebox.showerror(
            "Corte de caja",
            "No se pudieron cargar las ventas:\n\n" + str(error),
            parent=self,
        )

    def _apply_sales(self, rows: list[dict]) -> None:
        self._sales = rows
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
        self.total_label.configure(text=f"TOTAL GENERAL: {money(total, symbol)}")
        self.tickets_label.configure(text=f"Tickets: {len(self._sales)}")

    def _details(self) -> str:
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
        return " | ".join(parts)

    def _save(self) -> None:
        if self._saved:
            return
        total = sum(float(sale.get("total") or 0) for sale in self._sales)
        details = self._details() or "Sin ventas"
        try:
            cuts.save_cut(
                total=total,
                tickets=len(self._sales),
                details=details,
                user_name=self.master.user_name,
            )
        except Exception as error:
            messagebox.showerror(
                "Corte de caja",
                "No se pudo guardar el corte:\n\n" + str(error),
                parent=self,
            )
            return
        self._saved = True
        self.save_button.configure(state="disabled", text="Corte guardado")
        messagebox.showinfo(
            "Corte de caja", "Corte de caja guardado correctamente.", parent=self
        )
        self.master.refresh_history()
