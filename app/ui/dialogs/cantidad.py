import tkinter.messagebox as messagebox

import customtkinter as ctk

from app.services.formatting import qty_text
from app.ui import theme


class QuantityDialog(ctk.CTkToplevel):
    def __init__(self, master, product_name: str, current: float, on_apply) -> None:
        super().__init__(master)
        self.withdraw()
        theme.apply_window_icon(self)
        self.on_apply = on_apply
        self.title("Editar cantidad")
        self.geometry("360x250")
        self.resizable(False, False)
        self.configure(fg_color=theme.COLORS["bg"])
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self._build(product_name, current)
        self.after(10, self._activate)

    def _build(self, product_name: str, current: float) -> None:
        ctk.CTkLabel(
            self,
            text="Editar cantidad",
            font=(theme.FONT, 17, "bold"),
            text_color=theme.COLORS["text"],
        ).pack(pady=(18, 4))

        if product_name:
            ctk.CTkLabel(
                self,
                text=product_name,
                font=(theme.FONT, 12),
                text_color=theme.COLORS["muted"],
                wraplength=320,
            ).pack(padx=20, pady=(0, 12))

        ctk.CTkLabel(
            self,
            text="Nueva cantidad:",
            font=(theme.FONT, 12),
            text_color=theme.COLORS["text"],
        ).pack(pady=(0, 6))

        self.qty_entry = ctk.CTkEntry(
            self,
            width=160,
            height=34,
            corner_radius=4,
            fg_color=theme.COLORS["white"],
            border_color=theme.COLORS["border"],
            border_width=1,
            font=(theme.FONT, 13),
        )
        self.qty_entry.pack(pady=(0, 14))
        self.qty_entry.insert(0, qty_text(current))
        self.qty_entry.bind("<Return>", self._apply)
        self.bind("<Escape>", lambda event: self._cancel())

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", padx=24, pady=(0, 16))
        buttons.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            buttons,
            text="Aplicar",
            command=self._apply,
            height=34,
            corner_radius=5,
            fg_color=theme.COLORS["accent"],
            hover_color=theme.COLORS["accent_hover"],
            font=(theme.FONT, 12),
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            buttons,
            text="Cancelar",
            command=self._cancel,
            height=34,
            corner_radius=5,
            fg_color=theme.COLORS["muted"],
            hover_color="#4F4F4F",
            font=(theme.FONT, 12),
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

    def _apply(self, event=None) -> None:
        text = self.qty_entry.get().replace(",", ".").strip()
        try:
            quantity = float(text)
        except ValueError:
            messagebox.showwarning(
                "Editar cantidad", "Ingresá una cantidad válida.", parent=self
            )
            return
        if quantity <= 0:
            messagebox.showwarning(
                "Editar cantidad", "La cantidad debe ser mayor a cero.", parent=self
            )
            return
        self.on_apply(quantity)
        self._close()

    def _cancel(self, event=None) -> None:
        self._close()

    def _activate(self) -> None:
        theme.center_window(self, self.master)
        self.deiconify()
        self.grab_set()
        self.qty_entry.focus_set()
        self.qty_entry.select_range(0, "end")

    def _close(self) -> None:
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
