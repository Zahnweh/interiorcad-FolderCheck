"""
gui/settings_dialog.py
Einstellungen-Dialog (Cmd+, / Menü → Einstellungen).
"""

import tkinter as tk
from tkinter import ttk, messagebox

from core.prefs import get_pref, set_pref
from core import autostart
from gui import theme as T
from gui.widgets import style_toplevel


class SettingsDialog(tk.Toplevel):

    def __init__(self, parent, on_monitor_change=None):
        super().__init__(parent)
        self.title("Einstellungen")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        style_toplevel(self)
        self._on_monitor_change = on_monitor_change

        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - 420) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - 280) // 2
        self.geometry(f"420x280+{px}+{py}")

        self._build()
        self._load()

    # ── UI ────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        outer = ttk.Frame(self, padding=T.PAD_L)
        outer.pack(fill="both", expand=True)

        # ── Hintergrund-Prüfung ───────────────────────────────────────────
        ttk.Label(outer, text="Hintergrund-Prüfung",
                  font=T.FONT_SMALL_B, foreground=T.FG_SEC).pack(anchor="w")
        ttk.Separator(outer, orient="horizontal").pack(fill="x", pady=(2, T.PAD_S))

        self._monitor_var = tk.BooleanVar()
        ttk.Checkbutton(
            outer,
            text="AGO/BNO regelmäßig im Hintergrund prüfen",
            variable=self._monitor_var,
            command=self._on_monitor_toggle,
        ).pack(anchor="w")

        interval_frame = ttk.Frame(outer)
        interval_frame.pack(anchor="w", padx=(T.PAD_L * 2, 0), pady=(T.PAD_XS, 0))
        ttk.Label(interval_frame, text="Intervall:").pack(side="left", padx=(0, T.PAD_M))

        self._interval_var = tk.IntVar(value=30)
        self._interval_btns = []
        for minutes in (15, 30, 60):
            rb = ttk.Radiobutton(
                interval_frame,
                text=f"{minutes} Min.",
                variable=self._interval_var,
                value=minutes,
            )
            rb.pack(side="left", padx=(0, T.PAD_S))
            self._interval_btns.append(rb)

        # ── Autostart ─────────────────────────────────────────────────────
        ttk.Frame(outer, height=T.PAD_M).pack()
        ttk.Label(outer, text="Autostart",
                  font=T.FONT_SMALL_B, foreground=T.FG_SEC).pack(anchor="w")
        ttk.Separator(outer, orient="horizontal").pack(fill="x", pady=(2, T.PAD_S))

        self._autostart_var = tk.BooleanVar()
        self._autostart_cb = ttk.Checkbutton(
            outer,
            text="Nach dem Login automatisch starten",
            variable=self._autostart_var,
        )
        self._autostart_cb.pack(anchor="w")

        # ── Buttons ───────────────────────────────────────────────────────
        btn_frame = ttk.Frame(outer)
        btn_frame.pack(side="bottom", anchor="e", pady=(T.PAD_L, 0))
        ttk.Button(btn_frame, text="Abbrechen", command=self.destroy).pack(
            side="left", padx=(0, T.PAD_S))
        ttk.Button(btn_frame, text="Speichern", command=self._save).pack(side="left")

        self._update_interval_state()

    # ── Logik ─────────────────────────────────────────────────────────────

    def _load(self) -> None:
        self._monitor_var.set(get_pref("monitor_enabled", False))
        self._interval_var.set(get_pref("monitor_interval", 30))
        self._autostart_var.set(autostart.is_enabled())
        self._update_interval_state()

    def _on_monitor_toggle(self) -> None:
        self._update_interval_state()
        if not self._monitor_var.get():
            self._autostart_var.set(False)

    def _update_interval_state(self) -> None:
        state = "normal" if self._monitor_var.get() else "disabled"
        for rb in self._interval_btns:
            rb.config(state=state)
        self._autostart_cb.config(
            state="normal" if self._monitor_var.get() else "disabled"
        )

    def _save(self) -> None:
        monitor_enabled = self._monitor_var.get()
        interval        = self._interval_var.get()
        autostart_on    = self._autostart_var.get() and monitor_enabled

        set_pref("monitor_enabled", monitor_enabled)
        set_pref("monitor_interval", interval)

        ok = autostart.set_enabled(autostart_on)
        if not ok and autostart_on:
            messagebox.showwarning(
                "Autostart",
                "Autostart konnte nicht eingerichtet werden.\n"
                "Bitte die App-Berechtigungen prüfen.",
                parent=self,
            )

        if self._on_monitor_change:
            self._on_monitor_change(monitor_enabled, interval)

        self.destroy()
