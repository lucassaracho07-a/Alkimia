import tkinter.messagebox as messagebox

import customtkinter as ctk
from PIL import Image

from app import auth
from app.paths import resource_path
from app.ui import theme
from app.ui.main_window import MainWindow

BG = "#1E1E1E"
ENTRY_BG = "#F2F2F2"
PLACEHOLDER = "#8A8A8A"
FOOTER = "#8B8B8B"


class LoginWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.withdraw()
        theme.apply_window_icon(self)
        self.authenticated = False
        self.username = ""
        self.first_run = not auth.has_user()
        self.title("Login - ALKIMIA")
        self.geometry("440x400")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self._logo = self._load_logo()
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.bind("<Escape>", lambda event: self._close())
        self.after(10, self._activate)

    def _load_logo(self):
        path = resource_path("assets", "login_logo.png")
        try:
            image = Image.open(path)
            width = 420
            height = round(width * image.height / image.width)
            return ctk.CTkImage(light_image=image, size=(width, height))
        except Exception:
            return None

    def _entry(self, placeholder: str, hidden: bool = False) -> ctk.CTkEntry:
        entry = ctk.CTkEntry(
            self,
            width=280,
            height=36,
            corner_radius=6,
            fg_color=ENTRY_BG,
            border_width=0,
            text_color=theme.COLORS["text"],
            placeholder_text=placeholder,
            placeholder_text_color=PLACEHOLDER,
            font=(theme.FONT, 13),
            show="*" if hidden else "",
        )
        entry.bind("<Return>", lambda event: self._submit())
        return entry

    def _build(self) -> None:
        if self._logo is not None:
            logo = ctk.CTkLabel(self, image=self._logo, text="", fg_color=BG)
            logo.place(relx=0.5, rely=0.44, anchor="center")

        ctk.CTkLabel(
            self,
            text="Program by Saracho 🍺",
            font=(theme.FONT, 9, "italic"),
            text_color=FOOTER,
        ).pack(side="bottom", pady=(0, 10))

        if self.first_run:
            ctk.CTkLabel(
                self,
                text="Primera vez: creá el usuario administrador",
                font=(theme.FONT, 10),
                text_color="#A8A8A8",
            ).pack(pady=(64, 0))
            top = 12
        else:
            top = 118

        self.user_entry = self._entry("Usuario")
        self.user_entry.pack(pady=(top, 14))
        self.pass_entry = self._entry("Contraseña", hidden=True)
        self.pass_entry.pack(pady=(0, 14))

        self.confirm_entry = None
        if self.first_run:
            self.confirm_entry = self._entry("Confirmar contraseña", hidden=True)
            self.confirm_entry.pack(pady=(0, 18))

        ctk.CTkButton(
            self,
            text="Crear usuario y entrar" if self.first_run else "Iniciar Sesión",
            command=self._submit,
            width=245,
            height=36,
            corner_radius=6,
            fg_color=theme.COLORS["accent"],
            hover_color=theme.COLORS["accent_hover"],
            font=(theme.FONT, 13),
        ).pack(pady=(6, 0))

    def _activate(self) -> None:
        theme.center_window(self)
        self.deiconify()
        self.focus_set()

    def _submit(self) -> None:
        user = self.user_entry.get().strip()
        password = self.pass_entry.get()
        if not user or not password:
            messagebox.showwarning(
                "Login", "Completá usuario y contraseña.", parent=self
            )
            return
        if self.first_run:
            if password != self.confirm_entry.get():
                messagebox.showwarning(
                    "Login", "Las contraseñas no coinciden.", parent=self
                )
                return
            try:
                auth.create_user(user, password)
            except ValueError as error:
                messagebox.showerror("Login", str(error), parent=self)
                return
            self._finish(user)
            return
        if auth.verify(user, password):
            self._finish(user)
            return
        messagebox.showerror(
            "Login", "Usuario o contraseña incorrectos.", parent=self
        )
        self.pass_entry.delete(0, "end")
        self.pass_entry.focus_set()

    def _finish(self, user: str) -> None:
        try:
            self._main = MainWindow(self, user_name=user)
        except Exception as error:
            messagebox.showerror(
                "Login",
                "No se pudo iniciar el sistema:\n\n" + str(error),
                parent=self,
            )
            return
        self.authenticated = True
        self.username = user
        self.withdraw()

    def _close(self) -> None:
        self.authenticated = False
        self.destroy()
