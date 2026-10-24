import tkinter.messagebox as messagebox

import customtkinter as ctk

from app.services import updates
from app.ui import theme
from app.ui.async_task import run_async
from app.version import APP_VERSION


class UpdateDialog(ctk.CTkToplevel):
    def __init__(self, master, release: dict, mandatory: bool = False) -> None:
        super().__init__(master)
        self.withdraw()
        theme.apply_window_icon(self)
        self.release = release
        self.mandatory = mandatory
        self._busy = False
        self.title("Actualización disponible")
        self.geometry("480x380")
        self.resizable(False, False)
        self.configure(fg_color=theme.COLORS["bg"])
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self._build()
        self.after(10, self._activate)

    def _build(self) -> None:
        ctk.CTkLabel(
            self,
            text="Nueva versión disponible",
            font=(theme.FONT, 18, "bold"),
            text_color=theme.COLORS["text"],
        ).pack(pady=(18, 4))

        remote_version = self.release.get("version") or "?"
        ctk.CTkLabel(
            self,
            text=f"Instalada: v{APP_VERSION}   ·   Nueva: v{remote_version}",
            font=(theme.FONT, 12),
            text_color=theme.COLORS["muted"],
        ).pack(pady=(0, 10))

        if self.mandatory:
            ctk.CTkLabel(
                self,
                text="Actualización obligatoria para seguir usando el sistema.",
                font=(theme.FONT, 11, "bold"),
                text_color=theme.COLORS["danger"],
            ).pack(pady=(0, 8))

        ctk.CTkLabel(
            self,
            text="Novedades:",
            font=(theme.FONT, 11, "bold"),
            text_color=theme.COLORS["text"],
            anchor="w",
        ).pack(fill="x", padx=24)

        notes = str(self.release.get("notes") or "Sin detalles.")
        self.notes_box = ctk.CTkTextbox(
            self,
            height=110,
            corner_radius=4,
            border_width=0,
            fg_color=theme.COLORS["white"],
            text_color=theme.COLORS["text"],
            font=(theme.FONT, 11),
            wrap="word",
        )
        self.notes_box.pack(fill="x", padx=24, pady=(4, 10))
        self.notes_box.insert("1.0", notes)
        self.notes_box.configure(state="disabled")

        self.status = ctk.CTkLabel(
            self,
            text="",
            font=(theme.FONT, 11),
            text_color=theme.COLORS["muted"],
            height=18,
        )
        self.status.pack()

        self.progress = ctk.CTkProgressBar(
            self,
            height=6,
            corner_radius=3,
            mode="determinate",
            progress_color=theme.COLORS["accent"],
        )
        self.progress.pack(fill="x", padx=24, pady=(0, 10))
        self.progress.set(0)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", padx=24, pady=(0, 16))
        buttons.grid_columnconfigure((0, 1), weight=1)

        self.update_button = ctk.CTkButton(
            buttons,
            text="Actualizar ahora",
            command=self._start_update,
            height=34,
            corner_radius=5,
            fg_color=theme.COLORS["accent"],
            hover_color=theme.COLORS["accent_hover"],
            font=(theme.FONT, 12),
        )
        self.update_button.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        later_text = "Cerrar aplicación" if self.mandatory else "Más tarde"
        later_command = self._close_app if self.mandatory else self._close
        self.later_button = ctk.CTkButton(
            buttons,
            text=later_text,
            command=later_command,
            height=34,
            corner_radius=5,
            fg_color=theme.COLORS["muted"],
            hover_color="#4F4F4F",
            font=(theme.FONT, 12),
        )
        self.later_button.grid(row=0, column=1, padx=(6, 0), sticky="ew")

    def _start_update(self) -> None:
        if self._busy:
            return
        self._busy = True
        self.update_button.configure(state="disabled", text="Descargando...")
        self.later_button.configure(state="disabled")
        self.status.configure(text="Descargando actualización...")
        self.progress.configure(mode="indeterminate")
        self.progress.start()
        run_async(
            self,
            lambda: updates.download_installer(self.release),
            on_success=self._downloaded,
            on_error=self._failed,
        )

    def _downloaded(self, path) -> None:
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.progress.set(0)
        self.status.configure(text="Iniciando instalador...")
        try:
            updates.launch_installer(path)
        except Exception as error:
            self._failed(error)
            return
        self.after(800, self._close_app)

    def _failed(self, error) -> None:
        self._busy = False
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.progress.set(0)
        self.status.configure(text="No se pudo actualizar.")
        self.update_button.configure(state="normal", text="Reintentar")
        self.later_button.configure(state="normal")
        messagebox.showerror(
            "Actualización",
            "No se pudo descargar o instalar la actualización:\n\n" + str(error),
            parent=self,
        )

    def _cancel(self) -> None:
        if self._busy:
            return
        if self.mandatory:
            self._close_app()
        else:
            self._close()

    def _activate(self) -> None:
        theme.center_window(self, self.master)
        self.deiconify()
        self.grab_set()
        self.update_button.focus_set()

    def _close_app(self) -> None:
        try:
            close = getattr(self.master, "_on_close", None)
            if callable(close):
                close()
                return
        except Exception:
            pass
        try:
            self.master.destroy()
        except Exception:
            self.destroy()

    def _close(self) -> None:
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
