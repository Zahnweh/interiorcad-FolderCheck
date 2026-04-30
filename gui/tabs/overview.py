"""
gui/tabs/overview.py
Tab 1 – Übersicht: erkannte VW-Versionen, AGO/BNO-Pfade, Symlink-Status.
"""

import os
import tkinter as tk
from tkinter import ttk
import threading

from gui import theme as T
from gui.widgets import make_scrolled_tree, make_scrolled_text, SectionHeader, StatusBar
from core.detector import detect_all_installations, VWInstallation
from core.symlinks import analyze_path


class OverviewTab(tk.Frame):

    def __init__(self, parent, status_bar: StatusBar, **kw):
        super().__init__(parent, bg=T.BG_APP, **kw)
        self.status_bar = status_bar
        self.installations = []
        self._path_map = {}
        self._build_ui()

    def _build_ui(self):
        toolbar = tk.Frame(self, bg=T.BG_APP)
        toolbar.pack(fill="x", padx=T.PAD_L, pady=(T.PAD_L, T.PAD_S))
        tk.Label(toolbar, text="Installierte Vectorworks-Versionen",
                 bg=T.BG_APP, fg=T.FG_PRIMARY, font=T.FONT_HEADING,
                 ).pack(side="left")
        ttk.Button(toolbar, text="Erneut scannen",
                   style="Accent.TButton",
                   command=self._scan_threaded,
                   ).pack(side="right")

        SectionHeader(self, "VERSIONEN & PFADE").pack(
            fill="x", padx=T.PAD_L, pady=(T.PAD_S, T.PAD_XS))

        tree_frame, self.tree = make_scrolled_tree(
            self,
            columns=("type", "path", "status"),
            headings=("Typ", "Pfad", "Status"),
        )
        self.tree.column("#0",    width=160, stretch=False)
        self.tree.column("type",  width=80,  stretch=False)
        self.tree.column("path",  width=420)
        self.tree.column("status", width=120, stretch=False)
        tree_frame.pack(fill="both", expand=True, padx=T.PAD_L, pady=(0, T.PAD_S))

        SectionHeader(self, "SYMLINK-DETAIL").pack(
            fill="x", padx=T.PAD_L, pady=(T.PAD_S, T.PAD_XS))
        detail_frame, self.detail_text = make_scrolled_text(self, height=6)
        detail_frame.pack(fill="x", padx=T.PAD_L, pady=(0, T.PAD_L))

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _scan_threaded(self):
        self.status_bar.set("Scanne Installationen ...", "info")
        threading.Thread(target=self._run_scan, daemon=True).start()

    def _run_scan(self):
        installations = detect_all_installations()
        self.after(0, self._populate_tree, installations)

    def _populate_tree(self, installations):
        self.installations = installations
        self.tree.delete(*self.tree.get_children())
        self._path_map = {}

        if not installations:
            self.tree.insert("", "end", text="Keine VW-Installation gefunden",
                             values=("", "", ""))
            self.status_bar.set("Keine Installation gefunden", "warning")
            return

        for inst in installations:
            ver_id = self.tree.insert("", "end",
                text=f"Vectorworks {inst.version}",
                values=("Version", "", ""),
                tags=("version",), open=True,
            )
            self.tree.tag_configure("version",
                font=T.FONT_BODY_B, foreground=T.FG_PRIMARY)

            bno_path = inst.bno_path or "-"
            bno_status = self._path_status(inst.bno_path)
            bno_id = self.tree.insert(ver_id, "end",
                text="BNO (User)",
                values=("BNO", bno_path, bno_status[0]),
                tags=(bno_status[1],),
            )
            if inst.bno_path:
                self._path_map[bno_id] = inst.bno_path

            if inst.ago_paths:
                ago_parent = self.tree.insert(ver_id, "end",
                    text=f"AGO ({len(inst.ago_paths)})",
                    values=("AGO", "", ""), open=True,
                )
                for ago in inst.ago_paths:
                    status = self._path_status(ago)
                    item_id = self.tree.insert(ago_parent, "end",
                        text="",
                        values=("AGO", ago, status[0]),
                        tags=(status[1],),
                    )
                    self._path_map[item_id] = ago
            else:
                self.tree.insert(ver_id, "end",
                    text="Keine AGOs gefunden",
                    values=("AGO", "-", "-"),
                    tags=("muted",),
                )

        self.tree.tag_configure("ok",      foreground=T.SUCCESS)
        self.tree.tag_configure("warning", foreground=T.WARNING)
        self.tree.tag_configure("error",   foreground=T.ERROR)
        self.tree.tag_configure("muted",   foreground=T.FG_MUTED)

        total = sum(len(i.ago_paths) for i in installations)
        self.status_bar.set(
            f"{len(installations)} Version(en), {total} AGO(s) gefunden", "ok")

    def _path_status(self, path):
        if not path:
            return ("-", "muted")
        if not os.path.exists(path):
            return ("fehlt", "error")
        if os.path.islink(path):
            return ("Symlink", "warning")
        return ("OK", "ok")

    def _on_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        path = self._path_map.get(sel[0])
        if not path:
            return

        info = analyze_path(path)
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", "end")

        def w(text, tag=None):
            self.detail_text.insert("end", text, tag or "")

        w("Pfad:   ", "bold")
        w(info.path + "\n", "path")
        if info.is_symlink:
            w("Typ:    ", "bold")
            w("Symbolischer Link\n", "warning")
            w("Ziel:   ", "bold")
            w((info.real_path or "?") + "\n", "path")
            if len(info.chain) > 2:
                w("Kette:  ", "bold")
                w(" -> ".join(info.chain) + "\n", "mono")
        else:
            w("Typ:    ", "bold")
            w("Normaler Pfad\n")

        if info.broken:
            w("Status: ", "bold")
            w("Symlink zeigt auf nicht existierendes Ziel!\n", "error")
        elif not info.exists:
            w("Status: ", "bold")
            w("Pfad existiert nicht\n", "error")
        else:
            w("Status: ", "bold")
            w("Existiert\n", "ok")

        self.detail_text.config(state="disabled")

    def refresh(self):
        self._scan_threaded()
