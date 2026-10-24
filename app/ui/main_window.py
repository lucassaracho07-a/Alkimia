import tkinter as tk
import tkinter.messagebox as messagebox

import customtkinter as ctk

from app.config import settings
from app.db import store_settings
from app.paths import is_frozen
from app.services import updates
from app.ui import theme
from app.ui.async_task import run_async
from app.ui.dialogs.actualizacion import UpdateDialog
from app.ui.dialogs.agregar_producto import ProductFormDialog
from app.ui.views.caja import CajaView
from app.ui.views.configuracion import ConfiguracionWindow
from app.ui.views.corte_caja import CorteCajaWindow
from app.ui.views.historial_cortes import HistorialCortesWindow
from app.ui.views.inventario import InventarioWindow
from app.version import APP_VERSION


class MainWindow(ctk.CTkToplevel):
    def __init__(self, master, user_name: str = "") -> None:
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        super().__init__(master)
        self.withdraw()
        theme.apply_window_icon(self)
        theme.setup_tree_style(self)
        self._windows: dict[type, ctk.CTkToplevel] = {}
        self._update_check_running = False
        self._update_dialog: UpdateDialog | None = None
        self.login_user = (user_name or "").strip()
        self.store = dict(store_settings.DEFAULTS)
        self.user_name = self.login_user or self.store.get("user_name") or "ALKIMIA"
        self.title(f"{settings.app_title} - Usuario: {self.user_name}")
        self.geometry("1180x740")
        self.minsize(1024, 680)
        self.configure(fg_color=theme.COLORS["bg"])
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self.caja = CajaView(self)
        self.caja.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        self.bind("<F3>", self._edit_quantity_shortcut)
        self.bind("<F5>", lambda event: self.caja.open_search())
        self.bind("<F7>", lambda event: self.caja.toggle_mode())
        self.bind("<F9>", lambda event: self.caja.cobrar())
        self.bind("<F10>", self._open_corte_shortcut)
        self.bind("<Delete>", self._delete_selected_shortcut)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        theme.center_window(self)
        self.after(50, self._load_store_async)
        self.after(150, self._focus_caja)
        self.after(1500, self._check_updates)

    def _on_close(self) -> None:
        try:
            if self.master is not None and self.master.winfo_exists():
                self.master.destroy()
            else:
                self.destroy()
        except Exception:
            self.destroy()

    def _load_store_async(self) -> None:
        run_async(
            self,
            store_settings.get_settings,
            on_success=self._apply_store,
            on_error=self._store_error,
        )

    def _apply_store(self, values: dict) -> None:
        self.store = dict(values)
        self.user_name = self.login_user or self.store.get("user_name") or "ALKIMIA"
        self.title(f"{settings.app_title} - Usuario: {self.user_name}")
        self.caja.refresh_settings()

    def _store_error(self, error) -> None:
        messagebox.showerror(
            "Conexión",
            "No se pudo conectar con Supabase:\n\n" + str(error),
            parent=self,
        )

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(
            self, width=168, corner_radius=0, fg_color=theme.COLORS["bg"]
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(0, weight=1)
        sidebar.grid_columnconfigure(0, weight=1)

        panel = ctk.CTkFrame(
            sidebar,
            fg_color=theme.COLORS["sidebar_group"],
            corner_radius=8,
        )
        panel.grid(row=0, column=0, padx=6, pady=10, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(6, weight=1)

        specs = [
            ("Caja", self._focus_caja),
            ("Agregar producto", self._open_product_form),
            ("Inventario", lambda: self.open_window(InventarioWindow)),
            ("Corte de caja", lambda: self.open_window(CorteCajaWindow)),
            ("Historial de cortes", lambda: self.open_window(HistorialCortesWindow)),
            ("Configuración", lambda: self.open_window(ConfiguracionWindow)),
        ]
        for index, (label, command) in enumerate(specs):
            button = ctk.CTkButton(
                panel,
                text=label,
                command=command,
                height=36,
                width=148,
                corner_radius=7,
                fg_color=theme.COLORS["accent"],
                hover_color=theme.COLORS["accent_hover"],
                text_color="#FFFFFF",
                font=(theme.FONT, 12),
            )
            button.grid(
                row=index,
                column=0,
                padx=4,
                pady=(4 if index == 0 else 3, 0),
                sticky="ew",
            )

        credit = tk.Label(
            panel,
            text="Program By Lucas Saracho 🍺",
            font=(theme.FONT, 9, "italic"),
            bg=theme.COLORS["white"],
            fg=theme.COLORS["text"],
            padx=5,
            pady=1,
            bd=0,
        )
        credit.grid(row=7, column=0, padx=(10, 0), pady=(0, 23), sticky="sw")

    def currency_symbol(self) -> str:
        return self.store.get("currency_symbol") or "$"

    def _focus_caja(self) -> None:
        self.deiconify()
        self.lift()
        self.focus_force()
        self.caja.entry.focus_set()

    def _check_updates(self) -> None:
        self.check_updates(manual=False)

    def check_updates(self, manual: bool = False) -> None:
        if self._update_check_running:
            return
        if not manual and not is_frozen():
            return
        self._update_check_running = True
        run_async(
            self,
            updates.latest_release,
            on_success=lambda release: self._apply_update_check(release, manual),
            on_error=lambda error: self._update_check_error(error, manual),
        )

    def _apply_update_check(self, release, manual: bool) -> None:
        self._update_check_running = False
        if not release or not updates.is_newer(str(release.get("version") or "")):
            if manual:
                messagebox.showinfo(
                    "Actualizaciones",
                    f"Ya tenés la última versión (v{APP_VERSION}).",
                    parent=self,
                )
            return
        existing = self._update_dialog
        if existing is not None:
            try:
                if existing.winfo_exists():
                    existing.deiconify()
                    existing.lift()
                    existing.focus_force()
                    return
            except Exception:
                pass
        self._update_dialog = UpdateDialog(
            self, release, mandatory=updates.is_mandatory(release)
        )

    def _update_check_error(self, error, manual: bool) -> None:
        self._update_check_running = False
        if manual:
            messagebox.showerror(
                "Actualizaciones",
                "No se pudo consultar si hay actualizaciones:\n\n" + str(error),
                parent=self,
            )

    def _edit_quantity_shortcut(self, event=None):
        self.caja.edit_quantity()
        return "break"

    def _delete_selected_shortcut(self, event=None):
        focused = self.focus_get()
        if isinstance(focused, tk.Entry):
            try:
                if focused.get():
                    return None
            except Exception:
                return None
        if self.caja.remove_selected_item():
            return "break"

    def _open_corte_shortcut(self, event=None):
        self.open_window(CorteCajaWindow)
        return "break"

    def _open_product_form(self) -> None:
        ProductFormDialog(self, on_saved=self.refresh_after_sale)

    def open_window(self, window_class):
        existing = self._windows.get(window_class)
        if existing is not None and existing.winfo_exists():
            existing.deiconify()
            existing.lift()
            existing.focus_force()
            return existing
        window = window_class(self)
        self._windows[window_class] = window
        return window

    def refresh_after_sale(self) -> None:
        inventory = self._windows.get(InventarioWindow)
        if inventory is not None and inventory.winfo_exists():
            inventory.refresh()

    def refresh_history(self) -> None:
        history = self._windows.get(HistorialCortesWindow)
        if history is not None and history.winfo_exists():
            history.refresh()

    def reload_settings(self) -> None:
        try:
            self.store = store_settings.get_settings()
        except Exception as error:
            messagebox.showerror("Configuración", str(error), parent=self)
            return
        self.user_name = self.login_user or self.store.get("user_name") or "ALKIMIA"
        self.title(f"{settings.app_title} - Usuario: {self.user_name}")
        self.caja.refresh_settings()
