import tkinter.messagebox as messagebox
import tkinter.ttk as ttk

import customtkinter as ctk

from app.db import products
from app.services.formatting import money, qty_text
from app.ui import theme
from app.ui.async_task import run_async


class BuscarProductoDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        initial: str = "",
        on_select=None,
        title: str = "Buscar producto",
        mode: str = "normal",
    ) -> None:
        super().__init__(master)
        self.withdraw()
        theme.apply_window_icon(self)
        self.on_select = on_select
        self.mode = mode
        self._rows: dict[int, dict] = {}
        self._job = None
        self._generation = 0
        self.title(title)
        self.geometry("680x500")
        self.minsize(560, 400)
        self.configure(fg_color=theme.COLORS["bg"])
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self._close)
        self._build(initial)
        self.after(10, self._activate)

    def _build(self, initial: str) -> None:
        top = ctk.CTkFrame(self, fg_color=theme.COLORS["panel"], corner_radius=6)
        top.pack(fill="x", padx=10, pady=(10, 6))
        top.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(
            top,
            height=30,
            corner_radius=4,
            fg_color=theme.COLORS["white"],
            border_color=theme.COLORS["border"],
            border_width=1,
            font=(theme.FONT, 12),
            placeholder_text="Código, nombre o código de barras",
        )
        self.entry.grid(row=0, column=0, sticky="ew", padx=(10, 6), pady=10)
        self.entry.bind("<Return>", self._search)
        self.entry.bind("<KeyRelease>", self._schedule_search)

        ctk.CTkButton(
            top,
            text="Buscar",
            command=self._search,
            height=30,
            width=90,
            corner_radius=5,
            fg_color=theme.COLORS["accent"],
            hover_color=theme.COLORS["accent_hover"],
            font=(theme.FONT, 12),
        ).grid(row=0, column=1, padx=(0, 10), pady=10)

        holder = ctk.CTkFrame(self, fg_color=theme.COLORS["white"], corner_radius=3)
        holder.pack(fill="both", expand=True, padx=10)
        holder.grid_columnconfigure(0, weight=1)
        holder.grid_rowconfigure(0, weight=1)

        columns = ("name", "unit", "price", "stock")
        self.tree = ttk.Treeview(
            holder, columns=columns, show="headings", style=theme.TREE_STYLE
        )
        specs = [
            ("name", "Producto", 390, "center"),
            ("unit", "Unidad", 70, "center"),
            ("price", "Precio", 90, "center"),
            ("stock", "Stock", 70, "center"),
        ]
        for column, label, width, anchor in specs:
            self.tree.heading(column, text=label)
            self.tree.column(column, width=width, anchor=anchor)

        scrollbar = ttk.Scrollbar(holder, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<Double-1>", self._add_selected)
        self.tree.bind("<Return>", self._add_selected)

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=10, pady=10)
        bottom.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            bottom,
            text="Agregar al ticket",
            command=self._add_selected,
            height=34,
            corner_radius=5,
            fg_color=theme.COLORS["accent"],
            hover_color=theme.COLORS["accent_hover"],
            font=(theme.FONT, 12),
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            bottom,
            text="Cerrar",
            command=self._close,
            height=34,
            corner_radius=5,
            fg_color=theme.COLORS["muted"],
            hover_color="#4F4F4F",
            font=(theme.FONT, 12),
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

        self.entry.insert(0, initial)
        self._search()

    def _activate(self) -> None:
        theme.center_window(self, self.master)
        self.deiconify()
        self.grab_set()
        self.entry.focus_set()
        self.entry.select_range(0, "end")

    def _schedule_search(self, event=None) -> None:
        if event is not None and event.keysym in ("Return", "Escape"):
            return
        if self._job is not None:
            self.after_cancel(self._job)
        self._job = self.after(300, self._search)

    def _search(self, event=None) -> None:
        if self._job is not None:
            self.after_cancel(self._job)
            self._job = None
        self._generation += 1
        generation = self._generation
        term = self.entry.get().strip()
        run_async(
            self,
            lambda: products.list_products(term),
            on_success=lambda rows: self._apply_rows(rows, generation),
            on_error=self._search_error,
        )
        return "break"

    def _apply_rows(self, rows: list[dict], generation: int) -> None:
        if generation != self._generation:
            return
        self._rows = {int(row["id"]): row for row in rows}
        self.tree.delete(*self.tree.get_children())
        symbol = getattr(self.master, "currency_symbol", lambda: "$")()
        for row in rows:
            self.tree.insert(
                "",
                "end",
                iid=str(row["id"]),
                values=(
                    row.get("name") or "",
                    row.get("unit") or "",
                    money(self.price_for(row), symbol),
                    qty_text(row.get("stock")),
                ),
            )

    def _search_error(self, error) -> None:
        messagebox.showerror(
            "Buscar producto", "No se pudo buscar:\n\n" + str(error), parent=self
        )

    def price_for(self, product: dict) -> float:
        if self.mode == "mesa":
            wholesale = float(product.get("price_wholesale") or 0)
            if wholesale > 0:
                return wholesale
        return float(product.get("price") or 0)

    def _add_selected(self, event=None) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        product = self._rows.get(int(selection[0]))
        if product is not None and self.on_select is not None:
            self.on_select(product)
            self._close()
        return "break"

    def _close(self) -> None:
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
