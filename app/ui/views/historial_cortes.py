import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import tkinter.ttk as ttk
from datetime import date

import customtkinter as ctk

from app.db import cuts
from app.services.exports import export_cuts_csv, export_cuts_pdf
from app.services.formatting import datetime_text, money
from app.ui import theme
from app.ui.async_task import run_async


class HistorialCortesWindow(ctk.CTkToplevel):
    def __init__(self, master) -> None:
        super().__init__(master)
        self.withdraw()
        theme.apply_window_icon(self)
        self.title("Historial de Cortes de Caja")
        self.geometry("760x540")
        self.minsize(640, 420)
        self.configure(fg_color=theme.COLORS["bg"])
        self.transient(master)
        self._cuts: list[dict] = []
        self._build()
        self.refresh()
        self.after(10, self._activate)

    def _build(self) -> None:
        ctk.CTkLabel(
            self,
            text="HISTORIAL DE CORTES",
            font=(theme.FONT, 20, "bold"),
            text_color=theme.COLORS["text"],
        ).pack(pady=(16, 8))

        holder = ctk.CTkFrame(self, fg_color=theme.COLORS["white"], corner_radius=3)
        holder.pack(fill="both", expand=True, padx=14)
        holder.grid_columnconfigure(0, weight=1)
        holder.grid_rowconfigure(0, weight=1)

        columns = ("id", "created_at", "total", "tickets", "details")
        self.tree = ttk.Treeview(
            holder, columns=columns, show="headings", style=theme.TREE_STYLE
        )
        specs = [
            ("id", "ID", 50, "center"),
            ("created_at", "Fecha y Hora", 160, "center"),
            ("total", "Total ($)", 90, "center"),
            ("tickets", "Tickets", 70, "center"),
            ("details", "Detalles", 320, "center"),
        ]
        for column, label, width, anchor in specs:
            self.tree.heading(column, text=label)
            self.tree.column(column, width=width, anchor=anchor)

        scrollbar = ttk.Scrollbar(holder, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", padx=14, pady=14)
        buttons.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(
            buttons,
            text="Exportar a CSV",
            command=self._export_csv,
            height=34,
            corner_radius=5,
            fg_color=theme.COLORS["accent"],
            hover_color=theme.COLORS["accent_hover"],
            font=(theme.FONT, 12),
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            buttons,
            text="Exportar a PDF",
            command=self._export_pdf,
            height=34,
            corner_radius=5,
            fg_color=theme.COLORS["accent"],
            hover_color=theme.COLORS["accent_hover"],
            font=(theme.FONT, 12),
        ).grid(row=0, column=1, padx=6, sticky="ew")

        ctk.CTkButton(
            buttons,
            text="Cerrar",
            command=self.destroy,
            height=34,
            corner_radius=5,
            fg_color=theme.COLORS["accent"],
            hover_color=theme.COLORS["accent_hover"],
            font=(theme.FONT, 12),
        ).grid(row=0, column=2, padx=(6, 0), sticky="ew")

    def _activate(self) -> None:
        theme.center_window(self, self.master)
        self.deiconify()

    def refresh(self) -> None:
        run_async(
            self,
            cuts.list_cuts,
            on_success=self._apply_cuts,
            on_error=self._load_error,
        )

    def _load_error(self, error) -> None:
        messagebox.showerror(
            "Historial de cortes",
            "No se pudo cargar el historial:\n\n" + str(error),
            parent=self,
        )

    def _apply_cuts(self, rows: list[dict]) -> None:
        self._cuts = rows
        self.tree.delete(*self.tree.get_children())
        for cut in self._cuts:
            self.tree.insert(
                "",
                "end",
                iid=str(cut["id"]),
                values=(
                    cut.get("id"),
                    datetime_text(cut.get("created_at", "")),
                    money(cut.get("total")),
                    cut.get("tickets", 0),
                    cut.get("details") or "",
                ),
            )

    def _export_csv(self) -> None:
        self._export("csv")

    def _export_pdf(self) -> None:
        self._export("pdf")

    def _export(self, kind: str) -> None:
        if not self._cuts:
            messagebox.showinfo(
                "Historial de cortes",
                "No hay cortes para exportar.",
                parent=self,
            )
            return
        extension = ".csv" if kind == "csv" else ".pdf"
        filetypes = (
            [("Archivo CSV", "*.csv")]
            if kind == "csv"
            else [("Archivo PDF", "*.pdf")]
        )
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar historial",
            defaultextension=extension,
            filetypes=filetypes,
            initialfile=f"cortes_{date.today().isoformat()}{extension}",
        )
        if not path:
            return
        try:
            if kind == "csv":
                export_cuts_csv(self._cuts, path)
            else:
                export_cuts_pdf(
                    self._cuts, path, symbol=self.master.currency_symbol()
                )
        except Exception as error:
            messagebox.showerror(
                "Exportar", "No se pudo exportar:\n\n" + str(error), parent=self
            )
            return
        messagebox.showinfo(
            "Exportar", f"Archivo guardado en:\n{path}", parent=self
        )
