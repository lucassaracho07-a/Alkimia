import tkinter.messagebox as messagebox

import customtkinter as ctk

from app.db import products
from app.services.formatting import parse_number, price_text, qty_text
from app.ui import theme


class ProductFormDialog(ctk.CTkToplevel):
    FIELDS = [
        ("barcode", "Código de Barras:"),
        ("name", "Nombre:"),
        ("price", "Precio:"),
        ("price_wholesale", "Precio Mesa:"),
        ("unit", "Unidad:"),
        ("stock", "Stock:"),
    ]

    def __init__(self, master, product=None, on_saved=None) -> None:
        super().__init__(master)
        self.withdraw()
        theme.apply_window_icon(self)
        self.product = product
        self.on_saved = on_saved
        self.entries: dict[str, ctk.CTkEntry] = {}
        self.title("Agregar Producto" if product is None else "Editar Producto")
        self.geometry("400x415")
        self.resizable(False, False)
        self.configure(fg_color=theme.COLORS["bg"])
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self._close)
        self._build()
        if product is not None:
            self._fill(product)
        self.after(10, self._activate)

    def _build(self) -> None:
        heading = "Nuevo Producto" if self.product is None else "Editar Producto"
        ctk.CTkLabel(
            self,
            text=heading,
            font=(theme.FONT, 18, "bold"),
            text_color=theme.COLORS["text"],
        ).pack(pady=(16, 10))

        form = ctk.CTkFrame(self, fg_color=theme.COLORS["panel"], corner_radius=6)
        form.pack(fill="x", padx=18)
        form.grid_columnconfigure(1, weight=1)

        for row, (key, label) in enumerate(self.FIELDS):
            ctk.CTkLabel(
                form,
                text=label,
                font=(theme.FONT, 11),
                text_color=theme.COLORS["text"],
                anchor="w",
            ).grid(row=row, column=0, sticky="w", padx=(12, 6), pady=7)

            entry = ctk.CTkEntry(
                form,
                height=28,
                corner_radius=4,
                fg_color=theme.COLORS["white"],
                border_color=theme.COLORS["border"],
                border_width=1,
                font=(theme.FONT, 11),
            )
            entry.grid(row=row, column=1, sticky="ew", padx=(0, 12), pady=7)
            if key == "unit":
                entry.insert(0, "U")
            self.entries[key] = entry

        self.entries["name"].bind("<Return>", lambda event: self._save())

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", padx=18, pady=16)
        buttons.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            buttons,
            text="Guardar Producto",
            command=self._save,
            height=34,
            corner_radius=5,
            fg_color=theme.COLORS["accent"],
            hover_color=theme.COLORS["accent_hover"],
            font=(theme.FONT, 12),
        ).grid(row=0, column=0, sticky="ew")

        ctk.CTkButton(
            buttons,
            text="Cancelar",
            command=self._close,
            height=34,
            corner_radius=5,
            fg_color=theme.COLORS["accent"],
            hover_color=theme.COLORS["accent_hover"],
            font=(theme.FONT, 12),
        ).grid(row=1, column=0, sticky="ew", pady=(10, 0))

    def _fill(self, product: dict) -> None:
        values = {
            "barcode": product.get("barcode") or "",
            "name": product.get("name") or "",
            "price": price_text(product.get("price")),
            "price_wholesale": price_text(product.get("price_wholesale")),
            "unit": product.get("unit") or "U",
            "stock": qty_text(product.get("stock")),
        }
        for key, value in values.items():
            entry = self.entries[key]
            entry.delete(0, "end")
            entry.insert(0, value)

    def _collect(self) -> dict | None:
        data = {key: entry.get().strip() for key, entry in self.entries.items()}
        if not data["name"]:
            messagebox.showwarning(
                "Producto", "El nombre es obligatorio.", parent=self
            )
            return None
        try:
            data["price"] = parse_number(data["price"])
            data["price_wholesale"] = parse_number(data["price_wholesale"])
            data["stock"] = parse_number(data["stock"])
        except ValueError:
            messagebox.showwarning(
                "Producto",
                "Precio, Precio Mayoreo y Stock deben ser números.",
                parent=self,
            )
            return None
        data["unit"] = data["unit"] or "U"
        return data

    def _save(self) -> None:
        data = self._collect()
        if data is None:
            return
        try:
            if self.product is None:
                products.create_product(data)
            else:
                products.update_product(int(self.product["id"]), data)
        except Exception as error:
            message = str(error)
            if "duplicate key" in message.lower():
                message = "Ya existe un producto con ese código de barras."
            messagebox.showerror(
                "Producto", "No se pudo guardar:\n\n" + message, parent=self
            )
            return
        if self.on_saved is not None:
            self.on_saved()
        self._close()

    def _activate(self) -> None:
        theme.center_window(self, self.master)
        self.deiconify()
        self.grab_set()
        self.entries["barcode"].focus_set()

    def _close(self) -> None:
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
