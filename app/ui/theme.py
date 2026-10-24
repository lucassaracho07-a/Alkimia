import sys
import tkinter.ttk as ttk

import customtkinter as ctk

from app.paths import resource_path

if sys.platform == "win32":
    ctk.CTk._deactivate_windows_window_header_manipulation = True
    ctk.CTkToplevel._deactivate_windows_window_header_manipulation = True

COLORS = {
    "bg": "#EFEFEF",
    "panel": "#E3E3E3",
    "panel_dark": "#D6D6D6",
    "sidebar": "#E8E8E8",
    "sidebar_group": "#DCDCDC",
    "accent": "#3E8ED0",
    "accent_hover": "#2F6FA8",
    "text": "#1B1B1B",
    "muted": "#5F5F5F",
    "white": "#FFFFFF",
    "border": "#BFBFBF",
    "danger": "#C0392B",
    "green": "#2E9E5B",
    "green_hover": "#26814A",
}

FONT = "Segoe UI"
TREE_STYLE = "Pos.Treeview"


def apply_window_icon(window) -> None:
    try:
        window.iconbitmap(str(resource_path("assets", "alkimia.ico")))
    except Exception:
        pass


def setup_tree_style(root) -> None:
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure(
        TREE_STYLE,
        background=COLORS["white"],
        fieldbackground=COLORS["white"],
        foreground=COLORS["text"],
        rowheight=24,
        borderwidth=0,
        font=(FONT, 9),
    )
    style.configure(
        f"{TREE_STYLE}.Heading",
        background="#E9E9E9",
        foreground=COLORS["text"],
        font=(FONT, 9),
        relief="flat",
        borderwidth=0,
    )
    style.map(f"{TREE_STYLE}.Heading", background=[("active", "#DCDCDC")])
    style.map(
        TREE_STYLE,
        background=[("selected", COLORS["accent"])],
        foreground=[("selected", "#FFFFFF")],
    )


def center_window(window, parent=None) -> None:
    withdrawn = window.state() == "withdrawn"
    if withdrawn:
        try:
            window.attributes("-alpha", 0.0)
        except Exception:
            pass
        window.deiconify()
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    if parent is not None:
        x = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
    else:
        x = (window.winfo_screenwidth() - width) // 2
        y = (window.winfo_screenheight() - height) // 2
    window.geometry(f"+{max(x, 0)}+{max(y, 0)}")
    if withdrawn:
        try:
            window.attributes("-alpha", 1.0)
        except Exception:
            pass
