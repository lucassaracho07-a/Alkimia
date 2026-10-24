import tkinter.messagebox as messagebox

import customtkinter as ctk

from app.services.formatting import money
from app.ui import theme


class CobrarDialog(ctk.CTkToplevel):
    def __init__(
        self, master, ticket_number: int, total: float, symbol: str, on_confirm
    ) -> None:
        super().__init__(master)
        self.withdraw()
        theme.apply_window_icon(self)
        self.on_confirm = on_confirm
        self.total = float(total)
        self.symbol = symbol
        self.title("Cobrar")
        self.geometry("380x360")
        self.resizable(False, False)
        self.configure(fg_color=theme.COLORS["bg"])
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self._build(ticket_number)
        self.after(10, self._activate)

    def _build(self, ticket_number: int) -> None:
        ctk.CTkLabel(
            self,
            text=f"Ticket #{ticket_number}",
            font=(theme.FONT, 18, "bold"),
            text_color=theme.COLORS["text"],
        ).pack(pady=(18, 4))

        ctk.CTkLabel(
            self,
            text=f"Total a cobrar: {money(self.total, self.symbol)}",
            font=(theme.FONT, 15),
            text_color=theme.COLORS["text"],
        ).pack(pady=(0, 14))

        box = ctk.CTkFrame(self, fg_color=theme.COLORS["panel"], corner_radius=6)
        box.pack(fill="x", padx=24)

        ctk.CTkLabel(
            box, text="Recibido con:", font=(theme.FONT, 12), text_color=theme.COLORS["text"]
        ).grid(row=0, column=0, padx=(14, 8), pady=14)

        self.received_entry = ctk.CTkEntry(
            box,
            width=140,
            height=30,
            corner_radius=4,
            fg_color=theme.COLORS["white"],
            border_color=theme.COLORS["border"],
            border_width=1,
            font=(theme.FONT, 12),
        )
        self.received_entry.grid(row=0, column=1, padx=(0, 14), pady=14)
        self.received_entry.insert(0, f"{self.total:.2f}")
        self.received_entry.bind("<KeyRelease>", self._update_change)

        self.change_label = ctk.CTkLabel(
            self,
            text=f"Cambio: {money(0, self.symbol)}",
            font=(theme.FONT, 14, "bold"),
            text_color=theme.COLORS["text"],
        )
        self.change_label.pack(pady=12)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", padx=24, pady=(6, 16))
        buttons.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            buttons,
            text="Confirmar cobro",
            command=self._confirm,
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

    def _update_change(self, event=None) -> None:
        text = self.received_entry.get().replace(",", ".").strip()
        try:
            received = float(text)
        except ValueError:
            received = 0.0
        difference = received - self.total
        color = theme.COLORS["text"] if difference >= 0 else theme.COLORS["danger"]
        self.change_label.configure(
            text=f"Cambio: {money(max(difference, 0), self.symbol)}",
            text_color=color,
        )

    def _confirm(self) -> None:
        try:
            received = float(self.received_entry.get().replace(",", "."))
        except ValueError:
            messagebox.showwarning(
                "Cobrar", "Ingresá un importe válido.", parent=self
            )
            return
        if received + 1e-9 < self.total:
            messagebox.showwarning(
                "Cobrar", "El importe recibido es menor al total.", parent=self
            )
            return
        change = round(received - self.total, 2)
        if self.on_confirm(received, change):
            self._close()

    def _cancel(self) -> None:
        self._close()

    def _activate(self) -> None:
        theme.center_window(self, self.master)
        self.deiconify()
        self.grab_set()
        self.received_entry.focus_set()
        self.received_entry.select_range(0, "end")

    def _close(self) -> None:
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
