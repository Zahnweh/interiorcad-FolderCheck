"""
gui/app.py – natives macOS-Fenster
"""

import tkinter as tk
from tkinter import ttk

from core.version import APP_VERSION  # noqa: F401 (für Info.plist-Pendant im Build)
from .update_dialog import check_for_updates
from .widgets import apply_platform_style, StatusBar
from .tabs.ago_check_tab import AGOCheckTab
from .tabs.bno_check_tab import BNOCheckTab

APP_NAME   = "interiorcad FolderCheck"
WIN_WIDTH  = 860
WIN_HEIGHT = 1050


class AnalyzerApp:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}")
        self.root.minsize(680, 550)

        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - WIN_WIDTH) // 2
        y = (sh - WIN_HEIGHT) // 2
        self.root.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}+{x}+{y}")

        apply_platform_style(self.root)
        self._build_menu()
        self._build_ui()

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        app_menu = tk.Menu(menubar, name="apple", tearoff=0)
        menubar.add_cascade(menu=app_menu)

        hilfe_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hilfe", menu=hilfe_menu)
        hilfe_menu.add_command(
            label="Auf Updates prüfen …",
            command=lambda: check_for_updates(self.root),
        )

    def _build_ui(self):
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(side="bottom", fill="x")

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=0, pady=0)

        self.tab_ago = AGOCheckTab(notebook, self.status_bar)
        notebook.add(self.tab_ago, text="AGO-Prüfung")

        self.tab_bno = BNOCheckTab(notebook, self.status_bar)
        notebook.add(self.tab_bno, text="BNO-Prüfung")

        def _run_active():
            idx = notebook.index(notebook.select())
            if idx == 0:
                self.tab_ago._run_check_threaded()
            else:
                self.tab_bno._run_check_threaded()

        self.status_bar.set_action(_run_active)
        self.root.after(200, self._refresh_all)
        self.root.after(3000, lambda: check_for_updates(self.root, silent=True))

    def _refresh_all(self):
        self.tab_ago.refresh()
        self.tab_bno.refresh()

    def run(self):
        self.root.mainloop()
