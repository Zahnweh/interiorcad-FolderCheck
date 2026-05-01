"""
gui/app.py – natives macOS-Fenster
"""

import os
import sys
import tkinter as tk
from tkinter import ttk

from core.version import APP_VERSION
from .update_dialog import check_for_updates
from .widgets import apply_macos_style, StatusBar
from .tabs.ago_check_tab import AGOCheckTab
from .tabs.bno_check_tab import BNOCheckTab

APP_NAME    = "interiorcad FolderCheck"
APP_AUTHOR  = "Marcel Ostendorf"
APP_COMPANY = "extragroup GmbH"
WIN_WIDTH   = 860
WIN_HEIGHT  = 1050


def _resource_path(filename: str) -> str:
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.join(os.path.dirname(__file__), "..")
    return os.path.join(base, filename)


class _AboutDialog(tk.Toplevel):
    _W, _H = 360, 260

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        self.title(f"Über {APP_NAME}")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        px = parent.winfo_rootx() + (parent.winfo_width()  - self._W) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self._H) // 2
        self.geometry(f"{self._W}x{self._H}+{px}+{py}")

        self._icon_img = None
        self._build()
        self.bind("<Return>", lambda _: self.destroy())
        self.bind("<Escape>", lambda _: self.destroy())

    def _build(self) -> None:
        # Icon
        try:
            from PIL import Image, ImageTk
            img = Image.open(_resource_path("icon.png")).convert("RGBA")
            img = img.resize((72, 72), Image.LANCZOS)
            self._icon_img = ImageTk.PhotoImage(img)
            tk.Label(self, image=self._icon_img).pack(pady=(20, 6))
        except Exception:
            tk.Label(self, text="🖥", font=("Helvetica", 40)).pack(pady=(20, 6))

        tk.Label(
            self,
            text=APP_NAME,
            font=("Helvetica", 15, "bold"),
        ).pack()

        tk.Label(
            self,
            text=f"Version {APP_VERSION}",
            font=("Helvetica", 11),
        ).pack(pady=(2, 0))

        tk.Label(
            self,
            text=f"{APP_AUTHOR}  ·  © {APP_COMPANY}",
            font=("Helvetica", 10),
            fg="gray",
        ).pack(pady=(4, 0))

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=18)
        ttk.Button(
            btn_frame,
            text="Auf Updates prüfen …",
            command=self._check_updates,
        ).pack(side="left", padx=6)
        ttk.Button(
            btn_frame,
            text="Schließen",
            command=self.destroy,
        ).pack(side="left", padx=6)

    def _check_updates(self) -> None:
        self.destroy()
        check_for_updates(self.master)


class AnalyzerApp:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}")
        self.root.minsize(680, 550)

        # Fenster zentrieren
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - WIN_WIDTH) // 2
        y = (sh - WIN_HEIGHT) // 2
        self.root.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}+{x}+{y}")

        apply_macos_style(self.root)
        self._build_menu()
        self._build_ui()

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Auf macOS wird das erste Cascade-Menü zum App-Menü (unter dem Apple-Symbol)
        app_menu = tk.Menu(menubar, name="apple", tearoff=0)
        menubar.add_cascade(menu=app_menu)
        app_menu.add_command(
            label=f"Über {APP_NAME}",
            command=self._show_about,
        )
        app_menu.add_command(
            label="Auf Updates prüfen …",
            command=lambda: check_for_updates(self.root),
        )

    def _show_about(self):
        _AboutDialog(self.root)

    def _build_ui(self):
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(side="bottom", fill="x")

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=0, pady=0)

        self.tab_ago = AGOCheckTab(notebook, self.status_bar)
        notebook.add(self.tab_ago, text="AGO-Prüfung")

        self.tab_bno = BNOCheckTab(notebook, self.status_bar)
        notebook.add(self.tab_bno, text="BNO-Prüfung")

        # Statusleisten-Button startet Prüfung des aktiven Tabs
        def _run_active():
            idx = notebook.index(notebook.select())
            if idx == 0:
                self.tab_ago._run_check_threaded()
            else:
                self.tab_bno._run_check_threaded()

        self.status_bar.set_action(_run_active)
        self.root.after(200, self._refresh_all)

    def _refresh_all(self):
        self.tab_ago.refresh()
        self.tab_bno.refresh()

    def run(self):
        self.root.mainloop()
