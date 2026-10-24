import tkinter.messagebox as messagebox

import customtkinter as ctk

from app.db import store_settings
from app.db.client import get_client
from app.ui import theme
from app.version import APP_VERSION


class ConfiguracionWindow(ctk.CTkToplevel):
    FIELDS = [
        ("business_name", "Nombre del negocio:"),
        ("user_name", "Usuario:"),
        ("currency_symbol", "Símbolo de moneda:"),
        ("ticket_footer", "Pie de ticket:"),
    ]

    def __init__(self, master) -> None:
        super().__init__(master)
        self.withdraw()
        theme.apply_window_icon(self)
        self.title("Configuración")
        self.geometry("480x540")
        self.resizable(False, False)
        self.configure(fg_color=theme.COLORS["bg"])
        self.transient(master)
        self._entries: dict[str, ctk.CTkEntry] = {}
        self._build()
        self._load()
        self.after(10, self._activate)

    def _build(self) -> None:
        ctk.CTkLabel(
            self,
            text="CONFIGURACIÓN",
            font=(theme.FONT, 18, "bold"),
            text_color=theme.COLORS["text"],
        ).pack(pady=(16, 10))

        form = ctk.CTkFrame(self, fg_color=theme.COLORS["panel"], corner_radius=6)
        form.pack(fill="x", padx=20)
        form.grid_columnconfigure(1, weight=1)

        for row, (key, label) in enumerate(self.FIELDS):
            ctk.CTkLabel(
                form,
                text=label,
                font=(theme.FONT, 11),
                text_color=theme.COLORS["text"],
                anchor="w",
            ).grid(row=row, column=0, sticky="w", padx=(12, 8), pady=9)

            entry = ctk.CTkEntry(
                form,
                height=28,
                corner_radius=4,
                fg_color=theme.COLORS["white"],
                border_color=theme.COLORS["border"],
                border_width=1,
                font=(theme.FONT, 11),
            )
            entry.grid(row=row, column=1, sticky="ew", padx=(0, 12), pady=9)
            self._entries[key] = entry

        system = ctk.CTkFrame(self, fg_color=theme.COLORS["panel"], corner_radius=6)
        system.pack(fill="x", padx=20, pady=(12, 0))
        system.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            system,
            text=f"Versión instalada: v{APP_VERSION}",
            font=(theme.FONT, 11),
            text_color=theme.COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))

        ctk.CTkButton(
            system,
            text="Buscar actualizaciones",
            command=self._check_updates,
            height=32,
            corner_radius=5,
            fg_color=theme.COLORS["accent"],
            hover_color=theme.COLORS["accent_hover"],
            font=(theme.FONT, 12),
        ).grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", padx=20, pady=16)
        buttons.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            buttons,
            text="Guardar configuración",
            command=self._save,
            height=34,
            corner_radius=5,
            fg_color=theme.COLORS["accent"],
            hover_color=theme.COLORS["accent_hover"],
            font=(theme.FONT, 12),
        ).grid(row=0, column=0, sticky="ew")

        ctk.CTkButton(
            buttons,
            text="Probar conexión",
            command=self._test_connection,
            height=34,
            corner_radius=5,
            fg_color=theme.COLORS["accent"],
            hover_color=theme.COLORS["accent_hover"],
            font=(theme.FONT, 12),
        ).grid(row=1, column=0, sticky="ew", pady=(10, 0))

        ctk.CTkButton(
            buttons,
            text="Cerrar",
            command=self.destroy,
            height=34,
            corner_radius=5,
            fg_color=theme.COLORS["muted"],
            hover_color="#4F4F4F",
            font=(theme.FONT, 12),
        ).grid(row=2, column=0, sticky="ew", pady=(10, 0))

    def _activate(self) -> None:
        theme.center_window(self, self.master)
        self.deiconify()

    def _load(self) -> None:
        values = dict(getattr(self.master, "store", {}) or {})
        for key, entry in self._entries.items():
            entry.delete(0, "end")
            entry.insert(0, str(values.get(key, "")))

    def _save(self) -> None:
        values = {key: entry.get().strip() for key, entry in self._entries.items()}
        if not values.get("currency_symbol"):
            values["currency_symbol"] = "$"
        try:
            store_settings.save_settings(values)
        except Exception as error:
            messagebox.showerror(
                "Configuración",
                "No se pudo guardar:\n\n" + str(error),
                parent=self,
            )
            return
        self.master.reload_settings()
        messagebox.showinfo(
            "Configuración", "Configuración guardada correctamente.", parent=self
        )

    def _check_updates(self) -> None:
        checker = getattr(self.master, "check_updates", None)
        if not callable(checker):
            messagebox.showinfo(
                "Actualizaciones",
                "La búsqueda de actualizaciones no está disponible.",
                parent=self,
            )
            return
        checker(manual=True)

    def _test_connection(self) -> None:
        try:
            get_client().table("products").select("id").limit(1).execute()
        except Exception as error:
            messagebox.showerror(
                "Conexión",
                "No se pudo conectar con Supabase:\n\n" + str(error),
                parent=self,
            )
            return
        messagebox.showinfo(
            "Conexión", "Conexión con Supabase establecida correctamente.", parent=self
        )
