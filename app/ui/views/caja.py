import tkinter.messagebox as messagebox
import tkinter.ttk as ttk

import customtkinter as ctk
from PIL import Image

from app.db import products, sales
from app.paths import resource_path
from app.services.formatting import money, price_text, qty_text
from app.ui import theme
from app.ui.async_task import run_async
from app.ui.dialogs.buscar_producto import BuscarProductoDialog
from app.ui.dialogs.cantidad import QuantityDialog
from app.ui.dialogs.cobrar import CobrarDialog


class CajaView(ctk.CTkFrame):
    def __init__(self, master) -> None:
        super().__init__(master, fg_color=theme.COLORS["bg"], corner_radius=0)
        self.cart: dict[int, dict] = {}
        self.mode = "normal"
        self.ticket_number = 1
        self._build()
        self.refresh_settings()
        self._refresh_ticket_number()
        self.after(250, self.entry.focus_set)

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(self, fg_color=theme.COLORS["panel"], corner_radius=6)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        toolbar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            toolbar,
            text="Código o nombre:",
            font=(theme.FONT, 12),
            text_color=theme.COLORS["text"],
        ).grid(row=0, column=0, padx=(12, 6), pady=10)

        self.entry = ctk.CTkEntry(
            toolbar,
            height=30,
            corner_radius=4,
            fg_color=theme.COLORS["white"],
            border_color=theme.COLORS["border"],
            border_width=1,
            font=(theme.FONT, 12),
        )
        self.entry.grid(row=0, column=1, sticky="ew", pady=10)
        self.entry.bind("<Return>", self._on_enter)

        ctk.CTkButton(
            toolbar,
            text="ENTER - Agregar",
            command=self.add_from_entry,
            height=30,
            width=130,
            corner_radius=5,
            fg_color=theme.COLORS["accent"],
            hover_color=theme.COLORS["accent_hover"],
            font=(theme.FONT, 12),
        ).grid(row=0, column=2, padx=6, pady=10)

        ctk.CTkButton(
            toolbar,
            text="F5 - Buscar",
            command=self.open_search,
            height=30,
            width=110,
            corner_radius=5,
            fg_color=theme.COLORS["accent"],
            hover_color=theme.COLORS["accent_hover"],
            font=(theme.FONT, 12),
        ).grid(row=0, column=3, padx=(0, 6), pady=10)

        self.mode_button = ctk.CTkButton(
            toolbar,
                text="MODO: Normal",
            command=self.toggle_mode,
            height=30,
            width=130,
            fg_color="transparent",
            hover_color=theme.COLORS["border"],
            text_color=theme.COLORS["text"],
            font=(theme.FONT, 12),
        )
        self.mode_button.grid(row=0, column=4, padx=(0, 12), pady=10)

        panel = ctk.CTkFrame(self, fg_color=theme.COLORS["panel"], corner_radius=6)
        panel.grid(row=1, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        self.ticket_label = ctk.CTkLabel(
            panel,
            text=f"Ticket #{self.ticket_number}",
            font=(theme.FONT, 17, "bold"),
            text_color=theme.COLORS["text"],
            anchor="w",
        )
        self.ticket_label.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))

        tree_holder = ctk.CTkFrame(
            panel, fg_color=theme.COLORS["white"], corner_radius=3
        )
        tree_holder.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        tree_holder.grid_columnconfigure(0, weight=1)
        tree_holder.grid_rowconfigure(0, weight=1)

        columns = ("name", "unit", "price", "qty", "subtotal")
        self.tree = ttk.Treeview(
            tree_holder, columns=columns, show="headings", style=theme.TREE_STYLE
        )
        specs = [
            ("name", "Producto", 470, "center"),
            ("unit", "Unidad", 70, "center"),
            ("price", "Precio", 100, "center"),
            ("qty", "Cantidad", 70, "center"),
            ("subtotal", "Subtotal", 110, "center"),
        ]
        for column, label, width, anchor in specs:
            self.tree.heading(column, text=label)
            self.tree.column(column, width=width, anchor=anchor)

        scrollbar = ttk.Scrollbar(
            tree_holder, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<Delete>", self._remove_selected)
        self.tree.bind("<Double-1>", self.edit_quantity)

        self._watermark_image = None
        self.watermark = self._load_watermark(tree_holder)

        bottom = ctk.CTkFrame(self, fg_color=theme.COLORS["panel"], corner_radius=6)
        bottom.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        bottom.grid_columnconfigure(0, weight=1)

        self.total_label = ctk.CTkLabel(
            bottom,
            text="Total: $0.00",
            font=(theme.FONT, 17, "bold"),
            text_color=theme.COLORS["text"],
        )
        self.total_label.grid(row=0, column=0, pady=10)

        ctk.CTkButton(
            bottom,
            text="F9 - Cobrar",
            command=self.cobrar,
            height=34,
            width=140,
            corner_radius=5,
            fg_color=theme.COLORS["accent"],
            hover_color=theme.COLORS["accent_hover"],
            font=(theme.FONT, 12, "bold"),
        ).grid(row=0, column=1, padx=10, pady=8)

    def _load_watermark(self, parent):
        path = resource_path("assets", "watermark.png")
        if not path.exists():
            return None
        try:
            image = Image.open(path).convert("RGBA")
            alpha = image.getchannel("A").point(lambda value: int(value * 0.3))
            image.putalpha(alpha)
            image.thumbnail((420, 300), Image.Resampling.LANCZOS)
            self._watermark_image = ctk.CTkImage(
                light_image=image, dark_image=image, size=image.size
            )
            return ctk.CTkLabel(
                parent,
                text="",
                image=self._watermark_image,
                fg_color="transparent",
            )
        except Exception:
            return None

    def _update_watermark(self) -> None:
        if self.watermark is None:
            return
        if self.cart:
            self.watermark.place_forget()
        else:
            self.watermark.place(relx=0.5, rely=0.5, anchor="center")

    def refresh_settings(self) -> None:
        self._render()

    def _refresh_ticket_number(self) -> None:
        def apply(number: int) -> None:
            self.ticket_number = number
            self.ticket_label.configure(text=f"Ticket #{self.ticket_number}")

        run_async(self, sales.next_ticket_number, on_success=apply)

    def _price_for(self, product: dict) -> float:
        if self.mode == "mesa":
            wholesale = float(product.get("price_wholesale") or 0)
            if wholesale > 0:
                return wholesale
        return float(product.get("price") or 0)

    def _total(self) -> float:
        return sum(
            self._price_for(item["product"]) * item["qty"]
            for item in self.cart.values()
        )

    def _on_enter(self, event=None):
        self.add_from_entry()
        return "break"

    def add_from_entry(self) -> None:
        term = self.entry.get().strip()
        if not term:
            return
        try:
            product = products.find_exact(term)
            if product is None:
                matches = products.list_products(term)
                if len(matches) == 1:
                    product = matches[0]
                elif matches:
                    BuscarProductoDialog(
                        self.winfo_toplevel(),
                        initial=term,
                        on_select=self.add_product,
                        title="Seleccionar producto",
                        mode=self.mode,
                    )
                    return
        except Exception as error:
            messagebox.showerror(
                "Caja",
                "No se pudo buscar el producto:\n\n" + str(error),
                parent=self.winfo_toplevel(),
            )
            return
        if product is None:
            messagebox.showinfo(
                "Caja",
                f"No se encontró ningún producto con «{term}».",
                parent=self.winfo_toplevel(),
            )
            return
        self.add_product(product)

    def add_product(self, product: dict) -> None:
        product_id = int(product["id"])
        if product_id in self.cart:
            self.cart[product_id]["qty"] += 1
        else:
            self.cart[product_id] = {"product": product, "qty": 1}
        self._render()
        self._select_product(product_id)
        self.entry.delete(0, "end")
        self.entry.focus_set()

    def open_search(self) -> None:
        BuscarProductoDialog(
            self.winfo_toplevel(), on_select=self.add_product, mode=self.mode
        )

    def toggle_mode(self) -> None:
        self.mode = "mesa" if self.mode == "normal" else "normal"
        if self.mode == "mesa":
            self.mode_button.configure(
                text="MODO: Mesa",
                fg_color=theme.COLORS["green"],
                hover_color=theme.COLORS["green_hover"],
                text_color="#FFFFFF",
            )
        else:
            self.mode_button.configure(
            text="MODO: Normal",
                fg_color="transparent",
                hover_color=theme.COLORS["border"],
                text_color=theme.COLORS["text"],
            )
        self._render()

    def _render(self) -> None:
        selected = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        symbol = self.master.currency_symbol()
        total = 0.0
        for product_id, item in self.cart.items():
            product = item["product"]
            quantity = item["qty"]
            price = self._price_for(product)
            subtotal = round(price * quantity, 2)
            total += subtotal
            self.tree.insert(
                "",
                "end",
                iid=str(product_id),
                values=(
                    product.get("name") or "",
                    product.get("unit") or "",
                    price_text(price),
                    qty_text(quantity),
                    price_text(subtotal),
                ),
            )
        for iid in selected:
            if self.tree.exists(iid):
                self.tree.selection_add(iid)
        self.total_label.configure(text=f"Total: {money(total, symbol)}")
        self._update_watermark()

    def _select_product(self, product_id: int) -> None:
        iid = str(product_id)
        if not self.tree.exists(iid):
            return
        self.tree.selection_set(iid)
        self.tree.focus(iid)
        self.tree.see(iid)

    def _remove_selected(self, event=None):
        if self.remove_selected_item():
            return "break"

    def remove_selected_item(self) -> bool:
        selection = self.tree.selection()
        if not selection:
            return False
        for iid in selection:
            self.cart.pop(int(iid), None)
        self._render()
        return True

    def edit_quantity(self, event=None) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        product_id = int(selection[0])
        item = self.cart.get(product_id)
        if item is None:
            return
        QuantityDialog(
            self.winfo_toplevel(),
            product_name=item["product"].get("name") or "",
            current=item["qty"],
            on_apply=lambda quantity: self._set_quantity(product_id, quantity),
        )

    def _set_quantity(self, product_id: int, quantity: float) -> None:
        item = self.cart.get(product_id)
        if item is None:
            return
        item["qty"] = quantity
        self._render()
        self._select_product(product_id)

    def cobrar(self) -> None:
        if not self.cart:
            messagebox.showinfo(
                "Caja", "El ticket está vacío.", parent=self.winfo_toplevel()
            )
            return
        CobrarDialog(
            self.winfo_toplevel(),
            ticket_number=self.ticket_number,
            total=self._total(),
            symbol=self.master.currency_symbol(),
            on_confirm=self._confirm_sale,
        )

    def _confirm_sale(self, received: float, change: float) -> bool:
        items = []
        total = self._total()
        for product_id, item in self.cart.items():
            product = item["product"]
            quantity = item["qty"]
            price = self._price_for(product)
            items.append(
                {
                    "product_id": product_id,
                    "name": product.get("name"),
                    "unit": product.get("unit"),
                    "price": price,
                    "qty": quantity,
                    "subtotal": round(price * quantity, 2),
                    "mode": self.mode,
                }
            )
        try:
            result = sales.register_sale(
                items,
                amount_received=received,
                change_amount=change,
                user_name=self.master.user_name,
            )
        except Exception as error:
            messagebox.showerror(
                "Cobrar",
                "No se pudo registrar la venta:\n\n" + str(error),
                parent=self.winfo_toplevel(),
            )
            return False
        ticket = self.ticket_number
        if isinstance(result, dict) and result.get("ticket_number"):
            ticket = result["ticket_number"]
        symbol = self.master.currency_symbol()
        messagebox.showinfo(
            "Venta registrada",
            f"Ticket #{ticket} cobrado correctamente.\nTotal: {money(total, symbol)}",
            parent=self.winfo_toplevel(),
        )
        self.cart.clear()
        self._render()
        self._refresh_ticket_number()
        self.master.refresh_after_sale()
        self.entry.focus_set()
        return True
