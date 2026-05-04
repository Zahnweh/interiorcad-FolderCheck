"""
gui/app.py
"""

import os
import platform
import tkinter as tk
from tkinter import ttk

from core.version import APP_VERSION
from core.prefs import get_pref
from core.monitor import BackgroundMonitor
from core.notifier import notify
from .update_dialog import check_for_updates
from .settings_dialog import SettingsDialog
from .tray import TrayIcon
from .widgets import apply_platform_style, StatusBar
from .tabs.ago_check_tab import AGOCheckTab
from .tabs.bno_check_tab import BNOCheckTab

APP_NAME   = "interiorcad FolderCheck"
WIN_WIDTH  = 860
WIN_HEIGHT = 1050


class AnalyzerApp:

    def __init__(self, start_hidden: bool = False):
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}")
        self.root.minsize(680, 550)

        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x  = (sw - WIN_WIDTH)  // 2
        y  = (sh - WIN_HEIGHT) // 2
        self.root.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}+{x}+{y}")

        apply_platform_style(self.root)
        self._build_menu()
        self._build_ui()
        self._setup_monitor()
        self._setup_tray()

        # Fenster bei Autostart-Modus sofort verstecken
        if start_hidden:
            self.root.withdraw()

        # Dock-Klick auf macOS öffnet das Fenster wieder
        if platform.system() == "Darwin":
            self.root.createcommand(
                "::tk::mac::ReopenApplication", self._show_window
            )

        # Schließen-Button: verstecken statt beenden wenn Monitor aktiv
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Menü ──────────────────────────────────────────────────────────────

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
        if platform.system() == "Windows":
            hilfe_menu.add_separator()
            hilfe_menu.add_command(
                label="Einstellungen …",
                command=self._open_settings,
                accelerator="Ctrl+,",
            )

        # macOS: Preferences…-Eintrag im App-Menü aktivieren
        if platform.system() == "Darwin":
            self.root.createcommand(
                "::tk::mac::ShowPreferences", self._open_settings
            )

        self.root.bind("<Command-comma>", lambda _: self._open_settings())
        self.root.bind("<Control-comma>", lambda _: self._open_settings())

    # ── UI ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(side="bottom", fill="x")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self.tab_ago = AGOCheckTab(self.notebook, self.status_bar)
        self.notebook.add(self.tab_ago, text="AGO-Prüfung")

        self.tab_bno = BNOCheckTab(self.notebook, self.status_bar)
        self.notebook.add(self.tab_bno, text="BNO-Prüfung")

        def _run_active():
            idx = self.notebook.index(self.notebook.select())
            if idx == 0:
                self.tab_ago._run_check_threaded()
            else:
                self.tab_bno._run_check_threaded()

        self.status_bar.set_action(_run_active)
        self.root.after(200, self._refresh_all)
        self.root.after(3000, lambda: check_for_updates(self.root, silent=True))

    # ── Tray-Icon ─────────────────────────────────────────────────────────

    def _setup_tray(self) -> None:
        # Alle Callbacks müssen im Tk-Hauptthread laufen
        self._tray = TrayIcon(
            show_window_cb=lambda: self.root.after(50, self._show_window),
            run_once_cb=lambda: self.root.after(50, self._monitor.run_once),
            settings_cb=lambda: self.root.after(50, self._show_and_open_settings),
            quit_cb=lambda: os._exit(0),
            after_fn=self.root.after,
        )
        if get_pref("monitor_enabled", False):
            self._tray.start()

    # ── Hintergrund-Monitor ───────────────────────────────────────────────

    def _setup_monitor(self):
        self._monitor = BackgroundMonitor()
        self._monitor.add_callback(self._on_monitor_result)
        if get_pref("monitor_enabled", False):
            self._monitor.start()

    def _on_monitor_result(self, tab: str, count: int, results) -> None:
        label = "AGO" if tab == "ago" else "BNO"
        notify(
            title=APP_NAME,
            message=f"{count} Problem{'e' if count != 1 else ''} erkannt im {label}",
        )
        # Ergebnisse im UI-Thread anzeigen sobald Fenster sichtbar ist
        self.root.after(0, lambda: self._apply_background_results(tab, results))

    def _apply_background_results(self, tab: str, results) -> None:
        if tab == "ago":
            struct, names, folders, dupes = results
            self.tab_ago._show_results(struct, names, folders, dupes)
        else:
            struct, names, folders = results
            self.tab_bno._show_results(struct, names, folders)

    def _on_monitor_settings_change(self, enabled: bool, interval: int) -> None:
        if enabled:
            self._monitor.restart()
            self._tray.start()
        else:
            self._monitor.stop()
            self._tray.stop()

    # ── Einstellungen ─────────────────────────────────────────────────────

    def _open_settings(self) -> None:
        SettingsDialog(
            self.root,
            on_monitor_change=self._on_monitor_settings_change,
        )

    def _show_and_open_settings(self) -> None:
        self._show_window()
        self._open_settings()

    # ── Fenster-Lebenszyklus ──────────────────────────────────────────────

    def _on_close(self) -> None:
        if get_pref("monitor_enabled", False):
            self.root.withdraw()
        else:
            self._tray.stop()
            self.root.destroy()

    def _show_window(self) -> None:
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        # Letzte Ergebnisse sofort anzeigen falls vorhanden
        if self._monitor.last_ago_results:
            self._apply_background_results("ago", self._monitor.last_ago_results)
        if self._monitor.last_bno_results:
            self._apply_background_results("bno", self._monitor.last_bno_results)

    # ── Hilfsmethoden ─────────────────────────────────────────────────────

    def _refresh_all(self):
        self.tab_ago.refresh()
        self.tab_bno.refresh()

    def run(self):
        self.root.mainloop()
