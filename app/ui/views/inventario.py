import tkinter.messagebox as messagebox
import tkinter.ttk as ttk

import customtkinter as ctk

from app.db import products
from app.services.formatting import price_text, qty_text
from app.ui import theme
from app.ui.async_task import run_async
from app.ui.dialogs.agregar_producto import ProductFormDialog


class InventarioWindow(ctk.CTkToplevel):
    def __init__(self, master) -> None:
        super().__init__(master)
        self.withdraw()
        theme.apply_window_icon(self)
        self.title("Inventario de productos")
        self.geometry("980x580")
        self.minsize(820, 460)
        self.configure(fg_color=theme.COLORS["bg"])
        self.transient(master)
        self._rows: dict[int, dict] = {}
        self._job = None
        self._generation = 0
        self._build()
        self.refresh()
        self.after(10, self._activate)

    def _build(self) -> None:
        top = ctk.CTkFrame(self, fg_color=theme.COLORS["bg"], corner_radius=0)
        top.pack(fill="x", padx=10, pady=(10, 6))
        top.grid_columnconfigure(0, weight=1)

        self.search = ctk.CTkEntry(
            top,
            height=30,
            corner_radius=4,
            fg_color=theme.COLORS["white"],
            border_color=theme.COLORS["border"],
            border_width=1,
            font=(theme.FONT, 12),
            placeholder_text="Buscar producto...",
        )
        self.search.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.search.bind("<KeyRelease>", self._schedule_refresh)
        self.search.bind("<Return>", self.refresh)

        button_specs = [
            ("Agregar", self._add, theme.COLORS["accent"], theme.COLORS["accent_hover"]),
            ("Editar", self._edit, theme.COLORS["accent"], theme.COLORS["accent_hover"]),
            ("Eliminar", self._delete, theme.COLORS["accent"], theme.COLORS["accent_hover"]),
            ("Actualizar", self.refresh, theme.COLORS["accent"], theme.COLORS["accent_hover"]),
        ]
        for index, (label, command, color, hover) in enumerate(button_specs, start=1):
            ctk.CTkButton(
                top,
                text=label,
                command=command,
                height=30,
                width=105,
                corner_radius=5,
                fg_color=color,
                hover_color=hover,
                font=(theme.FONT, 12),
            ).grid(row=0, column=index, padx=(0 if index == 1 else 6, 0))

        holder = ctk.CTkFrame(self, fg_color=theme.COLORS["white"], corner_radius=3)
        holder.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        holder.grid_columnconfigure(0, weight=1)
        holder.grid_rowconfigure(0, weight=1)

        columns = ("id", "barcode", "name", "price", "price_wholesale", "stock")
        self.tree = ttk.Treeview(
            holder, columns=columns, show="headings", style=theme.TREE_STYLE
        )
        specs = [
            ("id", "Id", 50, "center"),
            ("barcode", "Código de Barras", 160, "center"),
            ("name", "Producto", 300, "center"),
            ("price", "Precio", 90, "center"),
            ("price_wholesale", "Precio Mesa", 110, "center"),
            ("stock", "Stock", 80, "center"),
        ]
        for column, label, width, anchor in specs:
            self.tree.heading(column, text=label)
            self.tree.column(column, width=width, anchor=anchor)

        scrollbar = ttk.Scrollbar(holder, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<Double-1>", self._edit)

    def _activate(self) -> None:
        theme.center_window(self, self.master)
        self.deiconify()
        self.search.focus_set()

    def _schedule_refresh(self, event=None) -> None:
        if self._job is not None:
            self.after_cancel(self._job)
        self._job = self.after(300, self.refresh)

    def refresh(self, event=None) -> None:
        if self._job is not None:
            self.after_cancel(self._job)
            self._job = None
        self._generation += 1
        generation = self._generation
        term = self.search.get().strip()
        run_async(
            self,
            lambda: products.list_products(term),
            on_success=lambda rows: self._apply_rows(rows, generation),
            on_error=self._load_error,
        )

    def _apply_rows(self, rows: list[dict], generation: int) -> None:
        if generation != self._generation:
            return
        self._rows = {int(row["id"]): row for row in rows}
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            self.tree.insert(
                "",
                "end",
                iid=str(row["id"]),
                values=(
                    row.get("id"),
                    row.get("barcode") or "",
                    row.get("name") or "",
                    price_text(row.get("price")),
                    price_text(row.get("price_wholesale")),
                    qty_text(row.get("stock")),
                ),
            )

    def _load_error(self, error) -> None:
        messagebox.showerror(
            "Inventario",
            "No se pudo cargar el inventario:\n\n" + str(error),
            parent=self,
        )

    def _selected(self) -> dict | None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo(
                "Inventario", "Seleccioná un producto primero.", parent=self
            )
            return None
        return self._rows.get(int(selection[0]))

    def _add(self) -> None:
        ProductFormDialog(self, on_saved=self.refresh)

    def _edit(self, event=None) -> None:
        product = self._selected()
        if product is None:
            return
        ProductFormDialog(self, product=product, on_saved=self.refresh)

    def _delete(self) -> None:
        product = self._selected()
        if product is None:
            return
        confirmed = messagebox.askyesno(
            "Eliminar producto",
            f"¿Eliminar «{product.get('name')}» del inventario?",
            parent=self,
        )
        if not confirmed:
            return
        try:
            products.delete_product(int(product["id"]))
        except Exception as error:
            messagebox.showerror(
                "Inventario", "No se pudo eliminar:\n\n" + str(error), parent=self
            )
            return
        self.refresh()
